export type RiskLabel = 'Low' | 'Medium' | 'High' | 'Critical';
export type FeedbackVerdict = 'true_positive' | 'false_positive' | 'needs_review';
export type ReportMode = 'template' | 'llm';

export interface AppStatus {
  status: string;
  product: string;
  llmAvailable: boolean;
  llmModel?: string | null;
  defaultReportMode: ReportMode;
}

export interface DatasetSummary {
  datasetId: string;
  title: string;
  description: string;
  samplePath: string;
  attackDescription: string;
  techniques: string[];
  sourceName: string;
  sourceUrl: string;
  collectionType: string;
  benchmarkTier?: string | null;
}

export interface Evidence {
  evidenceId: string;
  timestamp: string | null;
  host: string | null;
  user: string | null;
  process: string | null;
  parentProcess: string | null;
  commandLine: string | null;
  targetProcess: string | null;
  destinationIp: string | null;
  destinationDomain: string | null;
  filePath: string | null;
  hash: string | null;
  eventId: string | null;
  provider: string | null;
  rawReference: string;
  summary: string;
}

export interface Finding {
  findingId: string;
  ruleId: string;
  title: string;
  reason: string;
  evidenceIds: string[];
  evidence: Evidence[];
  mitreTechnique: string;
  tactic: string;
  scoreContribution: number;
  confidenceContribution: number;
}

export interface TacticHit {
  techniqueId: string;
  techniqueName: string;
  tactic: string;
  description: string;
  confidence: number;
  relatedRules: string[];
}

export interface ChainStep {
  stage: string;
  timestamp: string | null;
  summary: string;
  evidenceIds: string[];
  findingIds: string[];
  rawReferences: string[];
}

export interface ScoreComponent {
  label: string;
  value: number;
  reason: string;
}

export interface ScoreCard {
  riskScore: number;
  riskLabel: RiskLabel;
  confidenceScore: number;
  completeness: number;
  scoreTrace: ScoreComponent[];
  confidenceTrace: ScoreComponent[];
}

export interface Guardrails {
  modeRequested: string;
  modeSelected: string;
  safeForReport: boolean;
  payloadRedactions: number;
  reviewNote: string;
  llmModel?: string | null;
  fallbackApplied: boolean;
  structuredFindings: Array<Record<string, unknown>>;
}

export interface AuditEntry {
  analysisId: string;
  timestamp: string;
  datasetName: string;
  parserMode: string;
  rulesTriggered: string[];
  riskScore: number;
  confidenceScore: number;
  reportMode: string;
  safetyCheck: string;
  llmModel?: string | null;
  providerRequestId?: string | null;
}

export interface AuditPageResult {
  items: AuditEntry[];
  nextCursor: string | null;
  hasMore: boolean;
  total: number;
  limit: number;
}

export interface SimilarCase {
  ruleId: string;
  verdict: FeedbackVerdict;
  note?: string | null;
  count: number;
  datasetName: string;
  seenAt: string;
}

export interface AnalysisResult {
  analysisId: string;
  datasetName: string;
  parserMode: string;
  reportMode: string;
  evidenceCount: number;
  mitreCount: number;
  evidence: Evidence[];
  findings: Finding[];
  tactics: TacticHit[];
  attackChain: ChainStep[];
  scores: ScoreCard;
  analystBrief: string;
  guardrails: Guardrails;
  audit: AuditEntry;
  similarCases: SimilarCase[];
}

export interface EvaluationResult {
  dataset: string;
  benchmarkSource?: {
    sourceName: string;
    sourceUrl: string;
    benchmarkType: string;
  };
  matchedRules: string[];
  missingRules: string[];
  unexpectedRules: string[];
  matchedTechniques: string[];
  missingTechniques: string[];
  unexpectedTechniques: string[];
  rulePrecisionLike: number;
  ruleRecallLike: number;
  techniquePrecisionLike: number;
  techniqueRecallLike: number;
  stageRecallLike: number;
  expectedStages: string[];
  actualStages: string[];
  chainOrderAligned: boolean;
  citationCount: number;
  minimumCitationCount: number;
  citationCoverage: number;
  sectionsPresent: boolean;
  missingSections: string[];
  exportsReady: boolean;
  exportStatus: Record<string, boolean>;
  riskAligned: boolean;
  confidenceAligned: boolean;
  evidenceAligned: boolean;
  falsePositivePressureOk: boolean;
  benchmarkScore: number;
}

export interface PublicBenchmarkScenarioResult extends EvaluationResult {
  title: string;
  attackDescription: string;
  collectionType: string;
  benchmarkTier?: string | null;
}

export interface BenchmarkPackResult {
  packName: string;
  sourceName: string;
  sourceUrl: string;
  reportMode: ReportMode;
  datasetCount: number;
  averageBenchmarkScore: number;
  averageRuleRecall: number;
  averageTechniqueRecall: number;
  averageCitationCoverage: number;
  passRate: number;
  generatedAt: string;
  datasets: PublicBenchmarkScenarioResult[];
}

export interface ConfidenceOverrideResult {
  analystConfidence: number | null;
  overrideNote?: string | null;
  createdAt?: string | null;
}
