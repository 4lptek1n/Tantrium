import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SECTORS } from "@/lib/data";
import { ArrowRight, Activity, ShieldAlert, Cpu } from "lucide-react";

export function Home() {
  return (
    <div className="flex flex-col w-full">
      {/* Hero Section */}
      <section className="relative py-24 md:py-32 bg-background border-b border-border overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />
        
        <div className="container mx-auto px-4 relative z-10 max-w-5xl">
          <div className="flex flex-col gap-6 md:gap-8">
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter text-foreground max-w-4xl" data-testid="hero-headline">
              Give us one system that keeps failing. We find the boundary where it breaks.
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl">
              Precision boundary analysis for industrial and financial operators. We identify exactly when and why your most complex operations collapse, so you can build within the safe operating envelope.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button asChild size="lg" className="text-lg h-14 px-8 font-mono bg-primary text-primary-foreground hover:bg-primary/90" data-testid="btn-demo">
                <Link href="/demo">See a Live Demo</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="text-lg h-14 px-8 font-mono" data-testid="btn-pricing">
                <Link href="/pricing">Request a Boundary Report</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Sectors Section */}
      <section className="py-20 bg-background/50">
        <div className="container mx-auto px-4">
          <div className="mb-12 max-w-3xl">
            <h2 className="text-3xl font-bold tracking-tight mb-4">Sectors We Serve</h2>
            <p className="text-muted-foreground text-lg">
              We deploy boundary analysis across high-stakes industries where failure carries compounding costs.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {SECTORS.map((sector) => (
              <Card key={sector.id} className="bg-card/50 border-border/50 hover:border-primary/50 transition-colors">
                <CardHeader>
                  <CardTitle className="font-mono text-lg text-foreground">{sector.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{sector.tagline}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 bg-card border-t border-border">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center max-w-3xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">How Boundary Analysis Works</h2>
            <p className="text-muted-foreground text-lg">
              You do not need to understand our methodology. You just send the broken system. Tantrium finds the line.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="flex flex-col items-center text-center p-6 gap-4">
              <div className="w-16 h-16 rounded-full bg-background border border-border flex items-center justify-center text-primary shadow-sm">
                <Activity className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold font-mono">1. Submit the Case</h3>
              <p className="text-muted-foreground">
                You submit one failing case — operational data from a system that keeps breaking. We ingest the raw event logs, state metrics, and error traces.
              </p>
            </div>

            <div className="flex flex-col items-center text-center p-6 gap-4 relative">
              <div className="hidden md:block absolute top-14 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-border to-transparent -z-10" />
              <div className="w-16 h-16 rounded-full bg-background border border-border flex items-center justify-center text-primary shadow-sm">
                <Cpu className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold font-mono">2. Boundary Execution</h3>
              <p className="text-muted-foreground">
                Tantrium runs precision boundary analysis — identifying the exact safe operating envelope and mapping the multi-variable threshold where it collapses.
              </p>
            </div>

            <div className="flex flex-col items-center text-center p-6 gap-4 relative">
              <div className="hidden md:block absolute top-14 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-border to-transparent -z-10" />
              <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold font-mono">3. The Report</h3>
              <p className="text-muted-foreground">
                You receive the Boundary Report detailing the stable zone, the precise first failure boundary, the top compounding drivers, and a concrete stabilization path.
              </p>
            </div>
          </div>

          <div className="mt-16 text-center">
            <Button asChild size="lg" className="font-mono gap-2 group">
              <Link href="/pricing">
                Request Analysis <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
