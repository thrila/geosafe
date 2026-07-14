import type { FlightMenuModalProps } from "../types/modal";

interface Props extends FlightMenuModalProps {
  isLoading?: boolean;
}

export function FlightMenuModal({
  activeFlightId,
  onSelect,
  onClose,
  flights = [],
  isLoading = false,
}: Props) {
  return (
    <div className="flight-menu-shell">
      <div className="flight-menu-list" role="list">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
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
          : flights.length === 0 ? (
            <p className="flight-menu-empty">No flights uploaded yet.</p>
          ) : flights.map((flight) => {
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
