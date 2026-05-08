import { useMemo, useState } from 'react';

import { ArrowUpRight, GitCompare } from 'lucide-react';

import { getAnalysis } from '../lib/api';
import type { AnalysisResult } from '../lib/types';
import { EmptyState } from '../components/shared/EmptyState';
import { RiskBadge } from '../components/shared/RiskBadge';
import { useAleensApp } from '../router/AppStateContext';

type RiskFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

function scoreToLabel(score: number) {
  if (score >= 80) return 'Critical';
  if (score >= 60) return 'High';
  if (score >= 30) return 'Medium';
  return 'Low';
}

function scoreMatchesFilter(score: number, filter: RiskFilter) {
  if (filter === 'all') return true;
  return scoreToLabel(score).toLowerCase() === filter;
}

export function AuditPage() {
  const {
    audit,
    auditHasMore,
    auditLoadingMore,
    auditTotal,
    compareSelection,
    setCompareSelection,
    loadAnalysisById,
    loadMoreAudit,
  } = useAleensApp();
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');
  const [comparison, setComparison] = useState<[AnalysisResult, AnalysisResult] | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const filtered = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    return audit.filter((entry) => {
      if (!scoreMatchesFilter(entry.riskScore, riskFilter)) {
        return false;
      }
      if (!lowered) {
        return true;
      }
      return (
        entry.datasetName.toLowerCase().includes(lowered) ||
        entry.analysisId.toLowerCase().includes(lowered) ||
        entry.reportMode.toLowerCase().includes(lowered)
      );
    });
  }, [audit, query, riskFilter]);

  function toggleComparison(id: string) {
    setCompareSelection(
      compareSelection.includes(id)
        ? compareSelection.filter((item) => item !== id)
        : [...compareSelection, id].slice(-2),
    );
  }

  async function compareSelected() {
    if (compareSelection.length !== 2) {
      return;
    }
    setCompareLoading(true);
    try {
      const [left, right] = await Promise.all(compareSelection.map((id) => getAnalysis(id)));
      setComparison([left, right]);
    } finally {
      setCompareLoading(false);
    }
  }

  if (audit.length === 0) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No audit history yet"
          description="Run or upload telemetry first to build a clickable trail of historical analyses."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  return (
    <section className="page-shell audit-page">
      <article className="page-card audit-table-card">
        <div className="page-card-head">
          <div>
            <p className="eyebrow">Audit Trail</p>
            <h2 className="page-card-title">Historical Analyses</h2>
          </div>
          <div className="audit-head-actions">
            <span className="tag">
              {audit.length}/{auditTotal || audit.length}
            </span>
            {compareSelection.length === 2 ? (
              <button type="button" className="secondary-button" onClick={() => void compareSelected()}>
                <GitCompare size={16} />
                <span>{compareLoading ? 'Comparing...' : 'Compare Selected'}</span>
              </button>
            ) : null}
          </div>
        </div>

        <div className="audit-filter-row">
          <input
            type="search"
            className="field-input"
            placeholder="Filter by dataset or analysis ID..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            className="field-input audit-filter-select"
            value={riskFilter}
            onChange={(event) => setRiskFilter(event.target.value as RiskFilter)}
          >
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div className="audit-table-shell">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Compare</th>
                <th>Dataset</th>
                <th>Analysis ID</th>
                <th>Mode</th>
                <th>Risk</th>
                <th>Confidence</th>
                <th>Safety</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.analysisId} className="audit-row" onClick={() => void loadAnalysisById(entry.analysisId)}>
                  <td>
                    <input
                      type="checkbox"
                      checked={compareSelection.includes(entry.analysisId)}
                      onChange={(event) => {
                        event.stopPropagation();
                        toggleComparison(entry.analysisId);
                      }}
                      onClick={(event) => event.stopPropagation()}
                    />
                  </td>
                  <td>{entry.datasetName}</td>
                  <td className="audit-mono">{entry.analysisId}</td>
                  <td>
                    <span className={`audit-mode-badge ${entry.reportMode === 'llm' ? 'mode-llm' : 'mode-template'}`}>
                      {entry.reportMode.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <RiskBadge label={scoreToLabel(entry.riskScore)} score={entry.riskScore} compact />
                  </td>
                  <td>{entry.confidenceScore}%</td>
                  <td>{entry.safetyCheck}</td>
                  <td>
                    <div className="audit-date-cell">
                      <span>{new Date(entry.timestamp).toLocaleDateString()}</span>
                      <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="audit-pagination-row">
          <p className="audit-pagination-copy">
            Loaded {audit.length} of {auditTotal || audit.length} analyses.
          </p>
          {auditHasMore ? (
            <button type="button" className="secondary-button" onClick={() => void loadMoreAudit()} disabled={auditLoadingMore}>
              <span>{auditLoadingMore ? 'Loading...' : 'Load More'}</span>
            </button>
          ) : null}
        </div>
      </article>

      {comparison ? (
        <article className="page-card audit-compare-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Comparison Mode</p>
              <h2 className="page-card-title">Side-by-Side Analysis Diff</h2>
            </div>
            <button type="button" className="secondary-button" onClick={() => setComparison(null)}>
              Close
            </button>
          </div>

          <div className="compare-grid">
            {comparison.map((item) => (
              <div key={item.analysisId} className="compare-column">
                <p className="compare-column-title">{item.datasetName}</p>
                <p className="compare-column-meta">{item.analysisId}</p>
                <div className="compare-metric-row">
                  <span>Risk</span>
                  <strong>{item.scores.riskScore}</strong>
                </div>
                <div className="compare-metric-row">
                  <span>Confidence</span>
                  <strong>{item.scores.confidenceScore}%</strong>
                </div>
                <div className="compare-metric-row">
                  <span>MITRE</span>
                  <strong>{item.tactics.map((tactic) => tactic.techniqueId).join(', ')}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="compare-delta-panel">
            <p className="compare-delta-title">Delta Summary</p>
            <p>
              Risk delta: {comparison[1].scores.riskScore - comparison[0].scores.riskScore >= 0 ? '+' : ''}
              {comparison[1].scores.riskScore - comparison[0].scores.riskScore}
            </p>
            <p>
              Confidence delta:{' '}
              {comparison[1].scores.confidenceScore - comparison[0].scores.confidenceScore >= 0 ? '+' : ''}
              {comparison[1].scores.confidenceScore - comparison[0].scores.confidenceScore}
            </p>
            <p>
              Added techniques:{' '}
              {comparison[1].tactics
                .filter((item) => !comparison[0].tactics.some((left) => left.techniqueId === item.techniqueId))
                .map((item) => item.techniqueId)
                .join(', ') || 'none'}
            </p>
            <p>
              Removed techniques:{' '}
              {comparison[0].tactics
                .filter((item) => !comparison[1].tactics.some((right) => right.techniqueId === item.techniqueId))
                .map((item) => item.techniqueId)
                .join(', ') || 'none'}
            </p>
          </div>
        </article>
      ) : null}
    </section>
  );
}
