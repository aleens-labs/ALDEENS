import type { RiskLabel } from '../lib/types';

interface RiskCardProps {
  score: number;
  label: RiskLabel;
}

export function RiskCard({ score, label }: RiskCardProps) {
  const tone =
    label === 'Critical'
      ? 'from-signal-coral/35 to-signal-amber/15'
      : label === 'High'
        ? 'from-signal-amber/30 to-signal-coral/10'
        : label === 'Medium'
          ? 'from-signal-sky/20 to-signal-amber/10'
          : 'from-signal-teal/20 to-white/5';
  const helper =
    label === 'Critical'
      ? 'Critical means several high-risk behaviors appeared together, so this case should be reviewed first.'
      : label === 'High'
        ? 'High means the pattern is suspicious enough to warrant prompt analyst review.'
        : label === 'Medium'
          ? 'Medium means some suspicious behavior is present, but context is still important.'
          : 'Low means the available evidence does not yet suggest a severe incident chain.';

  return (
    <section className={`metric-card bg-gradient-to-br ${tone}`}>
      <p className="eyebrow">Risk Score</p>
      <div className="mt-4 flex flex-col gap-4">
        <div>
          <p className="metric-value">{score}</p>
          <p className="metric-subtle">Investigation priority based on weighted rule contributions</p>
        </div>
        <span className="metric-badge self-start">{label}</span>
        <p className="text-sm text-slate-400">{helper}</p>
      </div>
    </section>
  );
}
