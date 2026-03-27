import { useCallback, useEffect, useRef, useState } from "react";
import { Command } from "@tauri-apps/plugin-shell";

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: number;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

interface ProgressInfo {
  progress: number;
  message: string;
}

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (reason: Error) => void;
}

export function usePythonBridge() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastProgress, setLastProgress] = useState<ProgressInfo>({
    progress: 0,
    message: "",
  });

  const childRef = useRef<Awaited<ReturnType<Command<string>["spawn"]>> | null>(null);
  const requestIdRef = useRef(0);
  const pendingRef = useRef<Map<number, PendingRequest>>(new Map());
  const bufferRef = useRef("");
  const spawnedRef = useRef(false);

  const processLine = useCallback((line: string) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    let msg: JsonRpcResponse;
    try {
      msg = JSON.parse(trimmed);
    } catch {
      return;
    }

    // Progress notification (no id)
    if (msg.id === undefined) {
      const params = (msg as unknown as { params?: ProgressInfo }).params;
      if (params) {
        setLastProgress({
          progress: params.progress ?? 0,
          message: params.message ?? "",
        });
      }
      return;
    }

    const pending = pendingRef.current.get(msg.id);
    if (!pending) return;
    pendingRef.current.delete(msg.id);

    if (msg.error) {
      pending.reject(new Error(msg.error.message));
    } else {
      pending.resolve(msg.result);
    }
  }, []);

  const ensureSpawned = useCallback(async () => {
    if (spawnedRef.current && childRef.current) return;
    spawnedRef.current = true;

    const cmd = Command.sidecar("binaries/python-sidecar");

    cmd.stdout.on("data", (data: string) => {
      bufferRef.current += data;
      const lines = bufferRef.current.split("\n");
      bufferRef.current = lines.pop() ?? "";
      lines.forEach(processLine);
    });

    cmd.stderr.on("data", (data: string) => {
      console.warn("[python-sidecar stderr]", data);
    });

    cmd.on("close", () => {
      setIsConnected(false);
      childRef.current = null;
      spawnedRef.current = false;
      // Reject all pending requests
      pendingRef.current.forEach((p) =>
        p.reject(new Error("Sidecar process exited")),
      );
      pendingRef.current.clear();
    });

    cmd.on("error", (err: string) => {
      console.error("[python-sidecar error]", err);
      setIsConnected(false);
    });

    childRef.current = await cmd.spawn();
    setIsConnected(true);
  }, [processLine]);

  const sendRequest = useCallback(
    async (method: string, params?: Record<string, unknown>): Promise<unknown> => {
      await ensureSpawned();
      if (!childRef.current) {
        throw new Error("Sidecar not connected");
      }

      const id = ++requestIdRef.current;
      const request: JsonRpcRequest = {
        jsonrpc: "2.0",
        id,
        method,
        ...(params ? { params } : {}),
      };

      return new Promise((resolve, reject) => {
        pendingRef.current.set(id, { resolve, reject });
        childRef.current!.write(JSON.stringify(request) + "\n").catch(reject);
      });
    },
    [ensureSpawned],
  );

  useEffect(() => {
    return () => {
      if (childRef.current) {
        childRef.current.kill().catch(() => {});
      }
    };
  }, []);

  return { sendRequest, isConnected, lastProgress };
}
