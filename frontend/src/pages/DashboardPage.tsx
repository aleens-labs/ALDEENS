import { BarChart3, FileWarning, SearchCheck, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

import { KpiCard } from '../components/dashboard/KpiCard';
import { MiniAttackGraph } from '../components/dashboard/MiniAttackGraph';
import { MiniScoreChart } from '../components/dashboard/MiniScoreChart';
import { RecentAnalysisTable } from '../components/dashboard/RecentAnalysisTable';
import { CountUpNumber } from '../components/shared/CountUpNumber';
import { EmptyState } from '../components/shared/EmptyState';
import { RiskBadge } from '../components/shared/RiskBadge';
import { TacticBadge } from '../components/shared/TacticBadge';
import { useAleensApp } from '../router/AppStateContext';

function buildSparklinePath(points: number[], width: number, height: number) {
  if (points.length < 2) {
    return '';
  }
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const xStep = width / Math.max(1, points.length - 1);

  return points
    .map((point, index) => {
      const x = index * xStep;
      const y = height - ((point - min) / Math.max(1, max - min || 1)) * (height - 4) - 2;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

export function DashboardPage() {
  const { analysis, analystOverride, audit, loadAnalysisById } = useAleensApp();

  if (!analysis) {
    return (
      <section className="page-shell page-shell-center">
        <div className="dashboard-empty">
          <EmptyState
            title="No incident analysis is loaded yet"
            description="1. Go to Intake. 2. Select a reference incident or upload Windows telemetry. 3. Run analysis to populate the dashboard."
            ctaLabel="Start Analysis"
            ctaTo="/intake"
          />
        </div>
      </section>
    );
  }

  const averageRisk = audit.length ? Math.round(audit.reduce((sum, entry) => sum + entry.riskScore, 0) / audit.length) : 0;
  const averageConfidence = audit.length
    ? Math.round(audit.reduce((sum, entry) => sum + entry.confidenceScore, 0) / audit.length)
    : 0;
  const trendPoints = audit.slice(0, 10).map((entry) => entry.riskScore).reverse();
  const sparklinePath = buildSparklinePath(trendPoints, 220, 48);
  const activeOverride = analystOverride?.analysisId === analysis.analysisId ? analystOverride : null;

  return (
    <section className="page-shell dashboard-page">
      <div className="dashboard-grid">
        <div className="dashboard-kpis">
          <KpiCard
            eyebrow="Risk Score"
            title={analysis.scores.riskLabel}
            value={analysis.scores.riskScore}
            accent={
              analysis.scores.riskLabel === 'Critical'
                ? 'critical'
                : analysis.scores.riskLabel === 'High'
                  ? 'high'
                  : analysis.scores.riskLabel === 'Medium'
                    ? 'medium'
                    : 'low'
            }
            helper="Deterministic weighted investigation priority"
            footer={<RiskBadge label={analysis.scores.riskLabel} score={analysis.scores.riskScore} />}
          />

          <article className="kpi-card">
            <p className="eyebrow">Confidence</p>
            <p className="kpi-title">Pipeline Strength</p>
            <div className="confidence-ring-wrap">
              <svg viewBox="0 0 120 120" className="confidence-ring" aria-hidden="true">
                <circle cx="60" cy="60" r="48" className="confidence-ring-track" />
                <circle
                  cx="60"
                  cy="60"
                  r="48"
                  className="confidence-ring-fill"
                  style={{ strokeDasharray: `${2 * Math.PI * 48}`, strokeDashoffset: `${2 * Math.PI * 48 * (1 - analysis.scores.confidenceScore / 100)}` }}
                />
              </svg>
              <div className="confidence-ring-value">
                <CountUpNumber value={analysis.scores.confidenceScore} suffix="%" />
              </div>
            </div>
            <p className="kpi-helper">Evidence completeness {Math.round(analysis.scores.completeness * 100)}%</p>
            <div className="kpi-footer">
              <span className="tag">System {analysis.scores.confidenceScore}%</span>
              {activeOverride ? <span className="tag">Analyst {activeOverride.value}%</span> : null}
            </div>
          </article>

          <KpiCard
            eyebrow="Evidence Count"
            title="Artifacts"
            value={analysis.evidence.length}
            helper="Normalized artifacts available for trace review"
            footer={<span className="tag">{analysis.evidenceCount}/4 visible</span>}
          />

          <article className="kpi-card">
            <p className="eyebrow">MITRE Techniques</p>
            <p className="kpi-title">ATT&CK Coverage</p>
            <p className="kpi-value">
              <CountUpNumber value={analysis.tactics.length} />
            </p>
            <p className="kpi-helper">Mapped techniques from deterministic findings</p>
            <div className="kpi-footer tactic-tag-group">
              {analysis.tactics.map((item) => (
                <span key={item.techniqueId} className="tag">
                  {item.techniqueId}
                </span>
              ))}
            </div>
          </article>
        </div>

        <div className="dashboard-main-panels">
          <div className="dashboard-row-two">
            <MiniAttackGraph steps={analysis.attackChain} />
            <MiniScoreChart scoreTrace={analysis.scores.confidenceTrace} />
            <div className="panel-card quick-stats-card">
              <div className="panel-card-head">
                <div>
                  <p className="eyebrow">Quick Stats</p>
                  <h3 className="panel-card-title">Operational Snapshot</h3>
                </div>
                <BarChart3 size={18} className="text-signal-teal" />
              </div>

              <div className="quick-stats-grid">
                <div className="quick-stat">
                  <span className="quick-stat-label">Analyses Run</span>
                  <span className="quick-stat-value">{audit.length}</span>
                </div>
                <div className="quick-stat">
                  <span className="quick-stat-label">Avg Risk Score</span>
                  <span className="quick-stat-value">{averageRisk}</span>
                </div>
                <div className="quick-stat">
                  <span className="quick-stat-label">Avg Confidence</span>
                  <span className="quick-stat-value">{averageConfidence}%</span>
                </div>
                <div className="quick-stat">
                  <span className="quick-stat-label">Last Dataset</span>
                  <span className="quick-stat-value text-sm">{analysis.datasetName}</span>
                </div>
              </div>

              <div className="trend-shell">
                <span className="quick-stat-label">Risk Trend</span>
                {trendPoints.length >= 2 ? (
                  <svg viewBox="0 0 220 48" className="trend-sparkline" aria-hidden="true">
                    <path d={sparklinePath} className="trend-sparkline-path" />
                  </svg>
                ) : (
                  <p className="trend-empty">Run more analyses to see trend.</p>
                )}
              </div>

              <div className="quick-links">
                <Link to="/evidence" className="quick-link-card">
                  <SearchCheck size={18} />
                  <div>
                    <p>Evidence</p>
                    <span>Inspect host, user, and command details</span>
                  </div>
                </Link>
                <Link to="/analyst-brief" className="quick-link-card">
                  <FileWarning size={18} />
                  <div>
                    <p>Analyst Brief</p>
                    <span>Open the grounded narrative and exports</span>
                  </div>
                </Link>
                <Link to="/mitre" className="quick-link-card">
                  <ShieldAlert size={18} />
                  <div>
                    <p>MITRE</p>
                    <span>Review tactic coverage and technique tags</span>
                  </div>
                </Link>
              </div>
            </div>
          </div>

          <RecentAnalysisTable audit={audit} onOpen={(analysisId) => void loadAnalysisById(analysisId)} />
        </div>
      </div>
    </section>
  );
}
