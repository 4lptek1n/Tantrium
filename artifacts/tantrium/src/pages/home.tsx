import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { DATASET_REGISTRY } from "@/lib/dataset-registry";
import { 
  ArrowRight, ShieldCheck, AlertTriangle, Crosshair, Route, 
  Ban, Fingerprint, Tag 
} from "lucide-react";

export function Home() {
  const uniqueSectors = Array.from(new Set(DATASET_REGISTRY.map(d => d.sector))).sort();

  return (
    <div className="flex flex-col w-full">
      {/* HERO SECTION */}
      <section className="relative py-24 md:py-32 bg-background overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/15 via-background to-background" />
        
        <div className="container mx-auto px-4 relative z-10 max-w-6xl">
          <div className="flex flex-col gap-8">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="bg-primary/5 border-primary/20 text-[10px] uppercase tracking-wider">REAL DATA ONLY — No synthetic outputs</Badge>
              <Badge variant="outline" className="bg-primary/5 border-primary/20 text-[10px] uppercase tracking-wider">6 Industry Sectors</Badge>
              <Badge variant="outline" className="bg-primary/5 border-primary/20 text-[10px] uppercase tracking-wider">15 Problem Templates</Badge>
            </div>

            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight text-foreground leading-[0.9]">
              Give us one system <br />
              that keeps failing. <br />
              <span className="text-primary/80">We find the boundary where it breaks.</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground max-w-3xl leading-relaxed">
              Tantrium Boundary Engine converts operational data into four precise answers: the stable operating envelope, the exact break boundary, the first obstruction driving failure, and the path back to safety. No probability estimates. No guesswork.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button asChild size="lg" className="text-lg h-14 px-8 font-mono" data-testid="btn-hero-hunt">
                <Link href="/hunt">Start Problem Hunt →</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="text-lg h-14 px-8 font-mono" data-testid="btn-hero-reports">
                <Link href="/reports">View Live Reports</Link>
              </Button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-12 border-t border-border/50">
              <div className="space-y-1">
                <p className="text-3xl font-bold font-mono">15</p>
                <p className="text-xs text-muted-foreground uppercase tracking-widest">Problem Templates</p>
              </div>
              <div className="space-y-1">
                <p className="text-3xl font-bold font-mono">9</p>
                <p className="text-xs text-muted-foreground uppercase tracking-widest">Auto-Fetch Datasets</p>
              </div>
              <div className="space-y-1">
                <p className="text-3xl font-bold font-mono">$260K</p>
                <p className="text-xs text-muted-foreground uppercase tracking-widest">Avg. Hourly Downtime Cost</p>
              </div>
              <div className="space-y-1">
                <p className="text-3xl font-bold font-mono">6</p>
                <p className="text-xs text-muted-foreground uppercase tracking-widest">Industries Covered</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* WHAT WE DO */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="mb-16">
            <h2 className="text-4xl font-bold tracking-tight mb-4">Four answers. Every time.</h2>
            <p className="text-xl text-muted-foreground">Tantrium does not predict. It maps.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-border/50 bg-card/50">
              <CardHeader className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <CardTitle className="text-xl">Safe Operating Envelope</CardTitle>
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  The parameter ranges where your system runs without failure. Not an estimate — computed from your actual operational records.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardHeader className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <CardTitle className="text-xl">First Break Boundary</CardTitle>
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  The exact point where your system transitions from stable to unstable. The moment everything starts going wrong.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardHeader className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <Crosshair className="w-6 h-6" />
                </div>
                <CardTitle className="text-xl">First Obstruction</CardTitle>
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  The primary variable driving that boundary breach. The thing you actually need to control.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardHeader className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <Route className="w-6 h-6" />
                </div>
                <CardTitle className="text-xl">Closure Path</CardTitle>
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  A concrete sequence of operational changes to return from the unstable regime to the safe zone.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-24 bg-muted/30 border-y border-border/50">
        <div className="container mx-auto px-4 max-w-6xl">
          <h2 className="text-4xl font-bold tracking-tight mb-16 text-center">From broken data to boardroom-ready report.</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="space-y-4">
              <div className="text-5xl font-bold text-primary/20 font-mono">01</div>
              <h3 className="text-xl font-bold">Select a Problem Template</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Choose from 15 industry-specific problem templates across data centers, manufacturing, pharma, finance, energy, and logistics. Or upload your own dataset.
              </p>
            </div>

            <div className="space-y-4">
              <div className="text-5xl font-bold text-primary/20 font-mono">02</div>
              <h3 className="text-xl font-bold">Run Tantrium Analysis</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Our engine ingests your operational records, maps stable vs unstable populations, detects boundary transitions, scores failure drivers, and computes the stabilization path.
              </p>
            </div>

            <div className="space-y-4">
              <div className="text-5xl font-bold text-primary/20 font-mono">03</div>
              <h3 className="text-xl font-bold">Receive the Boundary Report</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                A certified, evidence-hashed report showing exactly where your system breaks, what drives the break, and how to prevent it. Shareable with your operations team.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTOR CARDS */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-4 max-w-6xl">
          <h2 className="text-4xl font-bold tracking-tight mb-12">Industry sectors</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {uniqueSectors.map((sector) => {
              const datasets = DATASET_REGISTRY.filter(d => d.sector === sector);
              const firstDataset = datasets[0];
              return (
                <Card key={sector} className="group hover:border-primary/50 transition-colors">
                  <CardHeader className="space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-primary">{sector}</span>
                      <Badge variant="secondary" className="text-[10px]">{datasets.length} problem templates</Badge>
                    </div>
                    <CardTitle className="text-xl">{sector}</CardTitle>
                    <CardDescription className="line-clamp-3 text-xs leading-relaxed">
                      {firstDataset?.problem.substring(0, 100)}...
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button asChild variant="ghost" className="w-full justify-between group-hover:bg-primary/5">
                      <Link href="/hunt">Explore <ArrowRight className="w-4 h-4" /></Link>
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* EVIDENCE SECTION */}
      <section className="py-24 bg-muted/20">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="max-w-3xl mb-16">
            <h2 className="text-4xl font-bold tracking-tight mb-4">Real data. Real output. Real evidence.</h2>
            <p className="text-muted-foreground">Every Tantrium analysis generates a cryptographic evidence hash — a fingerprint of the exact dataset, parameters, and results. No black boxes.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-full bg-background border flex items-center justify-center text-primary">
                <Ban className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold">No Synthetic Outputs</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Tantrium refuses to generate results from simulated or placeholder data. If your dataset has fewer than 10 valid rows, the engine returns a clear 'Insufficient Data' status.
              </p>
            </div>

            <div className="space-y-4">
              <div className="w-12 h-12 rounded-full bg-background border flex items-center justify-center text-primary">
                <Fingerprint className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold">Evidence Hash</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every certified analysis generates a SHA-256 fingerprint of the dataset + parameters + results. You can share this hash as proof of analysis.
              </p>
            </div>

            <div className="space-y-4">
              <div className="w-12 h-12 rounded-full bg-background border flex items-center justify-center text-primary">
                <Tag className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold">Labeled Modes</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every output is clearly labeled: REAL DATA (evidence-grade), DEMO (example only), or INSUFFICIENT DATA. You always know what you're looking at.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA BAND */}
      <section className="py-24 bg-card border-t border-border/50 text-center">
        <div className="container mx-auto px-4 max-w-3xl space-y-8">
          <h2 className="text-4xl font-bold tracking-tight">Ready to find your boundary?</h2>
          <p className="text-muted-foreground text-lg">Pick a problem. Upload your data. Get the report in minutes — or request a certified analyst-grade Boundary Report.</p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Button asChild size="lg" className="h-14 px-8 font-mono">
              <Link href="/hunt">Launch Problem Hunt →</Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="h-14 px-8 font-mono">
              <Link href="/pricing">Request Analyst Report</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function Badge({ children, variant = "default", className = "" }: { children: React.ReactNode, variant?: "default" | "outline" | "secondary", className?: string }) {
  const variants = {
    default: "bg-primary text-primary-foreground",
    outline: "border border-border",
    secondary: "bg-secondary text-secondary-foreground"
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}

