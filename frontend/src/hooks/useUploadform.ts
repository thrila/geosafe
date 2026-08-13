import { useRef, useState, type FormEvent } from "react";
import { uploadSchema } from "../form_schema/upload_schema";
import { ExternalEndpoints } from "../service/api";
import { z } from "zod";

type UploadForm = z.infer<typeof uploadSchema>;
type UploadErrors = Partial<Record<keyof UploadForm, string>>;

export function useUploadForm(onSuccess?: (data: unknown) => void) {
  const [name, setName] = useState("");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [textFile, setTextFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<UploadErrors>({});
  const [statusMessage, setStatusMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (isUploading) return;

    const result = uploadSchema.safeParse({
      name,
      videoFile,
      textFile,
    });

    if (!result.success) {
      const fieldErrors = result.error.flatten().fieldErrors;

      setErrors({
        name: fieldErrors.name?.[0],
        videoFile: fieldErrors.videoFile?.[0],
        textFile: fieldErrors.textFile?.[0],
      });

      return;
    }

    setErrors({});
    setStatusMessage(`Uploading "${result.data.name}"...`);
    setIsUploading(true);

    const controller = new AbortController();
    abortRef.current = controller;
    const timeout = setTimeout(() => controller.abort(), 60 * 60 * 1000);

    try {
      const job = await ExternalEndpoints.createUploadJob(
        result.data.name,
        result.data.videoFile,
        result.data.textFile,
        controller.signal,
      );
      setStatusMessage("Upload saved. Waiting for analysis…");
      const data = await waitForUploadJob(job.id, controller.signal, setStatusMessage);
      setStatusMessage("Upload complete.");
      onSuccess?.(data);
    } catch (e) {
      if (controller.signal.aborted) {
        setStatusMessage("Upload wait cancelled. A queued analysis will continue on the server.");
      } else {
        setStatusMessage(e instanceof Error ? e.message : "Upload failed.");
      }
    } finally {
      clearTimeout(timeout);
      abortRef.current = null;
      setIsUploading(false);
    }
  }

  function cancelUpload() {
    abortRef.current?.abort();
  }

  return {
    name,
    setName,
    videoFile,
    setVideoFile,
    textFile,
    setTextFile,
    errors,
    statusMessage,
    isUploading,
    handleSubmit,
    cancelUpload,
  };
}

async function waitForUploadJob(
  jobId: string,
  signal: AbortSignal,
  onStatus: (message: string) => void,
): Promise<unknown> {
  while (true) {
    const job = await ExternalEndpoints.getUploadJob(jobId, signal);
    if (job.status === "completed") return job.result;
    if (job.status === "failed") throw new Error(job.error || "Flight analysis failed.");
    onStatus(job.status === "queued" ? "Upload saved. Waiting for an available worker…" : "Analyzing flight video…");
    await waitForPollInterval(signal);
  }
}

function waitForPollInterval(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(resolve, 2000);
    signal.addEventListener("abort", () => {
      window.clearTimeout(timer);
      reject(new DOMException("Upload polling was cancelled.", "AbortError"));
    }, { once: true });
  });
}
