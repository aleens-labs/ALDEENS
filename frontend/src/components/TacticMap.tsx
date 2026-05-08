import type { TacticHit } from '../lib/types';

interface TacticMapProps {
  tactics: TacticHit[];
}

export function TacticMap({ tactics }: TacticMapProps) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">MITRE</p>
          <h2 className="panel-title">ATT&CK Tactic Map</h2>
        </div>
      </div>

      {tactics.length === 0 ? (
        <p className="empty-state">ATT&CK mappings appear after rule validation.</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {tactics.map((tactic) => (
            <article key={tactic.techniqueId} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white">{tactic.techniqueName}</p>
                  <p className="text-wrap-safe text-xs uppercase tracking-[0.24em] text-slate-500">
                    {tactic.techniqueId}
                  </p>
                </div>
                <span className="signal-pill">{tactic.tactic}</span>
              </div>
              <p className="text-wrap-safe mt-3 text-sm leading-6 text-slate-300">{tactic.description}</p>
              <p className="text-wrap-safe mt-3 text-xs text-slate-500">
                Confidence {Math.round(tactic.confidence * 100)}% | Rules {tactic.relatedRules.join(', ')}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
