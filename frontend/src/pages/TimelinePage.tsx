import { EmptyState } from '../components/shared/EmptyState';
import { useAleensApp } from '../router/AppStateContext';

const TACTIC_TONE: Record<string, string> = {
  'Initial Access': 'timeline-initial-access',
  Execution: 'timeline-execution',
  'Defense Evasion': 'timeline-defense-evasion',
  'Credential Access': 'timeline-credential-access',
  'Command and Control': 'timeline-command-control',
};

function formatUtcTime(ts: string | null) {
  if (!ts) {
    return 'Time unavailable';
  }
  const date = new Date(ts);
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())} UTC`;
}

function relativeOffset(base: string | null, ts: string | null) {
  if (!base || !ts || base === ts) {
    return '--';
  }
  const diff = Math.round((new Date(ts).getTime() - new Date(base).getTime()) / 1000);
  return diff > 0 ? `+${diff}s` : '--';
}

export function TimelinePage() {
  const { analysis } = useAleensApp();
  const steps = analysis?.attackChain ?? [];

  if (!analysis || steps.length === 0) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No incident timeline available"
          description="Run a dataset from Intake to reconstruct the chronological chain with timestamps and deltas."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  const baseTimestamp = steps[0]?.timestamp ?? null;

  return (
    <section className="page-shell timeline-page">
      <article className="page-card timeline-card">
        <div className="page-card-head">
          <div>
            <p className="eyebrow">Chain Reconstruction</p>
            <h2 className="page-card-title">Attack Timeline</h2>
          </div>
          <span className="tag">{steps.length} events</span>
        </div>

        <div className="timeline-page-body">
          <div className="timeline-page-line" />
          {steps.map((step, index) => (
            <article key={`${step.stage}-${index}`} className={`timeline-event-card ${TACTIC_TONE[step.stage] ?? 'timeline-execution'}`}>
              <div className="timeline-event-marker" />
              <div className="timeline-event-head">
                <div>
                  <p className="timeline-event-stage">{step.stage}</p>
                  <p className="timeline-event-time">{formatUtcTime(step.timestamp)}</p>
                </div>
                <span className="timeline-delta-badge">{relativeOffset(baseTimestamp, step.timestamp)}</span>
              </div>
              <p className="timeline-event-summary">{step.summary}</p>
              <div className="timeline-event-meta">
                <span>Evidence: {step.evidenceIds.join(', ')}</span>
                <span>Findings: {step.findingIds.join(', ')}</span>
              </div>
              <p className="timeline-event-meta">Raw refs: {step.rawReferences.join(', ')}</p>
            </article>
          ))}
        </div>
      </article>
    </section>
  );
}
