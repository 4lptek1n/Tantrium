import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { SECTORS } from "@/lib/data";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2 } from "lucide-react";

const contactSchema = z.object({
  name: z.string().min(2, "Name is required"),
  company: z.string().min(2, "Company is required"),
  industry: z.string().min(1, "Please select an industry"),
  package: z.enum(["screen", "report", "enterprise"], {
    required_error: "Please select a package",
  }),
  description: z.string().min(10, "Please provide a brief description of the failing system"),
});

type ContactFormValues = z.infer<typeof contactSchema>;

export function Pricing() {
  const { toast } = useToast();

  const form = useForm<ContactFormValues>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      name: "",
      company: "",
      industry: "",
      package: "report",
      description: "",
    },
  });

  const onSubmit = (data: ContactFormValues) => {
    console.log(data);
    toast({
      title: "Request Submitted",
      description: "A Tantrium analyst will contact you within 24 hours.",
    });
    form.reset();
  };

  return (
    <div className="flex flex-col w-full">
      {/* Pricing Header */}
      <section className="pt-20 pb-12 bg-background border-b border-border">
        <div className="container mx-auto px-4 max-w-4xl text-center">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tighter mb-6">Invest in Certainty</h1>
          <p className="text-xl text-muted-foreground">
            Precision analysis requires precision engineering. We do not do estimates or educated guesses. We find the boundary.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 bg-card border-b border-border">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
            
            {/* Quick Screen */}
            <Card className="bg-background border-border flex flex-col h-full">
              <CardHeader>
                <CardTitle className="text-xl font-mono">Quick Screen</CardTitle>
                <div className="text-3xl font-bold mt-4 mb-2">$5,000</div>
                <CardDescription className="text-sm">
                  Turnaround: 5 business days
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <p className="text-sm text-muted-foreground mb-6">
                  You submit one failing case. We tell you where the boundary is, what's driving the failures, and whether a full Boundary Report is warranted.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>2-page Boundary Screen</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>High-level boundary identification</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Boundary Report */}
            <Card className="bg-background border-primary shadow-lg shadow-primary/5 flex flex-col h-full relative">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-bold font-mono tracking-wider">
                STANDARD
              </div>
              <CardHeader>
                <CardTitle className="text-xl font-mono">Boundary Report</CardTitle>
                <div className="text-3xl font-bold mt-4 mb-2">$25,000</div>
                <CardDescription className="text-sm">
                  Turnaround: 3 weeks
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <p className="text-sm text-muted-foreground mb-6">
                  Full analysis of one operational system. The definitive guide to your system's failure modes.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Safe operating envelope</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>First failure boundary mapping</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Top failure drivers</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Concrete stabilization path</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>30-minute results briefing</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Enterprise Program */}
            <Card className="bg-background border-border flex flex-col h-full">
              <CardHeader>
                <CardTitle className="text-xl font-mono">Enterprise</CardTitle>
                <div className="text-3xl font-bold mt-4 mb-2">from $100k</div>
                <CardDescription className="text-sm">
                  Ongoing monitoring
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <p className="text-sm text-muted-foreground mb-6">
                  Ongoing boundary monitoring across multiple systems or facilities.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Multiple system analyses</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Quarterly re-analysis</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Alert threshold configuration</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>Dedicated Tantrium analyst</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4 max-w-2xl">
          <div className="mb-10">
            <h2 className="text-3xl font-bold tracking-tight mb-2">Request a Report</h2>
            <p className="text-muted-foreground">Submit your details and we will coordinate securely acquiring your data.</p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8 p-8 border border-border rounded-lg bg-card/50">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="font-mono">Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Jane Doe" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="company"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="font-mono">Company</FormLabel>
                      <FormControl>
                        <Input placeholder="Acme Corp" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="industry"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono">Industry</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select an industry" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {SECTORS.map((sector) => (
                          <SelectItem key={sector.id} value={sector.id}>{sector.name}</SelectItem>
                        ))}
                        <SelectItem value="other">Other / Custom</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Separator className="bg-border/50" />

              <FormField
                control={form.control}
                name="package"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormLabel className="font-mono">Which package?</FormLabel>
                    <FormControl>
                      <RadioGroup
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        className="flex flex-col space-y-2"
                      >
                        <FormItem className="flex items-center space-x-3 space-y-0 p-3 border border-border rounded-md hover:bg-muted/50 transition-colors cursor-pointer">
                          <FormControl>
                            <RadioGroupItem value="screen" />
                          </FormControl>
                          <div className="flex-1 cursor-pointer">
                            <FormLabel className="font-normal cursor-pointer text-sm">
                              <span className="font-bold block">Quick Screen</span>
                              <span className="text-muted-foreground">$5,000 — 5 business days</span>
                            </FormLabel>
                          </div>
                        </FormItem>
                        <FormItem className="flex items-center space-x-3 space-y-0 p-3 border border-primary/50 bg-primary/5 rounded-md hover:bg-primary/10 transition-colors cursor-pointer">
                          <FormControl>
                            <RadioGroupItem value="report" />
                          </FormControl>
                          <div className="flex-1 cursor-pointer">
                            <FormLabel className="font-normal cursor-pointer text-sm">
                              <span className="font-bold block">Boundary Report</span>
                              <span className="text-muted-foreground">$25,000 — 3 weeks</span>
                            </FormLabel>
                          </div>
                        </FormItem>
                        <FormItem className="flex items-center space-x-3 space-y-0 p-3 border border-border rounded-md hover:bg-muted/50 transition-colors cursor-pointer">
                          <FormControl>
                            <RadioGroupItem value="enterprise" />
                          </FormControl>
                          <div className="flex-1 cursor-pointer">
                            <FormLabel className="font-normal cursor-pointer text-sm">
                              <span className="font-bold block">Enterprise Program</span>
                              <span className="text-muted-foreground">Custom scope</span>
                            </FormLabel>
                          </div>
                        </FormItem>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-mono">Brief description of the failing system</FormLabel>
                    <FormControl>
                      <Textarea 
                        placeholder="E.g., CNC dimensional drift during extended shift runs..." 
                        className="min-h-[120px] resize-none"
                        {...field} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" size="lg" className="w-full font-mono font-bold text-base h-14" data-testid="btn-submit-contact">
                Submit Request
              </Button>
            </form>
          </Form>
        </div>
      </section>

    </div>
  );
}
