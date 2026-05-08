import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DATASET_REGISTRY } from "@/lib/dataset-registry";
import { Link } from "wouter";
import { ExternalLink, Play, Database, AlertCircle, CheckCircle2 } from "lucide-react";

export function DatasetsPage() {
  const sectors = Array.from(new Set(DATASET_REGISTRY.map((d) => d.sector)));

  return (
    <div className="container mx-auto px-4 py-12 max-w-6xl flex flex-col gap-12">
      <div className="flex flex-col gap-4 max-w-3xl">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tighter">Real Problem Dataset Registry</h1>
          <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20 font-mono">
            LIVE DATA MODE
          </Badge>
        </div>
        <p className="text-muted-foreground text-lg">
          These are real public datasets. Tantrium will compute genuine boundary estimates from them — not synthetic outputs.
        </p>
      </div>

      <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-lg flex gap-3 text-amber-700 dark:text-amber-400">
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
        <p className="text-sm">
          <strong>Notice:</strong> Many public datasets have strict CORS policies. For those marked "Manual Upload Required", 
          you will need to download the CSV from the source and upload it manually in the Analyze workflow.
        </p>
      </div>

      <Tabs defaultValue={sectors[0]} className="w-full">
        <TabsList className="w-full justify-start overflow-x-auto bg-transparent border-b border-border rounded-none h-auto p-0 gap-8">
          {sectors.map((sector) => (
            <TabsTrigger
              key={sector}
              value={sector}
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-0 pb-4 font-mono text-sm"
              data-testid={`tab-sector-${sector.toLowerCase().replace(/\s+/g, "-")}`}
            >
              {sector}
            </TabsTrigger>
          ))}
        </TabsList>

        {sectors.map((sector) => (
          <TabsContent key={sector} value={sector} className="pt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {DATASET_REGISTRY.filter((d) => d.sector === sector).map((dataset) => (
                <Card key={dataset.id} className="flex flex-col h-full bg-card border-border hover:border-primary/50 transition-colors shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start mb-2">
                      <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wider">
                        {dataset.id}
                      </Badge>
                      {dataset.corsReliable ? (
                        <Badge variant="secondary" className="bg-green-500/10 text-green-600 border-green-500/20 flex gap-1 items-center">
                          <CheckCircle2 className="w-3 h-3" /> Auto-Fetch
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-amber-500/10 text-amber-600 border-amber-500/20 flex gap-1 items-center">
                          <Database className="w-3 h-3" /> Manual Upload
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-xl font-bold leading-tight">{dataset.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col gap-4">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold">Problem Statement:</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {dataset.problem}
                      </p>
                    </div>

                    {dataset.expectedColumns && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Expected Columns:</p>
                        <div className="flex flex-wrap gap-1">
                          {dataset.expectedColumns.map((col) => (
                            <Badge key={col} variant="secondary" className="text-[10px] font-mono px-1 py-0 h-4">
                              {col}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-auto pt-4 flex items-center justify-between border-t border-border/50">
                      {dataset.url ? (
                        <a 
                          href={dataset.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline flex items-center gap-1 font-mono"
                          data-testid={`link-source-${dataset.id}`}
                        >
                          Source Link <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-xs text-muted-foreground font-mono">Manual Source Only</span>
                      )}
                      
                      <Button asChild size="sm" className="font-mono" data-testid={`btn-analyze-${dataset.id}`}>
                        <Link href={`/analyze?dataset=${dataset.id}`}>
                          Analyze This <Play className="w-3 h-3 ml-2 fill-current" />
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
