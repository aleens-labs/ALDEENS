import { ChevronLeft, ChevronRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { APP_LOGO_PATH, APP_NAME, APP_VERSION } from '../../lib/branding';
import { useAleensApp } from '../../router/AppStateContext';
import { NAV_ROUTES } from '../../router/navigation';
import { RiskBadge } from '../shared/RiskBadge';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { analysis } = useAleensApp();

  return (
    <aside className={`app-sidebar ${collapsed ? 'is-collapsed' : ''}`}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">
          <img src={APP_LOGO_PATH} alt={`${APP_NAME} logo`} className="sidebar-brand-logo" />
        </div>
        {!collapsed ? (
          <div className="sidebar-brand-copy">
            <p className="sidebar-brand-title">{APP_NAME}</p>
            <span className="sidebar-brand-version">{APP_VERSION}</span>
          </div>
        ) : null}
        <button
          type="button"
          className="sidebar-toggle"
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        {NAV_ROUTES.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'is-active' : ''} ${collapsed ? 'is-collapsed' : ''}`.trim()
              }
              title={collapsed ? item.label : undefined}
            >
              <span className="sidebar-link-icon">
                <Icon size={18} />
              </span>
              {!collapsed ? <span className="sidebar-link-label">{item.label}</span> : null}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        {!collapsed ? (
          <>
            <p className="sidebar-footer-label">Last Analysis</p>
            {analysis ? (
              <div className="sidebar-risk-card">
                <RiskBadge label={analysis.scores.riskLabel} score={analysis.scores.riskScore} compact />
                <p className="sidebar-risk-dataset">{analysis.datasetName}</p>
                <p className="sidebar-risk-meta">
                  Confidence {analysis.scores.confidenceScore}% | {analysis.reportMode.toUpperCase()}
                </p>
              </div>
            ) : (
              <div className="sidebar-risk-card">
                <p className="sidebar-risk-dataset">No analysis loaded</p>
                <p className="sidebar-risk-meta">Run intake to populate live incident state.</p>
              </div>
            )}
          </>
        ) : analysis ? (
          <div className="sidebar-footer-collapsed">
            <RiskBadge label={analysis.scores.riskLabel} compact />
          </div>
        ) : null}
      </div>
    </aside>
  );
}
