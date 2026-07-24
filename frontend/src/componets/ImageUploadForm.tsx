import { useMemo } from "react";
import { formatFileSize } from "../helpers/helper_functions";
import type { ImageStatus } from "../hooks/useImageUpload";

type Props = {
  imageFile: File | null;
  setImageFile: (file: File | null) => void;
  status: ImageStatus;
  errorMessage: string;
  onSubmit: (file: File) => void;
  onCancel: () => void;
  onReset: () => void;
  errors: { imageFile?: string };
};

export function ImageUploadForm({
  imageFile,
  setImageFile,
  status,
  errorMessage,
  onSubmit,
  onCancel,
  onReset,
  errors,
}: Props) {
  const isBusy = status === "loading";

  const previewUrl = useMemo(
    () => (imageFile ? URL.createObjectURL(imageFile) : null),
    [imageFile],
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageFile || isBusy) return;
    onSubmit(imageFile);
  }

  return (
    <section className="floating-panel" aria-label="Image classification panel">
      <form className="upload-form" onSubmit={handleSubmit}>
        {/* Image file */}
        <label className="field">
          <span className="field-label">Image (.jpg, .png, .webp)</span>

          {previewUrl && (
            <div className="image-preview-field">
              <img
                src={previewUrl}
                alt="Selected image preview"
                className="image-preview-field-img"
              />
              <span className="field-help-row">
                <span className="field-filename">{imageFile!.name}</span>
                <span className="numeric">({formatFileSize(imageFile!.size)})</span>
              </span>
            </div>
          )}

          {!previewUrl && (
            <input
              type="file"
              accept="image/*,.jpg,.jpeg,.png,.webp"
              className="file-input"
              disabled={isBusy}
              onChange={(e) => {
                const file = e.target.files?.[0] ?? null;
                setImageFile(file);
              }}
            />
          )}

          {previewUrl && !isBusy && (
            <button
              type="button"
              className="submit-button submit-button--subtle"
              onClick={() => setImageFile(null)}
            >
              Choose different image
            </button>
          )}

          {errors.imageFile && (
            <span className="field-error">{errors.imageFile}</span>
          )}
        </label>

        {/* Status feedback */}
        {status === "error" && (
          <p className="status-message status-message--error">{errorMessage}</p>
        )}

        <div className="panel-actions">
          {(status === "empty" || status === "error") && (
            <button
              type="submit"
              className="submit-button"
              disabled={!imageFile}
            >
              Classify
            </button>
          )}

          {status === "loading" && (
            <>
              <button
                type="button"
                className="submit-button"
                disabled
              >
                Classifying…
              </button>
              <button
                type="button"
                className="submit-button"
                onClick={onCancel}
              >
                Cancel
              </button>
            </>
          )}

          {status === "success" && (
            <button
              type="button"
              className="submit-button"
              onClick={onReset}
            >
              New image
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
