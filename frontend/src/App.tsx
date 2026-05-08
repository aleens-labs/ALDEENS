import { useEffect, useState } from 'react';

import { APP_NAME } from './lib/branding';
import {
  analyzeDataset,
  evaluateDataset,
  exportHref as buildExportHref,
  getAudit,
  getPublicBenchmarks,
  getDatasets,
  getStatus,
  sendFeedback,
  uploadLogs,
} from './lib/api';
import type {
  AnalysisResult,
  AppStatus,
  AuditEntry,
  BenchmarkPackResult,
  DatasetSummary,
  EvaluationResult,
  FeedbackVerdict,
  ReportMode,
} from './lib/types';
import { Dashboard } from './screens/Dashboard';

function App() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [selectedDataset, setSelectedDataset] = useState('officeToPowerShell');
  const [reportMode, setReportMode] = useState<ReportMode>('template');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [ambiguousEvaluation, setAmbiguousEvaluation] = useState<EvaluationResult | null>(null);
  const [benchmarkPack, setBenchmarkPack] = useState<BenchmarkPackResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [datasetList, auditPage, appStatus] = await Promise.all([getDatasets(), getAudit(50), getStatus()]);
        setDatasets(datasetList);
        setAudit(auditPage.items);
        setStatus(appStatus);
        setReportMode(appStatus.llmAvailable ? appStatus.defaultReportMode : 'template');
        if (datasetList.length > 0) {
          setSelectedDataset(datasetList[0].datasetId);
        }
      } catch (bootstrapError) {
        setError(bootstrapError instanceof Error ? bootstrapError.message : `Failed to load ${APP_NAME}.`);
      }
    }
    void bootstrap();
  }, []);

  async function refreshAudit() {
    const auditPage = await getAudit(50);
    setAudit(auditPage.items);
  }

  async function runAnalysis(forceDemo = false) {
    setBusy(true);
    setError(null);
    try {
      const isUpload = Boolean(selectedFile) && !forceDemo;
      const datasetId = forceDemo ? 'officeToPowerShell' : selectedDataset;
      const result = isUpload
        ? await uploadLogs(selectedFile as File, reportMode)
        : await analyzeDataset(datasetId, reportMode);
      setAnalysis(result);
      if (isUpload) {
        setEvaluation(null);
      } else {
        const referenceEvaluation = await evaluateDataset(datasetId, result.analysisId, reportMode);
        setEvaluation(referenceEvaluation);
      }
      await refreshAudit();
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Analysis failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runAmbiguousDemo() {
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeDataset('adminPowerShellInventory', reportMode);
      setAnalysis(result);
      const ev = await evaluateDataset('adminPowerShellInventory', result.analysisId, reportMode);
      setAmbiguousEvaluation(ev);
      await refreshAudit();
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Ambiguous reference case failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runPublicBenchmarkPack() {
    setBusy(true);
    setError(null);
    try {
      const pack = await getPublicBenchmarks(reportMode);
      setBenchmarkPack(pack);
      await refreshAudit();
    } catch (benchmarkError) {
      setError(benchmarkError instanceof Error ? benchmarkError.message : 'Failed to run public benchmark pack.');
    } finally {
      setBusy(false);
    }
  }

  async function handleFeedback(verdict: FeedbackVerdict, note: string) {
    if (!analysis) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await sendFeedback(
        analysis.analysisId,
        analysis.datasetName,
        verdict,
        note,
        analysis.findings.map((finding) => finding.ruleId),
      );
      await refreshAudit();
      const refreshed =
        selectedFile && analysis.datasetName === selectedFile.name
          ? await uploadLogs(selectedFile, reportMode)
          : await analyzeDataset(analysis.datasetName, reportMode);
      setAnalysis(refreshed);
    } catch (feedbackError) {
      setError(feedbackError instanceof Error ? feedbackError.message : 'Failed to save feedback.');
    } finally {
      setBusy(false);
    }
  }

  function exportLink(format: 'json' | 'md' | 'pdf') {
    if (!analysis) {
      return '#';
    }
    return buildExportHref(analysis.analysisId, format);
  }

  return (
    <Dashboard
      datasets={datasets}
      selectedDataset={selectedDataset}
      reportMode={reportMode}
      llmAvailable={status?.llmAvailable ?? false}
      llmModel={status?.llmModel ?? 'template-only'}
      selectedFileName={selectedFile?.name ?? null}
      analysis={analysis}
      audit={audit}
      evaluation={evaluation}
      ambiguousEvaluation={ambiguousEvaluation}
      benchmarkPack={benchmarkPack}
      busy={busy}
      error={error}
      onDatasetChange={setSelectedDataset}
      onReportModeChange={setReportMode}
      onFileChange={setSelectedFile}
      onAnalyze={() => void runAnalysis(false)}
      onRunDemo={() => void runAnalysis(true)}
      onRunAmbiguousDemo={() => void runAmbiguousDemo()}
      onRunPublicBenchmarks={() => void runPublicBenchmarkPack()}
      onFeedback={handleFeedback}
      exportHref={exportLink}
    />
  );
}

export default App;
