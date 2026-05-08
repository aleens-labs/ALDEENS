import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom';

import {
  analyzeDataset,
  evaluateDataset,
  downloadExport as fetchExport,
  exportHref as buildExportHref,
  getAnalysis,
  getAudit,
  getConfidenceOverride,
  getPublicBenchmarks,
  getDatasets,
  getStatus,
  saveConfidenceOverride as postConfidenceOverride,
  sendFeedback,
  uploadLogs,
} from '../lib/api';
import type {
  AnalysisResult,
  AppStatus,
  AuditEntry,
  BenchmarkPackResult,
  DatasetSummary,
  EvaluationResult,
  FeedbackVerdict,
  ReportMode,
} from '../lib/types';
import { AppShell } from '../components/layout/AppShell';
import { EmptyState } from '../components/shared/EmptyState';
import { APP_NAME } from '../lib/branding';
import { AppStateProvider, type AleensAppState, type AnalystOverrideState } from './AppStateContext';

const DashboardPage = lazy(() => import('../pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const IntakePage = lazy(() => import('../pages/IntakePage').then((module) => ({ default: module.IntakePage })));
const AttackGraphPage = lazy(() => import('../pages/AttackGraphPage').then((module) => ({ default: module.AttackGraphPage })));
const TimelinePage = lazy(() => import('../pages/TimelinePage').then((module) => ({ default: module.TimelinePage })));
const ScoringPage = lazy(() => import('../pages/ScoringPage').then((module) => ({ default: module.ScoringPage })));
const EvidencePage = lazy(() => import('../pages/EvidencePage').then((module) => ({ default: module.EvidencePage })));
const MitrePage = lazy(() => import('../pages/MitrePage').then((module) => ({ default: module.MitrePage })));
const AnalystBriefPage = lazy(() => import('../pages/AnalystBriefPage').then((module) => ({ default: module.AnalystBriefPage })));
const AuditPage = lazy(() => import('../pages/AuditPage').then((module) => ({ default: module.AuditPage })));

const LAST_ANALYSIS_KEY = 'aleens.lastAnalysisId';
const AUDIT_PAGE_SIZE = 50;

function AppRouterController() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [selectedDataset, setSelectedDataset] = useState('officeToPowerShell');
  const [reportMode, setReportMode] = useState<ReportMode>('template');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [auditNextCursor, setAuditNextCursor] = useState<string | null>(null);
  const [auditHasMore, setAuditHasMore] = useState(false);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditLoadingMore, setAuditLoadingMore] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [ambiguousEvaluation, setAmbiguousEvaluation] = useState<EvaluationResult | null>(null);
  const [benchmarkPack, setBenchmarkPack] = useState<BenchmarkPackResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compareSelection, setCompareSelection] = useState<string[]>([]);
  const [analystOverride, setAnalystOverride] = useState<AnalystOverrideState | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [datasetList, auditPage, appStatus] = await Promise.all([
          getDatasets(),
          getAudit(AUDIT_PAGE_SIZE),
          getStatus(),
        ]);
        setDatasets(datasetList);
        setAudit(auditPage.items);
        setAuditNextCursor(auditPage.nextCursor);
        setAuditHasMore(auditPage.hasMore);
        setAuditTotal(auditPage.total);
        setStatus(appStatus);
        setReportMode(appStatus.llmAvailable ? appStatus.defaultReportMode : 'template');
        if (datasetList.length > 0) {
          setSelectedDataset((current) => current || datasetList[0].datasetId);
        }

        const persistedAnalysisId = window.localStorage.getItem(LAST_ANALYSIS_KEY) ?? auditPage.items[0]?.analysisId;
        if (persistedAnalysisId) {
          try {
            const restored = await getAnalysis(persistedAnalysisId);
            setAnalysis(restored);
            const datasetExists = datasetList.some((item) => item.datasetId === restored.datasetName);
            if (datasetExists) {
              const restoredEvaluation = await evaluateDataset(
                restored.datasetName,
                restored.analysisId,
                restored.reportMode as ReportMode,
              );
              setEvaluation(restoredEvaluation);
            }
          } catch {
            window.localStorage.removeItem(LAST_ANALYSIS_KEY);
          }
        }
      } catch (bootstrapError) {
        setError(bootstrapError instanceof Error ? bootstrapError.message : `Failed to load ${APP_NAME}.`);
      }
    }
    void bootstrap();
  }, []);

  function persistLastAnalysisId(analysisId: string) {
    window.localStorage.setItem(LAST_ANALYSIS_KEY, analysisId);
  }

  useEffect(() => {
    async function syncOverride() {
      if (!analysis) {
        setAnalystOverride(null);
        return;
      }
      try {
        const response = await getConfidenceOverride(analysis.analysisId);
        if (response.analystConfidence == null) {
          setAnalystOverride(null);
          return;
        }
        setAnalystOverride({
          analysisId: analysis.analysisId,
          datasetName: analysis.datasetName,
          value: response.analystConfidence,
          note: response.overrideNote ?? '',
          savedAt: response.createdAt ?? '',
        });
      } catch {
        setAnalystOverride(null);
      }
    }

    void syncOverride();
  }, [analysis]);

  async function refreshAudit() {
    const auditPage = await getAudit(AUDIT_PAGE_SIZE);
    setAudit(auditPage.items);
    setAuditNextCursor(auditPage.nextCursor);
    setAuditHasMore(auditPage.hasMore);
    setAuditTotal(auditPage.total);
  }

  async function loadMoreAudit() {
    if (!auditHasMore || !auditNextCursor) {
      return;
    }
    setAuditLoadingMore(true);
    try {
      const auditPage = await getAudit(AUDIT_PAGE_SIZE, auditNextCursor);
      setAudit((current) => {
        const seen = new Set(current.map((item) => item.analysisId));
        const nextItems = auditPage.items.filter((item) => !seen.has(item.analysisId));
        return [...current, ...nextItems];
      });
      setAuditNextCursor(auditPage.nextCursor);
      setAuditHasMore(auditPage.hasMore);
      setAuditTotal(auditPage.total);
    } finally {
      setAuditLoadingMore(false);
    }
  }

  async function loadEvaluationForResult(result: AnalysisResult) {
    const datasetExists = datasets.some((item) => item.datasetId === result.datasetName);
    if (!datasetExists) {
      setEvaluation(null);
      return;
    }
    const nextEvaluation = await evaluateDataset(result.datasetName, result.analysisId, result.reportMode as ReportMode);
    setEvaluation(nextEvaluation);
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
      persistLastAnalysisId(result.analysisId);
      setBenchmarkPack(null);
      setAmbiguousEvaluation(null);
      if (isUpload) {
        setEvaluation(null);
      } else {
        const nextEvaluation = await evaluateDataset(datasetId, result.analysisId, reportMode);
        setEvaluation(nextEvaluation);
      }
      await refreshAudit();
      navigate('/attack-graph');
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
      persistLastAnalysisId(result.analysisId);
      const nextEvaluation = await evaluateDataset('adminPowerShellInventory', result.analysisId, reportMode);
      setAmbiguousEvaluation(nextEvaluation);
      setEvaluation(null);
      await refreshAudit();
      navigate('/attack-graph');
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
      navigate('/audit');
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
          : await getAnalysis(analysis.analysisId);
      setAnalysis(refreshed);
      persistLastAnalysisId(refreshed.analysisId);
      await loadEvaluationForResult(refreshed);
    } catch (feedbackError) {
      setError(feedbackError instanceof Error ? feedbackError.message : 'Failed to save feedback.');
    } finally {
      setBusy(false);
    }
  }

  async function loadAnalysisById(analysisId: string, navigateTo = '/attack-graph') {
    setBusy(true);
    setError(null);
    try {
      const result = await getAnalysis(analysisId);
      setAnalysis(result);
      persistLastAnalysisId(result.analysisId);
      await loadEvaluationForResult(result);
      navigate(navigateTo);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load historical analysis.');
    } finally {
      setBusy(false);
    }
  }

  async function saveAnalystOverride(value: number, note: string) {
    if (!analysis) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await postConfidenceOverride(analysis.analysisId, analysis.datasetName, value, note);
      setAnalystOverride({
        analysisId: analysis.analysisId,
        datasetName: analysis.datasetName,
        value: response.analystConfidence,
        note,
        savedAt: new Date().toISOString(),
      });
    } catch (overrideError) {
      setError(overrideError instanceof Error ? overrideError.message : 'Failed to save analyst confidence override.');
    } finally {
      setBusy(false);
    }
  }

  function exportHref(format: 'json' | 'md' | 'pdf') {
    if (!analysis) {
      return '#';
    }
    return buildExportHref(analysis.analysisId, format);
  }

  async function downloadExport(format: 'json' | 'md' | 'pdf') {
    if (!analysis) {
      return;
    }
    await fetchExport(analysis.analysisId, format);
  }

  const appState = useMemo<AleensAppState>(
    () => ({
      datasets,
      status,
      selectedDataset,
      reportMode,
      selectedFile,
      analysis,
      audit,
      evaluation,
      ambiguousEvaluation,
      benchmarkPack,
      busy,
      error,
      analystOverride,
      compareSelection,
      auditTotal,
      auditHasMore,
      auditLoadingMore,
      setSelectedDataset,
      setReportMode,
      setSelectedFile,
      setCompareSelection,
      clearError: () => setError(null),
      runAnalysis,
      runAmbiguousDemo,
      runPublicBenchmarkPack,
      handleFeedback,
      loadAnalysisById,
      saveAnalystOverride,
      loadMoreAudit,
      exportHref,
      downloadExport,
    }),
    [
      datasets,
      status,
      selectedDataset,
      reportMode,
      selectedFile,
      analysis,
      audit,
      evaluation,
      ambiguousEvaluation,
      benchmarkPack,
      busy,
      error,
      analystOverride,
      compareSelection,
      auditTotal,
      auditHasMore,
      auditLoadingMore,
    ],
  );

  return (
    <AppStateProvider value={appState}>
      <Suspense
        fallback={
          <div className="page-shell page-shell-center">
            <EmptyState
              title="Loading workspace"
              description={`The next ${APP_NAME} view is being prepared.`}
            />
          </div>
        }
      >
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/intake" element={<IntakePage />} />
            <Route path="/attack-graph" element={<AttackGraphPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/scoring" element={<ScoringPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/mitre" element={<MitrePage />} />
            <Route path="/analyst-brief" element={<AnalystBriefPage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AppStateProvider>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppRouterController />
    </BrowserRouter>
  );
}
