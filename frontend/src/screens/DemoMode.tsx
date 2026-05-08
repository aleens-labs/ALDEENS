import type { BenchmarkPackResult, EvaluationResult } from '../lib/types';

interface DemoModeProps {
  onRun: () => void;
  onRunAmbiguousDemo: () => void;
  onRunPublicBenchmarks: () => void;
  busy: boolean;
  evaluation: EvaluationResult | null;
  ambiguousEvaluation: EvaluationResult | null;
  benchmarkPack: BenchmarkPackResult | null;
}

export function DemoMode({
  onRun,
  onRunAmbiguousDemo,
  onRunPublicBenchmarks,
  busy,
  evaluation,
  ambiguousEvaluation,
  benchmarkPack,
}: DemoModeProps) {
  const passedDatasets = benchmarkPack
    ? Math.round(benchmarkPack.passRate * benchmarkPack.datasetCount)
    : 0;

  return (
    <section className="hero-shell animate-rise">
      <div className="max-w-3xl">
        <p className="eyebrow">Aleens - Windows Incident Triage Assistant</p>
        <h1 className="hero-title">Turn confusing Windows security logs into a prioritized incident summary.</h1>
        <p className="hero-copy">
          Aleens helps analysts answer three questions faster: what likely happened, how urgent it is, and which
          log evidence supports that conclusion. Deterministic evidence extraction, ATT&amp;CK mapping, scoring, audit
          logging, and analyst memory come first; an optional LLM only rewrites those structured findings into a clearer
          narrative.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <span className="signal-pill">Weighted rule engine</span>
          <span className="tag">Explainable score trace</span>
          <span className="tag">Optional LLM narrative</span>
          <span className="tag">Analyst feedback loop</span>
          <span className="tag">Local-first</span>
        </div>
      </div>

      <div className="mt-6 grid gap-3 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">What it helps with</p>
          <p className="mt-2">Prioritizing suspicious Windows activity so an analyst knows which case to review first.</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">What Critical means</p>
          <p className="mt-2">
            Critical means the pattern looks highly suspicious and should be investigated first, not that compromise is
            already proven.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">How to start</p>
          <p className="mt-2">Upload exported Windows, Sysmon, or Defender JSON, or begin with a bundled reference incident.</p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button className="primary-button" onClick={onRun} disabled={busy}>
          {busy ? 'Running...' : 'Analyze Reference Attack Chain'}
        </button>
        <button className="secondary-button" onClick={onRunAmbiguousDemo} disabled={busy}>
          {busy ? 'Running...' : 'Analyze Ambiguous Reference Case'}
        </button>
        <button className="secondary-button" onClick={onRunPublicBenchmarks} disabled={busy}>
          {busy ? 'Benchmarking...' : 'Validate Public OTRF Fixture Pack'}
        </button>
      </div>

      {(evaluation || ambiguousEvaluation || benchmarkPack) ? (
        <div className="mt-4 flex flex-wrap gap-3">
          {evaluation ? (
            <div className="text-wrap-safe rounded-2xl border border-signal-teal/25 bg-signal-teal/10 px-4 py-3 text-sm text-slate-100">
              <span className="font-medium text-signal-teal">Reference attack chain</span> - benchmark{' '}
              {evaluation.benchmarkScore}/100 | rule recall {Math.round(evaluation.ruleRecallLike * 100)}% | ATT&amp;CK{' '}
              {Math.round(evaluation.techniqueRecallLike * 100)}%
            </div>
          ) : null}
          {ambiguousEvaluation ? (
            <div className="text-wrap-safe rounded-2xl border border-signal-amber/25 bg-signal-amber/10 px-4 py-3 text-sm text-slate-100">
              <span className="font-medium text-signal-amber">Ambiguous reference case</span> - benchmark{' '}
              {ambiguousEvaluation.benchmarkScore}/100 | risk {ambiguousEvaluation.riskAligned ? 'Low ok' : 'misaligned'}{' '}
              | {ambiguousEvaluation.falsePositivePressureOk ? 'no false positives' : 'FP pressure'}
            </div>
          ) : null}
          {benchmarkPack ? (
            <div className="text-wrap-safe rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-100">
              Public fixtures {passedDatasets}/{benchmarkPack.datasetCount} passed | avg benchmark{' '}
              {benchmarkPack.averageBenchmarkScore}/100 | avg rule recall{' '}
              {Math.round(benchmarkPack.averageRuleRecall * 100)}%
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
