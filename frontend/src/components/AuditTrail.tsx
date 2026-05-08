import { useState } from 'react';
import type { AuditEntry } from '../lib/types';

type RiskFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

const RISK_THRESHOLDS: Record<RiskFilter, [number, number]> = {
  all:      [0, Infinity],
  critical: [80, Infinity],
  high:     [60, 79],
  medium:   [30, 59],
  low:      [0, 29],
};

interface AuditTrailProps {
  audit: AuditEntry[];
}

export function AuditTrail({ audit }: AuditTrailProps) {
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');

  const [min, max] = RISK_THRESHOLDS[riskFilter];
  const filtered = audit.filter((entry) => {
    const score = entry.riskScore ?? 0;
    if (score < min || score > max) return false;
    if (query.trim()) {
      const q = query.toLowerCase();
      return (
        (entry.datasetName ?? '').toLowerCase().includes(q) ||
        (entry.analysisId ?? '').toLowerCase().includes(q) ||
        (entry.reportMode ?? '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Audit</p>
          <h2 className="panel-title">Analysis Trail</h2>
        </div>
        {audit.length > 0 && (
          <span className="tag">{filtered.length}/{audit.length}</span>
        )}
      </div>

      {audit.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by dataset or analysis ID…"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 placeholder-slate-600 outline-none focus:border-signal-teal/50 focus:ring-1 focus:ring-signal-teal/30"
          />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as RiskFilter)}
            className="rounded-xl border border-white/10 bg-chrome-900 px-3 py-2 text-sm text-slate-300 outline-none focus:border-signal-teal/50"
          >
            <option value="all">All risk levels</option>
            <option value="critical">Critical (80+)</option>
            <option value="high">High (60–79)</option>
            <option value="medium">Medium (30–59)</option>
            <option value="low">Low (0–29)</option>
          </select>
        </div>
      )}

      {audit.length === 0 ? (
        <p className="empty-state">Audit records will appear here after the first analysis.</p>
      ) : filtered.length === 0 ? (
        <p className="empty-state">No audit entries match the current filter.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {filtered.map((entry) => (
            <article key={entry.analysisId} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white">{entry.datasetName}</p>
                  <p className="text-wrap-safe text-xs uppercase tracking-[0.24em] text-slate-500">
                    {entry.analysisId}
                  </p>
                </div>
                <span className="tag">{entry.reportMode}</span>
              </div>
              <p className="text-wrap-safe mt-2 text-sm text-slate-300">
                Risk {entry.riskScore} | Confidence {entry.confidenceScore} | Safety {entry.safetyCheck}
              </p>
              {entry.llmModel ? (
                <p className="text-wrap-safe mt-2 text-xs text-slate-500">
                  LLM model {entry.llmModel}
                  {entry.providerRequestId ? ` | Request ${entry.providerRequestId}` : ''}
                </p>
              ) : null}
              <p className="mt-2 text-xs text-slate-500">{new Date(entry.timestamp).toLocaleString()}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
