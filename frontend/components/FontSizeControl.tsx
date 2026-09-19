"use client";

import { useEffect, useState } from "react";

const KEY = "nasalter-font-scale";
const MIN = 0.85;
const MAX = 1.5;
const STEP = 0.05;
const DEFAULT = 1;

function clamp(value: number): number {
  if (Number.isNaN(value)) return DEFAULT;
  return Math.min(MAX, Math.max(MIN, value));
}

function apply(scale: number) {
  document.documentElement.style.setProperty("--font-scale", String(scale));
}

export function FontSizeControl() {
  const [scale, setScale] = useState(DEFAULT);

  useEffect(() => {
    try {
      const saved =
        localStorage.getItem(KEY) || localStorage.getItem("putokaz-font-scale");
      if (saved) setScale(clamp(Number(saved)));
    } catch {
      /* localStorage nedostupan — ostaje podrazumevano */
    }
  }, []);

  function update(next: number) {
    const value = clamp(next);
    setScale(value);
    apply(value);
    try {
      localStorage.setItem(KEY, String(value));
    } catch {
      /* ignore */
    }
  }

  const percent = Math.round(scale * 100);

  return (
    <div className="fontsize no-print">
      <div className="fontsize-head">
        <span className="fontsize-title">Veličina slova</span>
        <span className="fontsize-value" aria-hidden="true">
          {percent}%
        </span>
      </div>
      <div className="fontsize-row">
        <button
          type="button"
          className="fontsize-step"
          aria-label="Smanji slova"
          onClick={() => update(scale - STEP)}
          disabled={scale <= MIN}
        >
          A
        </button>
        <input
          type="range"
          min={MIN}
          max={MAX}
          step={STEP}
          value={scale}
          aria-label="Veličina slova"
          onChange={(e) => update(Number(e.target.value))}
        />
        <button
          type="button"
          className="fontsize-step big"
          aria-label="Povećaj slova"
          onClick={() => update(scale + STEP)}
          disabled={scale >= MAX}
        >
          A
        </button>
      </div>
    </div>
  );
}
