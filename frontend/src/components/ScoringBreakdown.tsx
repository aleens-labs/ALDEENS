import type { AnalysisResult, ScoreComponent } from '../lib/types';

interface ScoringBreakdownProps {
  result: AnalysisResult | null;
}

function componentBarWidth(value: number, maxValue: number) {
  return `${Math.max(8, Math.round((Math.abs(value) / Math.max(1, maxValue)) * 100))}%`;
}

function traceRow(component: ScoreComponent, maxValue: number, tone: string) {
  return (
    <div key={`${component.label}-${component.value}`} className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white">{component.label}</p>
          <p className="text-wrap-safe mt-1 text-xs text-slate-400">{component.reason}</p>
        </div>
        <span className="tag">{component.value >= 0 ? `+${component.value}` : component.value}</span>
      </div>
      <div className="mt-3 h-2 rounded-full bg-white/5">
        <div className={`h-2 rounded-full ${tone}`} style={{ width: componentBarWidth(component.value, maxValue) }} />
      </div>
    </div>
  );
}

export function ScoringBreakdown({ result }: ScoringBreakdownProps) {
  if (!result) {
    return (
      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Scoring</p>
            <h2 className="panel-title">Why This Scored This Way</h2>
          </div>
        </div>
        <p className="empty-state">Run an analysis to inspect deterministic risk and confidence contributions.</p>
      </section>
    );
  }

  const riskMax = Math.max(...result.scores.scoreTrace.map((item) => Math.abs(item.value)), 1);
  const confidenceMax = Math.max(...result.scores.confidenceTrace.map((item) => Math.abs(item.value)), 1);

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Scoring</p>
          <h2 className="panel-title">Why This Scored This Way</h2>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">Risk score formula</p>
          <p className="text-wrap-safe mt-2 font-mono text-xs text-slate-400">
            risk = Σ(rule_contributions) + tactic_diversity_bonus − evidence_gap_penalty
          </p>
          <p className="text-wrap-safe mt-2">
            Each fired rule adds its fixed weight. Three or more distinct ATT&CK tactics add +10. Missing evidence
            fields reduce the score by 5–15 depending on completeness ratio.
          </p>
        </div>
        <div className="rounded-2xl border border-signal-teal/20 bg-signal-teal/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">
            Why overall confidence differs from per-technique confidence
          </p>
          <p className="text-wrap-safe mt-2 font-mono text-xs text-slate-400">
            pipeline_confidence = 25 (baseline) + completeness×35 + rule_trace_quality + tactic_coverage×2
          </p>
          <p className="text-wrap-safe mt-2">
            Per-technique confidence (e.g. T1071 = 16%) is the rule-weight for that single ATT&CK mapping, calibrated
            on a 0–1 scale. Pipeline confidence (e.g. 97%) measures overall evidence quality across the full analysis:
            completeness ratio, number of corroborating rules, and tactic breadth. They are independent dimensions —
            a single weak rule can fire at low per-technique confidence while the pipeline still has strong evidence
            coverage.
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <div className="space-y-3">
          <div>
            <p className="text-sm font-semibold text-white">Risk contributors</p>
            <p className="mt-1 text-xs text-slate-500">
              Final risk: {result.scores.riskScore}/100 ({result.scores.riskLabel})
            </p>
          </div>
          {result.scores.scoreTrace.map((component) =>
            traceRow(
              component,
              riskMax,
              component.value >= 0 ? 'bg-gradient-to-r from-signal-coral to-signal-amber' : 'bg-slate-500',
            ),
          )}
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-sm font-semibold text-white">Confidence contributors</p>
            <p className="mt-1 text-xs text-slate-500">Final confidence: {result.scores.confidenceScore}/100</p>
          </div>
          {result.scores.confidenceTrace.map((component) =>
            traceRow(component, confidenceMax, 'bg-gradient-to-r from-signal-teal to-signal-sky'),
          )}
        </div>
      </div>
    </section>
  );
}
