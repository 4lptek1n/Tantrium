// ─── Tantrium Core Methodology Layer ────────────────────────────────────────
// Plain-English descriptions of each Tantrium workflow step.
// Used in the Core page and advanced methodology panel.
// Business-facing language on the main UI; technical detail in the advanced panel.

export interface MethodologyStep {
  id: string;
  label: string;          // Short display label (e.g. "DATA_INGEST")
  title: string;          // Human title (e.g. "Data Ingest")
  businessSummary: string; // 1-2 sentences, plain English, no formulas
  whatItDoes: string;     // Slightly more detailed, still no formulas
  whatItProduces: string; // The output artifact of this step
  advancedDetail: string; // Technical detail for the advanced panel
  icon: string;           // Lucide icon name
}

export const METHODOLOGY_STEPS: MethodologyStep[] = [
  {
    id: "DATA_INGEST",
    label: "DATA_INGEST",
    title: "Data Ingest",
    businessSummary:
      "Tantrium reads your operational records and identifies which columns contain measurable system parameters.",
    whatItDoes:
      "Every row is a snapshot of your system at a moment in time. Tantrium ingests those rows, identifies numeric measurement columns, counts missing values, and confirms the target metric is present and readable.",
    whatItProduces:
      "A validated dataset summary: row count, column inventory, data completeness report, and basic range statistics per parameter.",
    advancedDetail:
      "PapaParse with dynamicTyping=true and skipEmptyLines=true. Columns are classified as numeric if at least one row contains a JavaScript number type. Missing value count is per-column. Only rows with a valid numeric value in the target metric column are passed to subsequent steps.",
    icon: "Database",
  },
  {
    id: "STABLE_REGION",
    label: "STABLE_REGION",
    title: "Stable Region",
    businessSummary:
      "Tantrium splits your records into two populations: the system operating normally, and the system in a failure state.",
    whatItDoes:
      "Using the target metric and the failure threshold you define, every row is classified as stable (operating within normal bounds) or unstable (in or approaching failure). The stable population is then used to define the safe operating envelope — the parameter ranges where your system runs without incident.",
    whatItProduces:
      "Stable row count, unstable row count, and a Safe Operating Envelope: for each key parameter, the range of values observed in stable operation (mean ± 1.5 standard deviations of the stable population).",
    advancedDetail:
      "Classification: a row is unstable if target >= threshold (direction: above) or target <= threshold (direction: below). Safe envelope per column: mean ± 1.5σ of stable-population values, clamped to observed stable min/max. Coverage percent: fraction of all rows (stable + unstable) within the computed envelope.",
    icon: "ShieldCheck",
  },
  {
    id: "BREAK_BOUNDARY",
    label: "BREAK_BOUNDARY",
    title: "Break Boundary",
    businessSummary:
      "Tantrium finds the exact threshold where your system transitions from stable operation into failure — not a probability, a specific value.",
    whatItDoes:
      "Tantrium sorts all records by the primary failure driver and scans for the point where the failure rate jumps sharply. This is the Break Boundary: the operational value at which your system reliably crosses from stable to unstable behavior.",
    whatItProduces:
      "The Break Boundary value for the primary driver, the confidence level of the detected transition (based on the sharpness of the stable-to-unstable jump), and the number of distinct transition events found in the data.",
    advancedDetail:
      "Rows are sorted ascending on the primary driver. A sliding window (size = max(5, 5% of n)) computes local failure rate on the left and right of each position. A transition is detected when rightFailRate − leftFailRate > 0.30. The boundary is the midpoint between the last stable and first unstable value at the highest-confidence transition. If no transition is detected above the threshold, the fallback is the 10th percentile of unstable rows on the primary driver.",
    icon: "AlertTriangle",
  },
  {
    id: "FIRST_OBSTRUCTION",
    label: "FIRST_OBSTRUCTION",
    title: "First Obstruction",
    businessSummary:
      "Tantrium identifies the single parameter or pair of parameters exerting the most pressure against your system's safe boundary.",
    whatItDoes:
      "Every parameter is scored on four dimensions: how strongly it tracks the failure metric, how often it breaks out of the safe zone during failures, how close it sits to the boundary, and whether it moves consistently toward failure. The parameter with the highest combined score is the First Obstruction — the primary lever that, if controlled, addresses the most boundary pressure.",
    whatItProduces:
      "A ranked list of all parameters by Tantrium Boundary Pressure Score (0–100), with the First Obstruction highlighted and a plain-English statement of why it is the primary driver.",
    advancedDetail:
      "Tantrium Score = 0.35 × |Pearson r| + 0.30 × crossingStrength + 0.20 × boundaryProximity + 0.15 × monotonicScore. crossingStrength: fraction of unstable rows where the driver falls outside mean ± 1.5σ of the stable population. boundaryProximity: 1 − (gap between unstable mean and stable boundary) / totalObservedRange. monotonicScore: |unstableMean − stableMean| / stableStdDev, normalized to [0,1] at 2σ separation.",
    icon: "Crosshair",
  },
  {
    id: "CLOSURE_PATH",
    label: "CLOSURE_PATH",
    title: "Closure Path",
    businessSummary:
      "Tantrium produces a concrete operational path back to the safe zone: specific parameter targets to move each driver away from the failure boundary.",
    whatItDoes:
      "For each of the top three failure drivers, Tantrium computes the median value of that parameter in the failure population, compares it to the center of the safe operating envelope, and generates a specific directional recommendation to move back into the safe zone.",
    whatItProduces:
      "Three prioritized operational recommendations, each specifying the parameter, its current failure-zone level, the target value, and the safe operating range to maintain.",
    advancedDetail:
      "For each top driver: current position = median of that driver across unstable rows. Target = safeMean (stable population mean). Direction = reduce if currentMedian > safeMean, else increase. Safe bounds = stable envelope [safeMin, safeMax]. Recommendations are ordered by Tantrium Score descending.",
    icon: "Route",
  },
  {
    id: "EVIDENCE_HASH",
    label: "EVIDENCE_HASH",
    title: "Evidence Hash",
    businessSummary:
      "Every completed analysis is fingerprinted with a unique Evidence Hash, certifying that the results were computed from real rows of data.",
    whatItDoes:
      "Tantrium generates a unique hash at the end of every real-data analysis. This hash encodes the dataset identity, target metric, threshold, row counts, primary driver, boundary value, and timestamp. It can be used to verify that a report came from a specific real analysis — not a synthetic demo.",
    whatItProduces:
      "A short alphanumeric Evidence Hash (format: TBE-XXXXXXXX) that uniquely identifies this analysis run. Stored in the Evidence Log with the full result record.",
    advancedDetail:
      "DJB2 hash of a pipe-delimited fingerprint string: datasetName|targetMetric|threshold|direction|validRowCount|stableRows|unstableRows|firstObstruction|boundaryValue|timestamp. Hash is prefixed with 'TBE-' to identify it as a Tantrium Boundary Engine output. A result is marked certified=true only when validRowCount > 0 and the hash is successfully generated.",
    icon: "Fingerprint",
  },
];

// ─── What Tantrium Is (and Is Not) ───────────────────────────────────────────

export const TANTRIUM_CORE_STATEMENT = {
  what: `Tantrium does not predict failure probability. It converts operational data into four precise outputs: a stable operating region, the exact boundary where the system breaks, the primary obstruction driving that break, and a concrete path back to safety.`,

  notProbability: `Most risk models tell you "there's a 73% chance of failure." That number doesn't tell an operator what to do. Tantrium tells you: "When Torque exceeds 47 Nm and Tool Wear is above 180 minutes, failure becomes systematic. Reduce Torque below 42 Nm to re-enter the safe zone."`,

  whenItWorks: `Tantrium works when you have operational records — any system that logs readings over time or across production runs. It requires a target metric (the thing that fails), a threshold (the value that defines failure), and at least one parameter that could be driving that failure. Give Tantrium a dataset with at least 50 rows, and it will find the boundary.`,

  guarantee: `Tantrium never labels a result as certified unless real rows were processed and an Evidence Hash was generated. Synthetic demos are clearly marked. Only a report generated from actual data carries the REAL DATA MODE label.`,
};

// ─── Glossary ─────────────────────────────────────────────────────────────────

export interface GlossaryEntry {
  term: string;
  plain: string;
}

export const TANTRIUM_GLOSSARY: GlossaryEntry[] = [
  {
    term: "Safe Operating Envelope",
    plain: "The range of parameter values observed when the system is running without failure. Think of it as the zone your system must stay inside.",
  },
  {
    term: "Break Boundary",
    plain: "The specific parameter value where stable operation reliably transitions into failure. This is the line Tantrium finds.",
  },
  {
    term: "First Obstruction",
    plain: "The single parameter applying the most pressure against your safe boundary. Controlling this one parameter addresses the majority of your failure risk.",
  },
  {
    term: "Closure Path",
    plain: "The operational steps needed to move each key parameter from its current failure-zone level back into the safe operating envelope.",
  },
  {
    term: "Boundary Pressure Score",
    plain: "A 0–100 index Tantrium assigns to each parameter, combining how strongly it correlates with failure, how often it escapes the safe zone, how close it sits to the boundary, and how consistently it moves toward failure.",
  },
  {
    term: "Evidence Hash",
    plain: "A unique fingerprint generated at the end of every real-data analysis. It certifies that the results came from actual rows of processed data, not a demo.",
  },
  {
    term: "Stable Population",
    plain: "The subset of your records where the target metric is within normal operating bounds. Tantrium uses these rows to define what 'normal' looks like.",
  },
  {
    term: "Unstable Population",
    plain: "The subset of your records where the system is in or approaching a failure state. Tantrium analyzes these rows to find what's different about them.",
  },
  {
    term: "Monotonic Direction",
    plain: "Whether a parameter consistently rises or consistently falls as the system moves toward failure. A parameter with strong monotonic direction is more actionable — you know which way to push it.",
  },
  {
    term: "Crossing Strength",
    plain: "The fraction of failure observations where a parameter has already escaped the safe zone. High crossing strength means the parameter is almost always outside its safe range when the system is failing.",
  },
];
