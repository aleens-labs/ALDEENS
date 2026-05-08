import { useState } from 'react';

import { ProgressBar } from '../components/shared/ProgressBar';
import { EmptyState } from '../components/shared/EmptyState';
import { useAleensApp } from '../router/AppStateContext';

export function ScoringPage() {
  const { analysis, evaluation } = useAleensApp();
  const [expandedLabel, setExpandedLabel] = useState<string | null>(null);

  if (!analysis) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No scoring data available"
          description="Run an incident analysis first to inspect the deterministic risk and confidence formulas."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  const confidenceCards = analysis.scores.confidenceTrace.filter((item) => item.label !== 'BASELINE');

  return (
    <section className="page-shell scoring-page">
      <div className="scoring-grid">
        <article className="page-card formula-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Deterministic Risk</p>
              <h2 className="page-card-title">Risk Formula</h2>
            </div>
            <span className="tag">{analysis.scores.riskScore}/100</span>
          </div>
          <p className="formula-code">
            risk = sum(rule_contributions) + tactic_diversity_bonus - evidence_gap_penalty
          </p>
          <div className="formula-math-list">
            {analysis.scores.scoreTrace.map((component) => (
              <div key={`${component.label}-${component.value}`} className="formula-row">
                <span>{component.label}</span>
                <strong>{component.value >= 0 ? `+${component.value}` : component.value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="page-card formula-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Pipeline Confidence</p>
              <h2 className="page-card-title">Confidence Formula</h2>
            </div>
            <span className="tag">{analysis.scores.confidenceScore}%</span>
          </div>
          <p className="formula-code">
            pipeline_confidence = 25 + completeness x 35 + rule_trace_quality + tactic_coverage x 2
          </p>
          <div className="formula-math-list">
            {analysis.scores.confidenceTrace.map((component) => (
              <div key={`${component.label}-${component.value}`} className="formula-row">
                <span>{component.label}</span>
                <strong>{component.value >= 0 ? `+${component.value}` : component.value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="page-card scoring-contribution-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Confidence Contributors</p>
              <h2 className="page-card-title">Expandable Score Cards</h2>
            </div>
          </div>

          <div className="score-card-stack">
            {confidenceCards.map((component) => (
              <button
                key={component.label}
                type="button"
                className={`score-card-item ${expandedLabel === component.label ? 'is-open' : ''}`}
                onClick={() => setExpandedLabel((current) => (current === component.label ? null : component.label))}
              >
                <div className="score-card-head">
                  <div>
                    <p className="score-card-title">{component.label}</p>
                    <p className="score-card-subtitle">{component.reason}</p>
                  </div>
                  <span className="tag">+{component.value}</span>
                </div>
                <ProgressBar value={component.value} max={35} tone="cyan" />
                {expandedLabel === component.label ? (
                  <p className="score-card-detail">
                    This contribution is part of the preserved pipeline confidence formula and is computed from real
                    analysis output, not a mock narrative layer.
                  </p>
                ) : null}
              </button>
            ))}
          </div>
        </article>

        <article className="page-card evaluator-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Evaluator Mode</p>
              <h2 className="page-card-title">Benchmark Alignment</h2>
            </div>
            {evaluation ? <span className="tag">{evaluation.benchmarkScore}/100</span> : null}
          </div>

          {evaluation ? (
            <div className="evaluator-grid">
              <div className="evaluator-item">
                <span>Rule precision / recall</span>
                <strong>
                  {Math.round(evaluation.rulePrecisionLike * 100)}% / {Math.round(evaluation.ruleRecallLike * 100)}%
                </strong>
              </div>
              <div className="evaluator-item">
                <span>ATT&CK precision / recall</span>
                <strong>
                  {Math.round(evaluation.techniquePrecisionLike * 100)}% / {Math.round(evaluation.techniqueRecallLike * 100)}%
                </strong>
              </div>
              <div className="evaluator-item">
                <span>Chain order</span>
                <strong>{evaluation.chainOrderAligned ? 'Aligned' : 'Needs review'}</strong>
              </div>
              <div className="evaluator-item">
                <span>Citation coverage</span>
                <strong>{Math.round(evaluation.citationCoverage * 100)}%</strong>
              </div>
            </div>
          ) : (
            <p className="empty-state">Run a dataset-backed analysis to populate evaluator metrics.</p>
          )}
        </article>
      </div>
    </section>
  );
}
