import type { ChangeEvent } from 'react';

import { APP_NAME } from '../lib/branding';
import type { DatasetSummary, ReportMode } from '../lib/types';

interface IntakePanelProps {
  datasets: DatasetSummary[];
  selectedDataset: string;
  reportMode: ReportMode;
  llmAvailable: boolean;
  llmModel: string;
  busy: boolean;
  fileName: string | null;
  onDatasetChange: (value: string) => void;
  onReportModeChange: (value: ReportMode) => void;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
  onRunDemo: () => void;
}

export function IntakePanel({
  datasets,
  selectedDataset,
  reportMode,
  llmAvailable,
  llmModel,
  busy,
  fileName,
  onDatasetChange,
  onReportModeChange,
  onFileChange,
  onAnalyze,
  onRunDemo,
}: IntakePanelProps) {
  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    onFileChange(event.target.files?.[0] ?? null);
  }

  const selected = datasets.find((dataset) => dataset.datasetId === selectedDataset);

  return (
    <section className="panel animate-rise">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Intake</p>
          <h2 className="panel-title">Incident Input</h2>
        </div>
        <span className="signal-pill">Local-first</span>
      </div>

      <p className="text-sm text-slate-400">
        Upload suspicious Windows telemetry or start with a reference incident. {APP_NAME} helps prioritize review and
        explain the evidence; it does not automatically prove compromise.
      </p>

      <label className="field-label">Reference Incident</label>
      <select
        className="field-input"
        value={selectedDataset}
        onChange={(event) => onDatasetChange(event.target.value)}
        disabled={busy}
      >
        {datasets.map((dataset) => (
          <option key={dataset.datasetId} value={dataset.datasetId}>
            {dataset.title}
          </option>
        ))}
      </select>

      {selected ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <p className="font-medium text-white">{selected.attackDescription}</p>
          <p className="mt-2 text-slate-400">{selected.description}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
            <span className="rounded-full border border-white/10 px-3 py-1">
              {selected.benchmarkTier === 'public-upstream' ? 'Public upstream fixture' : 'Reference incident'}
            </span>
            <span className="rounded-full border border-white/10 px-3 py-1">{selected.collectionType}</span>
          </div>
          <p className="mt-3 text-xs text-slate-500">{selected.sourceName}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {selected.techniques.map((technique) => (
              <span key={technique} className="tag">
                {technique}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <label className="field-label mt-5">Report Mode</label>
      <select
        className="field-input"
        value={reportMode}
        onChange={(event) => onReportModeChange(event.target.value as ReportMode)}
        disabled={busy}
      >
        <option value="template">Deterministic Template</option>
        <option value="llm" disabled={!llmAvailable}>
          LLM Narrative{llmAvailable ? '' : ' (API key required)'}
        </option>
      </select>
      <p className="mt-2 text-xs text-slate-500">
        {llmAvailable
          ? `Optional LLM narrative is available via ${llmModel ?? 'the configured provider'}; the report still stays grounded in structured findings and guardrails.`
          : `No API key is configured, so ${APP_NAME} will stay in deterministic template mode.`}
      </p>

      <label className="field-label mt-5">Upload JSON</label>
      <label className="upload-drop">
        <input type="file" accept=".json,application/json" className="hidden" onChange={handleFileSelect} />
        <span className="text-sm text-slate-200">
          {fileName ? `Queued: ${fileName}` : 'Drop a Sysmon or Defender-style JSON export here'}
        </span>
        <span className="text-xs text-slate-500">Use exported Windows, Sysmon, or Defender JSON from a lab or real environment.</span>
      </label>

      <div className="mt-5 grid gap-3">
        <button className="primary-button" onClick={onAnalyze} disabled={busy}>
          {busy ? 'Analyzing...' : 'Analyze Incident'}
        </button>
        <button className="secondary-button" onClick={onRunDemo} disabled={busy}>
          Analyze Reference Incident
        </button>
      </div>
    </section>
  );
}
