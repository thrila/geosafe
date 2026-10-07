import { useId, useState } from "react";
import type { TelemetryItem } from "../types/data";

export function TelemetryElement({
  label,
  value,
  detail,
  icon,
}: TelemetryItem) {
  const [open, setOpen] = useState(false);
  const popoverId = useId();

  return (
    <button
      type="button"
      className="telemetry-item"
      aria-label={`${label}: ${value}`}
      aria-describedby={popoverId}
      aria-expanded={open}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <span className="telemetry-icon" aria-hidden="true">{icon}</span>
      <span className="telemetry-label">{label}</span>
      <span className="telemetry-popover" id={popoverId}>
        <span className="telemetry-value numeric">{value}</span>{" "}
        <span aria-hidden="true">&bull;</span> {detail}
      </span>
    </button>
  );
}
