interface ConfidenceCardProps {
  confidence: number;
  completeness: number;
}

export function ConfidenceCard({ confidence, completeness }: ConfidenceCardProps) {
  return (
    <section className="metric-card bg-gradient-to-br from-signal-teal/20 to-signal-sky/10">
      <p className="eyebrow">Confidence</p>
      <div className="mt-4 flex flex-col gap-4">
        <div>
          <p className="metric-value">{confidence}</p>
          <p className="metric-subtle">
            Evidence strength and internal consistency with completeness {Math.round(completeness * 100)}%
          </p>
        </div>
        <div className="h-14 w-14 shrink-0 rounded-full border border-white/15 bg-white/5 p-1">
          <div
            className="flex h-full w-full items-center justify-center rounded-full border border-signal-teal/50 bg-signal-teal/10 text-sm font-semibold text-signal-teal"
          >
            {Math.round(completeness * 100)}%
          </div>
        </div>
        <p className="text-sm text-slate-400">
          High confidence means the visible logs support the conclusion well. It does not guarantee full incident scope
          is already known.
        </p>
      </div>
    </section>
  );
}
