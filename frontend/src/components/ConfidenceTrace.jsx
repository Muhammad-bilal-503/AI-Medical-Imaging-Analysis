/**
 * Signature UI element for this app: a thin horizontal trace with a
 * tick marker and mono-font readout, styled after an oscilloscope /
 * EKG strip rather than a generic progress bar. Used everywhere an
 * AI confidence score appears — patient cards, findings tables,
 * report pages — so the "how sure is the model" question always
 * renders the same clinical-instrument way.
 */
export default function ConfidenceTrace({ label, confidence, size = "md" }) {
  const pct = Math.max(0, Math.min(100, confidence));
  const tone =
    pct >= 70 ? "bg-red" : pct >= 40 ? "bg-amber" : "bg-teal";
  const height = size === "sm" ? "h-1" : "h-1.5";

  return (
    <div className="flex items-center gap-3">
      {label && (
        <span className="text-sm text-ink/90 flex-1 truncate">{label}</span>
      )}
      <div className="flex items-center gap-2 w-32">
        <div className={`relative flex-1 ${height} bg-line rounded-full overflow-hidden`}>
          <div
            className={`absolute inset-y-0 left-0 ${tone} rounded-full transition-all duration-500`}
            style={{ width: `${pct}%` }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-ink/40"
            style={{ left: `${pct}%` }}
          />
        </div>
        <span className="font-mono text-xs text-muted tabular-nums w-11 text-right">
          {pct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
