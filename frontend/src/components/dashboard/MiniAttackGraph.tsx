import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import type { ChainStep } from '../../lib/types';
import { TacticBadge } from '../shared/TacticBadge';

interface MiniAttackGraphProps {
  steps: ChainStep[];
}

export function MiniAttackGraph({ steps }: MiniAttackGraphProps) {
  if (steps.length === 0) {
    return (
      <div className="panel-card panel-card-muted">
        <p className="eyebrow">Attack Graph</p>
        <h3 className="panel-card-title">No chain loaded</h3>
        <p className="panel-card-copy">Run an analysis to populate the reconstructed incident chain.</p>
      </div>
    );
  }

  return (
    <Link to="/attack-graph" className="panel-card panel-card-link">
      <div className="panel-card-head">
        <div>
          <p className="eyebrow">Attack Graph</p>
          <h3 className="panel-card-title">Chain Preview</h3>
        </div>
        <span className="tag">{steps.length} stages</span>
      </div>

      <div className="mini-chain">
        {steps.map((step, index) => (
          <div key={`${step.stage}-${index}`} className="mini-chain-step">
            <TacticBadge tactic={step.stage} />
            <p className="mini-chain-time">
              {step.timestamp ? new Date(step.timestamp).toISOString().slice(11, 19) : 'n/a'}
            </p>
            {index < steps.length - 1 ? <ArrowRight size={15} className="mini-chain-arrow" /> : null}
          </div>
        ))}
      </div>
    </Link>
  );
}
