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
        <div className="field">
          <label className="field-label" htmlFor="flight-name">
            Name
          </label>

          <input
            id="flight-name"
            name="name"
            type="text"
            value={form.name}
            onChange={(event) => form.setName(event.target.value)}
            placeholder="Enter a name, e.g. Otuoke survey 01…"
            className="text-input"
            autoComplete="off"
            aria-invalid={form.errors.name ? true : undefined}
            aria-describedby={form.errors.name ? "flight-name-error" : undefined}
          />

          {form.errors.name && (
            <span className="field-error" id="flight-name-error" role="alert">
              {form.errors.name}
            </span>
          )}
        </div>

        {/* Video */}
        <div className="field">
          <label className="field-label" htmlFor="flight-video">
            Video (.mp4, .mkv)
          </label>
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
            id="flight-video"
            name="video"
            type="file"
            accept="video/*"
            className="file-input"
            autoComplete="off"
            aria-invalid={form.errors.videoFile ? true : undefined}
            aria-describedby={
              form.errors.videoFile ? "flight-video-error" : undefined
            }
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
            <span className="field-error" id="flight-video-error" role="alert">
              {form.errors.videoFile}
            </span>
          )}
        </div>

        {/* Text file */}
        <div className="field">
          <label className="field-label" htmlFor="flight-log">
            Text file (.txt)
          </label>

          <input
            id="flight-log"
            name="log"
            type="file"
            accept=".txt,text/plain"
            className="file-input"
            autoComplete="off"
            aria-invalid={form.errors.textFile ? true : undefined}
            aria-describedby={
              form.errors.textFile ? "flight-log-error" : undefined
            }
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
            <span className="field-error" id="flight-log-error" role="alert">
              {form.errors.textFile}
            </span>
          )}
        </div>

        {form.statusMessage && (
          <p className="status-message" role="status">
            {form.statusMessage}
          </p>
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
              Stop waiting
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
