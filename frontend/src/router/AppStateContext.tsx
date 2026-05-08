import { createContext, useContext } from 'react';

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

export interface AnalystOverrideState {
  analysisId: string;
  datasetName: string;
  value: number;
  note: string;
  savedAt: string;
}

export interface AleensAppState {
  datasets: DatasetSummary[];
  status: AppStatus | null;
  selectedDataset: string;
  reportMode: ReportMode;
  selectedFile: File | null;
  analysis: AnalysisResult | null;
  audit: AuditEntry[];
  evaluation: EvaluationResult | null;
  ambiguousEvaluation: EvaluationResult | null;
  benchmarkPack: BenchmarkPackResult | null;
  busy: boolean;
  error: string | null;
  analystOverride: AnalystOverrideState | null;
  compareSelection: string[];
  auditTotal: number;
  auditHasMore: boolean;
  auditLoadingMore: boolean;
  setSelectedDataset: (value: string) => void;
  setReportMode: (value: ReportMode) => void;
  setSelectedFile: (file: File | null) => void;
  setCompareSelection: (analysisIds: string[]) => void;
  clearError: () => void;
  runAnalysis: (forceDemo?: boolean) => Promise<void>;
  runAmbiguousDemo: () => Promise<void>;
  runPublicBenchmarkPack: () => Promise<void>;
  handleFeedback: (verdict: FeedbackVerdict, note: string) => Promise<void>;
  loadAnalysisById: (analysisId: string, navigateTo?: string) => Promise<void>;
  saveAnalystOverride: (value: number, note: string) => Promise<void>;
  loadMoreAudit: () => Promise<void>;
  exportHref: (format: 'json' | 'md' | 'pdf') => string;
  downloadExport: (format: 'json' | 'md' | 'pdf') => Promise<void>;
}

const AppStateContext = createContext<AleensAppState | null>(null);

export function AppStateProvider({
  value,
  children,
}: {
  value: AleensAppState;
  children: React.ReactNode;
}) {
  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAleensApp() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAleensApp must be used within AppStateProvider.');
  }
  return context;
}
