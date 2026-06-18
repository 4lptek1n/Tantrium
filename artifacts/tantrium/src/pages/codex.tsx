import { useState, useRef } from "react";
import {
  CODEX_PARADIGMS,
  CODEX_EDGES,
  CATEGORY_COLORS,
  type CodexParadigm,
} from "@/lib/aleph-tekin-codex";

const NODE_R = 28;
const SVG_W = 1200;
const SVG_H = 720;

// ── Arrow marker defs ────────────────────────────────────────────────────────
function Defs() {
  return (
    <defs>
      {Object.entries(CATEGORY_COLORS).map(([cat, c]) => (
        <marker
          key={cat}
          id={`arrow-${cat}`}
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L0,6 L8,3 z" fill={c.stroke} opacity="0.7" />
        </marker>
      ))}
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
  );
}

// ── Compute edge path between two nodes ─────────────────────────────────────
function edgePath(from: CodexParadigm, to: CodexParadigm, offset: number = 0): string {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist === 0) return "";
  const ux = dx / dist;
  const uy = dy / dist;
  // Start and end at node perimeter
  const x1 = from.x + ux * (NODE_R + 2);
  const y1 = from.y + uy * (NODE_R + 2);
  const x2 = to.x - ux * (NODE_R + 6);
  const y2 = to.y - uy * (NODE_R + 6);
  if (offset === 0) return `M ${x1} ${y1} L ${x2} ${y2}`;
  // Slight curve for bidirectional
  const mx = (x1 + x2) / 2 - uy * offset;
  const my = (y1 + y2) / 2 + ux * offset;
  return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

// ── Single edge ──────────────────────────────────────────────────────────────
function Edge({
  edge,
  byId,
  selected,
}: {
  edge: (typeof CODEX_EDGES)[0];
  byId: Map<string, CodexParadigm>;
  selected: string | null;
}) {
  const from = byId.get(edge.from);
  const to = byId.get(edge.to);
  if (!from || !to) return null;

  const isActive = selected === edge.from || selected === edge.to;
  const cat = from.category;
  const color = CATEGORY_COLORS[cat];

  const fwd = edgePath(from, to, edge.bidirectional ? 18 : 0);
  const rev = edge.bidirectional ? edgePath(to, from, 18) : null;

  return (
    <g opacity={selected ? (isActive ? 1 : 0.15) : 0.55}>
      <path
        d={fwd}
        stroke={color.stroke}
        strokeWidth={isActive ? 2 : 1.2}
        fill="none"
        markerEnd={`url(#arrow-${cat})`}
        strokeDasharray={isActive ? "none" : "5,4"}
      />
      {rev && (
        <path
          d={rev}
          stroke={CATEGORY_COLORS[to.category].stroke}
          strokeWidth={isActive ? 2 : 1.2}
          fill="none"
          markerEnd={`url(#arrow-${to.category})`}
          strokeDasharray={isActive ? "none" : "5,4"}
        />
      )}
    </g>
  );
}

// ── Single node ──────────────────────────────────────────────────────────────
function Node({
  p,
  selected,
  onClick,
}: {
  p: CodexParadigm;
  selected: boolean;
  onClick: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const c = CATEGORY_COLORS[p.category];
  const active = selected || hovered;

  return (
    <g
      transform={`translate(${p.x},${p.y})`}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ cursor: "pointer" }}
    >
      {active && (
        <circle
          r={NODE_R + 8}
          fill={c.fill}
          opacity={0.25}
          filter="url(#glow)"
        />
      )}
      <circle
        r={NODE_R}
        fill={c.fill}
        stroke={c.stroke}
        strokeWidth={selected ? 2.5 : hovered ? 2 : 1.2}
      />
      <text
        textAnchor="middle"
        dominantBaseline="central"
        fill={c.text}
        fontSize={p.letter.length > 2 ? "11" : p.letter.length > 1 ? "13" : "18"}
        fontFamily="serif"
        fontWeight="bold"
        style={{ pointerEvents: "none", userSelect: "none" }}
      >
        {p.letter}
      </text>
      {(active) && (
        <text
          y={NODE_R + 14}
          textAnchor="middle"
          fill={c.text}
          fontSize="10"
          fontFamily="monospace"
          style={{ pointerEvents: "none", userSelect: "none" }}
        >
          {p.name}
        </text>
      )}
    </g>
  );
}

// ── Detail panel ─────────────────────────────────────────────────────────────
function DetailPanel({ p }: { p: CodexParadigm | null }) {
  if (!p) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center gap-4 p-8">
        <div className="text-5xl font-serif opacity-20">א</div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Bir düğüme tıkla — paradigmanın tam teoremini ve implementasyonunu gör.
        </p>
      </div>
    );
  }

  const c = CATEGORY_COLORS[p.category];
  const catLabel: Record<CodexParadigm["category"], string> = {
    meta:        "META",
    foundation:  "TEMEL",
    structure:   "YAPI",
    computation: "HESAP",
    physical:    "FİZİK",
    terminal:    "TERMİNAL",
  };

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <span
            className="text-3xl font-serif"
            style={{ color: c.text, textShadow: `0 0 12px ${c.stroke}` }}
          >
            {p.letter}
          </span>
          <div>
            <h2 className="text-xl font-bold tracking-tight">{p.name}</h2>
            <span
              className="text-[10px] font-mono px-2 py-0.5 rounded"
              style={{ background: c.fill + "60", color: c.text, border: `1px solid ${c.stroke}40` }}
            >
              {catLabel[p.category]}
            </span>
          </div>
        </div>
        <p className="text-sm font-semibold text-primary">{p.paradigm}</p>
      </div>

      {/* Math */}
      <div
        className="rounded-lg px-4 py-3 font-mono text-sm"
        style={{ background: c.fill + "30", border: `1px solid ${c.stroke}30`, color: c.text }}
      >
        {p.math}
      </div>

      {/* Theorem */}
      <div className="space-y-1">
        <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Teorem</div>
        <p className="text-sm leading-relaxed text-foreground/85">{p.theorem}</p>
      </div>

      {/* Implementation */}
      <div className="space-y-1">
        <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Implementasyon</div>
        <code className="text-xs text-primary font-mono">{p.implementation}</code>
      </div>
    </div>
  );
}

// ── Category legend ───────────────────────────────────────────────────────────
function Legend() {
  const labels: [CodexParadigm["category"], string][] = [
    ["meta",        "Meta"],
    ["foundation",  "Temel"],
    ["structure",   "Yapı"],
    ["computation", "Hesap"],
    ["physical",    "Fizik"],
    ["terminal",    "Terminal"],
  ];
  return (
    <div className="flex flex-wrap gap-3 px-2">
      {labels.map(([cat, label]) => {
        const c = CATEGORY_COLORS[cat];
        return (
          <div key={cat} className="flex items-center gap-1.5 text-xs font-mono">
            <span
              className="inline-block w-3 h-3 rounded-full border"
              style={{ background: c.fill, borderColor: c.stroke }}
            />
            <span className="text-muted-foreground">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export function CodexPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const byId = new Map(CODEX_PARADIGMS.map((p) => [p.id, p]));
  const selectedParadigm = selected ? byId.get(selected) ?? null : null;

  const handleNodeClick = (id: string) => {
    setSelected((prev) => (prev === id ? null : id));
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="border-b border-border px-6 py-5 space-y-1">
        <div className="flex items-baseline gap-3">
          <h1 className="text-2xl font-black tracking-tighter">Aleph-Tekin Kodeksi</h1>
          <span className="text-xs font-mono text-muted-foreground">22+1 Matematiksel Paradigma</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Her iddia ya kanıtlanır ya da açık adıyla bilinmez — tahmin yok, hallüsinasyon yok.
        </p>
        <Legend />
      </div>

      {/* Body: graph + detail */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* SVG Graph */}
        <div className="flex-1 min-w-0 overflow-hidden bg-background/50 relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${SVG_W} ${SVG_H}`}
            width="100%"
            height="100%"
            preserveAspectRatio="xMidYMid meet"
            className="w-full h-full"
            style={{ display: "block" }}
          >
            <Defs />

            {/* Background grid */}
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="currentColor" strokeWidth="0.3" opacity="0.06" />
              </pattern>
            </defs>
            <rect width={SVG_W} height={SVG_H} fill="url(#grid)" />

            {/* Category group labels */}
            <text x="95" y="130" fontSize="9" fill="#60a5fa" opacity="0.5" fontFamily="monospace" textAnchor="middle">TEMEL</text>
            <text x="230" y="540" fontSize="9" fill="#34d399" opacity="0.5" fontFamily="monospace" textAnchor="middle">YAPI</text>
            <text x="960" y="130" fontSize="9" fill="#fbbf24" opacity="0.5" fontFamily="monospace" textAnchor="middle">HESAP</text>
            <text x="430" y="680" fontSize="9" fill="#fb923c" opacity="0.5" fontFamily="monospace" textAnchor="middle">FİZİK</text>
            <text x="660" y="690" fontSize="9" fill="#f472b6" opacity="0.5" fontFamily="monospace" textAnchor="middle">TERMİNAL</text>

            {/* Edges (below nodes) */}
            {CODEX_EDGES.map((e) => (
              <Edge key={`${e.from}-${e.to}`} edge={e} byId={byId} selected={selected} />
            ))}

            {/* Nodes */}
            {CODEX_PARADIGMS.map((p) => (
              <Node
                key={p.id}
                p={p}
                selected={selected === p.id}
                onClick={() => handleNodeClick(p.id)}
              />
            ))}
          </svg>

          {/* Click-outside to deselect */}
          {selected && (
            <button
              className="absolute top-3 right-3 text-xs font-mono text-muted-foreground hover:text-foreground px-2 py-1 rounded border border-border bg-background/80"
              onClick={() => setSelected(null)}
            >
              ✕ kapat
            </button>
          )}
        </div>

        {/* Detail panel */}
        <div
          className="w-80 shrink-0 border-l border-border bg-card/60 overflow-hidden flex flex-col"
          style={{ minHeight: 0 }}
        >
          <DetailPanel p={selectedParadigm} />
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-border px-6 py-3 flex items-center justify-between">
        <span className="text-xs font-mono text-muted-foreground">
          {CODEX_PARADIGMS.length} paradigma · {CODEX_EDGES.length} kenar · Hankel PSD sertifikalı
        </span>
        <span className="text-xs font-mono text-muted-foreground opacity-50">
          Aleph-Tekin Kodeksi — topoloji = bilgi
        </span>
      </div>
    </div>
  );
}
