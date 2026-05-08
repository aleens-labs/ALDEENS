interface TacticBadgeProps {
  tactic: string;
  className?: string;
}

const TACTIC_CLASS: Record<string, string> = {
  'Initial Access': 'tactic-initial-access',
  Execution: 'tactic-execution',
  'Defense Evasion': 'tactic-defense-evasion',
  'Credential Access': 'tactic-credential-access',
  'Command and Control': 'tactic-command-and-control',
  Persistence: 'tactic-persistence',
};

export function TacticBadge({ tactic, className = '' }: TacticBadgeProps) {
  const tone = TACTIC_CLASS[tactic] ?? 'tactic-default';
  return <span className={`tactic-badge ${tone} ${className}`.trim()}>{tactic}</span>;
}
