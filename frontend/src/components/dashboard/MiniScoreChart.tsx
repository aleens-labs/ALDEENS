import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { ScoreComponent } from '../../lib/types';

interface MiniScoreChartProps {
  scoreTrace: ScoreComponent[];
}

export function MiniScoreChart({ scoreTrace }: MiniScoreChartProps) {
  const rows = scoreTrace
    .filter((item) => item.label !== 'BASELINE')
    .map((item) => ({
      label: item.label.replace(/-/g, ' '),
      value: item.value,
    }));

  if (rows.length === 0) {
    return (
      <div className="panel-card panel-card-muted">
        <p className="eyebrow">Scoring</p>
        <h3 className="panel-card-title">No score trace</h3>
        <p className="panel-card-copy">Confidence contributors appear after the rule engine completes.</p>
      </div>
    );
  }

  return (
    <div className="panel-card">
      <div className="panel-card-head">
        <div>
          <p className="eyebrow">Scoring</p>
          <h3 className="panel-card-title">Confidence Contributors</h3>
        </div>
        <span className="tag">{rows.length} signals</span>
      </div>

      <div className="mini-chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fill: '#cbd5e1', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={124}
            />
            <Tooltip
              cursor={{ fill: 'rgba(0,255,200,0.07)' }}
              contentStyle={{
                background: '#111827',
                border: '1px solid #1E293B',
                borderRadius: 10,
                color: '#F8FAFC',
              }}
            />
            <Bar dataKey="value" radius={[6, 6, 6, 6]}>
              {rows.map((item) => (
                <Cell
                  key={item.label}
                  fill={item.label.includes('EVIDENCE') ? '#00FFC8' : item.label.includes('RULE') ? '#38BDF8' : '#A78BFA'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
