import type { ChainStep } from '../lib/types';

interface AttackTimelineProps {
  steps: ChainStep[];
}

function formatUtcTime(ts: string): string {
  const d = new Date(ts);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
}

function relativeOffset(base: string, ts: string): string {
  const diffMs = new Date(ts).getTime() - new Date(base).getTime();
  if (diffMs <= 0) return '';
  const secs = Math.round(diffMs / 1000);
  if (secs < 60) return `+${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return rem > 0 ? `+${mins}m${rem}s` : `+${mins}m`;
}

export function AttackTimeline({ steps }: AttackTimelineProps) {
  const baseTimestamp = steps.find((s) => s.timestamp)?.timestamp ?? null;

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Chain</p>
          <h2 className="panel-title">Attack Timeline</h2>
        </div>
      </div>

      {steps.length === 0 ? (
        <p className="empty-state">No chain has been reconstructed yet.</p>
      ) : (
        <div className="relative mt-2 space-y-4 border-l border-white/10 pl-5">
          {steps.map((step, index) => {
            const offset =
              step.timestamp && baseTimestamp && step.timestamp !== baseTimestamp
                ? relativeOffset(baseTimestamp, step.timestamp)
                : '';
            return (
              <article key={`${step.stage}-${index}`} className="timeline-node">
                <div className="timeline-dot" />
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-base font-semibold text-white">{step.stage}</h3>
                  <div className="flex items-center gap-2">
                    {offset ? (
                      <span className="rounded bg-signal-teal/15 px-1.5 py-0.5 text-xs font-mono text-signal-teal">
                        {offset}
                      </span>
                    ) : null}
                    <span className="text-wrap-safe font-mono text-xs text-slate-500">
                      {step.timestamp ? formatUtcTime(step.timestamp) : 'Time unavailable'}
                    </span>
                  </div>
                </div>
                <p className="text-wrap-safe mt-2 text-sm leading-6 text-slate-300">{step.summary}</p>
                <p className="text-wrap-safe mt-2 text-xs text-slate-500">
                  Evidence: {step.evidenceIds.join(', ')} | Findings: {step.findingIds.join(', ')}
                </p>
                <p className="text-wrap-safe mt-1 text-xs text-slate-500">Raw refs: {step.rawReferences.join(', ')}</p>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
