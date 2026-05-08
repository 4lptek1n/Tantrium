import { useState, useEffect } from "react";
import { Link } from "wouter";
import { motion, AnimatePresence } from "framer-motion";
import { SECTORS } from "@/lib/data";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ShieldCheck, AlertTriangle, ListFilter, Wrench, Download, ArrowRight, Loader2, Activity } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function Demo() {
  const { toast } = useToast();
  const [selectedSector, setSelectedSector] = useState(SECTORS[0].id);
  const [selectedDataset, setSelectedDataset] = useState(SECTORS[0].datasets[0].id);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const sector = SECTORS.find(s => s.id === selectedSector);
  const dataset = sector?.datasets.find(d => d.id === selectedDataset);

  // Reset dataset selection when sector changes
  useEffect(() => {
    if (sector) {
      setSelectedDataset(sector.datasets[0].id);
      setShowResults(false);
    }
  }, [sector]);

  const handleRunAnalysis = () => {
    setIsAnalyzing(true);
    setShowResults(false);
    
    // Synthetic delay to simulate analysis
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowResults(true);
    }, 2000);
  };

  const handleDownload = () => {
    toast({
      title: "Sample Report Downloaded",
      description: "A PDF of this sample boundary analysis has been saved.",
    });
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-6xl flex flex-col gap-12">
      <div className="flex flex-col gap-4 max-w-3xl">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tighter">Interactive Demo</h1>
        <p className="text-muted-foreground text-lg">
          Select a sector and a synthetic dataset to see what a Boundary Analysis Report looks like. The engine maps the exact operational thresholds where failure cascades begin.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Controls */}
        <div className="lg:col-span-4 flex flex-col gap-6 p-6 rounded-lg border border-border bg-card shadow-sm sticky top-24">
          <div className="space-y-2">
            <label className="text-sm font-medium font-mono text-muted-foreground">Select Sector</label>
            <Select value={selectedSector} onValueChange={setSelectedSector}>
              <SelectTrigger data-testid="select-sector">
                <SelectValue placeholder="Select a sector" />
              </SelectTrigger>
              <SelectContent>
                {SECTORS.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium font-mono text-muted-foreground">Select Synthetic Dataset</label>
            <Select value={selectedDataset} onValueChange={setSelectedDataset}>
              <SelectTrigger data-testid="select-dataset">
                <SelectValue placeholder="Select a dataset" />
              </SelectTrigger>
              <SelectContent>
                {sector?.datasets.map(d => (
                  <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button 
            className="w-full mt-4 font-mono font-bold" 
            size="lg"
            onClick={handleRunAnalysis}
            disabled={isAnalyzing}
            data-testid="btn-run-analysis"
          >
            {isAnalyzing ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing Boundary...</>
            ) : (
              "Run Analysis"
            )}
          </Button>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8 min-h-[600px] flex flex-col relative">
          <AnimatePresence mode="wait">
            {!showResults && !isAnalyzing && (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-center p-12 border border-dashed border-border rounded-lg bg-card/30"
              >
                <div className="w-16 h-16 rounded-full bg-background border border-border flex items-center justify-center text-muted-foreground mb-4">
                  <Activity className="w-8 h-8 opacity-50" />
                </div>
                <h3 className="text-xl font-medium text-muted-foreground">Ready to Analyze</h3>
                <p className="text-sm text-muted-foreground mt-2 max-w-sm">
                  Select your parameters and run the analysis to generate a boundary report.
                </p>
              </motion.div>
            )}

            {isAnalyzing && (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-center p-12 border border-border rounded-lg bg-card"
              >
                <Loader2 className="w-12 h-12 animate-spin text-primary mb-6" />
                <h3 className="text-xl font-mono font-bold text-foreground">Mapping Boundaries</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Scanning state metrics and identifying multi-variable failure thresholds...
                </p>
              </motion.div>
            )}

            {showResults && dataset && (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col gap-6"
                data-testid="results-panel"
              >
                <div className="flex items-center justify-between pb-4 border-b border-border">
                  <div>
                    <h2 className="text-2xl font-bold tracking-tight">Boundary Analysis Report</h2>
                    <p className="text-sm text-muted-foreground font-mono mt-1">{dataset.name}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleDownload} className="font-mono">
                    <Download className="w-4 h-4 mr-2" />
                    PDF
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Safe Envelope */}
                  <Card className="bg-card border-border shadow-sm">
                    <CardHeader className="pb-3 border-b border-border/50 bg-background/50">
                      <CardTitle className="flex items-center gap-2 text-base font-mono">
                        <ShieldCheck className="w-5 h-5 text-primary" />
                        Safe Operating Envelope
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <p className="text-sm leading-relaxed text-foreground">
                        {dataset.envelope}
                      </p>
                    </CardContent>
                  </Card>

                  {/* Failure Boundary */}
                  <Card className="bg-card border-destructive/20 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-destructive/5 rounded-bl-full -mr-8 -mt-8 pointer-events-none" />
                    <CardHeader className="pb-3 border-b border-destructive/10 bg-destructive/5">
                      <CardTitle className="flex items-center gap-2 text-base font-mono text-destructive">
                        <AlertTriangle className="w-5 h-5" />
                        First Failure Boundary
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 relative z-10">
                      <p className="text-sm leading-relaxed text-foreground font-medium">
                        {dataset.boundary}
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Drivers */}
                <Card className="bg-card border-border shadow-sm">
                  <CardHeader className="pb-3 border-b border-border/50">
                    <CardTitle className="flex items-center gap-2 text-base font-mono">
                      <ListFilter className="w-5 h-5 text-muted-foreground" />
                      Top 3 Failure Drivers
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-6">
                    {dataset.drivers.map((driver, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex justify-between items-end">
                          <div>
                            <span className="font-semibold text-sm">{driver.name}</span>
                            <p className="text-xs text-muted-foreground">{driver.explanation}</p>
                          </div>
                          <span className="text-xs font-mono font-bold text-accent">{driver.impact}% Impact</span>
                        </div>
                        <Progress value={driver.impact} className="h-2 [&>div]:bg-accent" />
                      </div>
                    ))}
                  </CardContent>
                </Card>

                {/* Stabilization Path */}
                <Card className="bg-card border-border shadow-sm">
                  <CardHeader className="pb-3 border-b border-border/50 bg-background/50">
                    <CardTitle className="flex items-center gap-2 text-base font-mono">
                      <Wrench className="w-5 h-5 text-muted-foreground" />
                      Stabilization Path
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ul className="space-y-3">
                      {dataset.path.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-3 text-sm">
                          <div className="w-5 h-5 rounded bg-muted flex items-center justify-center text-xs font-mono text-muted-foreground shrink-0 mt-0.5">
                            {idx + 1}
                          </div>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <div className="pt-8 border-t border-border flex justify-between items-center bg-card/50 p-6 rounded-lg">
                  <div>
                    <h4 className="font-bold">Ready to analyze your real system?</h4>
                    <p className="text-sm text-muted-foreground mt-1">Get precise boundaries for your own operational data.</p>
                  </div>
                  <Button asChild className="font-mono">
                    <Link href="/pricing">Request a Boundary Report <ArrowRight className="w-4 h-4 ml-2" /></Link>
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
