import { useEffect, useMemo, useState } from 'react';

interface ProgressBarProps {
  value: number;
  max?: number;
  tone?: 'cyan' | 'risk' | 'amber' | 'slate';
  height?: number;
  label?: string;
  showValue?: boolean;
  className?: string;
}

const TONE_CLASS: Record<NonNullable<ProgressBarProps['tone']>, string> = {
  cyan: 'progress-cyan',
  risk: 'progress-risk',
  amber: 'progress-amber',
  slate: 'progress-slate',
};

export function ProgressBar({
  value,
  max = 100,
  tone = 'cyan',
  height = 8,
  label,
  showValue = false,
  className = '',
}: ProgressBarProps) {
  const normalized = useMemo(() => {
    if (max <= 0) {
      return 0;
    }
    return Math.max(0, Math.min(100, Math.round((value / max) * 100)));
  }, [max, value]);

  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const raf = window.requestAnimationFrame(() => setAnimatedValue(normalized));
    return () => window.cancelAnimationFrame(raf);
  }, [normalized]);

  return (
    <div className={`progress-wrap ${className}`.trim()}>
      {label || showValue ? (
        <div className="progress-meta">
          {label ? <span>{label}</span> : <span />}
          {showValue ? <span>{normalized}%</span> : null}
        </div>
      ) : null}
      <div className="progress-track" style={{ height }}>
        <div
          className={`progress-fill ${TONE_CLASS[tone]}`}
          style={{ width: `${animatedValue}%` }}
        />
      </div>
    </div>
  );
}
