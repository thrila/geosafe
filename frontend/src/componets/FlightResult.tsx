import { useState } from "react";
import { ChevronLeft, ChevronRight, AlertTriangle, CheckCircle } from "react-feather";
import { formatCoordinate } from "../helpers/helper_functions";
import type { FlightResultProps, FlightSlide } from "../types/result";

interface Props extends FlightResultProps {
  slides?: FlightSlide[];
  isLoading?: boolean;
}

export const FlightResult = ({
  routeDistanceKm,
  startPoint,
  endPoint,
  batteryDrainedPct,
  maxSpeedMs,
  maxHeightM,
  batteryTempC,
  diseasesDetected,
  slides = [],
  isLoading = false,
}: Props) => {
  const [idx, setIdx] = useState(0);
  const total = slides.length;
  const prev = () => setIdx((i) => (i - 1 + total) % total);
  const next = () => setIdx((i) => (i + 1) % total);
  const current = slides[idx];
  const hasSlides = total > 0;
  const hasDisease = diseasesDetected.length > 0;

  return (
    <aside className="flight-results" aria-label="Flight path results">

      {/* ── Stats grid ── */}
      {isLoading ? (
        <div className="results-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="results-item">
              <span className="skeleton-label" style={{ animationDelay: `${i * 0.07}s` }} />
              <span className="skeleton-value" style={{ animationDelay: `${i * 0.07 + 0.04}s` }} />
            </div>
          ))}
        </div>
      ) : (
        <div className="results-grid">
          <div className="results-item">
            <span className="results-label">Distance</span>
            <span className="results-value numeric">{routeDistanceKm.toFixed(2)} km</span>
          </div>
          <div className="results-item">
            <span className="results-label">Start</span>
            <span className="results-value numeric">
              {startPoint ? formatCoordinate(startPoint) : "—"}
            </span>
          </div>
          <div className="results-item">
            <span className="results-label">Stop</span>
            <span className="results-value numeric">
              {endPoint ? formatCoordinate(endPoint) : "—"}
            </span>
          </div>
          <div className="results-item">
            <span className="results-label">Battery used</span>
            <span className="results-value numeric">{batteryDrainedPct}%</span>
          </div>
          <div className="results-item">
            <span className="results-label">Max speed</span>
            <span className="results-value numeric">{maxSpeedMs.toFixed(1)} m/s</span>
          </div>
          <div className="results-item">
            <span className="results-label">Max height</span>
            <span className="results-value numeric">{maxHeightM.toFixed(0)} m</span>
          </div>
          <div className="results-item">
            <span className="results-label">Battery temp</span>
            <span className="results-value numeric">{batteryTempC}°C</span>
          </div>
          <div className="results-item">
            <span className="results-label">Diseases</span>
            <span className={`results-value results-value--badge ${hasDisease ? "badge--warn" : "badge--ok"}`}>
              {hasDisease
                ? <><AlertTriangle size={9} />{diseasesDetected.length} found</>
                : <><CheckCircle size={9} />Clean</>
              }
            </span>
          </div>
        </div>
      )}

      {/* ── Disease table ── */}
      {isLoading ? (
        <div className="disease-table-skeleton">
          <span className="skeleton-label" style={{ width: "38%", animationDelay: "0.1s" }} />
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="skeleton-disease-row" style={{ animationDelay: `${0.15 + i * 0.08}s` }} />
          ))}
        </div>
      ) : hasDisease ? (
        <div className="disease-table">
          <span className="disease-table__heading">Detected diseases</span>
          <ul className="disease-table__list">
            {diseasesDetected.map((name, i) => (
              <li key={i} className="disease-table__row">
                <span className="disease-table__index">{String(i + 1).padStart(2, "0")}</span>
                <span className="disease-table__name">{name}</span>
                <span className="disease-table__dot" />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* ── Image carousel ── */}
      {isLoading ? (
        <div className="skeleton-carousel" />
      ) : hasSlides ? (
        <div className="carousel">
          {total > 1 && (
            <div className="carousel-nav">
              <button className="carousel-btn" onClick={prev} aria-label="Previous">
                <ChevronLeft size={13} />
              </button>
              <span className="carousel-dots">
                {slides.map((_, i) => (
                  <button
                    key={i}
                    className={`carousel-dot${i === idx ? " carousel-dot--active" : ""}`}
                    onClick={() => setIdx(i)}
                    aria-label={`Slide ${i + 1}`}
                  />
                ))}
              </span>
              <button className="carousel-btn" onClick={next} aria-label="Next">
                <ChevronRight size={13} />
              </button>
            </div>
          )}
          <div className="carousel-image-wrap">
            <img
              src={current.src}
              alt={current.caption ?? "Flight image"}
              className="carousel-image"
            />
            {current.caption && (
              <span className="carousel-caption">{current.caption}</span>
            )}
          </div>
        </div>
      ) : null}

    </aside>
  );
};
