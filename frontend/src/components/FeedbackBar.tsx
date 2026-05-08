import { useState } from 'react';

import type { AnalysisResult, FeedbackVerdict } from '../lib/types';

interface FeedbackBarProps {
  result: AnalysisResult | null;
  busy: boolean;
  onSubmit: (verdict: FeedbackVerdict, note: string) => Promise<void>;
}

const VERDICT_LABEL: Record<string, string> = {
  true_positive: 'True Positive',
  false_positive: 'False Positive',
  needs_review: 'Needs Review',
};

export function FeedbackBar({ result, busy, onSubmit }: FeedbackBarProps) {
  const [note, setNote] = useState('');
  const [lastVerdict, setLastVerdict] = useState<FeedbackVerdict | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const totalPriorFeedback = result?.similarCases.reduce((sum, item) => sum + item.count, 0) ?? 0;

  async function handleSubmit(verdict: FeedbackVerdict) {
    await onSubmit(verdict, note);
    setLastVerdict(verdict);
    setSubmitted(true);
    setNote('');
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Feedback</p>
          <h2 className="panel-title">Analyst Memory</h2>
        </div>
        {totalPriorFeedback > 0 ? (
          <span className="rounded-full border border-signal-teal/30 bg-signal-teal/10 px-3 py-1 text-xs text-signal-teal">
            {totalPriorFeedback} prior verdict{totalPriorFeedback !== 1 ? 's' : ''} loaded
          </span>
        ) : null}
      </div>

      {submitted && lastVerdict ? (
        <div className="mt-4 flex items-start gap-3 rounded-2xl border border-signal-teal/30 bg-signal-teal/10 p-4 text-sm text-signal-teal">
          <span className="mt-0.5 text-base">✓</span>
          <div>
            <p className="font-medium">Verdict saved: {VERDICT_LABEL[lastVerdict]}</p>
            <p className="mt-1 text-xs text-slate-400">
              This verdict is now stored in local analyst memory. The next analysis of the same rule set will surface
              this context in the Analyst Brief and adjust the similar-cases panel accordingly.
            </p>
          </div>
        </div>
      ) : null}

      <textarea
        className="field-input mt-4 min-h-24"
        placeholder="Add a short analyst note, false-positive rationale, or triage context."
        value={note}
        onChange={(event) => { setNote(event.target.value); setSubmitted(false); }}
        disabled={!result || busy}
      />

      <div className="mt-4 flex flex-wrap gap-3">
        <button className="secondary-button" disabled={!result || busy} onClick={() => handleSubmit('true_positive')}>
          Mark True Positive
        </button>
        <button className="secondary-button" disabled={!result || busy} onClick={() => handleSubmit('false_positive')}>
          Mark False Positive
        </button>
        <button className="secondary-button" disabled={!result || busy} onClick={() => handleSubmit('needs_review')}>
          Needs Review
        </button>
      </div>

      <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
        <p className="font-medium text-white">How the feedback loop works</p>
        <ol className="mt-2 space-y-1 text-xs text-slate-400 list-decimal list-inside">
          <li>Analyst marks a verdict (True Positive / False Positive / Needs Review).</li>
          <li>Verdict is persisted to local SQLite memory, keyed by rule IDs.</li>
          <li>Next analysis of any dataset that fires the same rules surfaces the prior verdict in the brief.</li>
          <li>The deterministic score does not change — only the context layer updates.</li>
        </ol>
      </div>

      {result?.similarCases && result.similarCases.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-signal-amber/20 bg-signal-amber/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-signal-amber">Prior analyst context loaded into this analysis</p>
          <div className="mt-3 space-y-2">
            {result.similarCases.slice(0, 4).map((item) => (
              <p key={`${item.ruleId}-${item.seenAt}`} className="text-wrap-safe text-xs">
                <span className="font-mono text-signal-teal">{item.ruleId}</span> →{' '}
                <strong className="text-white">{VERDICT_LABEL[item.verdict] ?? item.verdict}</strong> ({item.count}×
                in <span className="italic">{item.datasetName}</span>
                {item.note ? ` — "${item.note}"` : ''})
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
