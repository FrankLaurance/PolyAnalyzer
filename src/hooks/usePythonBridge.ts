import { useCallback, useEffect, useState } from "react";
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

type SidecarChild = Awaited<ReturnType<Command<string>["spawn"]>>;

const progressListeners = new Set<(progress: ProgressInfo) => void>();
const connectionListeners = new Set<(connected: boolean) => void>();
const pendingRequests = new Map<number, PendingRequest>();

let sidecarChild: SidecarChild | null = null;
let spawnPromise: Promise<void> | null = null;
let requestId = 0;
let stdoutBuffer = "";
let lastProgressSnapshot: ProgressInfo = { progress: 0, message: "" };

function emitConnection(connected: boolean) {
  connectionListeners.forEach((listener) => listener(connected));
}

function emitProgress(progress: ProgressInfo) {
  lastProgressSnapshot = progress;
  progressListeners.forEach((listener) => listener(progress));
}

function rejectPending(reason: Error) {
  pendingRequests.forEach((pending) => pending.reject(reason));
  pendingRequests.clear();
}

function processLine(line: string) {
  const trimmed = line.trim();
  if (!trimmed) return;

  let msg: JsonRpcResponse;
  try {
    msg = JSON.parse(trimmed);
  } catch {
    return;
  }

  if (msg.id === undefined) {
    const params = (msg as unknown as { params?: ProgressInfo }).params;
    if (params) {
      emitProgress({
        progress: params.progress ?? 0,
        message: params.message ?? "",
      });
    }
    return;
  }

  const pending = pendingRequests.get(msg.id);
  if (!pending) return;
  pendingRequests.delete(msg.id);

  if (msg.error) {
    pending.reject(new Error(msg.error.message));
  } else {
    pending.resolve(msg.result);
  }
}

async function ensureSidecarSpawned() {
  if (sidecarChild) return;
  if (spawnPromise) return spawnPromise;

  const cmd = Command.sidecar("binaries/polyanalyzer-engine");

  cmd.stdout.on("data", (data: string) => {
    stdoutBuffer += data;
    const lines = stdoutBuffer.split("\n");
    stdoutBuffer = lines.pop() ?? "";
    lines.forEach(processLine);
  });

  cmd.stderr.on("data", (data: string) => {
    console.warn("[python-sidecar stderr]", data);
  });

  cmd.on("close", () => {
    sidecarChild = null;
    spawnPromise = null;
    stdoutBuffer = "";
    emitConnection(false);
    rejectPending(new Error("Sidecar process exited"));
  });

  cmd.on("error", (err: string) => {
    emitConnection(false);
    rejectPending(new Error(err));
  });

  spawnPromise = cmd.spawn()
    .then((child) => {
      sidecarChild = child;
      emitConnection(true);
    })
    .catch((err: unknown) => {
      sidecarChild = null;
      throw err;
    })
    .finally(() => {
      spawnPromise = null;
    });

  return spawnPromise;
}

async function sendJsonRpcRequest(method: string, params?: Record<string, unknown>) {
  await ensureSidecarSpawned();
  if (!sidecarChild) {
    throw new Error("Sidecar not connected");
  }

  const id = ++requestId;
  const request: JsonRpcRequest = {
    jsonrpc: "2.0",
    id,
    method,
    ...(params ? { params } : {}),
  };

  return new Promise((resolve, reject) => {
    pendingRequests.set(id, { resolve, reject });
    sidecarChild!.write(JSON.stringify(request) + "\n").catch((err: unknown) => {
      pendingRequests.delete(id);
      reject(err instanceof Error ? err : new Error(String(err)));
    });
  });
}

export function usePythonBridge() {
  const [isConnected, setIsConnected] = useState(Boolean(sidecarChild));
  const [lastProgress, setLastProgress] = useState<ProgressInfo>(lastProgressSnapshot);

  useEffect(() => {
    progressListeners.add(setLastProgress);
    connectionListeners.add(setIsConnected);
    return () => {
      progressListeners.delete(setLastProgress);
      connectionListeners.delete(setIsConnected);
    };
  }, []);

  const sendRequest = useCallback(
    (method: string, params?: Record<string, unknown>): Promise<unknown> =>
      sendJsonRpcRequest(method, params),
    [],
  );

  return { sendRequest, isConnected, lastProgress };
}
