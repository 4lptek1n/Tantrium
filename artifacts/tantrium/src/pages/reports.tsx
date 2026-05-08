import { useState, useEffect } from "react";
import { Link } from "wouter";
import { runTantriumWorkflow, parseCSV } from "@/lib/analysis-engine";
import type { TantriumObject } from "@/lib/analysis-engine";
import { DATASET_REGISTRY } from "@/lib/dataset-registry";
import { getSavedReports, upsertSavedReport, type SavedReport } from "@/lib/report-store";
import { getEvidenceLog } from "@/lib/evidence-log";
import type { EvidenceEntry } from "@/lib/evidence-log";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { 
  ShieldCheck, AlertTriangle, Crosshair, Route, Fingerprint, 
  Loader2, CheckCircle2, RefreshCw, BarChart3, Database, ArrowRight
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function ReportsPage() {
  const [savedReports, setSavedReports] = useState<SavedReport[]>([]);
  const [computingIds, setComputingIds] = useState<Set<string>>(new Set());
  const [computeErrors, setComputeErrors] = useState<Record<string, string>>({});
  const [userLogs, setUserLogs] = useState<EvidenceEntry[]>([]);
  const [expandedReportId, setExpandedReportId] = useState<string | null>(null);

  const targetDatasets = ["server-temp", "insurance-claims", "wine-quality", "diamonds"];

  const loadData = () => {
    const reports = getSavedReports();
    setSavedReports(reports);
    setUserLogs(getEvidenceLog());
    return reports;
  };

  useEffect(() => {
    const reports = loadData();
    const existingIds = new Set(reports.map(r => r.datasetId));
    
    targetDatasets.forEach(id => {
      if (!existingIds.has(id)) {
        computeReport(id);
      }
    });
  }, []);

  const computeReport = async (datasetId: string) => {
    setComputingIds(prev => new Set(prev).add(datasetId));
    setComputeErrors(prev => {
      const next = { ...prev };
      delete next[datasetId];
      return next;
    });

    try {
      const entry = DATASET_REGISTRY.find(d => d.id === datasetId);
      if (!entry || !entry.url) throw new Error("Dataset not found or no URL");

      const response = await fetch(entry.url);
      if (!response.ok) throw new Error(`Fetch failed: ${response.statusText}`);
      const text = await response.text();
      const parsed = parseCSV(text);

      const obj = await runTantriumWorkflow(
        parsed.data as Record<string, any>[],
        entry.suggestedTargetCol || "",
        entry.suggestedThreshold || 0,
        entry.suggestedDirection || "above",
        entry.name,
        entry.url,
        entry.sector
      );

      const report: SavedReport = {
        id: crypto.randomUUID(),
        computedAt: obj.timestamp,
        datasetId: datasetId,
        datasetName: obj.datasetName,
        sector: obj.sector,
        rowsProcessed: obj.ingest.validRowCount,
        stableRows: obj.stableRegion.stableRowCount,
        unstableRows: obj.stableRegion.unstableRowCount,
        stablePercent: obj.stableRegion.stablePercent,
        targetCol: obj.targetMetric,
        threshold: obj.failureThreshold,
        direction: obj.failureDirection,
        topDriverName: obj.firstObstruction?.driver.name ?? "—",
        topDriverScore: obj.firstObstruction?.driver.tantriumScore ?? 0,
        obstructionStatement: obj.firstObstruction?.obstructionStatement ?? "",
        boundaryValue: obj.breakBoundary?.boundaryValue ?? null,
        boundaryDriver: obj.breakBoundary?.driverName ?? null,
        boundaryConfidence: obj.breakBoundary?.confidence ?? null,
        envelopeRanges: obj.stableRegion.envelope.slice(0, 5).map(e => ({
          col: e.column,
          safeMin: e.safeMin,
          safeMax: e.safeMax,
          observedMin: e.observedMin,
          observedMax: e.observedMax,
          coverage: e.coveragePercent
        })),
        closureSteps: obj.closurePath.map(c => ({
          businessAction: c.businessAction,
          direction: c.direction.toUpperCase() as "REDUCE" | "INCREASE"
        })),
        allDrivers: obj.allDrivers.slice(0, 8).map(d => ({
          name: d.name,
          tantriumScore: d.tantriumScore
        })),
        evidenceHash: obj.evidenceHash,
        sourceUrl: obj.sourceUrl,
        mode: obj.mode,
        certified: obj.certified,
        executiveSummary: obj.firstObstruction?.obstructionStatement ?? "" // Formula from hunt page is essentially this
      };

      upsertSavedReport(report);
      loadData();
    } catch (err: any) {
      setComputeErrors(prev => ({ ...prev, [datasetId]: err.message }));
    } finally {
      setComputingIds(prev => {
        const next = new Set(prev);
        next.delete(datasetId);
        return next;
      });
    }
  };

  const handleRerunAll = () => {
    localStorage.removeItem("tantrium_live_reports_v1");
    setSavedReports([]);
    targetDatasets.forEach(id => computeReport(id));
  };

  const formatNum = (n: number | null) => {
    if (n === null) return "—";
    return n % 1 === 0 ? n.toFixed(0) : n.toFixed(2);
  };

  return (
    <div className="flex-1 w-full max-w-screen-xl mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live Boundary Reports</h1>
          <p className="text-muted-foreground">Real analysis. Real public datasets. Evidence-grade outputs.</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Badge variant="outline" className="bg-primary/5">
            {savedReports.length} Reports Generated
          </Badge>
          <Badge variant="outline" className="bg-primary/5">
            {userLogs.length} User Analyses
          </Badge>
          <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-200">
            Real Data Only
          </Badge>
          <Button onClick={handleRerunAll} variant="outline" size="sm" className="ml-2">
            <RefreshCw className="w-4 h-4 mr-2" /> Re-run All
          </Button>
        </div>
      </div>

      <Tabs defaultValue="live" className="space-y-6">
        <TabsList>
          <TabsTrigger value="live">Live Reports</TabsTrigger>
          <TabsTrigger value="my">My Analyses</TabsTrigger>
        </TabsList>

        <TabsContent value="live" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            {targetDatasets.map(id => {
              const report = savedReports.find(r => r.datasetId === id);
              const isComputing = computingIds.has(id);
              const error = computeErrors[id];
              const entry = DATASET_REGISTRY.find(d => d.id === id);

              if (isComputing) {
                return (
                  <Card key={id} className="animate-pulse">
                    <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4 min-h-[300px]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold">{entry?.name}</span>
                        <Badge variant="secondary" className="text-[10px]">{entry?.sector}</Badge>
                      </div>
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                      <div className="space-y-2 w-full max-w-xs">
                        <p className="text-sm font-medium">Fetching and analyzing rows of real operational data...</p>
                        <Progress value={undefined} className="h-1" />
                        <p className="text-[10px] text-muted-foreground truncate">Source: {entry?.url}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              }

              if (error) {
                return (
                  <Card key={id} className="border-destructive/20">
                    <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4 min-h-[300px]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold">{entry?.name}</span>
                        <Badge variant="destructive" className="text-[10px]">FETCH FAILED</Badge>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-destructive" />
                      <p className="text-sm text-destructive">{error}</p>
                      <Button onClick={() => computeReport(id)} variant="outline" size="sm">
                        <RefreshCw className="w-4 h-4 mr-2" /> Retry
                      </Button>
                    </CardContent>
                  </Card>
                );
              }

              if (!report) return null;

              const isExpanded = expandedReportId === report.id;

              return (
                <Card key={report.id} className="overflow-hidden border-primary/10">
                  <CardHeader className="bg-muted/30 pb-4">
                    <div className="flex justify-between items-start gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <CardTitle className="text-xl">{report.datasetName}</CardTitle>
                          <Badge variant="secondary" className="text-[10px]">{report.sector}</Badge>
                          {report.certified && <Badge className="bg-green-600 text-[10px]">REAL DATA</Badge>}
                        </div>
                        <p className="text-[10px] text-muted-foreground">
                          Computed: {new Date(report.computedAt).toLocaleString()}
                        </p>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => setExpandedReportId(isExpanded ? null : report.id)}
                      >
                        {isExpanded ? "Collapse" : "View Full Report"}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6 space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-mono">Rows</p>
                        <p className="text-lg font-bold">{report.rowsProcessed}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-mono">Stable</p>
                        <p className="text-lg font-bold text-green-600">{report.stableRows} ({report.stablePercent}%)</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-mono">Unstable</p>
                        <p className="text-lg font-bold text-amber-600">{report.unstableRows} ({100 - report.stablePercent}%)</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-mono">Driver Score</p>
                        <p className="text-lg font-bold">{report.topDriverScore}/100</p>
                      </div>
                    </div>

                    <div className="border-l-4 border-amber-500 bg-amber-500/5 p-4 rounded-r-lg space-y-2">
                      <div className="flex items-center gap-2">
                        <Crosshair className="w-4 h-4 text-amber-600" />
                        <span className="text-xs font-bold uppercase tracking-wider text-amber-800">First Obstruction: {report.topDriverName}</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] font-mono">
                          <span>Boundary Pressure Index</span>
                          <span>{report.topDriverScore}/100</span>
                        </div>
                        <Progress value={report.topDriverScore} className="h-1.5 bg-amber-200" />
                      </div>
                      <p className={`text-xs text-muted-foreground leading-relaxed ${!isExpanded ? "line-clamp-2" : ""}`}>
                        {report.obstructionStatement}
                      </p>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/20">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-primary" />
                        <span className="text-xs font-medium">
                          {report.boundaryValue 
                            ? `Breach at ${report.boundaryDriver} = ${formatNum(report.boundaryValue)}`
                            : "No clear transition detected — broaden threshold range"
                          }
                        </span>
                      </div>
                      {report.boundaryConfidence !== null && (
                        <Badge variant="outline" className="text-[10px]">
                          Confidence: {Math.round(report.boundaryConfidence * 100)}%
                        </Badge>
                      )}
                    </div>

                    {!isExpanded && (
                      <div className="flex justify-between items-center pt-2">
                        <code className="text-[10px] text-muted-foreground font-mono">
                          Hash: {report.evidenceHash.substring(0, 16)}...
                        </code>
                        <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => setExpandedReportId(report.id)}>
                          Full Report ↓
                        </Button>
                      </div>
                    )}

                    {isExpanded && (
                      <div className="pt-4 space-y-8 animate-in fade-in slide-in-from-top-4 duration-300">
                        <div className="space-y-3">
                          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Executive Summary</h4>
                          <p className="text-sm leading-relaxed">{report.executiveSummary}</p>
                        </div>

                        <div className="space-y-4">
                          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Safe Operating Envelope</h4>
                          <div className="grid gap-4">
                            {report.envelopeRanges.slice(0, 3).map((e, i) => {
                              const range = e.observedMax - e.observedMin;
                              const leftPct = range === 0 ? 0 : ((e.safeMin - e.observedMin) / range) * 100;
                              const widthPct = range === 0 ? 0 : ((e.safeMax - e.safeMin) / range) * 100;

                              return (
                                <div key={i} className="space-y-1.5">
                                  <div className="flex justify-between items-end">
                                    <span className="text-xs font-bold font-mono">{e.col}</span>
                                    <span className="text-[10px] text-muted-foreground">Safe: {formatNum(e.safeMin)} – {formatNum(e.safeMax)} | Coverage: {e.coverage}%</span>
                                  </div>
                                  <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                                    <div 
                                      className="absolute h-full bg-primary/40 rounded-full"
                                      style={{ left: `${Math.max(0, leftPct)}%`, width: `${Math.min(100, widthPct)}%` }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">All Boundary Drivers</h4>
                          <div className="h-[200px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={report.allDrivers} layout="vertical" margin={{ left: 0, right: 20 }}>
                                <XAxis type="number" domain={[0, 100]} hide />
                                <YAxis 
                                  dataKey="name" 
                                  type="category" 
                                  width={130} 
                                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} 
                                />
                                <Tooltip 
                                  cursor={{ fill: "hsl(var(--muted)/0.2)" }}
                                  contentStyle={{ borderRadius: "8px", border: "1px solid hsl(var(--border))", fontSize: "12px" }}
                                />
                                <Bar dataKey="tantriumScore" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} barSize={20} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Closure Path</h4>
                          <div className="space-y-3">
                            {report.closureSteps.map((step, i) => (
                              <div key={i} className="flex gap-4 p-3 rounded-lg border bg-background">
                                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold">
                                  {i + 1}
                                </div>
                                <div className="space-y-1">
                                  <p className="text-xs leading-relaxed">{step.businessAction}</p>
                                  <Badge variant={step.direction === "REDUCE" ? "destructive" : "default"} className="text-[8px] h-4 px-1">
                                    {step.direction}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="pt-6 border-t space-y-4">
                          <div className="flex flex-col gap-1">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Evidence Hash</span>
                            <code className="text-xs bg-muted p-2 rounded block font-mono break-all">
                              {report.evidenceHash}
                            </code>
                          </div>
                          <div className="flex gap-3">
                            <Button variant="outline" size="sm" onClick={() => computeReport(report.datasetId)}>
                              <RefreshCw className="w-4 h-4 mr-2" /> Run Again
                            </Button>
                            <Button asChild size="sm">
                              <Link href="/pricing">Request Analyst Report <ArrowRight className="w-4 h-4 ml-2" /></Link>
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="my" className="space-y-6">
          {userLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32 text-center space-y-4 border-2 border-dashed rounded-xl border-muted">
              <Database className="w-12 h-12 text-muted-foreground opacity-20" />
              <div className="space-y-2">
                <h3 className="text-xl font-semibold">No analyses yet</h3>
                <p className="text-muted-foreground max-w-sm mx-auto">Run a problem in the Problem Hunt to generate your first evidence entry.</p>
              </div>
              <Button asChild>
                <Link href="/hunt">Go to Problem Hunt <ArrowRight className="w-4 h-4 ml-2" /></Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {userLogs.map(log => (
                <Card key={log.id} className="border-primary/5 hover:border-primary/20 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold">{log.datasetName}</h4>
                          <Badge variant="secondary" className="text-[10px]">{log.sector}</Badge>
                          <Badge variant="outline" className="text-[10px]">{log.mode}</Badge>
                        </div>
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString()}
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-6 md:gap-8">
                        <div className="text-center">
                          <p className="text-[9px] text-muted-foreground uppercase font-mono">Rows / Stable</p>
                          <p className="text-sm font-bold">{log.rowsProcessed} / {log.stableRows}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-[9px] text-muted-foreground uppercase font-mono">Top Driver</p>
                          <p className="text-sm font-bold">{log.topDriver}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-[9px] text-muted-foreground uppercase font-mono">Score</p>
                          <p className="text-sm font-bold">{log.tantriumScore}</p>
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-1">
                        <code className="text-[10px] text-muted-foreground font-mono bg-muted/50 px-1.5 py-0.5 rounded">
                          {log.evidenceHash.substring(0, 12)}...
                        </code>
                        <Button variant="ghost" size="sm" className="h-6 text-[10px]" asChild>
                          <Link href="/hunt">View in Hunt</Link>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
