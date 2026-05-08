import { useState } from 'react';
import type { ChainStep, TacticHit } from '../lib/types';

interface AttackGraphProps {
  steps: ChainStep[];
  tactics: TacticHit[];
}

const TACTIC_COLOR: Record<string, { fill: string; stroke: string; text: string }> = {
  'Initial Access':     { fill: 'rgba(255,114,98,0.18)',  stroke: '#ff7262', text: '#ff9b8e' },
  'Execution':          { fill: 'rgba(246,161,45,0.18)',  stroke: '#f6a12d', text: '#f6c46d' },
  'Defense Evasion':    { fill: 'rgba(110,203,255,0.18)', stroke: '#6ecbff', text: '#9edaff' },
  'Credential Access':  { fill: 'rgba(168,85,247,0.18)',  stroke: '#a855f7', text: '#c084fc' },
  'Command and Control':{ fill: 'rgba(61,226,210,0.18)',  stroke: '#3de2d2', text: '#5eeedd' },
  'Persistence':        { fill: 'rgba(100,116,139,0.18)', stroke: '#64748b', text: '#94a3b8' },
  'Lateral Movement':   { fill: 'rgba(236,72,153,0.18)',  stroke: '#ec4899', text: '#f472b6' },
  'Exfiltration':       { fill: 'rgba(244,63,94,0.18)',   stroke: '#f43f5e', text: '#fb7185' },
};

const DEFAULT_COLOR = { fill: 'rgba(255,255,255,0.08)', stroke: 'rgba(255,255,255,0.25)', text: '#cbd5e1' };

const NODE_W = 152;
const NODE_H = 76;
const GAP = 56;
const ARROW_LEN = GAP;
const SVG_H = 160;
const PAD_X = 16;
const PAD_Y = 24;

function relOffset(base: string | null, ts: string | null): string {
  if (!base || !ts || base === ts) return '';
  const diff = Math.round((new Date(ts).getTime() - new Date(base).getTime()) / 1000);
  if (diff <= 0) return '';
  return diff < 60 ? `+${diff}s` : `+${Math.floor(diff / 60)}m${diff % 60 > 0 ? (diff % 60) + 's' : ''}`;
}

function wrap(text: string, maxChars: number): [string, string] {
  if (text.length <= maxChars) return [text, ''];
  const idx = text.lastIndexOf(' ', maxChars);
  return idx > 0 ? [text.slice(0, idx), text.slice(idx + 1)] : [text.slice(0, maxChars), text.slice(maxChars)];
}

export function AttackGraph({ steps, tactics }: AttackGraphProps) {
  const [activeStage, setActiveStage] = useState<string | null>(null);

  const activeStep = steps.find((s) => s.stage === activeStage) ?? null;
  const activeTactics = tactics.filter((t) => t.tactic === activeStage);

  if (steps.length === 0) {
    return (
      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Visual</p>
            <h2 className="panel-title">Attack Graph</h2>
          </div>
        </div>
        <p className="empty-state">Run an analysis to generate the attack graph.</p>
      </section>
    );
  }

  const baseTs = steps.find((s) => s.timestamp)?.timestamp ?? null;
  const totalW = PAD_X * 2 + steps.length * NODE_W + (steps.length - 1) * GAP;
  const svgH = SVG_H;

  const techniqueByStage: Record<string, string> = {};
  for (const tactic of tactics) {
    for (const step of steps) {
      if (tactic.tactic === step.stage && !techniqueByStage[step.stage]) {
        techniqueByStage[step.stage] = tactic.techniqueId;
      }
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Visual</p>
          <h2 className="panel-title">Attack Graph</h2>
        </div>
        <span className="tag">{steps.length} stage{steps.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-2">
        <svg
          width={Math.max(totalW, 400)}
          height={svgH}
          viewBox={`0 0 ${Math.max(totalW, 400)} ${svgH}`}
          xmlns="http://www.w3.org/2000/svg"
          style={{ display: 'block', minWidth: '100%' }}
        >
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.3)" />
            </marker>
          </defs>

          {steps.map((step, i) => {
            const x = PAD_X + i * (NODE_W + GAP);
            const y = PAD_Y;
            const color = TACTIC_COLOR[step.stage] ?? DEFAULT_COLOR;
            const techId = techniqueByStage[step.stage] ?? '';
            const offset = relOffset(baseTs, step.timestamp);
            const [line1, line2] = wrap(step.stage, 16);

            return (
              <g
                key={step.stage}
                style={{ cursor: 'pointer' }}
                onClick={() => setActiveStage(activeStage === step.stage ? null : step.stage)}
              >
                {/* Arrow to next node */}
                {i < steps.length - 1 ? (
                  <line
                    x1={x + NODE_W}
                    y1={y + NODE_H / 2}
                    x2={x + NODE_W + ARROW_LEN - 2}
                    y2={y + NODE_H / 2}
                    stroke="rgba(255,255,255,0.25)"
                    strokeWidth="1.5"
                    markerEnd="url(#arrow)"
                  />
                ) : null}

                {/* Node background */}
                <rect
                  x={x}
                  y={y}
                  width={NODE_W}
                  height={NODE_H}
                  rx={14}
                  ry={14}
                  fill={activeStage === step.stage ? color.stroke.replace(')', ', 0.28)').replace('rgb', 'rgba') : color.fill}
                  stroke={color.stroke}
                  strokeWidth={activeStage === step.stage ? 2 : 1.2}
                />

                {/* Stage name */}
                <text
                  x={x + NODE_W / 2}
                  y={y + (line2 ? 22 : 28)}
                  textAnchor="middle"
                  fill={color.text}
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="IBM Plex Sans, sans-serif"
                >
                  {line1}
                </text>
                {line2 ? (
                  <text
                    x={x + NODE_W / 2}
                    y={y + 38}
                    textAnchor="middle"
                    fill={color.text}
                    fontSize="12"
                    fontWeight="600"
                    fontFamily="IBM Plex Sans, sans-serif"
                  >
                    {line2}
                  </text>
                ) : null}

                {/* Technique ID */}
                {techId ? (
                  <text
                    x={x + NODE_W / 2}
                    y={y + NODE_H - 14}
                    textAnchor="middle"
                    fill="rgba(255,255,255,0.45)"
                    fontSize="10"
                    fontFamily="IBM Plex Mono, monospace"
                  >
                    {techId}
                  </text>
                ) : null}

                {/* Timestamp + offset below node */}
                <text
                  x={x + NODE_W / 2}
                  y={y + NODE_H + 18}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.3)"
                  fontSize="9"
                  fontFamily="IBM Plex Mono, monospace"
                >
                  {step.timestamp
                    ? new Date(step.timestamp).toISOString().slice(11, 19) + ' UTC'
                    : '—'}
                </text>
                {offset ? (
                  <text
                    x={x + NODE_W / 2}
                    y={y + NODE_H + 32}
                    textAnchor="middle"
                    fill="#3de2d2"
                    fontSize="9"
                    fontFamily="IBM Plex Mono, monospace"
                  >
                    {offset}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-2">
        {steps.map((step) => {
          const color = TACTIC_COLOR[step.stage] ?? DEFAULT_COLOR;
          const isActive = activeStage === step.stage;
          return (
            <button
              key={step.stage}
              onClick={() => setActiveStage(isActive ? null : step.stage)}
              className="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-[0.2em] transition"
              style={{
                borderColor: color.stroke,
                color: color.text,
                background: isActive ? color.stroke + '44' : color.fill,
                fontWeight: isActive ? 700 : 400,
              }}
            >
              <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: color.stroke }} />
              {step.stage}
            </button>
          );
        })}
        {activeStage ? (
          <span className="ml-1 text-[10px] text-slate-500 self-center">← click to deselect</span>
        ) : (
          <span className="ml-1 text-[10px] text-slate-500 self-center">click a node or badge for details</span>
        )}
      </div>

      {/* Detail panel — shown when a stage is selected */}
      {activeStep ? (
        <div
          className="mt-4 rounded-2xl border p-4 text-sm text-slate-300"
          style={{
            borderColor: (TACTIC_COLOR[activeStep.stage] ?? DEFAULT_COLOR).stroke + '55',
            background: (TACTIC_COLOR[activeStep.stage] ?? DEFAULT_COLOR).fill,
          }}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p
                className="font-display font-semibold"
                style={{ color: (TACTIC_COLOR[activeStep.stage] ?? DEFAULT_COLOR).text }}
              >
                {activeStep.stage}
              </p>
              <p className="mt-1 text-xs text-slate-400">{activeStep.summary}</p>
            </div>
            <button
              onClick={() => setActiveStage(null)}
              className="shrink-0 rounded-lg px-2 py-1 text-xs text-slate-500 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Evidence IDs</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {activeStep.evidenceIds.map((id) => (
                  <span key={id} className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">
                    {id}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Raw References</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {activeStep.rawReferences.map((ref) => (
                  <span key={ref} className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">
                    {ref}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {activeTactics.length > 0 ? (
            <div className="mt-3">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">ATT&amp;CK Techniques</p>
              <div className="mt-1 space-y-1">
                {activeTactics.map((t) => (
                  <p key={t.techniqueId} className="text-xs">
                    <span className="font-mono text-signal-teal">{t.techniqueId}</span>{' '}
                    <span className="text-white">{t.techniqueName}</span>
                    <span className="ml-2 text-slate-500">
                      confidence {Math.round(t.confidence * 100)}%
                    </span>
                  </p>
                ))}
              </div>
            </div>
          ) : null}

          <p className="mt-3 text-[10px] text-slate-500">
            Firing rules: {activeStep.findingIds.join(', ')}
          </p>
        </div>
      ) : null}
    </section>
  );
}
