import { ArrowUpRight } from 'lucide-react';

import type { AuditEntry } from '../../lib/types';
import { RiskBadge } from '../shared/RiskBadge';

interface RecentAnalysisTableProps {
  audit: AuditEntry[];
  onOpen: (analysisId: string) => void;
}

export function RecentAnalysisTable({ audit, onOpen }: RecentAnalysisTableProps) {
  return (
    <div className="panel-card recent-analysis-card">
      <div className="panel-card-head">
        <div>
          <p className="eyebrow">Recent Analysis Trail</p>
          <h3 className="panel-card-title">Last 5 Analyses</h3>
        </div>
        <span className="tag">{Math.min(5, audit.length)}/{audit.length || 0}</span>
      </div>

      {audit.length === 0 ? (
        <p className="panel-card-copy">Audit history will populate after the first analysis run.</p>
      ) : (
        <div className="recent-analysis-table">
          {audit.slice(0, 5).map((entry) => (
            <button
              key={entry.analysisId}
              type="button"
              className="recent-analysis-row"
              onClick={() => onOpen(entry.analysisId)}
            >
              <div className="recent-analysis-primary">
                <span className="recent-analysis-dataset">{entry.datasetName}</span>
                <span className="recent-analysis-id">{entry.analysisId}</span>
              </div>
              <div className="recent-analysis-secondary">
                <RiskBadge
                  label={
                    entry.riskScore >= 80
                      ? 'Critical'
                      : entry.riskScore >= 60
                        ? 'High'
                        : entry.riskScore >= 30
                          ? 'Medium'
                          : 'Low'
                  }
                  score={entry.riskScore}
                  compact
                />
                <span className="recent-analysis-meta">{entry.confidenceScore}%</span>
                <span className="recent-analysis-meta">{new Date(entry.timestamp).toLocaleString()}</span>
                <span className={`recent-analysis-mode ${entry.reportMode === 'llm' ? 'mode-llm' : 'mode-template'}`}>
                  {entry.reportMode.toUpperCase()}
                </span>
                <ArrowUpRight size={14} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
