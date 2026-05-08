import type { ChangeEvent } from 'react';

import { AlertTriangle, Bot, DatabaseZap, ShieldCheck } from 'lucide-react';

import { APP_NAME } from '../lib/branding';
import { TacticBadge } from '../components/shared/TacticBadge';
import { useAleensApp } from '../router/AppStateContext';

export function IntakePage() {
  const {
    datasets,
    selectedDataset,
    reportMode,
    status,
    selectedFile,
    setSelectedDataset,
    setReportMode,
    setSelectedFile,
    runAnalysis,
    runAmbiguousDemo,
    runPublicBenchmarkPack,
  } = useAleensApp();

  const selected = datasets.find((item) => item.datasetId === selectedDataset) ?? null;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  return (
    <section className="page-shell intake-page">
      <div className="intake-grid">
        <article className="page-card intake-actions">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Incident Input</p>
              <h2 className="page-card-title">Choose data source</h2>
            </div>
            <span className="signal-pill">Local-first</span>
          </div>

          <label className="field-label">Reference Incident</label>
          <select
            className="field-input"
            value={selectedDataset}
            onChange={(event) => setSelectedDataset(event.target.value)}
          >
            {datasets.map((dataset) => (
              <option key={dataset.datasetId} value={dataset.datasetId}>
                {dataset.title}
              </option>
            ))}
          </select>

          <label className="field-label">Narrative Mode</label>
          <select
            className="field-input"
            value={reportMode}
            onChange={(event) => setReportMode(event.target.value as typeof reportMode)}
          >
            <option value="template">Deterministic Template</option>
            <option value="llm" disabled={!status?.llmAvailable}>
              LLM Narrative{status?.llmAvailable ? '' : ' (API key required)'}
            </option>
          </select>
          <p className="intake-helper-text">
            {status?.llmAvailable
              ? `LLM narrative is available via ${status.llmModel ?? 'the configured provider'}, but the findings remain constrained by structured evidence and guardrails.`
              : `No LLM key is active, so ${APP_NAME} will stay in deterministic template mode.`}
          </p>

          <label className="field-label">Upload JSON</label>
          <label className="upload-drop intake-upload">
            <input type="file" accept=".json,application/json" className="hidden" onChange={handleFileChange} />
            <div className="intake-upload-copy">
              <DatabaseZap size={18} className="text-signal-teal" />
              <div>
                <p>{selectedFile ? `Queued: ${selectedFile.name}` : 'Drop Sysmon or Defender JSON here'}</p>
                <span>Exported Windows telemetry from a lab or real environment</span>
              </div>
            </div>
          </label>

          <div className="intake-action-stack">
            <button type="button" className="primary-button" onClick={() => void runAnalysis(false)}>
              Analyze Incident
            </button>
            <div className="intake-secondary-actions">
              <button type="button" className="secondary-button" onClick={() => void runAnalysis(true)}>
                Analyze Reference Attack Chain
              </button>
              <button type="button" className="secondary-button" onClick={() => void runAmbiguousDemo()}>
                Analyze Ambiguous Reference Case
              </button>
            </div>
            <button type="button" className="secondary-button" onClick={() => void runPublicBenchmarkPack()}>
              Validate Public OTRF Fixture Pack
            </button>
          </div>
        </article>

        <article className="page-card intake-preview">
          <div className="page-card-head">
            <div>
              <p className="eyebrow">Source Preview</p>
              <h2 className="page-card-title">{selected?.title ?? 'No dataset selected'}</h2>
            </div>
            <div className="intake-status-badges">
              {selected?.benchmarkTier === 'public-upstream' ? (
                <span className="tag">Public Upstream Fixture</span>
              ) : (
                <span className="tag">Reference Incident</span>
              )}
              {selected?.collectionType ? <span className="tag">{selected.collectionType}</span> : null}
            </div>
          </div>

          {selected ? (
            <>
              <div className="intake-preview-hero">
                <div className="intake-preview-callout">
                  <AlertTriangle size={18} />
                  <p>{selected.attackDescription}</p>
                </div>
                <p className="intake-preview-description">{selected.description}</p>
              </div>

              <div className="intake-preview-grid">
                <div className="intake-preview-stat">
                  <ShieldCheck size={18} className="text-signal-teal" />
                  <div>
                    <span>Source</span>
                    <p>{selected.sourceName}</p>
                  </div>
                </div>
                <div className="intake-preview-stat">
                  <Bot size={18} className="text-signal-teal" />
                  <div>
                    <span>Report mode</span>
                    <p>{reportMode === 'llm' ? 'LLM narrative' : 'Deterministic template'}</p>
                  </div>
                </div>
              </div>

              <div className="intake-technique-cloud">
                {selected.techniques.map((technique) => (
                  <TacticBadge
                    key={technique}
                    tactic={technique}
                    className="technique-pill"
                  />
                ))}
              </div>

              <div className="intake-mitre-reference">
                <p className="eyebrow">Expected technique tags</p>
                <div className="intake-technique-tags">
                  {selected.techniques.map((technique) => (
                    <span key={technique} className="tag">
                      {technique}
                    </span>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <p className="empty-state">Select a source to review its provenance metadata and expected ATT&CK tags.</p>
          )}
        </article>
      </div>
    </section>
  );
}
