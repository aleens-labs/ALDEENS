import { Fragment, useMemo, useState } from 'react';

import type { Evidence } from '../lib/types';
import { EmptyState } from '../components/shared/EmptyState';
import { useAleensApp } from '../router/AppStateContext';

interface VerificationState {
  status: 'verified' | 'mismatch' | 'missing';
  computed: string;
}

function normalizeReferenceHash(item: Evidence) {
  return (item.hash ?? item.evidenceId ?? '').replace(/[^a-fA-F0-9]/g, '').toUpperCase();
}

async function computeEvidenceHash(item: Evidence) {
  const payload = JSON.stringify(item);
  const bytes = new TextEncoder().encode(payload);
  const digest = await window.crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest))
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase();
}

export function EvidencePage() {
  const { analysis } = useAleensApp();
  const [query, setQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [verifications, setVerifications] = useState<Record<string, VerificationState>>({});

  const evidence = analysis?.evidence ?? [];
  const filtered = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    if (!lowered) {
      return evidence;
    }
    return evidence.filter((item) =>
      [
        item.process,
        item.host,
        item.user,
        item.parentProcess,
        item.commandLine,
        item.hash,
        item.evidenceId,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(lowered)),
    );
  }, [evidence, query]);

  async function handleVerify(item: Evidence) {
    const computed = await computeEvidenceHash(item);
    const reference = normalizeReferenceHash(item);
    const status =
      reference.length === 0 ? 'missing' : computed === reference || computed.startsWith(reference) ? 'verified' : 'mismatch';
    setVerifications((current) => ({
      ...current,
      [item.evidenceId]: {
        status,
        computed,
      },
    }));
  }

  if (!analysis || evidence.length === 0) {
    return (
      <section className="page-shell page-shell-center">
        <EmptyState
          title="No normalized evidence yet"
          description="Run an analysis first to inspect Windows telemetry, commands, and forensic evidence fields."
          ctaLabel="Open Intake"
          ctaTo="/intake"
        />
      </section>
    );
  }

  return (
    <section className="page-shell evidence-page">
      <article className="page-card evidence-table-card">
        <div className="page-card-head">
          <div>
            <p className="eyebrow">Normalized Evidence</p>
            <h2 className="page-card-title">Evidence Board</h2>
          </div>
          <span className="tag">
            {filtered.length}/{evidence.length}
          </span>
        </div>

        <div className="evidence-filter-row">
          <input
            type="search"
            className="field-input"
            placeholder="Filter by process, command, host, user..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <div className="evidence-table-shell">
          <table className="evidence-table">
            <thead>
              <tr>
                <th>Process</th>
                <th>Host</th>
                <th>User</th>
                <th>Parent</th>
                <th>Event ID</th>
                <th>Command</th>
                <th>Hash</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => {
                const verification = verifications[item.evidenceId];
                const isExpanded = expandedRows[item.evidenceId] ?? false;
                return (
                  <Fragment key={item.evidenceId}>
                    <tr
                      className="evidence-row"
                      onClick={() =>
                        setExpandedRows((current) => ({
                          ...current,
                          [item.evidenceId]: !current[item.evidenceId],
                        }))
                      }
                    >
                      <td>{item.process ?? 'n/a'}</td>
                      <td>{item.host ?? 'n/a'}</td>
                      <td>{item.user ?? 'n/a'}</td>
                      <td>{item.parentProcess ?? 'n/a'}</td>
                      <td>{item.eventId ?? 'n/a'}</td>
                      <td className="table-command-preview">{item.commandLine ?? 'n/a'}</td>
                      <td>
                        <div className="evidence-hash-cell">
                          <span className="evidence-hash-value">{item.hash ?? item.evidenceId}</span>
                          <button
                            type="button"
                            className="verify-button"
                            onClick={(event) => {
                              event.stopPropagation();
                              void handleVerify(item);
                            }}
                          >
                            Verify
                          </button>
                        </div>
                        {verification ? (
                          <span className={`verify-badge verify-${verification.status}`}>
                            {verification.status === 'verified'
                              ? 'Hash Verified'
                              : verification.status === 'mismatch'
                                ? 'Hash Mismatch'
                                : 'No reference hash'}
                          </span>
                        ) : null}
                      </td>
                    </tr>
                    {isExpanded ? (
                      <tr className="evidence-row-expanded">
                        <td colSpan={7}>
                          <div className="evidence-expanded-shell">
                            <p className="evidence-expanded-title">Full command line</p>
                            <code>{item.commandLine ?? 'n/a'}</code>
                            <p className="evidence-expanded-title">Summary</p>
                            <p>{item.summary}</p>
                            {verification ? (
                              <>
                                <p className="evidence-expanded-title">Computed SHA-256</p>
                                <code>{verification.computed}</code>
                              </>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
