import { TelemetryElement } from "./telementryElement"
import { formatDateTime } from "../helpers/helper_functions"
import type { TelemetryHudProps } from "../types/data"

export const TelemetryHud = ({
  cards,
  startTime,
  stopTime,
  status = "success",
  errorMessage,
}: TelemetryHudProps) => {
  return (
    <section className="telemetry-hud" aria-label="Drone telemetry">
      <div className="telemetry-hud-head">
        <div>
          <div className="telemetry-strip">

            {/* ── Loading ── */}
            {status === "loading" && (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="telemetry-item telemetry-item--skeleton">
                  <span className="skeleton-bar skeleton-bar--meta" style={{ animationDelay: `${i * 0.08}s` }} />
                  <span className="skeleton-bar skeleton-bar--meta skeleton-bar--meta-mid" style={{ animationDelay: `${i * 0.08 + 0.04}s` }} />
                </div>
              ))
            )}

            {/* ── Empty ── */}
            {status === "empty" && (
              <span className="telemetry-placeholder">Awaiting telemetry data</span>
            )}

            {/* ── Error ── */}
            {status === "error" && (
              <span className="telemetry-placeholder telemetry-placeholder--error">
                {errorMessage || "Telemetry unavailable"}
              </span>
            )}

            {/* ── Success ── */}
            {status === "success" && cards.map((card, idx) => (
              <TelemetryElement key={idx} {...card} />
            ))}
          </div>
        </div>
        <span className="numeric telemetry-time">
          UTC {formatDateTime(startTime)} – {formatDateTime(stopTime)}
        </span>
      </div>
    </section>
  );
};
