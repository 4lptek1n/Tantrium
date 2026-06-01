import { ReactNode, useState } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";

export function Layout({ children }: { children: ReactNode }) {
  const [location, setLocation] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/hunt", label: "Problem Hunt", badge: "LIVE" },
    { href: "/reports", label: "Reports", badge: "LIVE", badgeColor: "bg-blue-500/20 text-blue-400" },
    { href: "/core", label: "Tantrium Core" },
    { href: "/codex", label: "Codex" },
    { href: "/demo", label: "Demo" },
    { href: "/pricing", label: "Pricing" },
  ];

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground font-sans">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-mono font-bold tracking-tighter text-xl text-primary">
            <div className="w-4 h-4 bg-primary rounded-sm" />
            TANTRIUM
          </Link>
          
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            {navLinks.map((link) => (
              <Link 
                key={link.href}
                href={link.href} 
                className={`flex items-center gap-1.5 transition-colors hover:text-foreground ${location === link.href ? "text-foreground" : ""}`}
              >
                {link.label}
                {link.badge === "LIVE" && !link.badgeColor && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                )}
                {link.badge === "LIVE" && link.badgeColor && (
                  <span className={`text-[8px] font-mono ${link.badgeColor} px-1 rounded`}>LIVE</span>
                )}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <Button asChild variant="default" className="hidden md:flex font-mono font-semibold tracking-tight" data-testid="button-nav-cta">
              <Link href="/pricing">Request Report</Link>
            </Button>
            
            <Button 
              variant="ghost" 
              size="icon" 
              className="md:hidden" 
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Nav Overlay */}
        {mobileOpen && (
          <div className="md:hidden fixed inset-0 top-16 z-40 bg-background/95 backdrop-blur animate-in fade-in slide-in-from-top-4 duration-200">
            <nav className="flex flex-col p-8 gap-6 text-lg font-medium">
              {navLinks.map((link) => (
                <Link 
                  key={link.href}
                  href={link.href} 
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center justify-between transition-colors hover:text-foreground ${location === link.href ? "text-primary" : "text-muted-foreground"}`}
                >
                  {link.label}
                  {link.badge === "LIVE" && (
                    <span className={`text-[10px] font-mono ${link.badgeColor || "bg-green-500/20 text-green-400"} px-2 py-0.5 rounded`}>LIVE</span>
                  )}
                </Link>
              ))}
              <Button asChild variant="default" className="mt-4 font-mono font-semibold tracking-tight h-14" onClick={() => setMobileOpen(false)}>
                <Link href="/pricing">Request Report</Link>
              </Button>
            </nav>
          </div>
        )}
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
              <li><Link href="/hunt" className="hover:text-foreground">Problem Hunt</Link></li>
              <li><Link href="/reports" className="hover:text-foreground">Live Reports</Link></li>
              <li><Link href="/core" className="hover:text-foreground">Tantrium Core</Link></li>
              <li><Link href="/demo" className="hover:text-foreground">Interactive Demo</Link></li>
              <li><Link href="/pricing" className="hover:text-foreground">Pricing</Link></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
