import { TelemetryElement } from "./telementryElement"
import { formatDateTime } from "../helpers/helper_functions"
import type { TelemetryHudProps } from "../types/data"



export const TelemetryHud = ({ cards, startTime, stopTime }: TelemetryHudProps) => {
  return (
    <section className="telemetry-hud" aria-label="Drone telemetry">
      <div className="telemetry-hud-head">
        <div>
          <div className="telemetry-strip">
            {cards.map((card, idx) => (
              <TelemetryElement key={idx} {...card} />
            ))}
          </div>
        </div>
        <span className="numeric telemetry-time">
          {/* Show start and stop times */}
          UTC {formatDateTime(startTime)} – {formatDateTime(stopTime)}
        </span>
      </div>
    </section>
  );
};
