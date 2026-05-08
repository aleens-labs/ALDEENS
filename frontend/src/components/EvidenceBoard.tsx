import { useState } from 'react';
import type { Evidence } from '../lib/types';

interface EvidenceBoardProps {
  evidence: Evidence[];
}

export function EvidenceBoard({ evidence }: EvidenceBoardProps) {
  const [query, setQuery] = useState('');

  const filtered = query.trim()
    ? evidence.filter((item) => {
        const q = query.toLowerCase();
        return (
          (item.process ?? '').toLowerCase().includes(q) ||
          (item.summary ?? '').toLowerCase().includes(q) ||
          (item.commandLine ?? '').toLowerCase().includes(q) ||
          (item.host ?? '').toLowerCase().includes(q) ||
          (item.user ?? '').toLowerCase().includes(q) ||
          (item.evidenceId ?? '').toLowerCase().includes(q)
        );
      })
    : evidence;

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Evidence</p>
          <h2 className="panel-title">Normalized Evidence Board</h2>
        </div>
        {evidence.length > 0 && (
          <span className="tag">{filtered.length}/{evidence.length}</span>
        )}
      </div>

      {evidence.length > 0 && (
        <div className="mt-3">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by process, command, host, user…"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 placeholder-slate-600 outline-none focus:border-signal-teal/50 focus:ring-1 focus:ring-signal-teal/30"
          />
        </div>
      )}

      {evidence.length === 0 ? (
        <p className="empty-state">Upload an incident dataset or JSON export to populate evidence.</p>
      ) : filtered.length === 0 ? (
        <p className="empty-state">No evidence matches "{query}".</p>
      ) : (
        <div className="mt-4 grid gap-3 2xl:grid-cols-2">
          {filtered.map((item) => (
            <article key={item.evidenceId} className="evidence-card">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <span className="font-medium text-white">{item.process ?? 'unknown-process'}</span>
                <span className="text-wrap-safe text-xs uppercase tracking-[0.24em] text-slate-500">
                  {item.evidenceId}
                </span>
              </div>
              <p className="text-wrap-safe mt-2 text-sm text-slate-300">{item.summary}</p>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-400">
                <div>
                  <dt className="text-slate-500">Host</dt>
                  <dd className="text-wrap-safe">{item.host ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">User</dt>
                  <dd className="text-wrap-safe">{item.user ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Parent</dt>
                  <dd className="text-wrap-safe">{item.parentProcess ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Event</dt>
                  <dd>{item.eventId ?? 'n/a'}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-slate-500">Command</dt>
                  <dd className="text-wrap-safe mt-1 text-slate-300">{item.commandLine ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Target</dt>
                  <dd className="text-wrap-safe">{item.targetProcess ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Destination</dt>
                  <dd className="text-wrap-safe">{item.destinationDomain ?? item.destinationIp ?? 'n/a'}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
