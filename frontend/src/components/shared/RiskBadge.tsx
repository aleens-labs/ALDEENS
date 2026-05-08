import type { RiskLabel } from '../../lib/types';

interface RiskBadgeProps {
  label: RiskLabel | string;
  score?: number | null;
  compact?: boolean;
  className?: string;
}

const RISK_CLASS: Record<string, string> = {
  Critical: 'risk-critical',
  High: 'risk-high',
  Medium: 'risk-medium',
  Low: 'risk-low',
};

export function RiskBadge({ label, score, compact = false, className = '' }: RiskBadgeProps) {
  const tone = RISK_CLASS[label] ?? 'risk-low';

  return (
    <span
      className={`risk-badge ${tone} ${compact ? 'risk-badge-compact' : ''} ${className}`.trim()}
      title={score != null ? `${label} (${score}/100)` : String(label)}
    >
      {score != null ? `${label} ${score}` : label}
    </span>
  );
}
