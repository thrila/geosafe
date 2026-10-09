import type { TelemetryItem } from "../types/data";

export function TelemetryElement({
  label,
  value,
  detail,
  icon,
  inactive = false,
}: TelemetryItem) {
  return (
    <button
      type="button"
      className={`telemetry-item${inactive ? " telemetry-item--inactive" : ""}`}
      aria-label={inactive ? `${label}: no drone data loaded` : `${label}: ${value}`}
      disabled={inactive}
    >
      <span className="telemetry-icon">{icon}</span>
      <span className="telemetry-label">{label}</span>
      <span className="telemetry-popover"> <span className="telemetry-value numeric"> {value} </span> <span>&bull;</span> {detail}</span>
    </button>
  );
}
