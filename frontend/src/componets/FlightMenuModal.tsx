import { AlertCircle } from "react-feather";
import type { FlightMenuModalProps } from "../types/modal";

export type FlightMenuStatus = "loading" | "empty" | "error" | "success";

interface Props extends FlightMenuModalProps {
  status?: FlightMenuStatus;
  errorMessage?: string;
}

export function FlightMenuModal({
  activeFlightId,
  onSelect,
  onClose,
  flights = [],
  status = "success",
  errorMessage = "",
}: Props) {
  return (
    <div className="flight-menu-shell">
      <div className="flight-menu-list" role="list">

        {/* ── Loading ── */}
        {status === "loading" && (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flight-menu-item flight-menu-item--skeleton"
              role="listitem"
            >
              <span className="flight-menu-main">
                <span
                  className="skeleton-bar skeleton-bar--name"
                  style={{ animationDelay: `${i * 0.1}s` }}
                />
              </span>
              <span className="flight-menu-meta flight-menu-meta--skeleton">
                <span
                  className="skeleton-bar skeleton-bar--meta"
                  style={{ animationDelay: `${i * 0.1 + 0.05}s` }}
                />
                <span
                  className="skeleton-bar skeleton-bar--meta skeleton-bar--meta-mid"
                  style={{ animationDelay: `${i * 0.1 + 0.08}s` }}
                />
                <span
                  className="skeleton-bar skeleton-bar--meta skeleton-bar--meta-long"
                  style={{ animationDelay: `${i * 0.1 + 0.11}s` }}
                />
              </span>
            </div>
          ))
        )}

        {/* ── Empty ── */}
        {status === "empty" && (
          <p className="flight-menu-empty">No flights uploaded yet.</p>
        )}

        {/* ── Error ── */}
        {status === "error" && (
          <div className="flight-menu-error">
            <div className="flight-menu-error-icon">
              <AlertCircle size={16} />
            </div>
            <p className="flight-menu-error-text">{errorMessage || "Failed to load flights."}</p>
          </div>
        )}

        {/* ── Success ── */}
        {status === "success" && flights.map((flight) => {
          const isActive = flight.id === activeFlightId;
          return (
            <div
              key={flight.id}
              role="listitem"
              className={`flight-menu-item ${isActive ? "is-active" : ""}`}
            >
              <button
                type="button"
                className="flight-menu-item-btn"
                onClick={() => {
                  onSelect(flight);
                  onClose();
                }}
              >
                <span className="flight-menu-main">
                  <span className="flight-menu-name">{flight.name}</span>
                </span>
                <span className="flight-menu-meta">
                  <span>
                    Date <span className="numeric">{flight.date}</span>
                  </span>
                  <span>&bull;</span>
                  <span>
                    Duration <span className="numeric">{flight.duration}</span>
                  </span>
                  <span>&bull;</span>
                  <span>
                    Location <span className="numeric">{flight.location}</span>
                  </span>
                </span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
