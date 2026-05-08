import type {
  AnalysisResult,
  AppStatus,
  AuditEntry,
  AuditPageResult,
  BenchmarkPackResult,
  ConfidenceOverrideResult,
  DatasetSummary,
  EvaluationResult,
  FeedbackVerdict,
  ReportMode,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const LEGACY_ENV_PREFIX = ['DEFENDER', 'LENS'].join('');
const ENV = import.meta.env as Record<string, string | undefined>;
const API_KEY = (
  ENV.VITE_ALEENS_API_KEY ??
  ENV[`VITE_${LEGACY_ENV_PREFIX}_API_KEY`] ??
  ''
).trim();

function authHeaders(): HeadersInit {
  return API_KEY ? { 'X-API-Key': API_KEY } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const payload = await response.text();
    throw new Error(payload || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDatasets(): Promise<DatasetSummary[]> {
  return request<DatasetSummary[]>('/api/datasets');
}

export function getStatus(): Promise<AppStatus> {
  return request<AppStatus>('/api/health');
}

export function getAudit(limit = 20, cursor?: string | null): Promise<AuditPageResult> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) {
    params.set('cursor', cursor);
  }
  return request<AuditPageResult>(`/api/audit?${params.toString()}`);
}

export function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  return request<AnalysisResult>(`/api/analysis/${analysisId}`);
}

export function getPublicBenchmarks(reportMode: ReportMode = 'template'): Promise<BenchmarkPackResult> {
  return request<BenchmarkPackResult>(`/api/benchmarks/public?report_mode=${reportMode}`);
}

export function analyzeDataset(datasetName: string, reportMode: ReportMode = 'template'): Promise<AnalysisResult> {
  return request<AnalysisResult>('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ datasetName, reportMode }),
  });
}

export async function uploadLogs(file: File, reportMode: ReportMode = 'template'): Promise<AnalysisResult> {
  const body = new FormData();
  body.append('file', file);
  if (reportMode) {
    body.append('report_mode', reportMode);
  }

  const response = await fetch(`${API_BASE}/api/analyze/upload`, {
    method: 'POST',
    body,
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<AnalysisResult>;
}

export function evaluateDataset(
  datasetName: string,
  analysisId?: string,
  reportMode: ReportMode = 'template',
): Promise<EvaluationResult> {
  return request<EvaluationResult>('/api/evaluate', {
    method: 'POST',
    body: JSON.stringify({ datasetName, analysisId, reportMode }),
  });
}

export function sendFeedback(
  analysisId: string,
  datasetName: string,
  verdict: FeedbackVerdict,
  note: string,
  ruleIds: string[],
): Promise<{ status: string }> {
  return request<{ status: string }>('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({
      analysisId,
      datasetName,
      verdict,
      note,
      ruleIds,
    }),
  });
}

export function getConfidenceOverride(analysisId: string): Promise<ConfidenceOverrideResult> {
  return request<ConfidenceOverrideResult>(`/api/feedback/confidence-override/${analysisId}`);
}

export function saveConfidenceOverride(
  analysisId: string,
  datasetName: string,
  analystConfidence: number,
  overrideNote: string,
): Promise<{ status: string; analystConfidence: number }> {
  return request<{ status: string; analystConfidence: number }>('/api/feedback/confidence-override', {
    method: 'POST',
    body: JSON.stringify({
      analysisId,
      datasetName,
      analystConfidence,
      overrideNote,
    }),
  });
}

export function exportHref(analysisId: string, format: 'json' | 'md' | 'pdf'): string {
  return `${API_BASE}/api/exports/${analysisId}/${format}`;
}

export async function downloadExport(analysisId: string, format: 'json' | 'md' | 'pdf'): Promise<void> {
  const response = await fetch(exportHref(analysisId, format), {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;

  const contentDisposition = response.headers.get('Content-Disposition') ?? '';
  const match = /filename="?([^"]+)"?/i.exec(contentDisposition);
  anchor.download = match?.[1] ?? `aleens-export.${format}`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(objectUrl);
}
