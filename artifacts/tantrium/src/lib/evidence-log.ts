import type { TantriumObject } from "./analysis-engine";

export interface EvidenceEntry {
  id: string;
  timestamp: string;
  datasetName: string;
  sector: string;
  rowsProcessed: number;
  stableRows: number;
  unstableRows: number;
  targetCol: string;
  threshold: number;
  direction: "above" | "below";
  topDriver: string;
  tantriumScore: number;
  boundaryValue: number | null;
  evidenceHash: string;
  mode: "REAL DATA" | "DEMO" | "INSUFFICIENT DATA";
  certified: boolean;
}

const STORAGE_KEY = "tantrium_evidence_log_v2";

export function addEvidenceEntry(obj: TantriumObject): EvidenceEntry {
  const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

  const entry: EvidenceEntry = {
    id,
    timestamp: obj.timestamp,
    datasetName: obj.datasetName,
    sector: obj.sector,
    rowsProcessed: obj.ingest.validRowCount,
    stableRows: obj.stableRegion.stableRowCount,
    unstableRows: obj.stableRegion.unstableRowCount,
    targetCol: obj.targetMetric,
    threshold: obj.failureThreshold,
    direction: obj.failureDirection,
    topDriver: obj.firstObstruction?.driver.name ?? "—",
    tantriumScore: obj.firstObstruction?.driver.tantriumScore ?? 0,
    boundaryValue: obj.breakBoundary?.boundaryValue ?? null,
    evidenceHash: obj.evidenceHash,
    mode: obj.mode,
    certified: obj.certified,
  };

  const current = getEvidenceLog();
  const updated = [entry, ...current].slice(0, 50);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

  return entry;
}

export function getEvidenceLog(): EvidenceEntry[] {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return [];
  try {
    return JSON.parse(stored) as EvidenceEntry[];
  } catch {
    return [];
  }
}

export function clearEvidenceLog(): void {
  localStorage.removeItem(STORAGE_KEY);
}
