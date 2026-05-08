export interface SavedReport {
  id: string;
  computedAt: string;
  datasetId: string;
  datasetName: string;
  sector: string;
  rowsProcessed: number;
  stableRows: number;
  unstableRows: number;
  stablePercent: number;
  targetCol: string;
  threshold: number;
  direction: "above" | "below";
  topDriverName: string;
  topDriverScore: number;
  obstructionStatement: string;
  boundaryValue: number | null;
  boundaryDriver: string | null;
  boundaryConfidence: number | null;
  envelopeRanges: Array<{
    col: string;
    safeMin: number;
    safeMax: number;
    observedMin: number;
    observedMax: number;
    coverage: number;
  }>;
  closureSteps: Array<{
    businessAction: string;
    direction: "REDUCE" | "INCREASE";
  }>;
  allDrivers: Array<{ name: string; tantriumScore: number }>;
  evidenceHash: string;
  sourceUrl: string;
  mode: "REAL DATA" | "DEMO" | "INSUFFICIENT DATA";
  certified: boolean;
  executiveSummary: string;
}

const KEY = "tantrium_live_reports_v1";

export function getSavedReports(): SavedReport[] {
  const stored = localStorage.getItem(KEY);
  if (!stored) return [];
  try {
    return JSON.parse(stored) as SavedReport[];
  } catch {
    return [];
  }
}

export function upsertSavedReport(report: SavedReport): void {
  const current = getSavedReports();
  const idx = current.findIndex((r) => r.datasetId === report.datasetId);
  if (idx >= 0) {
    current[idx] = report;
  } else {
    current.unshift(report);
  }
  localStorage.setItem(KEY, JSON.stringify(current));
}

export function deleteSavedReport(id: string): void {
  const updated = getSavedReports().filter((r) => r.id !== id);
  localStorage.setItem(KEY, JSON.stringify(updated));
}

export function clearSavedReports(): void {
  localStorage.removeItem(KEY);
}
