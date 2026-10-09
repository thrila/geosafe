import { TelemetryElement } from "./telementryElement"
import type { TelemetryHudProps } from "../types/data"

export const TelemetryHud = ({
  cards,
  status = "success",
  errorMessage,
}: TelemetryHudProps) => {
  const hasTelemetry = status === "success";

  return (
    <section className="telemetry-hud" aria-label="Drone telemetry">
      <div className="telemetry-strip" aria-busy={status === "loading"}>
        {cards.map((card) => (
          <TelemetryElement
            key={card.label}
            {...card}
            inactive={!hasTelemetry}
          />
        ))}
        {status === "error" && (
          <span className="telemetry-placeholder telemetry-placeholder--error" role="status">
            {errorMessage || "Telemetry unavailable"}
          </span>
        )}
      </div>
    </section>
  );
};
