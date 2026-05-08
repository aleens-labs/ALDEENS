import { AnalystBrief } from '../components/AnalystBrief';
import { AttackGraph } from '../components/AttackGraph';
import { AttackTimeline } from '../components/AttackTimeline';
import { AuditTrail } from '../components/AuditTrail';
import { ConfidenceCard } from '../components/ConfidenceCard';
import { EvidenceBoard } from '../components/EvidenceBoard';
import { FeedbackBar } from '../components/FeedbackBar';
import { IntakePanel } from '../components/IntakePanel';
import { RiskCard } from '../components/RiskCard';
import { RuleTrace } from '../components/RuleTrace';
import { ScoringBreakdown } from '../components/ScoringBreakdown';
import { TacticMap } from '../components/TacticMap';
import type {
  AnalysisResult,
  AuditEntry,
  BenchmarkPackResult,
  DatasetSummary,
  EvaluationResult,
  FeedbackVerdict,
  ReportMode,
} from '../lib/types';
import { DemoMode } from './DemoMode';
import { ReportView } from './ReportView';

interface DashboardProps {
  datasets: DatasetSummary[];
  selectedDataset: string;
  reportMode: ReportMode;
  llmAvailable: boolean;
  llmModel: string;
  selectedFileName: string | null;
  analysis: AnalysisResult | null;
  audit: AuditEntry[];
  evaluation: EvaluationResult | null;
  ambiguousEvaluation: EvaluationResult | null;
  benchmarkPack: BenchmarkPackResult | null;
  busy: boolean;
  error: string | null;
  onDatasetChange: (value: string) => void;
  onReportModeChange: (value: ReportMode) => void;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
  onRunDemo: () => void;
  onRunAmbiguousDemo: () => void;
  onRunPublicBenchmarks: () => void;
  onFeedback: (verdict: FeedbackVerdict, note: string) => Promise<void>;
  exportHref: (format: 'json' | 'md' | 'pdf') => string;
}

const NAV_SECTIONS = [
  { id: 'overview',    label: 'Overview' },
  { id: 'graph',       label: 'Attack Graph' },
  { id: 'timeline',    label: 'Timeline' },
  { id: 'scoring',     label: 'Scoring' },
  { id: 'evidence',    label: 'Evidence' },
  { id: 'brief',       label: 'Analyst Brief' },
  { id: 'audit',       label: 'Audit' },
];

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export function Dashboard({
  datasets,
  selectedDataset,
  reportMode,
  llmAvailable,
  llmModel,
  selectedFileName,
  analysis,
  audit,
  evaluation,
  ambiguousEvaluation,
  benchmarkPack,
  busy,
  error,
  onDatasetChange,
  onReportModeChange,
  onFileChange,
  onAnalyze,
  onRunDemo,
  onRunAmbiguousDemo,
  onRunPublicBenchmarks,
  onFeedback,
  exportHref,
}: DashboardProps) {
  return (
    <>
      {/* Loading overlay */}
      {busy ? (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-chrome-950/80 backdrop-blur-sm">
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-3 w-3 rounded-full bg-signal-teal"
                style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
              />
            ))}
          </div>
          <p className="text-sm font-medium text-slate-300">Running analysis pipeline…</p>
          <p className="text-xs text-slate-500">Evidence extraction → MITRE mapping → Risk scoring → Analyst Brief</p>
        </div>
      ) : null}

      {/* Sticky section navbar */}
      <nav className="sticky top-0 z-40 border-b border-white/10 bg-chrome-950/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1560px] items-center gap-1 overflow-x-auto px-4 py-2 md:px-8">
          <span className="mr-3 shrink-0 font-display text-sm font-semibold text-signal-teal">Aleens</span>
          {NAV_SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => scrollTo(s.id)}
              className="shrink-0 rounded-xl px-3 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-white/8 hover:text-white"
            >
              {s.label}
            </button>
          ))}
          {analysis ? (
            <div className="ml-auto flex shrink-0 gap-2">
              <a
                href={exportHref('pdf')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl border border-signal-teal/30 bg-signal-teal/10 px-3 py-1.5 text-xs font-semibold text-signal-teal transition hover:bg-signal-teal/20"
              >
                ↓ PDF
              </a>
              <a
                href={exportHref('json')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20"
              >
                ↓ JSON
              </a>
              <a
                href={exportHref('md')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20"
              >
                ↓ MD
              </a>
            </div>
          ) : null}
        </div>
      </nav>

      <main className="min-h-screen px-4 py-6 md:px-8">
        <div className="mx-auto max-w-[1560px] space-y-6">
          <DemoMode
            onRun={onRunDemo}
            onRunAmbiguousDemo={onRunAmbiguousDemo}
            onRunPublicBenchmarks={onRunPublicBenchmarks}
            busy={busy}
            evaluation={evaluation}
            ambiguousEvaluation={ambiguousEvaluation}
            benchmarkPack={benchmarkPack}
          />

          {error ? (
            <div className="rounded-2xl border border-signal-coral/30 bg-signal-coral/10 px-4 py-3 text-sm text-slate-100">
              {error}
            </div>
          ) : null}

          {/* Stats strip */}
          {audit.length > 0 ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: 'Analyses Run', value: audit.length },
                {
                  label: 'Avg Risk Score',
                  value: Math.round(audit.reduce((s, e) => s + e.riskScore, 0) / audit.length),
                },
                {
                  label: 'Avg Confidence',
                  value: Math.round(audit.reduce((s, e) => s + e.confidenceScore, 0) / audit.length) + '%',
                },
                {
                  label: 'Last Dataset',
                  value: audit[0]?.datasetName ?? '—',
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-center"
                >
                  <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{stat.label}</p>
                  <p className="mt-1 truncate font-display text-lg font-semibold text-white">{stat.value}</p>
                </div>
              ))}
            </div>
          ) : null}

          {/* Overview section */}
          <div id="overview" className="scroll-mt-16 grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)] 2xl:grid-cols-[320px_minmax(0,1fr)_380px]">
            <div className="space-y-6">
              <IntakePanel
                datasets={datasets}
                selectedDataset={selectedDataset}
                reportMode={reportMode}
                llmAvailable={llmAvailable}
                llmModel={llmModel}
                busy={busy}
                fileName={selectedFileName}
                onDatasetChange={onDatasetChange}
                onReportModeChange={onReportModeChange}
                onFileChange={onFileChange}
                onAnalyze={onAnalyze}
                onRunDemo={onRunDemo}
              />
              <ReportView result={analysis} evaluation={evaluation} exportHref={exportHref} />
            </div>

            <div className="min-w-0 space-y-6">
              <div className="grid gap-6 md:grid-cols-2 2xl:grid-cols-4">
                <RiskCard score={analysis?.scores.riskScore ?? 0} label={analysis?.scores.riskLabel ?? 'Low'} />
                <ConfidenceCard
                  confidence={analysis?.scores.confidenceScore ?? 0}
                  completeness={analysis?.scores.completeness ?? 0}
                />
                <section className="metric-card">
                  <p className="eyebrow">Evidence Count</p>
                  <p className="metric-value mt-4">{analysis?.evidenceCount ?? 0}</p>
                  <p className="metric-subtle">Normalized artifacts</p>
                </section>
                <section className="metric-card">
                  <p className="eyebrow">MITRE Techniques</p>
                  <p className="metric-value mt-4">{analysis?.mitreCount ?? 0}</p>
                  <p className="metric-subtle">Mapped ATT&amp;CK IDs</p>
                </section>
              </div>

              {/* Attack Graph */}
              <div id="graph" className="scroll-mt-16">
                <AttackGraph
                  steps={analysis?.attackChain ?? []}
                  tactics={analysis?.tactics ?? []}
                />
              </div>

              {/* Timeline */}
              <div id="timeline" className="scroll-mt-16">
                <AttackTimeline steps={analysis?.attackChain ?? []} />
              </div>

              {/* Scoring */}
              <div id="scoring" className="scroll-mt-16">
                <ScoringBreakdown result={analysis} />
              </div>

              {/* Evidence */}
              <div id="evidence" className="scroll-mt-16">
                <EvidenceBoard evidence={analysis?.evidence ?? []} />
              </div>

              <TacticMap tactics={analysis?.tactics ?? []} />
            </div>

            <div className="min-w-0 space-y-6">
              {/* Analyst Brief */}
              <div id="brief" className="scroll-mt-16">
                <AnalystBrief brief={analysis?.analystBrief ?? ''} exportHref={exportHref} />
              </div>
              <RuleTrace findings={analysis?.findings ?? []} />
            </div>
          </div>

          {/* Audit section */}
          <div id="audit" className="scroll-mt-16 grid gap-6 2xl:grid-cols-[minmax(0,1fr)_380px]">
            <AuditTrail audit={audit} />
            <FeedbackBar result={analysis} busy={busy} onSubmit={onFeedback} />
          </div>
        </div>
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </>
  );
}
