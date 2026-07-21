const STATUS_STYLES = {
  pending: "bg-line/60 text-muted",
  ai_generated: "bg-amber-bg text-amber",
  reviewed: "bg-teal-dim text-teal-deep",
  finalized: "bg-green-bg text-green",
  amended: "bg-amber-bg text-amber",
};

const STATUS_LABELS = {
  pending: "Pending",
  ai_generated: "AI Draft",
  reviewed: "Reviewed",
  finalized: "Finalized",
  amended: "Amended",
};

const SEVERITY_STYLES = {
  low: "bg-teal-dim text-teal-deep",
  moderate: "bg-amber-bg text-amber",
  high: "bg-red-bg text-red",
  critical: "bg-red text-white",
};

export function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium ${
        STATUS_STYLES[status] || STATUS_STYLES.pending
      }`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  if (!severity) return null;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium uppercase tracking-wide ${
        SEVERITY_STYLES[severity] || SEVERITY_STYLES.low
      }`}
    >
      {severity}
    </span>
  );
}
