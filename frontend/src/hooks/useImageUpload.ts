import { useRef, useState, useCallback } from "react";
import { ExternalEndpoints } from "../service/api";
import type { ImageClassificationResponse } from "../types/image";

export type ImageStatus = "empty" | "loading" | "error" | "success";

export function useImageUpload(onSuccess?: () => void) {
  const [status, setStatus] = useState<ImageStatus>("empty");
  const [result, setResult] = useState<ImageClassificationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const classify = useCallback(async (file: File) => {
    setStatus("loading");
    setErrorMessage("");
    setResult(null);

    const controller = new AbortController();
    abortRef.current = controller;

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    try {
      const data: ImageClassificationResponse =
        await ExternalEndpoints.classifyImage(file, controller.signal);
      setResult(data);
      setStatus("success");
      onSuccess?.();
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") {
        setErrorMessage("Classification was cancelled.");
      } else {
        setErrorMessage(e instanceof Error ? e.message : "Classification failed.");
      }
      setResult(null);
      setStatus("error");
    } finally {
      abortRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onSuccess is stable via useCallback in caller
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setResult(null);
    setErrorMessage("");
    setStatus("empty");
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  }, [previewUrl]);

  return {
    status,
    result,
    errorMessage,
    previewUrl,
    classify,
    cancel,
    reset,
  };
}
