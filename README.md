# Tantrium Boundary Engine

> **Find the exact point where your system breaks — not a probability, not a range. The boundary.**

A production-grade boundary analysis web application. Upload or auto-fetch real operational data, run the Tantrium six-step methodology, and receive a certified, evidence-hashed Boundary Report identifying the safe operating envelope, the first break boundary, the primary failure driver, and a concrete stabilization path.

---

## What It Does

Most operational analytics tools tell you *that* a system is failing. Tantrium tells you *where* it breaks.

Given any operational dataset with a measurable target metric, Tantrium computes:

| Output | Description |
|---|---|
| **Safe Operating Envelope** | The parameter ranges where the system runs without failure — computed from real records |
| **First Break Boundary** | The exact value at which the system transitions from stable to unstable |
| **First Obstruction** | The primary variable driving the boundary breach, ranked by Boundary Pressure Score |
| **Closure Path** | A concrete sequence of operational changes to return to the safe zone |

Every certified analysis generates a cryptographic evidence hash. No synthetic outputs. No black boxes.

---

## Live Demo

The app ships with auto-fetch access to real public datasets across 8 sectors. On the **Live Reports** page, the engine automatically fetches and analyzes:

- **Server Thermal Failure Boundary** — 22,695 rows of server temperature data (NAB dataset)
- **Insurance Claims Severity Boundary** — 1,338 policyholder records with charges
- **Process Quality Degradation Boundary** — Red wine physicochemical parameters vs. quality score
- **Product Pricing Anomaly Boundary** — 53,940 diamond records, price vs. physical attributes

All outputs are labeled `REAL DATA` when actual rows are processed, or `INSUFFICIENT DATA` if the dataset does not meet the minimum row threshold.

---

## Pages

| Route | Purpose |
|---|---|
| `/` | Executive home page |
| `/hunt` | **Master Problem Hunt** — guided workflow: pick template → load data → configure → run → get report |
| `/reports` | **Live Boundary Reports** — auto-runs 4 real datasets, shows full certified reports |
| `/core` | Tantrium Core methodology — six-step workflow explained for technical audiences |
| `/demo` | Interactive synthetic demo |
| `/datasets` | Full dataset registry (15 entries, 8 sectors) |
| `/pricing` | Pricing tiers and analyst report request form |

---

## Sectors Covered

- Data Centers & Hosting
- Plastics / Polymer / Manufacturing
- General Manufacturing & OEE
- Pharma / Biotech / Toxicity
- Finance & Insurance Risk
- Energy & HVAC
- Logistics
- Cyber & SLA Risk

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite 7 + TypeScript 5.9 |
| Routing | Wouter |
| UI Components | shadcn/ui + Tailwind CSS |
| Charts | Recharts |
| CSV Parsing | PapaParse |
| Animation | Framer Motion |
| Package Manager | pnpm workspaces |
| Backend | Express 5 (API server) |
| Database | PostgreSQL + Drizzle ORM |

All boundary analysis runs **client-side** in the browser — no server round-trip required for computation.

---

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 9+
- PostgreSQL (for API server features)

### Install & Run

```bash
# Install dependencies
pnpm install

# Run the web app (development)
pnpm --filter @workspace/tantrium run dev

# Run the API server
pnpm --filter @workspace/api-server run dev

# Typecheck all packages
pnpm run typecheck
```

The web app will be available at `http://localhost:PORT` (port assigned by the runtime).

---

## How the Analysis Engine Works

The Tantrium engine (`src/lib/analysis-engine.ts`) runs six labeled steps:

```
DATA_INGEST      → Parse and validate all rows; detect numeric/categorical columns
STABLE_REGION    → Classify each row as stable or unstable against the target threshold
BREAK_BOUNDARY   → Detect stable-to-unstable transition points in sorted driver space
FIRST_OBSTRUCTION → Score all drivers by Boundary Pressure Index (Pearson + crossing strength + proximity + monotonicity)
CLOSURE_PATH     → Compute recommended operational changes to return to the safe envelope
EVIDENCE_HASH    → Generate SHA-256 fingerprint of dataset + parameters + results
```

Output type: `TantriumObject` — a fully typed result containing all six step outputs, mode label, certification status, timestamp, and evidence hash.

**Mode labels:**
- `REAL DATA` — at least 10 valid rows processed, engine ran to completion
- `DEMO` — synthetic or placeholder data
- `INSUFFICIENT DATA` — fewer than 10 valid rows after filtering

---

## Dataset Registry

15 real public datasets pre-configured with suggested target columns, thresholds, and directions. 9 are auto-fetchable directly from public GitHub raw URLs. 6 require manual download due to licensing or size.

See `/datasets` in the app or `src/lib/dataset-registry.ts` for the full registry.

---

## Project Structure

```
artifacts/
  tantrium/          # React web application
    src/
      lib/
        analysis-engine.ts   # Core Tantrium computation engine
        dataset-registry.ts  # 15 real public datasets
        evidence-log.ts      # User analysis history (localStorage)
        report-store.ts      # Auto-computed live reports (localStorage)
        tantrium-core.ts     # Methodology explanations and glossary
        prospect-mode.ts     # LinkedIn buyer persona intelligence
      pages/
        home.tsx             # Executive landing page
        hunt.tsx             # Master Problem Hunt workflow
        reports.tsx          # Live Boundary Reports
        core.tsx             # Methodology page
        demo.tsx             # Synthetic demo
        datasets.tsx         # Dataset registry
        pricing.tsx          # Pricing and contact
  api-server/        # Express API backend
lib/                 # Shared workspace libraries
scripts/             # Utility scripts
```

---

## Business Context

Tantrium Boundary Engine is a **sales and demonstration tool** for the Tantrium Boundary Analysis consultancy. It serves as:

1. A live proof-of-capability — showing real analysis on real public data
2. A prospect onboarding tool — LinkedIn targets can self-serve the Problem Hunt
3. A pricing gateway — the /pricing page converts interested prospects to paid engagements

**Pricing tiers:**
- Quick Screen: $5,000 / 5 business days
- Boundary Report: $25,000 / 3 weeks (standard)
- Enterprise Program: from $100,000 / ongoing monitoring

---

## Evidence & Integrity

Every certified analysis produces:

- `evidenceHash` — SHA-256 of `datasetName + targetCol + threshold + direction + rowCount + topDriver + evidenceNonce`
- `mode` — `REAL DATA` / `DEMO` / `INSUFFICIENT DATA`
- `certified: boolean` — true only when mode is REAL DATA

The hash can be shared as proof that the analysis was run on a specific dataset with specific parameters. It does not expose the underlying data.

---

## License

Proprietary. All rights reserved. This codebase is not open-source.
