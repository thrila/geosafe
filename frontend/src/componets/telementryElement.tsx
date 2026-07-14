import type { TelemetryItem } from "../types/data";

export function TelemetryElement({
  label,
  value,
  detail,
  icon,
}: TelemetryItem) {
  return (
    <button
      type="button"
      className="telemetry-item"
      aria-label={`${label}: ${value}`}
    >
      <span className="telemetry-icon">{icon}</span>
      <span className="telemetry-label">{label}</span>
      <span className="telemetry-popover"> <span className="telemetry-value numeric"> {value} </span> <span>&bull;</span> {detail}</span>
    </button>
  );
}
