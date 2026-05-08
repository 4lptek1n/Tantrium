import Papa from "papaparse";

export interface DataSummary {
  rowCount: number;
  colCount: number;
  missingValues: Record<string, number>;
  numericStats: Record<string, {
    min: number;
    max: number;
    mean: number;
    stdDev: number;
  }>;
}

export interface DriverResult {
  name: string;
  correlation: number;
  impact: number;
  explanation: string;
}

export interface SafeEnvelopeRange {
  column: string;
  min: number;
  max: number;
  mean: number;
}

export interface AnalysisResult {
  datasetName: string;
  targetCol: string;
  threshold: number;
  direction: "above" | "below";
  summary: DataSummary;
  stableCount: number;
  unstableCount: number;
  drivers: DriverResult[];
  boundaryValue: number | null;
  boundaryDriver: string | null;
  safeEnvelope: SafeEnvelopeRange[];
}

export function parseCSV(text: string) {
  return Papa.parse(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
}

export function summarizeDataset(data: any[]): DataSummary {
  if (data.length === 0) {
    return { rowCount: 0, colCount: 0, missingValues: {}, numericStats: {} };
  }

  const keys = Object.keys(data[0]);
  const rowCount = data.length;
  const colCount = keys.length;
  const missingValues: Record<string, number> = {};
  const numericStats: Record<string, { min: number; max: number; mean: number; stdDev: number }> = {};

  keys.forEach((key) => {
    let missing = 0;
    const values: number[] = [];

    data.forEach((row) => {
      const val = row[key];
      if (val === null || val === undefined || val === "") {
        missing++;
      } else if (typeof val === "number") {
        values.push(val);
      }
    });

    missingValues[key] = missing;

    if (values.length > 0) {
      const min = Math.min(...values);
      const max = Math.max(...values);
      const sum = values.reduce((a, b) => a + b, 0);
      const mean = sum / values.length;
      const squareDiffs = values.map((v) => Math.pow(v - mean, 2));
      const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / values.length;
      const stdDev = Math.sqrt(avgSquareDiff);

      numericStats[key] = { min, max, mean, stdDev };
    }
  });

  return { rowCount, colCount, missingValues, numericStats };
}

export function classifyRows(data: any[], targetCol: string, threshold: number, direction: "above" | "below") {
  const stable: any[] = [];
  const unstable: any[] = [];

  data.forEach((row) => {
    const val = row[targetCol];
    if (typeof val !== "number") return;

    const isUnstable = direction === "above" ? val >= threshold : val <= threshold;
    if (isUnstable) {
      unstable.push(row);
    } else {
      stable.push(row);
    }
  });

  return { stable, unstable };
}

function computePearson(data: any[], colX: string, colY: string): number {
  const x: number[] = [];
  const y: number[] = [];

  data.forEach((row) => {
    if (typeof row[colX] === "number" && typeof row[colY] === "number") {
      x.push(row[colX]);
      y.push(row[colY]);
    }
  });

  const n = x.length;
  if (n < 2) return 0;

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
  for (let i = 0; i < n; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
    sumY2 += y[i] * y[i];
  }

  const num = n * sumXY - sumX * sumY;
  const den = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

  if (den === 0) return 0;
  return num / den;
}

export function computeDriverCorrelations(data: any[], targetCol: string): DriverResult[] {
  if (data.length === 0) return [];

  const keys = Object.keys(data[0]);
  const results: DriverResult[] = [];

  keys.forEach((key) => {
    if (key === targetCol) return;
    
    // Check if column is numeric
    const isNumeric = data.some(row => typeof row[key] === 'number');
    if (!isNumeric) return;

    const r = computePearson(data, key, targetCol);
    results.push({
      name: key,
      correlation: r,
      impact: Math.round(Math.abs(r) * 100),
      explanation: `Statistical relationship between ${key} and ${targetCol}.`
    });
  });

  return results.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
}

export function estimateBreakBoundary(data: any[], driverCol: string, targetCol: string, threshold: number) {
  if (data.length === 0) return null;

  // For break boundary: sort unstable rows by driver value ascending, take the p10 value (10th percentile)
  const values = data
    .map(row => row[driverCol])
    .filter(val => typeof val === 'number')
    .sort((a, b) => a - b);

  if (values.length === 0) return null;

  const idx = Math.floor(values.length * 0.1);
  return values[idx];
}

export function computeSafeEnvelope(stableRows: any[], topDriverCols: string[]): SafeEnvelopeRange[] {
  const summary = summarizeDataset(stableRows);
  return topDriverCols.map(col => {
    const stats = summary.numericStats[col];
    if (!stats) return { column: col, min: 0, max: 0, mean: 0 };
    
    // mean ± 1.5σ range
    return {
      column: col,
      min: stats.mean - 1.5 * stats.stdDev,
      max: stats.mean + 1.5 * stats.stdDev,
      mean: stats.mean
    };
  });
}

export async function generateAnalysisResult(
  data: any[], 
  targetCol: string, 
  threshold: number, 
  direction: "above" | "below", 
  datasetName: string
): Promise<AnalysisResult> {
  const summary = summarizeDataset(data);
  const { stable, unstable } = classifyRows(data, targetCol, threshold, direction);
  const drivers = computeDriverCorrelations(data, targetCol);
  
  const topDrivers = drivers.slice(0, 3).map(d => d.name);
  const safeEnvelope = computeSafeEnvelope(stable, topDrivers);
  
  let boundaryValue: number | null = null;
  let boundaryDriver: string | null = null;

  if (drivers.length > 0 && unstable.length > 0) {
    boundaryDriver = drivers[0].name;
    boundaryValue = estimateBreakBoundary(unstable, boundaryDriver, targetCol, threshold);
  }

  return {
    datasetName,
    targetCol,
    threshold,
    direction,
    summary,
    stableCount: stable.length,
    unstableCount: unstable.length,
    drivers,
    boundaryValue,
    boundaryDriver,
    safeEnvelope
  };
}
