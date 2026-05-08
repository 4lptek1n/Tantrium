import Papa from "papaparse";

// ─── Tantrium Methodology Step Labels ───────────────────────────────────────
export type TantriumStep =
  | "DATA_INGEST"
  | "STABLE_REGION"
  | "BREAK_BOUNDARY"
  | "FIRST_OBSTRUCTION"
  | "CLOSURE_PATH"
  | "EVIDENCE_HASH";

// ─── Core Data Types ─────────────────────────────────────────────────────────

export interface ColumnStats {
  min: number;
  max: number;
  mean: number;
  stdDev: number;
  count: number;
}

export interface DataSummary {
  rowCount: number;
  colCount: number;
  numericColumns: string[];
  categoricalColumns: string[];
  missingValues: Record<string, number>;
  numericStats: Record<string, ColumnStats>;
}

// Each driver scored by the Tantrium composite method
export interface DriverResult {
  name: string;
  // Raw Pearson correlation with target
  correlation: number;
  // |correlation| × 100 for display
  correlationStrength: number;
  // Fraction of unstable rows where driver is outside stable envelope (0–100)
  crossingStrength: number;
  // How tight the gap is between stable max and unstable min (0–100, higher = closer to boundary)
  boundaryProximity: number;
  // Whether driver moves monotonically toward failure (1 = monotonic, 0 = not)
  monotonicScore: number;
  // Combined Tantrium score: weighted sum of above components (0–100)
  tantriumScore: number;
  // Direction: which way the driver moves into failure
  failureDirection: "increasing" | "decreasing" | "non-monotonic";
  // Business explanation (auto-generated)
  explanation: string;
}

export interface SafeEnvelopeRange {
  column: string;
  safeMin: number;
  safeMax: number;
  safeMean: number;
  // Observed min/max across all rows
  observedMin: number;
  observedMax: number;
  // Fraction of rows inside safe envelope
  coveragePercent: number;
}

export interface BreakBoundaryPoint {
  // The primary driver at the boundary
  driverName: string;
  // Value at which stable→unstable transition first occurs
  boundaryValue: number;
  // Confidence: fraction of rows near this boundary that are unstable (0–1)
  confidence: number;
  // Number of transition events detected
  transitionCount: number;
}

export interface ClosureRecommendation {
  driverName: string;
  currentUnstableMedian: number;
  targetValue: number;  // Center of safe envelope
  safeMin: number;
  safeMax: number;
  direction: "reduce" | "increase";
  businessAction: string;
}

// ─── TantriumObject ──────────────────────────────────────────────────────────
// The formal representation of a dataset being analyzed through the Tantrium workflow

export interface TantriumObject {
  // Input identity
  datasetName: string;
  sourceUrl: string;
  sector: string;

  // System definition
  targetMetric: string;
  failureThreshold: number;
  failureDirection: "above" | "below";

  // DATA_INGEST
  ingest: {
    rawRowCount: number;
    validRowCount: number;
    summary: DataSummary;
  };

  // STABLE_REGION
  stableRegion: {
    stableRowCount: number;
    unstableRowCount: number;
    stablePercent: number;
    envelope: SafeEnvelopeRange[];
  };

  // BREAK_BOUNDARY
  breakBoundary: BreakBoundaryPoint | null;

  // FIRST_OBSTRUCTION
  firstObstruction: {
    driver: DriverResult;
    obstructionStatement: string;
  } | null;
  allDrivers: DriverResult[];

  // CLOSURE_PATH
  closurePath: ClosureRecommendation[];

  // EVIDENCE_HASH (populated last)
  evidenceHash: string;
  timestamp: string;

  // Mode guard — never "certified" unless real rows were processed
  mode: "REAL DATA" | "INSUFFICIENT DATA";
  certified: boolean;  // true only if validRowCount > 0 and hash generated
}

// ─── Step 0: CSV Parsing (DATA_INGEST) ───────────────────────────────────────

export function parseCSV(text: string) {
  return Papa.parse(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
}

function isNumericColumn(data: Record<string, unknown>[], col: string): boolean {
  return data.some(row => typeof row[col] === "number" && !isNaN(row[col] as number));
}

function getNumericValues(data: Record<string, unknown>[], col: string): number[] {
  return data
    .map(row => row[col])
    .filter((v): v is number => typeof v === "number" && !isNaN(v));
}

function computeStats(values: number[]): ColumnStats {
  if (values.length === 0) return { min: 0, max: 0, mean: 0, stdDev: 0, count: 0 };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / values.length;
  const variance = values.reduce((acc, v) => acc + (v - mean) ** 2, 0) / values.length;
  return { min, max, mean, stdDev: Math.sqrt(variance), count: values.length };
}

export function summarizeDataset(data: Record<string, unknown>[]): DataSummary {
  if (data.length === 0) {
    return { rowCount: 0, colCount: 0, numericColumns: [], categoricalColumns: [], missingValues: {}, numericStats: {} };
  }

  const keys = Object.keys(data[0]);
  const numericColumns: string[] = [];
  const categoricalColumns: string[] = [];
  const missingValues: Record<string, number> = {};
  const numericStats: Record<string, ColumnStats> = {};

  keys.forEach(key => {
    const missing = data.filter(row => row[key] === null || row[key] === undefined || row[key] === "").length;
    missingValues[key] = missing;

    if (isNumericColumn(data, key)) {
      numericColumns.push(key);
      numericStats[key] = computeStats(getNumericValues(data, key));
    } else {
      categoricalColumns.push(key);
    }
  });

  return {
    rowCount: data.length,
    colCount: keys.length,
    numericColumns,
    categoricalColumns,
    missingValues,
    numericStats,
  };
}

// ─── Step 1: STABLE_REGION ───────────────────────────────────────────────────

export function classifyRows(
  data: Record<string, unknown>[],
  targetCol: string,
  threshold: number,
  direction: "above" | "below"
): { stable: Record<string, unknown>[]; unstable: Record<string, unknown>[] } {
  const stable: Record<string, unknown>[] = [];
  const unstable: Record<string, unknown>[] = [];

  for (const row of data) {
    const val = row[targetCol];
    if (typeof val !== "number") continue;
    const isUnstable = direction === "above" ? val >= threshold : val <= threshold;
    (isUnstable ? unstable : stable).push(row);
  }

  return { stable, unstable };
}

export function computeSafeEnvelope(
  stableRows: Record<string, unknown>[],
  allRows: Record<string, unknown>[],
  topDriverNames: string[]
): SafeEnvelopeRange[] {
  return topDriverNames.map(col => {
    const stableVals = getNumericValues(stableRows, col);
    const allVals = getNumericValues(allRows, col);

    if (stableVals.length === 0) {
      return { column: col, safeMin: 0, safeMax: 0, safeMean: 0, observedMin: 0, observedMax: 0, coveragePercent: 0 };
    }

    const stats = computeStats(stableVals);
    // Safe envelope: mean ± 1.5σ, clamped to observed stable range
    const rawMin = stats.mean - 1.5 * stats.stdDev;
    const rawMax = stats.mean + 1.5 * stats.stdDev;
    const safeMin = Math.max(rawMin, stats.min);
    const safeMax = Math.min(rawMax, stats.max);

    const allStats = computeStats(allVals);

    // Fraction of all rows inside the safe envelope
    const inside = allVals.filter(v => v >= safeMin && v <= safeMax).length;
    const coveragePercent = allVals.length > 0 ? Math.round((inside / allVals.length) * 100) : 0;

    return {
      column: col,
      safeMin,
      safeMax,
      safeMean: stats.mean,
      observedMin: allStats.min,
      observedMax: allStats.max,
      coveragePercent,
    };
  });
}

// ─── Step 2: BREAK_BOUNDARY ──────────────────────────────────────────────────
// Find actual stable→unstable transitions by sorting rows on the primary driver
// and scanning for where the failure rate switches from low to high.

export function detectBreakBoundary(
  allRows: Record<string, unknown>[],
  primaryDriver: string,
  targetCol: string,
  threshold: number,
  direction: "above" | "below"
): BreakBoundaryPoint | null {
  const sorted = [...allRows]
    .filter(row => typeof row[primaryDriver] === "number" && typeof row[targetCol] === "number")
    .sort((a, b) => (a[primaryDriver] as number) - (b[primaryDriver] as number));

  if (sorted.length < 10) return null;

  const windowSize = Math.max(5, Math.floor(sorted.length * 0.05));
  let bestBoundary: number | null = null;
  let bestConfidence = 0;
  let transitionCount = 0;

  // Slide a window and look for failure-rate transition
  for (let i = windowSize; i < sorted.length - windowSize; i++) {
    const leftWindow = sorted.slice(Math.max(0, i - windowSize), i);
    const rightWindow = sorted.slice(i, Math.min(sorted.length, i + windowSize));

    const isUnstable = (row: Record<string, unknown>) => {
      const val = row[targetCol] as number;
      return direction === "above" ? val >= threshold : val <= threshold;
    };

    const leftFailRate = leftWindow.filter(isUnstable).length / leftWindow.length;
    const rightFailRate = rightWindow.filter(isUnstable).length / rightWindow.length;
    const jump = rightFailRate - leftFailRate;

    if (jump > 0.3 && rightFailRate > bestConfidence) {
      bestBoundary = ((sorted[i - 1][primaryDriver] as number) + (sorted[i][primaryDriver] as number)) / 2;
      bestConfidence = rightFailRate;
      transitionCount++;
    }
  }

  if (bestBoundary === null) {
    // Fallback: 10th percentile of unstable rows
    const unstableVals = sorted
      .filter(row => {
        const val = row[targetCol] as number;
        return direction === "above" ? val >= threshold : val <= threshold;
      })
      .map(row => row[primaryDriver] as number);

    if (unstableVals.length === 0) return null;
    const idx = Math.floor(unstableVals.length * 0.1);
    bestBoundary = unstableVals[idx];
    bestConfidence = 0.5;
    transitionCount = 1;
  }

  return {
    driverName: primaryDriver,
    boundaryValue: bestBoundary,
    confidence: bestConfidence,
    transitionCount,
  };
}

// ─── Step 3: FIRST_OBSTRUCTION ───────────────────────────────────────────────
// Rank drivers by a combined Tantrium score:
// 1. Correlation score: |Pearson r| with target
// 2. Crossing strength: fraction of unstable rows where driver is outside stable envelope
// 3. Boundary proximity: how tight the gap is between stable max/min and unstable min/max
// 4. Monotonic score: whether driver consistently moves in one direction as target crosses threshold

function computePearson(data: Record<string, unknown>[], colX: string, colY: string): number {
  const pairs = data
    .filter(row => typeof row[colX] === "number" && typeof row[colY] === "number")
    .map(row => ({ x: row[colX] as number, y: row[colY] as number }));

  const n = pairs.length;
  if (n < 3) return 0;

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
  for (const { x, y } of pairs) {
    sumX += x; sumY += y; sumXY += x * y; sumX2 += x * x; sumY2 += y * y;
  }

  const num = n * sumXY - sumX * sumY;
  const den = Math.sqrt((n * sumX2 - sumX ** 2) * (n * sumY2 - sumY ** 2));
  return den === 0 ? 0 : Math.max(-1, Math.min(1, num / den));
}

function computeMonotonicScore(
  stableVals: number[],
  unstableVals: number[],
  direction: "above" | "below"
): { score: number; failureDirection: "increasing" | "decreasing" | "non-monotonic" } {
  if (stableVals.length === 0 || unstableVals.length === 0) {
    return { score: 0, failureDirection: "non-monotonic" };
  }

  const stableMean = stableVals.reduce((a, b) => a + b, 0) / stableVals.length;
  const unstableMean = unstableVals.reduce((a, b) => a + b, 0) / unstableVals.length;
  const diff = unstableMean - stableMean;

  // Score based on how cleanly the means separate
  const stableStd = computeStats(stableVals).stdDev || 1;
  const separation = Math.abs(diff) / stableStd;
  const score = Math.min(1, separation / 2); // normalize: separation of 2σ = score 1.0

  const failureDirection: "increasing" | "decreasing" | "non-monotonic" =
    separation < 0.3 ? "non-monotonic" : diff > 0 ? "increasing" : "decreasing";

  return { score, failureDirection };
}

export function scoreDrivers(
  allRows: Record<string, unknown>[],
  stableRows: Record<string, unknown>[],
  unstableRows: Record<string, unknown>[],
  targetCol: string,
  direction: "above" | "below"
): DriverResult[] {
  if (allRows.length === 0) return [];

  const keys = Object.keys(allRows[0]).filter(k => k !== targetCol && isNumericColumn(allRows, k));
  const results: DriverResult[] = [];

  for (const key of keys) {
    const allVals = getNumericValues(allRows, key);
    const stableVals = getNumericValues(stableRows, key);
    const unstableVals = getNumericValues(unstableRows, key);

    if (allVals.length < 5) continue;

    // 1. Correlation score
    const r = computePearson(allRows, key, targetCol);
    const correlationScore = Math.abs(r);

    // 2. Crossing strength: fraction of unstable rows outside stable envelope
    const stableStats = computeStats(stableVals);
    const stableLow = stableStats.mean - 1.5 * stableStats.stdDev;
    const stableHigh = stableStats.mean + 1.5 * stableStats.stdDev;
    const outsideEnvelope = unstableVals.filter(v => v < stableLow || v > stableHigh).length;
    const crossingStrength = unstableVals.length > 0 ? outsideEnvelope / unstableVals.length : 0;

    // 3. Boundary proximity: how close is the gap between stable boundary and unstable cluster?
    // Measure the gap as fraction of total observed range
    const totalRange = stableStats.max - stableStats.min;
    let proximityScore = 0;
    if (totalRange > 0 && unstableVals.length > 0) {
      const unstableStats = computeStats(unstableVals);
      const gap = Math.min(
        Math.abs(unstableStats.mean - stableHigh),
        Math.abs(unstableStats.mean - stableLow)
      );
      proximityScore = Math.max(0, 1 - gap / (totalRange + 0.0001));
    }

    // 4. Monotonic score
    const { score: monotonicScore, failureDirection } = computeMonotonicScore(stableVals, unstableVals, direction);

    // Tantrium composite score (weighted)
    const tantriumScore = Math.round(
      (correlationScore * 0.35 + crossingStrength * 0.30 + proximityScore * 0.20 + monotonicScore * 0.15) * 100
    );

    // Business explanation
    const strengthLabel =
      correlationScore > 0.7 ? "strong" :
      correlationScore > 0.45 ? "moderate" :
      correlationScore > 0.2 ? "notable" : "weak";

    const dirLabel = failureDirection === "increasing"
      ? "rises as the system approaches failure"
      : failureDirection === "decreasing"
      ? "falls as the system approaches failure"
      : "shows irregular movement near failure";

    const explanation =
      `${key} has a ${strengthLabel} relationship with ${targetCol} and ${dirLabel}. ` +
      `In the stable operating population, ${key} stays within a tighter range. ` +
      `${Math.round(crossingStrength * 100)}% of failure observations fall outside that safe zone.`;

    results.push({
      name: key,
      correlation: r,
      correlationStrength: Math.round(correlationScore * 100),
      crossingStrength: Math.round(crossingStrength * 100),
      boundaryProximity: Math.round(proximityScore * 100),
      monotonicScore: Math.round(monotonicScore * 100),
      tantriumScore,
      failureDirection,
      explanation,
    });
  }

  return results.sort((a, b) => b.tantriumScore - a.tantriumScore);
}

// ─── Step 4: CLOSURE_PATH ────────────────────────────────────────────────────
// For each top driver: recommend moving from current (unstable median) toward safe envelope

export function computeClosurePath(
  unstableRows: Record<string, unknown>[],
  topDrivers: DriverResult[],
  safeEnvelope: SafeEnvelopeRange[]
): ClosureRecommendation[] {
  const recommendations: ClosureRecommendation[] = [];

  for (const driver of topDrivers.slice(0, 3)) {
    const envelope = safeEnvelope.find(e => e.column === driver.name);
    if (!envelope) continue;

    const unstableVals = getNumericValues(unstableRows, driver.name).sort((a, b) => a - b);
    if (unstableVals.length === 0) continue;

    const medianIdx = Math.floor(unstableVals.length / 2);
    const currentUnstableMedian = unstableVals[medianIdx];
    const targetValue = envelope.safeMean;
    const direction: "reduce" | "increase" = currentUnstableMedian > targetValue ? "reduce" : "increase";

    const fmt = (n: number) => n % 1 === 0 ? n.toFixed(0) : n.toFixed(2);

    const businessAction =
      direction === "reduce"
        ? `Reduce ${driver.name} from its current failure-zone level (median: ${fmt(currentUnstableMedian)}) toward the safe operating center (${fmt(targetValue)}). Keep within ${fmt(envelope.safeMin)} – ${fmt(envelope.safeMax)}.`
        : `Increase ${driver.name} from its current failure-zone level (median: ${fmt(currentUnstableMedian)}) toward the safe operating center (${fmt(targetValue)}). Keep within ${fmt(envelope.safeMin)} – ${fmt(envelope.safeMax)}.`;

    recommendations.push({
      driverName: driver.name,
      currentUnstableMedian,
      targetValue,
      safeMin: envelope.safeMin,
      safeMax: envelope.safeMax,
      direction,
      businessAction,
    });
  }

  return recommendations;
}

// ─── Step 5: EVIDENCE_HASH ───────────────────────────────────────────────────

function djb2(str: string): string {
  let h = 5381;
  for (let i = 0; i < str.length; i++) h = (h * 33) ^ str.charCodeAt(i);
  return (h >>> 0).toString(16).toUpperCase();
}

export function generateEvidenceHash(obj: TantriumObject): string {
  const fingerprint = [
    obj.datasetName,
    obj.targetMetric,
    obj.failureThreshold,
    obj.failureDirection,
    obj.ingest.validRowCount,
    obj.stableRegion.stableRowCount,
    obj.stableRegion.unstableRowCount,
    obj.firstObstruction?.driver.name ?? "none",
    obj.breakBoundary?.boundaryValue ?? "none",
    obj.timestamp,
  ].join("|");
  return `TBE-${djb2(fingerprint)}`;
}

// ─── Master Orchestrator ─────────────────────────────────────────────────────
// Runs the full Tantrium workflow and returns a TantriumObject.
// onProgress callback fires with each step label as it completes.

export async function runTantriumWorkflow(
  rawData: Record<string, unknown>[],
  targetCol: string,
  threshold: number,
  direction: "above" | "below",
  datasetName: string,
  sourceUrl: string,
  sector: string,
  onProgress?: (step: TantriumStep) => void
): Promise<TantriumObject> {

  const timestamp = new Date().toISOString();

  // ── DATA_INGEST ──────────────────────────────────────────────────────
  const validRows = rawData.filter(row => typeof row[targetCol] === "number");
  const summary = summarizeDataset(validRows);
  onProgress?.("DATA_INGEST");

  // Guard: need real rows
  if (validRows.length < 10) {
    return {
      datasetName, sourceUrl, sector,
      targetMetric: targetCol, failureThreshold: threshold, failureDirection: direction,
      ingest: { rawRowCount: rawData.length, validRowCount: validRows.length, summary },
      stableRegion: { stableRowCount: 0, unstableRowCount: 0, stablePercent: 0, envelope: [] },
      breakBoundary: null,
      firstObstruction: null,
      allDrivers: [],
      closurePath: [],
      evidenceHash: "",
      timestamp,
      mode: "INSUFFICIENT DATA",
      certified: false,
    };
  }

  // ── STABLE_REGION ────────────────────────────────────────────────────
  const { stable, unstable } = classifyRows(validRows, targetCol, threshold, direction);
  onProgress?.("STABLE_REGION");

  // ── Score drivers (needed for envelope + boundary) ───────────────────
  const allDrivers = scoreDrivers(validRows, stable, unstable, targetCol, direction);
  const top5Names = allDrivers.slice(0, 5).map(d => d.name);

  const envelope = computeSafeEnvelope(stable, validRows, top5Names);
  const stablePercent = Math.round((stable.length / validRows.length) * 100);

  // ── BREAK_BOUNDARY ───────────────────────────────────────────────────
  const primaryDriver = allDrivers[0]?.name ?? null;
  const breakBoundary = primaryDriver
    ? detectBreakBoundary(validRows, primaryDriver, targetCol, threshold, direction)
    : null;
  onProgress?.("BREAK_BOUNDARY");

  // ── FIRST_OBSTRUCTION ────────────────────────────────────────────────
  const firstDriver = allDrivers[0] ?? null;
  const firstObstruction = firstDriver
    ? {
        driver: firstDriver,
        obstructionStatement:
          `The primary obstruction is ${firstDriver.name}. ` +
          `It scores ${firstDriver.tantriumScore}/100 on the Tantrium boundary pressure index — ` +
          `driven by a ${firstDriver.correlationStrength}% correlation with ${targetCol}, ` +
          `${firstDriver.crossingStrength}% of failure observations outside the safe envelope, ` +
          `and a ${firstDriver.failureDirection === "non-monotonic" ? "non-monotonic" : firstDriver.failureDirection + " trend"} toward the boundary.`,
      }
    : null;
  onProgress?.("FIRST_OBSTRUCTION");

  // ── CLOSURE_PATH ─────────────────────────────────────────────────────
  const top3Envelope = envelope.slice(0, 3);
  const closurePath = computeClosurePath(unstable, allDrivers, top3Envelope);
  onProgress?.("CLOSURE_PATH");

  // ── EVIDENCE_HASH ────────────────────────────────────────────────────
  const partial: TantriumObject = {
    datasetName, sourceUrl, sector,
    targetMetric: targetCol, failureThreshold: threshold, failureDirection: direction,
    ingest: { rawRowCount: rawData.length, validRowCount: validRows.length, summary },
    stableRegion: {
      stableRowCount: stable.length,
      unstableRowCount: unstable.length,
      stablePercent,
      envelope,
    },
    breakBoundary,
    firstObstruction,
    allDrivers,
    closurePath,
    evidenceHash: "",
    timestamp,
    mode: "REAL DATA",
    certified: false,
  };

  const evidenceHash = generateEvidenceHash(partial);
  onProgress?.("EVIDENCE_HASH");

  return {
    ...partial,
    evidenceHash,
    certified: validRows.length > 0 && evidenceHash.length > 0,
  };
}
