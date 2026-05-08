import { ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";

export function Layout({ children }: { children: ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground font-sans">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-mono font-bold tracking-tighter text-xl text-primary">
            <div className="w-4 h-4 bg-primary rounded-sm" />
            TANTRIUM
          </Link>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <Link href="/" className={`transition-colors hover:text-foreground ${location === "/" ? "text-foreground" : ""}`}>
              Home
            </Link>
            <Link href="/datasets" className={`transition-colors hover:text-foreground ${location === "/datasets" ? "text-foreground" : ""}`}>
              Datasets
            </Link>
            <Link href="/analyze" className={`transition-colors hover:text-foreground ${location === "/analyze" ? "text-foreground" : ""}`}>
              Analyze
            </Link>
            <Link href="/demo" className={`transition-colors hover:text-foreground ${location === "/demo" ? "text-foreground" : ""}`}>
              Demo
            </Link>
            <Link href="/pricing" className={`transition-colors hover:text-foreground ${location === "/pricing" ? "text-foreground" : ""}`}>
              Pricing
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <Button asChild variant="default" className="font-mono font-semibold tracking-tight" data-testid="button-nav-cta">
              <Link href="/pricing">Request Report</Link>
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col">
        {children}
      </main>
      <footer className="border-t border-border bg-card/50 py-12 mt-auto">
        <div className="container mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 font-mono font-bold tracking-tighter text-lg text-primary mb-4">
              <div className="w-3 h-3 bg-primary rounded-sm" />
              TANTRIUM
            </div>
            <p className="text-sm text-muted-foreground">
              Precision boundary analysis for industrial and financial operators.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Platform</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/demo" className="hover:text-foreground">Interactive Demo</Link></li>
              <li><Link href="/pricing" className="hover:text-foreground">Pricing</Link></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
