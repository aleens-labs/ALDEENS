import { EmptyState } from '../components/shared/EmptyState';
import { ProgressBar } from '../components/shared/ProgressBar';
import { TacticBadge } from '../components/shared/TacticBadge';
import { useAleensApp } from '../router/AppStateContext';

const KILL_CHAIN_PHASES = [
  'Initial Access',
  'Execution',
  'Persistence',
  'Defense Evasion',
  'Credential Access',
  'Lateral Movement',
  'Command and Control',
];

export function MitrePage() {
  const { analysis } = useAleensApp();
  const tactics = analysis?.tactics ?? [];

  if (!analysis || tactics.length === 0) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No ATT&CK coverage yet"
          description="Run an incident first to map deterministic findings into ATT&CK techniques and tactic coverage."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  const coveredPhases = KILL_CHAIN_PHASES.filter((phase) => tactics.some((item) => item.tactic === phase));
  const coveragePercent = Math.round((coveredPhases.length / KILL_CHAIN_PHASES.length) * 100);

  return (
    <section className="page-shell mitre-page">
      <div className="mitre-grid">
        {tactics.map((tactic) => (
          <article key={tactic.techniqueId} className="page-card mitre-technique-card">
            <div className="page-card-head">
              <div>
                <p className="eyebrow">Technique</p>
                <h2 className="page-card-title">{tactic.techniqueName}</h2>
              </div>
              <span className="tag">{tactic.techniqueId}</span>
            </div>

            <div className="mitre-card-body">
              <TacticBadge tactic={tactic.tactic} />
              <p className="mitre-card-description">{tactic.description}</p>
              <div className="mitre-card-meta">
                <span>Confidence {Math.round(tactic.confidence * 100)}%</span>
                <span>Rules {tactic.relatedRules.join(', ')}</span>
              </div>
            </div>
          </article>
        ))}
      </div>

      <article className="page-card mitre-coverage-card">
        <div className="page-card-head">
          <div>
            <p className="eyebrow">Kill Chain Coverage</p>
            <h2 className="page-card-title">
              {coveredPhases.length} of {KILL_CHAIN_PHASES.length} phases covered
            </h2>
          </div>
          <span className="tag">{coveragePercent}%</span>
        </div>

        <ProgressBar value={coveredPhases.length} max={KILL_CHAIN_PHASES.length} tone="cyan" />

        <div className="kill-chain-phase-row">
          {KILL_CHAIN_PHASES.map((phase) => {
            const covered = coveredPhases.includes(phase);
            return (
              <div key={phase} className={`kill-chain-phase ${covered ? 'is-covered' : ''}`}>
                <span className="kill-chain-dot" />
                <p>{phase}</p>
              </div>
            );
          })}
        </div>
      </article>
    </section>
  );
}
