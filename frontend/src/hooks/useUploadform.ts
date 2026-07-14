import { useState, type FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

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

    try {
      const data = await ExternalEndpoints.uploadFile(
        result.data.name,
        result.data.videoFile,
        result.data.textFile
      );
      setStatusMessage("Upload complete.");
      onSuccess?.(data);
    } catch (e) {
      setStatusMessage(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
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
  };
}
