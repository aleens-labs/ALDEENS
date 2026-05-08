import type { ReactNode } from 'react';

import { CountUpNumber } from '../shared/CountUpNumber';

interface KpiCardProps {
  eyebrow: string;
  title: string;
  value: number;
  suffix?: string;
  accent?: 'cyan' | 'critical' | 'high' | 'medium' | 'low';
  helper: string;
  footer?: ReactNode;
}

export function KpiCard({
  eyebrow,
  title,
  value,
  suffix = '',
  accent = 'cyan',
  helper,
  footer,
}: KpiCardProps) {
  return (
    <article className={`kpi-card kpi-${accent}`}>
      <p className="eyebrow">{eyebrow}</p>
      <p className="kpi-title">{title}</p>
      <p className="kpi-value">
        <CountUpNumber value={value} suffix={suffix} />
      </p>
      <p className="kpi-helper">{helper}</p>
      {footer ? <div className="kpi-footer">{footer}</div> : null}
    </article>
  );
}
