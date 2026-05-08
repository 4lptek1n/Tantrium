import { useState, useEffect, useRef, useMemo } from "react";
import { Link } from "wouter";
import { 
  Database, ShieldCheck, AlertTriangle, Crosshair, Route, Fingerprint, 
  Search, CheckCircle2, Circle, Loader2, ExternalLink, Upload, 
  ArrowRight, Copy, ChevronRight, Activity 
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell 
} from "recharts";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { 
  Table, TableHeader, TableRow, TableHead, TableBody, TableCell 
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useToast } from "@/hooks/use-toast";

import { runTantriumWorkflow, parseCSV } from "@/lib/analysis-engine";
import type { TantriumObject, DriverResult, SafeEnvelopeRange, ClosureRecommendation } from "@/lib/analysis-engine";
import { DATASET_REGISTRY } from "@/lib/dataset-registry";
import { SECTOR_PROSPECTS } from "@/lib/prospect-mode";
import { addEvidenceEntry, getEvidenceLog, clearEvidenceLog } from "@/lib/evidence-log";

// ─── Sub-Components ─────────────────────────────────────────────────────────

function RangeBar({ safeMin, safeMax, observedMin, observedMax }: { 
  safeMin: number, safeMax: number, observedMin: number, observedMax: number 
}) {
  const range = observedMax - observedMin;
  if (range === 0) return <div className="relative h-3 bg-muted rounded-full" />;
  
  const leftPct = ((safeMin - observedMin) / range) * 100;
  const widthPct = ((safeMax - safeMin) / range) * 100;
  
  return (
    <div className="relative h-3 bg-muted rounded-full overflow-hidden">
      <div 
        className="absolute h-3 bg-primary/30 rounded-full" 
        style={{ left: `${Math.max(0, leftPct)}%`, width: `${Math.min(100, widthPct)}%` }} 
      />
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export function HuntPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("hunt");
  const [evidenceLog, setEvidenceLog] = useState(() => getEvidenceLog());
  
  // Problem Hunt State
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSector, setSelectedSector] = useState("All");
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  
  // Workflow State
  const [workflowStep, setWorkflowStep] = useState(1);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [loadedData, setLoadedData] = useState<Record<string, any>[] | null>(null);
  
  // Configuration State
  const [targetMetric, setTargetMetric] = useState("");
  const [failureThreshold, setFailureThreshold] = useState<number>(0);
  const [failureDirection, setFailureDirection] = useState<"above" | "below">("above");
  
  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<TantriumObject | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Stats for Header
  const autoFetchCount = DATASET_REGISTRY.filter(d => d.difficulty === "auto-fetch").length;
  const manualUploadCount = DATASET_REGISTRY.filter(d => d.difficulty === "manual-upload").length;
  
  const sectors = useMemo(() => {
    const s = new Set(DATASET_REGISTRY.map(d => d.sector));
    return ["All", ...Array.from(s)];
  }, []);

  const filteredProblems = DATASET_REGISTRY.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = selectedSector === "All" || p.sector === selectedSector;
    return matchesSearch && matchesSector;
  });

  const selectedProblem = DATASET_REGISTRY.find(p => p.id === selectedProblemId);

  useEffect(() => {
    if (selectedProblem) {
      setWorkflowStep(1);
      setLoadedData(null);
      setFetchError(null);
      setAnalysisResult(null);
      setTargetMetric(selectedProblem.suggestedTargetCol || "");
      setFailureThreshold(selectedProblem.suggestedThreshold || 0);
      setFailureDirection(selectedProblem.suggestedDirection || "above");
    }
  }, [selectedProblemId]);

  const handleFetchDataset = async () => {
    if (!selectedProblem?.url) return;
    setIsFetching(true);
    setFetchError(null);
    try {
      const response = await fetch(selectedProblem.url);
      if (!response.ok) throw new Error("Network response was not ok");
      const text = await response.text();
      const parsed = parseCSV(text);
      setLoadedData(parsed.data as Record<string, any>[]);
      toast({ title: "Dataset Loaded", description: `${parsed.data.length} rows detected.` });
    } catch (err) {
      setFetchError("Auto-fetch failed. The data source has blocked direct browser access (CORS restriction). Download the file manually from the source link and upload below.");
    } finally {
      setIsFetching(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const parsed = parseCSV(text);
    setLoadedData(parsed.data as Record<string, any>[]);
    toast({ title: "Dataset Loaded", description: `${parsed.data.length} rows detected.` });
  };

  const handleRunAnalysis = async () => {
    if (!loadedData || !selectedProblem) return;
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setWorkflowStep(3);

    const steps = 6;
    const interval = setInterval(() => {
      setAnalysisProgress(prev => Math.min(prev + 1, steps - 1));
    }, 400);

    try {
      const result = await runTantriumWorkflow(
        loadedData,
        targetMetric,
        failureThreshold,
        failureDirection,
        selectedProblem.name,
        selectedProblem.url || "manual-upload",
        selectedProblem.sector
      );
      
      clearInterval(interval);
      setAnalysisProgress(steps);
      setAnalysisResult(result);
      setWorkflowStep(4);
    } catch (err) {
      clearInterval(interval);
      setIsAnalyzing(false);
      toast({ title: "Analysis Failed", description: "An error occurred during processing.", variant: "destructive" });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLogAnalysis = () => {
    if (analysisResult) {
      addEvidenceEntry(analysisResult);
      setEvidenceLog(getEvidenceLog());
      toast({ title: "Success", description: "Analysis logged to Evidence Log." });
    }
  };

  const handleClearLog = () => {
    if (confirm("Are you sure? This cannot be undone.")) {
      clearEvidenceLog();
      setEvidenceLog([]);
      toast({ title: "Log Cleared" });
    }
  };

  const formatNum = (n: number) => n % 1 === 0 ? n.toFixed(0) : n.toFixed(2);

  const [showOnboarding, setShowOnboarding] = useState(true);

  return (
    <div className="flex-1 w-full max-w-screen-xl mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Master Problem Hunt</h1>
          <p className="text-muted-foreground">Find the boundary. Process real data. Generate evidence.</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-200">
            Auto-Fetch Ready: {autoFetchCount}
          </Badge>
          <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-200">
            Analyses in Log: {evidenceLog.length}
          </Badge>
          <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-200">
            Manual Upload Required: {manualUploadCount}
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="hunt">Problem Hunt</TabsTrigger>
          <TabsTrigger value="log">Evidence Log</TabsTrigger>
          <TabsTrigger value="prospect">Prospect Mode</TabsTrigger>
        </TabsList>

        {/* ─── TAB 1: PROBLEM HUNT ────────────────────────────────────────── */}
        <TabsContent value="hunt" className="space-y-8">
          {showOnboarding && (
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                      <Activity className="w-4 h-4" />
                    </div>
                    <CardTitle className="text-lg">How to use Problem Hunt</CardTitle>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setShowOnboarding(false)} className="h-8 px-2 text-xs">Dismiss</Button>
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="space-y-1">
                    <p className="text-xs font-bold uppercase tracking-wider text-primary">Step 1: Pick a problem</p>
                    <p className="text-xs text-muted-foreground">Choose an industry problem from the list on the left. Look for green AUTO-FETCH badges — these run immediately.</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold uppercase tracking-wider text-primary">Step 2: Load the data</p>
                    <p className="text-xs text-muted-foreground">Click 'Fetch Dataset' to automatically load real operational data. The system detects the columns for you.</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold uppercase tracking-wider text-primary">Step 3: Get your report</p>
                    <p className="text-xs text-muted-foreground">Click 'Run Tantrium Analysis' and the engine maps the failure boundary in real-time.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid lg:grid-cols-12 gap-8 items-start">
            {/* LEFT PANEL */}
            <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24 max-h-[80vh] overflow-y-auto pr-2">
              <div className="space-y-4">
                <div className="text-[10px] font-mono font-bold text-muted-foreground uppercase tracking-wider">
                  Select a Problem
                </div>
                <Input 
                  placeholder="Search problems..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  data-testid="input-problem-search"
                />
                <div className="flex flex-wrap gap-2">
                  {sectors.map(sector => (
                    <Button 
                      key={sector}
                      variant={selectedSector === sector ? "default" : "outline"}
                      size="sm"
                      className="text-[10px] h-7 px-2"
                      onClick={() => setSelectedSector(sector)}
                    >
                      {sector}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {filteredProblems.map(problem => (
                  <Card 
                    key={problem.id}
                    className={`cursor-pointer transition-all hover:border-primary/50 ${selectedProblemId === problem.id ? "border-primary bg-primary/5" : "border-border"}`}
                    onClick={() => setSelectedProblemId(problem.id)}
                  >
                    <CardContent className="p-4 space-y-2">
                      <div className="flex justify-between items-start gap-2">
                        <Badge variant="secondary" className="text-[9px] h-4 px-1 uppercase">{problem.sector.split(' ')[0]}</Badge>
                        <Badge 
                          variant="outline" 
                          className={`text-[9px] h-4 px-1 uppercase ${
                            problem.difficulty === 'auto-fetch' ? 'border-green-200 text-green-600' : 
                            problem.difficulty === 'manual-upload' ? 'border-amber-200 text-amber-600' : 'border-gray-200 text-gray-600'
                          }`}
                        >
                          {problem.difficulty === 'auto-fetch' ? 'Auto-Fetch' : problem.difficulty === 'manual-upload' ? 'Manual' : 'Demo'}
                        </Badge>
                      </div>
                      <h3 className="font-semibold text-sm leading-tight">{problem.name}</h3>
                      <p className="text-[10px] text-muted-foreground line-clamp-2">
                        {problem.financialImpact.split('.')[0]}.
                      </p>
                      <Button variant="outline" size="sm" className="w-full h-7 text-[10px]">Select</Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* RIGHT PANEL */}
            <div className="lg:col-span-8 space-y-8">
              {!selectedProblem ? (
                <div className="flex flex-col items-center justify-center py-32 text-center space-y-4 border-2 border-dashed rounded-xl border-muted">
                  <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center">
                    <Crosshair className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold">Ready to Begin?</h3>
                    <p className="text-muted-foreground max-w-sm mx-auto">Select a problem template from the left to start the Tantrium workflow.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  {/* STEP 1: PROBLEM BRIEF */}
                  <Card className={workflowStep >= 1 ? "border-primary/20" : "opacity-50"}>
                    <CardHeader className="pb-4">
                      <div className="flex justify-between items-start">
                        <div className="space-y-1">
                          <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Step 1 of 4</div>
                          <CardTitle className="text-2xl">Problem Brief</CardTitle>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="secondary">{selectedProblem.sector}</Badge>
                          <Badge variant="outline" className="capitalize">{selectedProblem.difficulty.replace('-', ' ')}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="space-y-2">
                        <h2 className="text-xl font-bold">{selectedProblem.name}</h2>
                        <p className="text-sm text-muted-foreground">{selectedProblem.problem}</p>
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <h4 className="text-sm font-bold flex items-center gap-2"><Activity className="w-4 h-4 text-primary" /> Financial Impact</h4>
                          <p className="text-xs text-muted-foreground">{selectedProblem.financialImpact}</p>
                        </div>
                        <div className="space-y-2">
                          <h4 className="text-sm font-bold flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-primary" /> What Tantrium Delivers</h4>
                          <p className="text-xs text-muted-foreground">{selectedProblem.tantriumOutput}</p>
                        </div>
                      </div>

                      {selectedProblem.sourceLink && (
                        <a href={selectedProblem.sourceLink} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                          View Data Source <ExternalLink className="w-3 h-3" />
                        </a>
                      )}

                      <Separator />

                      <div className="bg-muted/30 p-4 rounded-lg space-y-4">
                        {selectedProblem.difficulty === "auto-fetch" && !loadedData && (
                          <div className="space-y-4">
                            <p className="text-sm">No data science knowledge required — the engine handles everything automatically.</p>
                            <p className="text-sm text-muted-foreground">This dataset can be fetched automatically from our verified source.</p>
                            <Button 
                              onClick={handleFetchDataset} 
                              disabled={isFetching}
                              className="w-full md:w-auto"
                              data-testid="btn-fetch-dataset"
                            >
                              {isFetching ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Fetching...</> : "Fetch Dataset"}
                            </Button>
                            {fetchError && (
                              <Alert variant="destructive">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertTitle>Fetch Error</AlertTitle>
                                <AlertDescription className="text-xs">
                                  {fetchError}
                                </AlertDescription>
                              </Alert>
                            )}
                          </div>
                        )}

                        {(selectedProblem.difficulty === "manual-upload" || fetchError) && !loadedData && (
                          <div className="space-y-4">
                            <p className="text-sm">{selectedProblem.manualNote}</p>
                            <div 
                              className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
                              onClick={() => fileInputRef.current?.click()}
                            >
                              <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                              <p className="text-sm font-medium">Click to upload CSV</p>
                              <p className="text-xs text-muted-foreground">or drop your file here</p>
                              <input 
                                type="file" 
                                ref={fileInputRef} 
                                className="hidden" 
                                accept=".csv" 
                                onChange={handleFileUpload} 
                              />
                            </div>
                          </div>
                        )}

                        {loadedData && (
                          <div className="space-y-4">
                            <Alert className="bg-green-500/10 border-green-200">
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                              <AlertTitle className="text-green-800">Dataset Loaded</AlertTitle>
                              <AlertDescription className="text-xs text-green-700">
                                {loadedData.length} rows, {Object.keys(loadedData[0] || {}).length} columns detected.
                              </AlertDescription>
                            </Alert>
                            <Button 
                              onClick={() => setWorkflowStep(2)}
                              className="w-full md:w-auto"
                            >
                              Proceed to Configuration <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* STEP 2: CONFIGURE ANALYSIS */}
                  {workflowStep >= 2 && loadedData && (
                    <Card className={workflowStep >= 2 ? "border-primary/20" : "opacity-50"}>
                      <CardHeader>
                        <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Step 2 of 4</div>
                        <CardTitle className="text-2xl">Configure Analysis</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        <div className="space-y-3">
                          <Label className="text-xs font-mono uppercase text-muted-foreground">Data Preview (First 5 Rows)</Label>
                          <div className="border rounded-md overflow-x-auto">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  {Object.keys(loadedData[0] || {}).slice(0, 8).map(col => (
                                    <TableHead key={col} className="text-[10px] font-mono whitespace-nowrap">{col}</TableHead>
                                  ))}
                                  {Object.keys(loadedData[0] || {}).length > 8 && <TableHead className="text-[10px] font-mono">...</TableHead>}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {loadedData.slice(0, 5).map((row, i) => (
                                  <TableRow key={i}>
                                    {Object.keys(row).slice(0, 8).map(col => (
                                      <TableCell key={col} className="text-[10px] font-mono py-1">{String(row[col])}</TableCell>
                                    ))}
                                    {Object.keys(row).length > 8 && <TableCell className="text-[10px] font-mono py-1">...</TableCell>}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-8">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label>Target Metric</Label>
                              <p className="text-[10px] text-muted-foreground">This is the number you want to protect (e.g., temperature, charges, quality score). Click the correct column name.</p>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {Object.keys(loadedData[0] || {}).filter(k => typeof loadedData[0][k] === 'number').map(col => (
                                  <Badge 
                                    key={col} 
                                    variant={targetMetric === col ? "default" : "outline"}
                                    className="cursor-pointer text-[10px]"
                                    onClick={() => setTargetMetric(col)}
                                  >
                                    {col}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <Label>Failure Threshold</Label>
                              <p className="text-[10px] text-muted-foreground">At what value does this number become a problem? (Already pre-filled based on the dataset type.)</p>
                              <Input 
                                type="number" 
                                value={failureThreshold} 
                                onChange={(e) => setFailureThreshold(Number(e.target.value))} 
                              />
                            </div>
                          </div>

                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label>Boundary Direction</Label>
                              <p className="text-[10px] text-muted-foreground">Should the number be below this threshold to be OK, or above it?</p>
                              <RadioGroup 
                                value={failureDirection} 
                                onValueChange={(v: "above" | "below") => setFailureDirection(v)}
                                className="flex flex-col gap-2 mt-2"
                              >
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="above" id="above" />
                                  <Label htmlFor="above" className="text-sm font-normal">Above threshold = failure</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="below" id="below" />
                                  <Label htmlFor="below" className="text-sm font-normal">Below threshold = failure</Label>
                                </div>
                              </RadioGroup>
                            </div>
                          </div>
                        </div>

                        <Button 
                          onClick={handleRunAnalysis} 
                          disabled={!targetMetric || isAnalyzing}
                          className="w-full h-12 text-base font-bold"
                          data-testid="btn-run-analysis"
                        >
                          {isAnalyzing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Running Tantrium Analysis...</> : "Run Tantrium Analysis →"}
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  {/* STEP 3: ANALYSIS IN PROGRESS */}
                  {workflowStep === 3 && (
                    <Card className="border-primary">
                      <CardHeader>
                        <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Step 3 of 4</div>
                        <CardTitle className="text-2xl">Analysis in Progress</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        <div className="space-y-4">
                          {[
                            { id: 0, label: "DATA_INGEST", text: "Ingesting dataset rows and validating structure..." },
                            { id: 1, label: "STABLE_REGION", text: "Mapping stable vs unstable operating populations..." },
                            { id: 2, label: "BREAK_BOUNDARY", text: "Detecting stable-to-unstable transition points..." },
                            { id: 3, label: "FIRST_OBSTRUCTION", text: "Scoring and ranking failure drivers by boundary pressure..." },
                            { id: 4, label: "CLOSURE_PATH", text: "Computing operational path back to safe envelope..." },
                            { id: 5, label: "EVIDENCE_HASH", text: "Generating evidence fingerprint..." },
                          ].map((step, idx) => (
                            <div key={step.label} className="flex items-center gap-4">
                              <div className="flex-shrink-0">
                                {analysisProgress > idx ? (
                                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                                ) : analysisProgress === idx ? (
                                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                                ) : (
                                  <Circle className="w-5 h-5 text-muted" />
                                )}
                              </div>
                              <div className="space-y-0.5">
                                <div className="text-[10px] font-mono font-bold text-primary">{step.label}</div>
                                <div className="text-sm text-muted-foreground">{step.text}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                        <Progress value={(analysisProgress / 6) * 100} className="h-2" />
                        <p className="text-xs text-muted-foreground text-center">Sit tight — Tantrium is reading every row of your data and computing where things go wrong. This usually takes a few seconds.</p>
                      </CardContent>
                    </Card>
                  )}

                  {/* STEP 4: BOUNDARY REPORT */}
                  {workflowStep === 4 && analysisResult && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                      {/* Mode Banner */}
                      {analysisResult.mode === "INSUFFICIENT DATA" ? (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>Insufficient Data</AlertTitle>
                          <AlertDescription>
                            Insufficient data. Only {analysisResult.ingest.validRowCount} valid rows found. Tantrium requires at least 10 rows with a numeric target metric. Adjust your threshold or upload a different dataset.
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <Alert className="bg-green-500/10 border-green-200">
                          <Fingerprint className="h-4 w-4 text-green-600" />
                          <AlertTitle className="text-green-800">REAL DATA MODE — Evidence-grade analysis computed</AlertTitle>
                          <AlertDescription className="text-xs text-green-700 font-mono">
                            {analysisResult.ingest.validRowCount} rows of operational data. Hash: {analysisResult.evidenceHash}
                          </AlertDescription>
                        </Alert>
                      )}

                      {analysisResult.certified && (
                        <>
                          {/* Panel A: Data Summary */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card className="p-4 space-y-1">
                              <div className="text-[10px] font-mono text-muted-foreground uppercase">Total Rows</div>
                              <div className="text-xl font-bold">{analysisResult.ingest.validRowCount}</div>
                            </Card>
                            <Card className="p-4 space-y-1">
                              <div className="text-[10px] font-mono text-muted-foreground uppercase">Stable</div>
                              <div className="text-xl font-bold">{analysisResult.stableRegion.stableRowCount} <span className="text-[10px] font-normal text-muted-foreground">({analysisResult.stableRegion.stablePercent}%)</span></div>
                            </Card>
                            <Card className="p-4 space-y-1">
                              <div className="text-[10px] font-mono text-muted-foreground uppercase">Unstable</div>
                              <div className="text-xl font-bold">{analysisResult.stableRegion.unstableRowCount} <span className="text-[10px] font-normal text-muted-foreground">({100 - analysisResult.stableRegion.stablePercent}%)</span></div>
                            </Card>
                            <Card className="p-4 space-y-1">
                              <div className="text-[10px] font-mono text-muted-foreground uppercase">Columns</div>
                              <div className="text-xl font-bold">{analysisResult.ingest.summary.colCount}</div>
                            </Card>
                          </div>

                          {/* Panel B: First Obstruction */}
                          {analysisResult.firstObstruction && (
                            <Card className="border-amber-500/50 shadow-md">
                              <CardHeader className="pb-2">
                                <div className="flex justify-between items-center">
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline" className="font-mono bg-amber-500/10 text-amber-600 border-amber-200">FIRST_OBSTRUCTION</Badge>
                                    <h3 className="text-lg font-bold">First Obstruction Identified</h3>
                                  </div>
                                  <Badge className="text-lg py-1 px-3 bg-amber-500">{analysisResult.firstObstruction.driver.tantriumScore}/100</Badge>
                                </div>
                              </CardHeader>
                              <CardContent className="space-y-6">
                                <div className="space-y-2">
                                  <div className="text-2xl font-black text-amber-600 uppercase tracking-tight">{analysisResult.firstObstruction.driver.name}</div>
                                  <p className="text-sm text-muted-foreground leading-relaxed italic">
                                    "{analysisResult.firstObstruction.obstructionStatement}"
                                  </p>
                                </div>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] font-bold uppercase"><span>Correlation Strength</span><span>{analysisResult.firstObstruction.driver.correlationStrength}%</span></div>
                                    <Progress value={analysisResult.firstObstruction.driver.correlationStrength} className="h-1.5" />
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] font-bold uppercase"><span>Crossing Strength</span><span>{analysisResult.firstObstruction.driver.crossingStrength}%</span></div>
                                    <Progress value={analysisResult.firstObstruction.driver.crossingStrength} className="h-1.5" />
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] font-bold uppercase"><span>Boundary Proximity</span><span>{analysisResult.firstObstruction.driver.boundaryProximity}%</span></div>
                                    <Progress value={analysisResult.firstObstruction.driver.boundaryProximity} className="h-1.5" />
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] font-bold uppercase"><span>Monotonic Score</span><span>{analysisResult.firstObstruction.driver.monotonicScore}%</span></div>
                                    <Progress value={analysisResult.firstObstruction.driver.monotonicScore} className="h-1.5" />
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* Panel C: Break Boundary */}
                          <Card>
                            <CardHeader className="pb-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="font-mono bg-primary/10 text-primary border-primary/20">BREAK_BOUNDARY</Badge>
                                <h3 className="text-lg font-bold">First Break Boundary</h3>
                              </div>
                            </CardHeader>
                            <CardContent>
                              {analysisResult.breakBoundary ? (
                                <div className="space-y-2">
                                  <p className="text-sm font-medium">
                                    Boundary breach detected when <span className="font-bold text-primary">{analysisResult.breakBoundary.driverName}</span> reaches <span className="font-bold text-primary">{formatNum(analysisResult.breakBoundary.boundaryValue)}</span>.
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {analysisResult.failureDirection === 'above' ? 'Above' : 'Below'} this level, the system transitions into the unstable operating regime.
                                  </p>
                                  <div className="flex items-center gap-4 pt-2">
                                    <div className="flex items-center gap-1.5">
                                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                                      <span className="text-xs font-semibold">{Math.round(analysisResult.breakBoundary.confidence * 100)}% Confidence</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                      <Activity className="w-4 h-4 text-blue-500" />
                                      <span className="text-xs font-semibold">{analysisResult.breakBoundary.transitionCount} Transition(s)</span>
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground">
                                  No clear transition detected with the current threshold. Try adjusting the failure threshold or using a different target metric.
                                </p>
                              )}
                            </CardContent>
                          </Card>

                          {/* Panel D: All Drivers Chart */}
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">Tantrium Pressure Index — All Drivers</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-8">
                              <div className="h-[300px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                  <BarChart 
                                    layout="vertical" 
                                    data={analysisResult.allDrivers.slice(0, 8).map(d => ({ name: d.name, score: d.tantriumScore }))}
                                    margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                                  >
                                    <XAxis type="number" domain={[0, 100]} hide />
                                    <YAxis 
                                      type="category" 
                                      dataKey="name" 
                                      width={100} 
                                      axisLine={false} 
                                      tickLine={false} 
                                      tick={{ fontSize: 10, fontWeight: 'bold' }} 
                                    />
                                    <Tooltip 
                                      cursor={{ fill: 'hsl(var(--muted)/0.3)' }}
                                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                    />
                                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                                      {analysisResult.allDrivers.slice(0, 8).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index === 0 ? "hsl(var(--primary))" : "hsl(var(--primary)/0.6)"} />
                                      ))}
                                    </Bar>
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                              
                              <div className="space-y-3">
                                {analysisResult.allDrivers.slice(0, 3).map((driver, i) => (
                                  <div key={driver.name} className="p-3 border rounded-lg space-y-2 bg-muted/20">
                                    <div className="flex items-center gap-2">
                                      <div className="w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-bold flex items-center justify-center">{i+1}</div>
                                      <div className="font-bold text-sm uppercase">{driver.name}</div>
                                      <Badge variant="outline" className="text-[10px] ml-auto">{driver.tantriumScore}/100</Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground leading-relaxed">{driver.explanation}</p>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>

                          {/* Panel E: Safe Operating Envelope */}
                          <Card>
                            <CardHeader className="pb-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="font-mono bg-green-500/10 text-green-600 border-green-200">STABLE_REGION</Badge>
                                <h3 className="text-lg font-bold">Safe Operating Envelope</h3>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-6">
                              {analysisResult.stableRegion.envelope.slice(0, 3).map((env) => (
                                <div key={env.column} className="space-y-2">
                                  <div className="flex justify-between items-end">
                                    <div className="font-mono text-[10px] font-bold uppercase">{env.column}</div>
                                    <div className="text-[10px] text-muted-foreground">Coverage: <span className="font-bold text-foreground">{env.coveragePercent}%</span></div>
                                  </div>
                                  <RangeBar 
                                    safeMin={env.safeMin} 
                                    safeMax={env.safeMax} 
                                    observedMin={env.observedMin} 
                                    observedMax={env.observedMax} 
                                  />
                                  <div className="flex justify-between text-[9px] font-mono text-muted-foreground">
                                    <span>Safe zone: {formatNum(env.safeMin)} – {formatNum(env.safeMax)}</span>
                                    <span>Observed: {formatNum(env.observedMin)} – {formatNum(env.observedMax)}</span>
                                  </div>
                                </div>
                              ))}
                            </CardContent>
                          </Card>

                          {/* Panel F: Closure Path */}
                          <Card>
                            <CardHeader className="pb-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="font-mono bg-primary/10 text-primary border-primary/20">CLOSURE_PATH</Badge>
                                <h3 className="text-lg font-bold">Recommended Stabilization Path</h3>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              {analysisResult.closurePath.map((rec, i) => (
                                <div key={rec.driverName} className="flex gap-4 p-4 border rounded-lg items-start">
                                  <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center shrink-0">{i+1}</div>
                                  <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                      <div className="text-sm font-bold uppercase">{rec.driverName}</div>
                                      <Badge 
                                        className={rec.direction === 'reduce' ? 'bg-destructive/10 text-destructive' : 'bg-green-500/10 text-green-600'}
                                        variant="outline"
                                      >
                                        {rec.direction.toUpperCase()}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">{rec.businessAction}</p>
                                  </div>
                                </div>
                              ))}
                            </CardContent>
                          </Card>

                          {/* Panel G: Executive Summary */}
                          <Card className="bg-primary/5 border-primary/20">
                            <CardHeader>
                              <CardTitle className="text-lg">Executive Summary</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm leading-relaxed text-muted-foreground">
                                Analysis of {analysisResult.ingest.validRowCount} operational records from {analysisResult.datasetName} identifies {analysisResult.stableRegion.unstableRowCount} observations ({100 - analysisResult.stableRegion.stablePercent}%) operating outside the safe regime. 
                                The primary failure driver is {analysisResult.firstObstruction?.driver.name} (Tantrium Boundary Pressure: {analysisResult.firstObstruction?.driver.tantriumScore}/100). 
                                {analysisResult.breakBoundary && `The first boundary breach is detected when ${analysisResult.breakBoundary.driverName} reaches ${formatNum(analysisResult.breakBoundary.boundaryValue)}.`} 
                                The safe operating envelope requires {analysisResult.stableRegion.envelope[0]?.column} to remain within {formatNum(analysisResult.stableRegion.envelope[0]?.safeMin || 0)} – {formatNum(analysisResult.stableRegion.envelope[0]?.safeMax || 0)}. 
                                {analysisResult.closurePath[0]?.businessAction} 
                                <span className="block mt-4 pt-4 border-t font-mono text-[10px]">Evidence Hash: {analysisResult.evidenceHash}</span>
                              </p>
                            </CardContent>
                          </Card>

                          {/* Action Buttons */}
                          <div className="flex flex-col md:flex-row gap-4 pt-4">
                            <Button onClick={handleLogAnalysis} className="flex-1 h-12 font-bold gap-2">
                              <Fingerprint className="w-4 h-4" /> Log This Analysis
                            </Button>
                            <Button asChild variant="outline" className="flex-1 h-12 font-bold gap-2">
                              <Link href="/reports">View in Reports →</Link>
                            </Button>
                            <Button 
                              variant="outline" 
                              onClick={() => {
                                setWorkflowStep(1);
                                setSelectedProblemId(null);
                                setLoadedData(null);
                                setAnalysisResult(null);
                                window.scrollTo({ top: 0, behavior: 'smooth' });
                              }} 
                              className="flex-1 h-12 font-bold"
                            >
                              Reset / New Problem
                            </Button>
                          </div>
                          
                          <div className="bg-muted p-6 rounded-xl text-center space-y-4">
                            <div className="text-sm font-medium">Ready to run this on your production data?</div>
                            <Button asChild size="lg" className="font-bold bg-primary hover:bg-primary/90">
                              <Link href="/pricing">Request a Boundary Report →</Link>
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* ─── TAB 2: EVIDENCE LOG ────────────────────────────────────────── */}
        <TabsContent value="log" className="space-y-6">
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-2xl font-bold">Analysis Evidence Log</h2>
              <p className="text-sm text-muted-foreground">Historical record of all computed boundary analyses.</p>
            </div>
            {evidenceLog.length > 0 && (
              <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive hover:bg-destructive/10" onClick={handleClearLog}>
                Clear Log
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {evidenceLog.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center">
                    <Database className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">No analyses logged yet</h3>
                    <p className="text-sm text-muted-foreground max-w-sm mx-auto">Complete a real-data analysis on the Problem Hunt tab to generate your first evidence entry.</p>
                  </div>
                  <Button onClick={() => setActiveTab("hunt")}>Start Analysis</Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-[10px] font-bold uppercase">Timestamp</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Dataset</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Mode</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Rows</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Stable %</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Top Driver</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Score</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase">Hash</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {evidenceLog.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="text-[10px] font-mono whitespace-nowrap">
                          {new Date(entry.timestamp).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </TableCell>
                        <TableCell className="text-[11px] font-bold">{entry.datasetName}</TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className={`text-[9px] h-4 px-1 ${
                              entry.mode === 'REAL DATA' ? 'bg-green-500/10 text-green-600 border-green-200' : 
                              entry.mode === 'INSUFFICIENT DATA' ? 'bg-destructive/10 text-destructive border-destructive/20' : 
                              'bg-gray-500/10 text-gray-600 border-gray-200'
                            }`}
                          >
                            {entry.mode}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs font-mono">{entry.rowsProcessed}</TableCell>
                        <TableCell className="text-xs font-mono">
                          {entry.rowsProcessed > 0 ? Math.round((entry.stableRows / entry.rowsProcessed) * 100) : 0}%
                        </TableCell>
                        <TableCell className="text-[10px] font-bold uppercase">{entry.topDriver}</TableCell>
                        <TableCell className="text-xs font-mono font-bold">{entry.tantriumScore}/100</TableCell>
                        <TableCell className="text-[10px] font-mono text-muted-foreground">{entry.evidenceHash.substring(0, 12)}...</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── TAB 3: PROSPECT MODE ────────────────────────────────────────── */}
        <TabsContent value="prospect" className="space-y-8">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">LinkedIn Prospect Intelligence</h2>
            <p className="text-muted-foreground">Each problem category maps to specific buyer personas. Select a sector to see who to approach and what to say.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {SECTOR_PROSPECTS.map(sp => (
              <Button 
                key={sp.sector}
                variant={selectedSector === sp.sector ? "default" : "outline"}
                size="sm"
                className="text-[10px] h-8 px-3"
                onClick={() => setSelectedSector(sp.sector)}
              >
                {sp.sector}
              </Button>
            ))}
          </div>

          <div className="space-y-12">
            {SECTOR_PROSPECTS.filter(sp => selectedSector === "All" || sp.sector === selectedSector).map(sp => (
              <div key={sp.sector} className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <h3 className="text-2xl font-bold border-b pb-4">{sp.sector}</h3>
                
                <div className="space-y-4">
                  <h4 className="text-sm font-mono font-bold text-muted-foreground uppercase tracking-wider">Buyer Personas</h4>
                  <div className="grid md:grid-cols-3 gap-6">
                    {sp.personas.map(persona => (
                      <Card key={persona.title} className="bg-card/50">
                        <CardHeader className="p-4 pb-2">
                          <CardTitle className="text-sm font-bold">{persona.title}</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0 space-y-4">
                          <p className="text-[11px] text-muted-foreground leading-relaxed">
                            <span className="font-bold text-foreground">Pain point:</span> {persona.typicalPainPoint}
                          </p>
                          <div className="bg-muted p-2 rounded text-[10px] font-mono flex items-start gap-2 border">
                            <Activity className="w-3 h-3 mt-0.5 text-blue-500 shrink-0" />
                            <span>{persona.linkedInSearchTip}</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-mono font-bold text-muted-foreground uppercase tracking-wider">Outreach Pitch</h4>
                  <Card className="border-l-4 border-l-primary relative">
                    <CardContent className="p-6">
                      <p className="text-sm leading-relaxed pr-12">
                        {sp.outreachPitch}
                      </p>
                      <Button 
                        size="icon" 
                        variant="ghost" 
                        className="absolute top-4 right-4 h-8 w-8"
                        onClick={() => {
                          navigator.clipboard.writeText(sp.outreachPitch);
                          toast({ title: "Copied", description: "Pitch copied to clipboard" });
                        }}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </CardContent>
                  </Card>
                </div>

                <div className="space-y-2 bg-primary/5 p-6 rounded-xl border border-primary/10">
                  <h4 className="text-sm font-mono font-bold text-muted-foreground uppercase tracking-wider">Closing Hook</h4>
                  <div className="text-xl font-bold text-primary tracking-tight">
                    "{sp.closingLine}"
                  </div>
                  <p className="text-xs text-muted-foreground">Use this as your opening hook when reaching out on LinkedIn.</p>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
