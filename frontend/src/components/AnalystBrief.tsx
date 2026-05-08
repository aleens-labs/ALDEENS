import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface AnalystBriefProps {
  brief: string;
  exportHref?: (format: 'json' | 'md' | 'pdf') => string;
}

export function AnalystBrief({ brief, exportHref }: AnalystBriefProps) {
  const [copied, setCopied] = useState(false);

  async function copyBrief() {
    await navigator.clipboard.writeText(brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="panel h-full min-w-0">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Narrative</p>
          <h2 className="panel-title">Analyst Brief</h2>
        </div>
        {brief ? (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={copyBrief}
              className="inline-flex items-center gap-1 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
            {exportHref ? (
              <a
                href={exportHref('pdf')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-xl border border-signal-teal/30 bg-signal-teal/10 px-3 py-1.5 text-xs font-semibold text-signal-teal transition hover:bg-signal-teal/20"
              >
                Export PDF
              </a>
            ) : null}
          </div>
        ) : null}
      </div>

      {brief ? (
        <div className="markdown-shell text-wrap-safe mt-4">
          <ReactMarkdown>{brief}</ReactMarkdown>
        </div>
      ) : (
        <p className="empty-state">Run an analysis to generate the analyst brief.</p>
      )}
    </section>
  );
}
