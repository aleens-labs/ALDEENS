import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title: string;
  description: string;
  ctaLabel?: string;
  ctaTo?: string;
  compact?: boolean;
}

export function EmptyState({ title, description, ctaLabel, ctaTo, compact = false }: EmptyStateProps) {
  return (
    <div className={`empty-state-shell ${compact ? 'empty-state-compact' : ''}`}>
      <div className="empty-state-illustration" aria-hidden="true">
        <span className="empty-orb empty-orb-a" />
        <span className="empty-orb empty-orb-b" />
        <span className="empty-grid" />
      </div>
      <div className="empty-state-copy">
        <p className="empty-state-title">{title}</p>
        <p className="empty-state-description">{description}</p>
        {ctaLabel && ctaTo ? (
          <Link to={ctaTo} className="primary-button empty-state-action">
            {ctaLabel}
          </Link>
        ) : null}
      </div>
    </div>
  );
}
