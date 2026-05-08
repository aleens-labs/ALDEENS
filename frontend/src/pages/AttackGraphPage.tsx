import { useMemo, useState } from 'react';

import type { ChainStep, TacticHit } from '../lib/types';
import { useAleensApp } from '../router/AppStateContext';
import { EmptyState } from '../components/shared/EmptyState';
import { TacticBadge } from '../components/shared/TacticBadge';

const TACTIC_COLOR: Record<string, { fill: string; stroke: string; text: string }> = {
  'Initial Access': { fill: 'rgba(239,68,68,0.16)', stroke: '#EF4444', text: '#FCA5A5' },
  Execution: { fill: 'rgba(249,115,22,0.16)', stroke: '#F97316', text: '#FDBA74' },
  'Defense Evasion': { fill: 'rgba(56,189,248,0.16)', stroke: '#38BDF8', text: '#7DD3FC' },
  'Credential Access': { fill: 'rgba(168,85,247,0.16)', stroke: '#A855F7', text: '#D8B4FE' },
  'Command and Control': { fill: 'rgba(45,212,191,0.16)', stroke: '#2DD4BF', text: '#99F6E4' },
  Persistence: { fill: 'rgba(34,197,94,0.16)', stroke: '#22C55E', text: '#86EFAC' },
};

function offsetFromBase(base: string | null, next: string | null) {
  if (!base || !next || base === next) {
    return '--';
  }
  const delta = Math.round((new Date(next).getTime() - new Date(base).getTime()) / 1000);
  return delta > 0 ? `+${delta}s` : '--';
}

function stageTechnique(step: ChainStep, tactics: TacticHit[]) {
  return tactics.filter((item) => item.tactic === step.stage);
}

export function AttackGraphPage() {
  const { analysis } = useAleensApp();
  const [activeStage, setActiveStage] = useState<string | null>(null);

  const steps = analysis?.attackChain ?? [];
  const tactics = analysis?.tactics ?? [];

  const activeStep = useMemo(
    () => steps.find((step) => step.stage === activeStage) ?? steps[0] ?? null,
    [activeStage, steps],
  );

  if (!analysis || steps.length === 0) {
    return (
      <section className="page-shell page-shell-center">
        <div className="attack-graph-empty">
          <div className="attack-graph-empty-preview" aria-hidden="true">
            {['Initial Access', 'Execution', 'Defense Evasion', 'Credential Access', 'Command and Control'].map((label) => (
              <div key={label} className="attack-graph-empty-node">
                {label}
              </div>
            ))}
          </div>
          <EmptyState
            title="No active attack graph"
            description="Run a dataset from Intake to reconstruct the attack chain and inspect node-level evidence details."
            ctaLabel="Run Analysis"
            ctaTo="/intake"
          />
        </div>
      </section>
    );
  }

  const baseTimestamp = steps[0]?.timestamp ?? null;

  return (
    <section className="page-shell attack-graph-page">
      <div className="attack-graph-layout">
        <article className="page-card attack-graph-canvas">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Visual Chain</p>
              <h2 className="page-card-title">Reconstructed Attack Graph</h2>
            </div>
            <span className="tag">{steps.length} STAGES</span>
          </div>

          <div className="attack-graph-flow">
            {steps.map((step, index) => {
              const tone = TACTIC_COLOR[step.stage] ?? TACTIC_COLOR.Execution;
              const techniques = stageTechnique(step, tactics);
              const isActive = activeStep?.stage === step.stage;
              return (
                <button
                  key={`${step.stage}-${index}`}
                  type="button"
                  className={`attack-graph-node ${isActive ? 'is-active' : ''}`}
                  style={{ borderColor: tone.stroke, background: tone.fill }}
                  onClick={() => setActiveStage(step.stage)}
                >
                  <span className="attack-node-stage" style={{ color: tone.text }}>
                    {step.stage}
                  </span>
                  <span className="attack-node-time">
                    {step.timestamp ? new Date(step.timestamp).toISOString().slice(11, 19) : 'n/a'} UTC
                  </span>
                  <span className="attack-node-offset">{offsetFromBase(baseTimestamp, step.timestamp)}</span>
                  {techniques[0] ? <span className="attack-node-tech">{techniques[0].techniqueId}</span> : null}
                  {index < steps.length - 1 ? <span className="attack-node-arrow" aria-hidden="true" /> : null}
                </button>
              );
            })}
          </div>

          <div className="attack-graph-legend">
            {steps.map((step) => (
              <TacticBadge key={step.stage} tactic={step.stage} />
            ))}
          </div>
        </article>

        <aside className="page-card attack-graph-detail">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Stage Detail</p>
              <h2 className="page-card-title">{activeStep?.stage ?? 'No stage selected'}</h2>
            </div>
            {activeStep?.timestamp ? <span className="tag">{new Date(activeStep.timestamp).toISOString()}</span> : null}
          </div>

          {activeStep ? (
            <div className="attack-detail-stack">
              <p className="attack-detail-summary">{activeStep.summary}</p>

              <div className="detail-grid">
                <div className="detail-card">
                  <span className="detail-label">Timestamp</span>
                  <p>{activeStep.timestamp ? new Date(activeStep.timestamp).toUTCString() : 'Unavailable'}</p>
                </div>
                <div className="detail-card">
                  <span className="detail-label">Offset</span>
                  <p>{offsetFromBase(baseTimestamp, activeStep.timestamp)}</p>
                </div>
              </div>

              <div className="detail-card">
                <span className="detail-label">Evidence references</span>
                <div className="detail-chip-wrap">
                  {activeStep.evidenceIds.map((item) => (
                    <span key={item} className="detail-chip">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="detail-card">
                <span className="detail-label">Findings ID</span>
                <div className="detail-chip-wrap">
                  {activeStep.findingIds.map((item) => (
                    <span key={item} className="detail-chip">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="detail-card">
                <span className="detail-label">Raw event references</span>
                <div className="detail-chip-wrap">
                  {activeStep.rawReferences.map((item) => (
                    <span key={item} className="detail-chip">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="detail-card">
                <span className="detail-label">Mapped ATT&CK techniques</span>
                <div className="detail-techniques">
                  {stageTechnique(activeStep, tactics).map((item) => (
                    <div key={item.techniqueId} className="detail-technique-row">
                      <span className="tag">{item.techniqueId}</span>
                      <div>
                        <p>{item.techniqueName}</p>
                        <span>{Math.round(item.confidence * 100)}% confidence</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}
