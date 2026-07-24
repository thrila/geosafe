import { useMemo, useEffect } from "react";
import { formatFileSize } from "../helpers/helper_functions";
import { useUploadForm } from "../hooks/useUploadform";

type Props = {
  form: ReturnType<typeof useUploadForm>;
};

export function UploadForm({ form }: Props) {
  const previewUrl = useMemo(
    () => (form.videoFile ? URL.createObjectURL(form.videoFile) : null),
    [form.videoFile],
  );

  useEffect(() => {
    if (!previewUrl) return;
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  return (
    <section className="floating-panel" aria-label="Upload media panel">


      <form className="upload-form" onSubmit={form.handleSubmit}>
        {/* Name */}
        <label className="field">
          <span className="field-label">Name</span>

          <input
            type="text"
            value={form.name}
            onChange={(event) => form.setName(event.target.value)}
            placeholder="Enter a name"
            className="text-input"
          />

          {form.errors.name && (
            <span className="field-error">{form.errors.name}</span>
          )}
        </label>

        {/* Video */}
        <label className="field">
          <span className="field-label">Video (.mp4, .mkv)</span>
          {previewUrl && (
            <video controls
              width="100%"
              preload="metadata"
              autoPlay
              muted
              playsInline
              disablePictureInPicture
              controlsList="nodownload noremoteplayback noplaybackrate"
            >
              <source src={previewUrl} />
              Your browser does not support video playback.
            </video>
          )}
          <input
            type="file"
            accept="video/*"
            className="file-input"
            onChange={(event) =>
              form.setVideoFile(event.target.files?.[0] ?? null)
            }
          />

          <span className="field-help">
            {form.videoFile ? (
              <span className="field-help-row">
                <span className="field-filename">
                  {form.videoFile.name}
                </span>
                <span className="numeric">
                  ({formatFileSize(form.videoFile.size)})
                </span>
              </span>
            ) : null}
          </span>

          {form.errors.videoFile && (
            <span className="field-error">{form.errors.videoFile}</span>
          )}
        </label>

        {/* Text file */}
        <label className="field">
          <span className="field-label">Text file (.txt)</span>

          <input
            type="file"
            accept=".txt,text/plain"
            className="file-input"
            onChange={(event) =>
              form.setTextFile(event.target.files?.[0] ?? null)
            }
          />

          <span className="field-help">
            {form.textFile ? (
              <span className="field-help-row">
                <span className="field-filename">
                  {form.textFile.name}
                </span>
                <span className="numeric">
                  ({formatFileSize(form.textFile.size)})
                </span>
              </span>
            ) : null}
          </span>

          {form.errors.textFile && (
            <span className="field-error">{form.errors.textFile}</span>
          )}
        </label>

        {form.statusMessage && (
          <p className="status-message">{form.statusMessage}</p>
        )}

        <div className="panel-actions">
          <button
            type="submit"
            className="submit-button"
            disabled={form.isUploading}
          >
            {form.isUploading ? "Uploading…" : "Upload package"}
          </button>
          {form.isUploading && (
            <button
              type="button"
              className="submit-button"
              onClick={form.cancelUpload}
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
