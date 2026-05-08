export interface ProspectPersona {
  title: string;
  typicalPainPoint: string;
  linkedInSearchTip: string;
}

export interface SectorProspect {
  sector: string;
  personas: ProspectPersona[];
  outreachPitch: string;  // 2-3 sentence LinkedIn message template. Use [Name] placeholder.
  closingLine: string;    // The "one unstable system" hook adapted to this sector
}

export const SECTOR_PROSPECTS: SectorProspect[] = [
  // DATA CENTERS & HOSTING
  {
    sector: "DATA CENTERS & HOSTING",
    personas: [
      { title: "VP Infrastructure", typicalPainPoint: "Server thermal cascades that take hours to diagnose", linkedInSearchTip: "Search: 'VP Infrastructure' + 'data center' + 'reliability'" },
      { title: "Head of Reliability Engineering (SRE)", typicalPainPoint: "SLA breaches from unpredicted hardware failures", linkedInSearchTip: "Search: 'SRE' OR 'Site Reliability' + 'hyperscale' OR 'colocation'" },
      { title: "IT Operations Director", typicalPainPoint: "Recurring incidents with no clear root cause", linkedInSearchTip: "Search: 'Director IT Operations' + 'uptime' OR 'incident management'" }
    ],
    outreachPitch: "Hi [Name], I noticed you're managing infrastructure at [Company]. We work with operations teams to find the exact thermal or load threshold where their systems start failing — not a probability, but the actual boundary. If you have a server or rack that keeps acting up, we'd analyze it in under a week. Worth 20 minutes?",
    closingLine: "Give us one server that keeps failing. We find the boundary where it breaks."
  },
  // PLASTICS / POLYMER / MANUFACTURING
  {
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    personas: [
      { title: "VP Manufacturing", typicalPainPoint: "Reject rates that fluctuate without clear cause", linkedInSearchTip: "Search: 'VP Manufacturing' + 'plastics' OR 'polymer' OR 'injection molding'" },
      { title: "Process Engineering Director", typicalPainPoint: "Process drift that production teams can't pin down", linkedInSearchTip: "Search: 'Process Engineering Director' + 'extrusion' OR 'blow molding'" },
      { title: "Quality Director", typicalPainPoint: "Customer returns tied to batch variability", linkedInSearchTip: "Search: 'Quality Director' OR 'Head of QA' + 'polymer manufacturing'" }
    ],
    outreachPitch: "Hi [Name], I work with manufacturing teams dealing with unpredictable process drift — reject rates that spike without a clear trigger. We identify the exact parameter boundary where your process loses control, so your engineering team knows precisely what to hold. If you have a line that keeps going out of spec, we'd love to analyze it.",
    closingLine: "Give us one production line that keeps rejecting. We find the boundary where quality breaks."
  },
  // GENERAL MANUFACTURING & OEE
  {
    sector: "GENERAL MANUFACTURING & OEE",
    personas: [
      { title: "VP Operations", typicalPainPoint: "OEE that won't budge past a certain ceiling", linkedInSearchTip: "Search: 'VP Operations' + 'OEE' OR 'Overall Equipment Effectiveness'" },
      { title: "Maintenance Director", typicalPainPoint: "Unplanned downtime with shifting root causes", linkedInSearchTip: "Search: 'Director of Maintenance' OR 'Reliability Manager' + manufacturing" },
      { title: "Head of Continuous Improvement", typicalPainPoint: "Improvement projects that don't stick", linkedInSearchTip: "Search: 'Continuous Improvement Manager' OR 'Lean Director' + manufacturing" }
    ],
    outreachPitch: "Hi [Name], downtime that keeps recurring despite maintenance programs is usually a boundary problem — the machine works fine until a specific combination of conditions is reached. We've helped teams find that exact threshold. If you have equipment that keeps failing on a schedule no one can explain, we'd analyze it within days.",
    closingLine: "Give us one machine that keeps stopping. We find the boundary where it breaks."
  },
  // PHARMA / BIOTECH / TOXICITY
  {
    sector: "PHARMA / BIOTECH / TOXICITY",
    personas: [
      { title: "VP Quality Assurance", typicalPainPoint: "Batch failures with inconsistent root cause findings", linkedInSearchTip: "Search: 'VP Quality' OR 'Head QA' + 'pharma' OR 'biotech' OR 'biopharma'" },
      { title: "Regulatory Affairs Director", typicalPainPoint: "Out-of-spec findings that trigger regulatory scrutiny", linkedInSearchTip: "Search: 'Director Regulatory Affairs' + 'FDA' OR 'EMA' + 'manufacturing'" },
      { title: "Process Development Lead", typicalPainPoint: "Bioreactor or formulation processes that won't scale cleanly", linkedInSearchTip: "Search: 'Process Development' + 'bioreactor' OR 'cell culture' OR 'formulation'" }
    ],
    outreachPitch: "Hi [Name], batch failures in pharma manufacturing are almost always a boundary issue — a combination of process parameters that triggers failure only under specific conditions. We identify that combination precisely. If you have a process that keeps producing OOS results without a clear pattern, we'd run a boundary screen on it.",
    closingLine: "Give us one batch process that keeps failing. We find the boundary where it breaks."
  },
  // FINANCE & INSURANCE RISK
  {
    sector: "FINANCE & INSURANCE RISK",
    personas: [
      { title: "Chief Risk Officer (CRO)", typicalPainPoint: "Risk models that underperform in specific market conditions", linkedInSearchTip: "Search: 'Chief Risk Officer' OR 'CRO' + 'credit risk' OR 'insurance' OR 'financial risk'" },
      { title: "Head of Credit Risk", typicalPainPoint: "Default clusters that weren't predicted by the model", linkedInSearchTip: "Search: 'Head of Credit Risk' OR 'VP Credit Risk' + 'lending' OR 'bank' OR 'fintech'" },
      { title: "VP Risk Analytics", typicalPainPoint: "Portfolio segments that consistently exceed loss expectations", linkedInSearchTip: "Search: 'VP Risk Analytics' OR 'Director Risk' + 'portfolio' OR 'insurance'" }
    ],
    outreachPitch: "Hi [Name], portfolio segments that consistently exceed loss expectations are usually operating past their risk boundary — a combination of exposure variables that your current model doesn't identify as a failure region. We define that boundary precisely. If you have a segment that keeps surprising you, we'd run a boundary screen on it.",
    closingLine: "Give us one portfolio segment that keeps surprising you. We find the boundary where risk breaks."
  },
  // ENERGY & HVAC
  {
    sector: "ENERGY & HVAC",
    personas: [
      { title: "VP Facilities", typicalPainPoint: "Energy spikes that trigger peak-tier billing", linkedInSearchTip: "Search: 'VP Facilities' + 'energy management' + 'HVAC' OR 'data center'" },
      { title: "Sustainability Director", typicalPainPoint: "Efficiency targets missed due to sub-optimal system boundaries", linkedInSearchTip: "Search: 'Sustainability Director' + 'energy efficiency' + 'commercial real estate'" },
      { title: "Chief Operating Officer (COO)", typicalPainPoint: "Uncontrolled utility OpEx growth", linkedInSearchTip: "Search: 'COO' + 'facilities' OR 'logistics' + 'energy costs'" }
    ],
    outreachPitch: "Hi [Name], energy consumption spikes are rarely random — they happen when a facility's HVAC or load configuration crosses a specific boundary. We identify that exact breakpoint so you can cap consumption before it triggers peak billing. If you have a facility that's consistently over-budget on energy, we'd love to map its boundary.",
    closingLine: "Give us one facility that's over energy budget. We find the boundary where it breaks."
  },
  // LOGISTICS
  {
    sector: "LOGISTICS",
    personas: [
      { title: "VP Supply Chain", typicalPainPoint: "Fulfillment SLA collapses during demand spikes", linkedInSearchTip: "Search: 'VP Supply Chain' OR 'Head of Logistics' + 'e-commerce' OR 'distribution'" },
      { title: "Operations Director", typicalPainPoint: "Inventory stockouts despite high safety stock", linkedInSearchTip: "Search: 'Director Operations' + 'warehouse management' OR 'fulfillment'" },
      { title: "Last Mile Lead", typicalPainPoint: "Delivery failures when volume crosses a hidden threshold", linkedInSearchTip: "Search: 'Head of Last Mile' OR 'Logistics Manager' + 'delivery performance'" }
    ],
    outreachPitch: "Hi [Name], fulfillment collapses during demand spikes are usually a boundary issue — a specific volume/SKU mix that pushes your system past its stable regime. We find that exact threshold so you can allocate capacity ahead of the break. If you have a distribution center that keeps failing during peak, we'd run a boundary screen on it.",
    closingLine: "Give us one warehouse that keeps missing SLAs. We find the boundary where it breaks."
  },
  // CYBER & SLA RISK
  {
    sector: "CYBER & SLA RISK",
    personas: [
      { title: "CISO", typicalPainPoint: "Anomaly detection noise that hides genuine breaches", linkedInSearchTip: "Search: 'CISO' OR 'Chief Information Security Officer' + 'enterprise' OR 'infrastructure'" },
      { title: "VP Network Operations", typicalPainPoint: "Network performance degradation that's hard to trace", linkedInSearchTip: "Search: 'VP Network Ops' OR 'Director NetOps' + 'SLA' OR 'availability'" },
      { title: "Head of Security Ops (SOC)", typicalPainPoint: "Mean-time-to-detect (MTTD) is too high for zero-day boundaries", linkedInSearchTip: "Search: 'Head of SOC' OR 'Security Operations Manager' + 'threat detection'" }
    ],
    outreachPitch: "Hi [Name], network anomalies and SLA breaches usually happen when traffic parameters cross a multi-variable boundary that traditional monitors miss. We identify those boundaries precisely, cutting MTTD by up to 70%. If you have a network segment that's behaving unpredictably, we'd like to run a boundary screen on it.",
    closingLine: "Give us one network segment acting up. We find the boundary where risk breaks."
  }
];
