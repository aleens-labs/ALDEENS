import type { Finding } from '../lib/types';

interface RuleTraceProps {
  findings: Finding[];
}

export function RuleTrace({ findings }: RuleTraceProps) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Rules</p>
          <h2 className="panel-title">Traceable Rule Firing</h2>
        </div>
      </div>

      {findings.length === 0 ? (
        <p className="empty-state">No rules triggered on the current telemetry.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {findings.map((finding) => (
            <article key={finding.findingId} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white">{finding.title}</p>
                  <p className="text-wrap-safe text-xs uppercase tracking-[0.24em] text-slate-500">
                    {finding.ruleId} | {finding.mitreTechnique}
                  </p>
                </div>
                <span className="tag">+{finding.scoreContribution}</span>
              </div>
              <p className="text-wrap-safe mt-3 text-sm leading-6 text-slate-300">{finding.reason}</p>
              <p className="text-wrap-safe mt-3 text-xs text-slate-500">
                Evidence trace: {finding.evidenceIds.join(', ')} | Confidence contribution:{' '}
                {finding.confidenceContribution.toFixed(2)}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
