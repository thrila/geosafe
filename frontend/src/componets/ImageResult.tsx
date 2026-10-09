import { AlertTriangle, CheckCircle } from "react-feather";
import type { ImageClassificationResponse } from "../types/image";
import type { ImageStatus } from "../hooks/useImageUpload";
import { resolveApiUrl } from "../service/api";

type Props = {
  status: ImageStatus;
  result: ImageClassificationResponse | null;
  previewUrl: string | null;
  errorMessage: string;
  onClassifyAnother?: () => void;
};

export function ImageResult({ status, result, previewUrl, errorMessage, onClassifyAnother }: Props) {
  const disease = result?.prediction.disease.toLowerCase() ?? "";
  const isHealthy = disease === "healthy" || disease === "not detected";
  const hasPlant = result?.prediction.plant_type !== "not detected";
  const affectedTiles = result?.tiles.filter((tile) => {
    const label = tile.prediction.disease.toLowerCase();
    return label !== "healthy" && label !== "not detected";
  }) ?? [];

  return (
    <aside className="image-results" aria-label="Image classification results">

      {/* ── Loading ── */}
      {status === "loading" && (
        <div className="image-result-section">
          <div className="image-preview-skeleton" />
          <div className="results-grid">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="results-item">
                <span className="skeleton-label" style={{ animationDelay: `${i * 0.07}s` }} />
                <span className="skeleton-value" style={{ animationDelay: `${i * 0.07 + 0.04}s` }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Empty ── */}
      {status === "empty" && (
        <div className="image-empty-state">
          <p className="image-empty-text">
            Select an image to classify plant type and disease.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {status === "error" && (
        <div className="image-error-state">
          <div className="image-error-icon">
            <AlertTriangle size={18} />
          </div>
          <p className="image-error-text">{errorMessage}</p>
        </div>
      )}

      {/* ── Success ── */}
      {status === "success" && result && (
        <>
          {/* Preview image */}
          {previewUrl && (
            <div className="image-result-section">
              <div className="image-preview-wrap">
                <img
                  src={previewUrl}
                  alt={result.filename}
                  className="image-preview"
                />
                <span className="image-preview-name">{result.filename}</span>
              </div>
            </div>
          )}

          {/* Affected-area heatmap */}
          {result.image_url && (
            <section className="image-result-section image-heatmap-panel">
              <div className="image-heatmap-title-row">
                <span className="image-result-heading">Model-highlighted tiles</span>
                <span className="image-heatmap-count">
                  {affectedTiles.length} of {result.tiles.length} tiles flagged
                </span>
              </div>
              <div className="image-heatmap-frame">
                <img
                  src={resolveApiUrl(result.image_url)}
                  alt={`Annotated image showing ${affectedTiles.length} model-flagged tiles`}
                  className="image-heatmap-image"
                  decoding="async"
                />
              </div>
              <div className="image-heatmap-legend">
                <span className="image-heatmap-swatch" aria-hidden="true" />
                <span>Highlighted tile classified as {result.prediction.disease}</span>
              </div>
              <p className="image-heatmap-note">
                Warmth and the printed score reflect the raw model score, not disease severity. The overlay marks whole tiles, not disease pixels or individual plants.
              </p>
            </section>
          )}

          {/* Prediction cards */}
          <div className="image-result-section">
            <span className="image-result-heading">Classification</span>
            <div className="results-grid">
              <div className="results-item">
                <span className="results-label">Plant type</span>
                <span className={`results-value ${!hasPlant ? "results-value--muted" : ""}`}>
                  {result.prediction.plant_type}
                </span>
              </div>
              {hasPlant && (
                <>
                  <div className="results-item">
                    <span className="results-label">Plant model score</span>
                    <span className="results-value numeric">
                      {(result.prediction.plant_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="results-item">
                    <span className="results-label">Disease</span>
                    <span className={`results-value results-value--badge ${isHealthy ? "badge--ok" : "badge--warn"}`}>
                      {isHealthy
                        ? <><CheckCircle size={9} />Healthy</>
                        : <><AlertTriangle size={9} />{result.prediction.disease}</>
                      }
                    </span>
                  </div>
                  <div className="results-item">
                    <span className="results-label">Disease model score</span>
                    <span className="results-value numeric">
                      {(result.prediction.disease_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Tile breakdown */}
          {result.tiles.length > 1 && (() => {
            const detectableTiles = result.tiles.filter(
              (t) => t.prediction.plant_type !== "not detected"
            ).sort((a, b) => {
              const aAffected = a.prediction.disease.toLowerCase() !== "healthy";
              const bAffected = b.prediction.disease.toLowerCase() !== "healthy";
              return Number(bAffected) - Number(aAffected) ||
                b.prediction.disease_confidence - a.prediction.disease_confidence;
            });
            if (detectableTiles.length === 0) return null;
            return (
              <div className="image-result-section">
                <span className="image-result-heading">
                  Tile findings ({affectedTiles.length} flagged / {result.tiles.length} tiles)
                </span>
                <div className="image-tile-list">
                  {detectableTiles.map((t) => {
                    const tileHealthy = t.prediction.disease.toLowerCase() === "healthy";
                    return (
                      <div key={t.tile} className="image-tile-row">
                        <span className="image-tile-index">
                          {String(t.tile).padStart(2, "0")}
                        </span>
                        <span className="image-tile-plant">{t.prediction.plant_type}</span>
                        <span className="image-tile-coordinates">
                          x{t.region.x}, y{t.region.y}
                        </span>
                        <span className={`image-tile-disease ${tileHealthy ? "" : "image-tile-disease--warn"}`}>
                          {t.prediction.disease}
                        </span>
                        <span className="image-tile-conf numeric">
                          {(t.prediction.disease_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* Back to upload */}
          {onClassifyAnother && (
            <div className="image-result-section" style={{ paddingTop: "0.2rem" }}>
              <button
                type="button"
                className="submit-button"
                onClick={onClassifyAnother}
              >
                Classify another image
              </button>
            </div>
          )}
        </>
      )}
    </aside>
  );
}
