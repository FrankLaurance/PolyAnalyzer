import { useCallback, useRef, useState } from "react";
import type { FileListMethod, SendRpcRequest } from "../types/rpc";

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function useAnalyzerFiles(sendRequest: SendRpcRequest, method: FileListMethod) {
  const requestSequence = useRef(0);
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [fileError, setFileError] = useState("");

  const clearFiles = useCallback(() => {
    requestSequence.current += 1;
    setFileList([]);
    setSelectedFiles([]);
    setFilesLoading(false);
    setFileError("");
  }, []);

  const loadFiles = useCallback(async (path: string) => {
    const sequence = ++requestSequence.current;
    setFileList([]);
    setSelectedFiles([]);
    setFileError("");

    if (!path.trim()) {
      setFilesLoading(false);
      return;
    }

    setFilesLoading(true);
    try {
      const response = await sendRequest(method, { datadir: path });
      if (sequence !== requestSequence.current) return;
      const files = response.files ?? [];
      setFileList(files);
      setSelectedFiles(files);
    } catch (error) {
      if (sequence !== requestSequence.current) return;
      setFileError(getErrorMessage(error));
    } finally {
      if (sequence === requestSequence.current) setFilesLoading(false);
    }
  }, [method, sendRequest]);

  return {
    fileList,
    selectedFiles,
    setSelectedFiles,
    filesLoading,
    fileError,
    clearFiles,
    loadFiles,
  };
}
