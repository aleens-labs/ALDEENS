import { useEffect, useMemo, useState } from 'react';

import { Check, Clipboard, Download, FileJson, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

import { EmptyState } from '../components/shared/EmptyState';
import { useAleensApp } from '../router/AppStateContext';

export function AnalystBriefPage() {
  const {
    analysis,
    analystOverride,
    downloadExport,
    handleFeedback,
    saveAnalystOverride,
  } = useAleensApp();
  const [copied, setCopied] = useState(false);
  const [feedbackNote, setFeedbackNote] = useState('');
  const [overrideValue, setOverrideValue] = useState(analystOverride?.value ?? 75);
  const [overrideNote, setOverrideNote] = useState(analystOverride?.note ?? '');

  const briefMarkdownText = analysis?.analystBrief ?? '';
  const llmMeta = useMemo(() => {
    if (!analysis) {
      return null;
    }
    return analysis.audit.llmModel
      ? `${analysis.audit.llmModel}${analysis.audit.providerRequestId ? ` | ${analysis.audit.providerRequestId}` : ''}`
      : 'Deterministic template mode';
  }, [analysis]);

  useEffect(() => {
    if (!analysis) {
      return;
    }
    const nextValue = analystOverride?.analysisId === analysis.analysisId ? analystOverride.value : analysis.scores.confidenceScore;
    const nextNote = analystOverride?.analysisId === analysis.analysisId ? analystOverride.note : '';
    setOverrideValue(nextValue);
    setOverrideNote(nextNote);
  }, [analysis, analystOverride]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(briefMarkdownText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = briefMarkdownText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    }
  }

  if (!analysis) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No analyst brief loaded"
          description="Run an incident first to render the narrative, exports, and feedback workspace."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  const activeOverride = analystOverride?.analysisId === analysis.analysisId ? analystOverride : null;

  return (
    <section className="page-shell analyst-brief-page">
      <div className="brief-grid">
        <article className="page-card brief-markdown-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Narrative</p>
              <h2 className="page-card-title">Analyst Brief</h2>
            </div>
            <span className="tag">{analysis.reportMode.toUpperCase()}</span>
          </div>
          <div className="markdown-shell brief-markdown">
            <ReactMarkdown>{briefMarkdownText}</ReactMarkdown>
          </div>
        </article>

        <aside className="page-card brief-action-card">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Actions</p>
              <h2 className="page-card-title">Export & Verdicts</h2>
            </div>
          </div>

          <p className="brief-model-meta">{llmMeta}</p>

          <div className="brief-action-stack">
            <button
              type="button"
              onClick={() => void handleCopy()}
              className={`copy-feedback-button ${copied ? 'is-copied' : ''}`}
            >
              {copied ? <Check size={16} /> : <Clipboard size={16} />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>

            <button type="button" onClick={() => void downloadExport('pdf')} className="secondary-button">
              <Download size={16} />
              <span>Export PDF</span>
            </button>
            <button type="button" onClick={() => void downloadExport('json')} className="secondary-button">
              <FileJson size={16} />
              <span>Export JSON</span>
            </button>
            <button type="button" onClick={() => void downloadExport('md')} className="secondary-button">
              <FileText size={16} />
              <span>Export MD</span>
            </button>
          </div>

          <div className="brief-feedback-section">
            <p className="brief-section-title">Analyst Memory</p>
            <textarea
              className="field-input brief-textarea"
              value={feedbackNote}
              onChange={(event) => setFeedbackNote(event.target.value)}
              placeholder="Add triage rationale, context, or false-positive notes."
            />
            <div className="brief-verdict-grid">
              <button type="button" className="verdict-button verdict-true" onClick={() => void handleFeedback('true_positive', feedbackNote)}>
                True Positive
              </button>
              <button type="button" className="verdict-button verdict-false" onClick={() => void handleFeedback('false_positive', feedbackNote)}>
                False Positive
              </button>
              <button type="button" className="verdict-button verdict-review" onClick={() => void handleFeedback('needs_review', feedbackNote)}>
                ? Needs Review
              </button>
            </div>

            <details className="brief-details">
              <summary>How the feedback loop works</summary>
              <ul>
                <li>Verdicts are persisted from the analyst workflow and surfaced on future matching rule sets.</li>
                <li>Feedback adds human context without overriding the deterministic scoring engine.</li>
                <li>Notes travel with the same rule families to reduce repeated triage effort.</li>
                <li>PIONEER: Ready for backend confidence-calibration storage when the research schema is expanded.</li>
              </ul>
            </details>
          </div>

          <div className="brief-feedback-section">
            <p className="brief-section-title">Analyst Override</p>
            <p className="brief-model-meta">
              System: {analysis.scores.confidenceScore}%{activeOverride ? ` | Analyst: ${activeOverride.value}%` : ''}
            </p>
            <input
              type="range"
              min={0}
              max={100}
              value={overrideValue}
              onChange={(event) => setOverrideValue(Number(event.target.value))}
              className="override-slider"
            />
            <div className="override-label-row">
              <span>0</span>
              <strong>{overrideValue}%</strong>
              <span>100</span>
            </div>
            <textarea
              className="field-input brief-textarea"
              value={overrideNote}
              onChange={(event) => setOverrideNote(event.target.value)}
              placeholder="Why does analyst confidence differ from the automated pipeline?"
            />
            <button type="button" className="primary-button" onClick={() => void saveAnalystOverride(overrideValue, overrideNote)}>
              Save Analyst Override
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}
