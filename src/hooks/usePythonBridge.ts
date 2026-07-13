import { useCallback, useEffect, useState } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import { createSerialQueue } from "../core/serialQueue";
import type {
  AnalyzerName,
  RpcMethod,
  RpcParams,
  RpcResult,
  SendRpcRequest,
} from "../types/rpc";

export type BridgeAnalyzer = AnalyzerName;

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: number;
  method?: string;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
  params?: ProgressParams;
}

interface ProgressParams {
  analyzer?: BridgeAnalyzer;
  request_id?: number;
  progress: number;
  message: string;
}

export interface ProgressInfo {
  analyzer: BridgeAnalyzer;
  requestId?: number;
  progress: number;
  message: string;
}

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (reason: Error) => void;
  analyzer: BridgeAnalyzer;
  method: string;
  timeout: ReturnType<typeof setTimeout>;
}

type SidecarChild = Awaited<ReturnType<Command<string>["spawn"]>>;

const progressListeners = new Map<BridgeAnalyzer, Set<(progress: ProgressInfo) => void>>();
const connectionListeners = new Set<(connected: boolean) => void>();
const pendingRequests = new Map<number, PendingRequest>();

let sidecarChild: SidecarChild | null = null;
let spawnPromise: Promise<void> | null = null;
let sidecarGeneration = 0;
let requestId = 0;
let stdoutBuffer = "";
const requestQueue = createSerialQueue();
const lastProgressSnapshots = new Map<BridgeAnalyzer, ProgressInfo>();

const SHORT_REQUEST_TIMEOUT_MS = 30_000;
const ANALYZE_REQUEST_TIMEOUT_MS = 5 * 60_000;

function emitConnection(connected: boolean) {
  connectionListeners.forEach((listener) => listener(connected));
}

function emitProgress(analyzer: BridgeAnalyzer, progress: ProgressInfo) {
  lastProgressSnapshots.set(analyzer, progress);
  progressListeners.get(analyzer)?.forEach((listener) => listener(progress));
}

function rejectPending(reason: Error) {
  pendingRequests.forEach((pending) => {
    clearTimeout(pending.timeout);
    pending.reject(reason);
  });
  pendingRequests.clear();
}

function clearSidecarState(generation: number, reason: Error) {
  if (generation !== sidecarGeneration) return;
  sidecarGeneration += 1;
  sidecarChild = null;
  spawnPromise = null;
  stdoutBuffer = "";
  emitConnection(false);
  rejectPending(reason);
}

async function resetSidecar(reason: Error) {
  const child = sidecarChild;
  sidecarGeneration += 1;
  sidecarChild = null;
  spawnPromise = null;
  stdoutBuffer = "";
  emitConnection(false);
  rejectPending(reason);
  if (child) {
    try {
      await child.kill();
    } catch {
      // The process may already have exited.
    }
  }
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
    if (msg.method !== "progress" || !msg.params) return;

    const params = msg.params;
    const matchedRequest = params.request_id === undefined
      ? undefined
      : pendingRequests.get(params.request_id);
    if (params.request_id !== undefined && !matchedRequest) return;
    if (params.analyzer && matchedRequest && params.analyzer !== matchedRequest.analyzer) return;

    let analyzer = params.analyzer ?? matchedRequest?.analyzer;
    let matchedRequestId = params.request_id;

    // Compatibility with sidecars that predate analyzer/request_id progress metadata.
    if (!analyzer) {
      const activeAnalyses = [...pendingRequests.entries()].filter(([, pending]) =>
        pending.method.endsWith(".analyze"),
      );
      if (activeAnalyses.length !== 1) return;
      matchedRequestId = activeAnalyses[0][0];
      analyzer = activeAnalyses[0][1].analyzer;
    }

    emitProgress(analyzer, {
      analyzer,
      requestId: matchedRequestId,
      progress: params.progress ?? 0,
      message: params.message ?? "",
    });
    return;
  }

  const pending = pendingRequests.get(msg.id);
  if (!pending) return;
  pendingRequests.delete(msg.id);
  clearTimeout(pending.timeout);

  if (msg.error) {
    pending.reject(new Error(msg.error.message));
  } else {
    pending.resolve(msg.result);
  }
}

async function ensureSidecarSpawned() {
  if (sidecarChild) return;
  if (spawnPromise) return spawnPromise;

  const generation = ++sidecarGeneration;
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
    clearSidecarState(generation, new Error("Sidecar process exited"));
  });

  cmd.on("error", (err: string) => {
    clearSidecarState(generation, new Error(err));
  });

  spawnPromise = cmd.spawn()
    .then((child) => {
      if (generation !== sidecarGeneration) {
        void child.kill();
        throw new Error("Sidecar spawn was superseded");
      }
      sidecarChild = child;
      emitConnection(true);
    })
    .catch((err: unknown) => {
      if (generation === sidecarGeneration) {
        sidecarChild = null;
        emitConnection(false);
      }
      throw err;
    })
    .finally(() => {
      if (generation === sidecarGeneration) spawnPromise = null;
    });

  return spawnPromise;
}

async function performJsonRpcRequest<M extends RpcMethod>(
  analyzer: BridgeAnalyzer,
  method: M,
  params: RpcParams<M>,
): Promise<RpcResult<M>> {
  await ensureSidecarSpawned();
  if (!sidecarChild) {
    throw new Error("Sidecar not connected");
  }

  const id = ++requestId;
  const request: JsonRpcRequest = {
    jsonrpc: "2.0",
    id,
    method,
    params: {
      ...(params ?? {}),
      analyzer,
      request_id: id,
    },
  };

  if (method.endsWith(".analyze")) {
    emitProgress(analyzer, { analyzer, requestId: id, progress: 0, message: "" });
  }

  return new Promise<RpcResult<M>>((resolve, reject) => {
    const timeoutMs = method.endsWith(".analyze")
      ? ANALYZE_REQUEST_TIMEOUT_MS
      : SHORT_REQUEST_TIMEOUT_MS;
    const timeout = setTimeout(() => {
      const pending = pendingRequests.get(id);
      if (!pending) return;
      pendingRequests.delete(id);
      const error = new Error(`${method} timed out after ${Math.round(timeoutMs / 1000)}s`);
      pending.reject(error);
      void resetSidecar(error);
    }, timeoutMs);

    pendingRequests.set(id, {
      resolve: (value) => resolve(value as RpcResult<M>),
      reject,
      analyzer,
      method,
      timeout,
    });
    sidecarChild!.write(JSON.stringify(request) + "\n").catch((err: unknown) => {
      clearTimeout(timeout);
      pendingRequests.delete(id);
      const error = err instanceof Error ? err : new Error(String(err));
      reject(error);
      void resetSidecar(error);
    });
  });
}

function sendJsonRpcRequest<M extends RpcMethod>(
  analyzer: BridgeAnalyzer,
  method: M,
  params: RpcParams<M>,
): Promise<RpcResult<M>> {
  return requestQueue.run(() => performJsonRpcRequest(analyzer, method, params));
}

export function usePythonBridge(analyzer: BridgeAnalyzer) {
  const [isConnected, setIsConnected] = useState(Boolean(sidecarChild));
  const [lastProgress, setLastProgress] = useState<ProgressInfo>(
    () => lastProgressSnapshots.get(analyzer) ?? { analyzer, progress: 0, message: "" },
  );

  useEffect(() => {
    const listeners = progressListeners.get(analyzer) ?? new Set();
    listeners.add(setLastProgress);
    progressListeners.set(analyzer, listeners);
    setLastProgress(
      lastProgressSnapshots.get(analyzer) ?? { analyzer, progress: 0, message: "" },
    );
    connectionListeners.add(setIsConnected);
    return () => {
      const currentListeners = progressListeners.get(analyzer);
      currentListeners?.delete(setLastProgress);
      if (currentListeners?.size === 0) progressListeners.delete(analyzer);
      connectionListeners.delete(setIsConnected);
    };
  }, [analyzer]);

  const sendRequest = useCallback<SendRpcRequest>(
    (method, params) => sendJsonRpcRequest(analyzer, method, params),
    [analyzer],
  );

  return { sendRequest, isConnected, lastProgress };
}
