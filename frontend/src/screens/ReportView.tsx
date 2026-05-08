import type { AnalysisResult, EvaluationResult } from '../lib/types';

interface ReportViewProps {
  result: AnalysisResult | null;
  evaluation: EvaluationResult | null;
  exportHref: (format: 'json' | 'md' | 'pdf') => string;
}

export function ReportView({ result, evaluation, exportHref }: ReportViewProps) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Export</p>
          <h2 className="panel-title">Export Report</h2>
        </div>
      </div>

      {result ? (
        <>
          <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
            <p className="font-medium text-white">How to read this result</p>
            <p className="mt-2">
              Risk shows which case should be investigated first. Confidence shows how well the visible evidence
              supports that conclusion. The report is a triage summary, not an automatic declaration that compromise is
              fully confirmed.
            </p>
          </div>

          <div className="mt-4 flex flex-wrap gap-3">
            <a
              className="primary-button"
              href={exportHref('pdf')}
              target="_blank"
              rel="noreferrer"
            >
              ↓ Export PDF
            </a>
            <a className="secondary-button" href={exportHref('json')} target="_blank" rel="noreferrer">
              ↓ Export JSON
            </a>
            <a className="secondary-button" href={exportHref('md')} target="_blank" rel="noreferrer">
              ↓ Export Markdown
            </a>
          </div>

          <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
            <p className="font-medium text-white">Safety and fallback</p>
            <p className="text-wrap-safe mt-2">{result.guardrails.reviewNote}</p>
            <p className="text-wrap-safe mt-2 text-xs text-slate-500">
              Mode requested {result.guardrails.modeRequested} | Mode used {result.guardrails.modeSelected} | Redactions{' '}
              {result.guardrails.payloadRedactions}
            </p>
          </div>

          {evaluation ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="font-medium text-white">Evaluator Mode</p>
              <p className="mt-2">Benchmark score: {evaluation.benchmarkScore}/100</p>
              <p className="mt-2">
                Rule precision {Math.round(evaluation.rulePrecisionLike * 100)}% | Rule recall{' '}
                {Math.round(evaluation.ruleRecallLike * 100)}%
              </p>
              <p className="mt-2">
                ATT&CK precision {Math.round(evaluation.techniquePrecisionLike * 100)}% | ATT&CK recall{' '}
                {Math.round(evaluation.techniqueRecallLike * 100)}%
              </p>
              <p className="mt-2">
                Chain order {evaluation.chainOrderAligned ? 'aligned' : 'not aligned'} | Citation coverage{' '}
                {Math.round(evaluation.citationCoverage * 100)}%
              </p>
              <p className="mt-2">
                Exports {evaluation.exportsReady ? 'ready' : 'incomplete'} | Risk aligned{' '}
                {evaluation.riskAligned ? 'yes' : 'no'}
              </p>
              <p className="text-wrap-safe mt-2">Missing rules: {evaluation.missingRules.join(', ') || 'none'}</p>
              <p className="text-wrap-safe mt-2">
                Missing techniques: {evaluation.missingTechniques.join(', ') || 'none'}
              </p>
              <p className="text-wrap-safe mt-2">Missing sections: {evaluation.missingSections.join(', ') || 'none'}</p>
              {evaluation.benchmarkSource ? (
                <p className="text-wrap-safe mt-2 text-xs text-slate-500">
                  Benchmark source: {evaluation.benchmarkSource.sourceName} | {evaluation.benchmarkSource.benchmarkType}
                </p>
              ) : null}
            </div>
          ) : null}
        </>
      ) : (
        <p className="empty-state">Exports become available once an analysis result exists.</p>
      )}
    </section>
  );
}
