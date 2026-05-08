import { useState } from "react";
import { Link } from "wouter";
import { 
  Database, ShieldCheck, AlertTriangle, Crosshair, Route, Fingerprint, 
  ChevronDown, ChevronUp 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { METHODOLOGY_STEPS, TANTRIUM_CORE_STATEMENT, TANTRIUM_GLOSSARY } from "@/lib/tantrium-core";

export function CorePage() {
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  const toggleStep = (id: string) => {
    setExpandedSteps(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="flex-1 w-full max-w-4xl mx-auto px-4 py-16 space-y-24">
      {/* Section 1 — Hero */}
      <section className="space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl md:text-6xl font-black tracking-tighter">Tantrium Core</h1>
          <p className="text-2xl text-muted-foreground font-medium">A methodology, not a black box.</p>
        </div>
        
        <div className="space-y-6">
          <div className="border-l-4 border-primary bg-primary/5 p-8 rounded-r-lg">
            <p className="text-xl leading-relaxed text-foreground font-medium">
              {TANTRIUM_CORE_STATEMENT.what}
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 border rounded-xl bg-card">
              <p className="text-sm leading-relaxed text-muted-foreground italic">
                {TANTRIUM_CORE_STATEMENT.notProbability}
              </p>
            </div>
            <div className="p-6 border rounded-xl bg-card">
              <p className="text-sm leading-relaxed text-muted-foreground">
                {TANTRIUM_CORE_STATEMENT.whenItWorks}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2 — The Six-Step Workflow */}
      <section className="space-y-12">
        <h2 className="text-3xl font-bold tracking-tight">The Tantrium Workflow</h2>
        
        <div className="space-y-12">
          {METHODOLOGY_STEPS.map((step, index) => (
            <div key={step.id} className="relative pl-12 group">
              <div className="absolute left-0 top-0 h-full w-px bg-border group-last:h-8" />
              <div className="absolute left-[-4px] top-2 w-2 h-2 rounded-full bg-primary" />
              
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="font-mono text-primary border-primary/20 bg-primary/5">
                    STEP {index + 1}: {step.label}
                  </Badge>
                  <h3 className="text-2xl font-bold">{step.title}</h3>
                </div>
                
                <p className="text-xl font-semibold text-foreground leading-tight">
                  {step.businessSummary}
                </p>
                
                <p className="text-muted-foreground leading-relaxed">
                  {step.whatItDoes}
                </p>
                
                <div className="bg-muted/50 border rounded-lg p-4 text-sm font-medium">
                  <span className="text-primary font-bold mr-2">Output:</span>
                  {step.whatItProduces}
                </div>
                
                <div className="space-y-4">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="p-0 h-auto font-bold text-xs flex items-center gap-1 hover:bg-transparent text-primary"
                    onClick={() => toggleStep(step.id)}
                    data-testid={`toggle-technical-${step.id}`}
                  >
                    {expandedSteps[step.id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {expandedSteps[step.id] ? "HIDE TECHNICAL DETAIL" : "SHOW TECHNICAL DETAIL"}
                  </Button>
                  
                  {expandedSteps[step.id] && (
                    <div className="bg-muted font-mono text-xs rounded-lg p-6 border animate-in slide-in-from-top-2 duration-200">
                      <div className="text-muted-foreground mb-4 uppercase tracking-widest font-black">Methodology Implementation</div>
                      <div className="leading-relaxed whitespace-pre-wrap">
                        {step.advancedDetail}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Section 3 — Glossary */}
      <section className="space-y-12">
        <h2 className="text-3xl font-bold tracking-tight">Glossary of Tantrium Terms</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {TANTRIUM_GLOSSARY.map((entry) => (
            <Card key={entry.term} className="bg-card/50">
              <CardContent className="p-6 space-y-2">
                <div className="font-mono font-bold text-primary text-sm uppercase tracking-tight">{entry.term}</div>
                <p className="text-sm text-muted-foreground leading-relaxed">{entry.plain}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Section 4 — What Tantrium Is Not */}
      <section className="bg-muted rounded-2xl p-8 md:p-12 space-y-8">
        <blockquote className="text-2xl font-bold italic tracking-tight text-foreground/80">
          "{TANTRIUM_CORE_STATEMENT.notProbability}"
        </blockquote>
        
        <div className="flex items-start gap-4 p-6 bg-green-500/10 border border-green-500/20 rounded-xl text-green-700">
          <ShieldCheck className="w-6 h-6 shrink-0 mt-1" />
          <div className="space-y-1">
            <h4 className="font-bold">The Tantrium Guarantee</h4>
            <p className="text-sm font-medium leading-relaxed">
              {TANTRIUM_CORE_STATEMENT.guarantee}
            </p>
          </div>
        </div>
      </section>

      {/* Section 5 — CTA */}
      <section className="text-center space-y-8 py-12">
        <h2 className="text-3xl font-bold tracking-tight">Ready to run Tantrium on your real data?</h2>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button asChild size="lg" className="h-14 px-8 font-bold text-lg" data-testid="btn-launch-hunt">
            <Link href="/hunt">Launch Problem Hunt</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="h-14 px-8 font-bold text-lg" data-testid="btn-view-pricing">
            <Link href="/pricing">View Pricing</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
