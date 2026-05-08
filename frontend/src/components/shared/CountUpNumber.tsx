import { useEffect, useState } from 'react';

interface CountUpNumberProps {
  value: number;
  durationMs?: number;
  suffix?: string;
  className?: string;
}

export function CountUpNumber({ value, durationMs = 600, suffix = '', className = '' }: CountUpNumberProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const startValue = displayValue;

    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - elapsed, 3);
      const next = Math.round(startValue + (value - startValue) * eased);
      setDisplayValue(next);
      if (elapsed < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [durationMs, value]);

  return <span className={className}>{displayValue}{suffix}</span>;
}
