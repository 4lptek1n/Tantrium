export const SECTORS = [
  {
    id: "data-centers",
    name: "Data Centers & Hosting",
    tagline: "When your uptime SLA keeps slipping and you can't find the cause.",
    datasets: [
      {
        id: "dc-a",
        name: "Hyperscale rack thermal failure (cooling cascade scenarios)",
        envelope: "System remains stable when server utilization stays below 78% and thermal load is within acceptable range.",
        boundary: "Thermal cascade initiates when rack density exceeds 14.2 kW/rack combined with cooling response lag above 8 minutes.",
        drivers: [
          { name: "Cooling Response Lag", explanation: "HVAC ramp-up delay during utilization spikes", impact: 85 },
          { name: "Rack Density", explanation: "Concentration of high-compute nodes in specific zones", impact: 70 },
          { name: "Power Draw Spikes", explanation: "Transient surges overwhelming PDU capacity", impact: 45 }
        ],
        path: [
          "Reduce rack utilization below 72% during peak hours",
          "Implement staggered maintenance windows to avoid compounding thermal load",
          "Pre-cool zones dynamically based on predictive compute schedules"
        ]
      },
      {
        id: "dc-b",
        name: "Network edge node instability (latency spike clusters)",
        envelope: "Node routing remains optimal when packet ingress stays under 4.2M pps with buffer occupancy below 60%.",
        boundary: "Queue drops accelerate exponentially when burst traffic exceeds 1.5GB/s and routing table updates coincide.",
        drivers: [
          { name: "Burst Traffic", explanation: "Sudden ingress overwhelming port buffers", impact: 90 },
          { name: "Routing Table Updates", explanation: "CPU contention during BGP convergence", impact: 65 },
          { name: "Buffer Occupancy", explanation: "Sustained high watermarks leading to tail drops", impact: 50 }
        ],
        path: [
          "Increase port buffer allocation for critical edge uplinks",
          "Schedule BGP maintenance off-peak relative to local timezone",
          "Implement stricter rate limiting on non-priority ingress flows"
        ]
      }
    ]
  },
  {
    id: "plastics",
    name: "Plastics & Polymer Manufacturing",
    tagline: "When your process keeps drifting out of spec and rejects pile up.",
    datasets: [
      {
        id: "poly-a",
        name: "Injection molding reject rate surge",
        envelope: "Process yields 99.8% acceptable parts when melt temperature holds at 240°C ±2°C and holding pressure is >800 bar.",
        boundary: "Short shots occur when melt temperature drops below 237°C while mold cooling time is less than 12 seconds.",
        drivers: [
          { name: "Melt Temperature Variance", explanation: "Heater band cycling inconsistency", impact: 80 },
          { name: "Cooling Time", explanation: "Aggressive cycle time reduction", impact: 60 },
          { name: "Material Moisture", explanation: "Inadequate pre-drying of resin", impact: 40 }
        ],
        path: [
          "Recalibrate heater band PID loops for tighter temperature control",
          "Increase minimum cooling time interlock to 13.5 seconds",
          "Implement inline moisture sensing before feed throat"
        ]
      },
      {
        id: "poly-b",
        name: "Polymer extrusion viscosity drift",
        envelope: "Extrusion is stable when screw RPM is below 120 and feed throat temp is < 45°C.",
        boundary: "Viscosity drops sharply when screw RPM exceeds 125 leading to shear heating beyond material limits.",
        drivers: [
          { name: "Screw RPM Surge", explanation: "Aggressive speed settings to meet throughput targets", impact: 75 },
          { name: "Shear Heating", explanation: "Frictional heat generation exceeding barrel cooling capacity", impact: 65 },
          { name: "Resin Batch Variance", explanation: "Inconsistent melt flow index in raw material", impact: 50 }
        ],
        path: [
          "Cap max screw RPM at 118 for high-viscosity resins",
          "Increase barrel cooling zone capacity in zone 3",
          "Implement tighter MFI incoming inspection"
        ]
      }
    ]
  },
  {
    id: "manufacturing",
    name: "General Manufacturing & OEE",
    tagline: "When downtime keeps happening and the root cause keeps shifting.",
    datasets: [
      {
        id: "mfg-a",
        name: "Assembly line OEE degradation",
        envelope: "OEE remains above 85% when shift handovers are under 10 mins and micro-stops are < 5 per hour.",
        boundary: "OEE collapses below 70% when micro-stops exceed 8 per hour combined with upstream parts starvation.",
        drivers: [
          { name: "Micro-stops", explanation: "Brief unrecorded jams in automated fastening stations", impact: 85 },
          { name: "Parts Starvation", explanation: "AGV delivery delays from warehouse to line", impact: 60 },
          { name: "Shift Handover Delay", explanation: "Communication gaps leading to delayed start", impact: 40 }
        ],
        path: [
          "Implement predictive maintenance on fastening station actuators",
          "Increase buffer stock at line-side points by 15%",
          "Standardize digital shift handover checklist"
        ]
      },
      {
        id: "mfg-b",
        name: "CNC machining dimensional drift",
        envelope: "Tolerances held within ±0.005mm when coolant temp is < 22°C and tool wear is < 30%.",
        boundary: "Scrap rate spikes when coolant temp exceeds 25°C and spindle load indicates >40% tool wear.",
        drivers: [
          { name: "Coolant Temperature", explanation: "Inadequate chiller capacity during extended runs", impact: 75 },
          { name: "Tool Wear", explanation: "Aggressive feed rates accelerating edge degradation", impact: 70 },
          { name: "Spindle Vibration", explanation: "Harmonics at specific RPM ranges", impact: 45 }
        ],
        path: [
          "Upgrade coolant chiller system for high-load machines",
          "Implement automated tool change at 35% wear limit",
          "Optimize toolpaths to avoid resonant frequency RPMs"
        ]
      }
    ]
  },
  {
    id: "pharma",
    name: "Pharma & Biotech",
    tagline: "When batch failures and out-of-spec results threaten your regulatory standing.",
    datasets: [
      {
        id: "pharma-a",
        name: "Bioreactor batch failure clustering",
        envelope: "Cell viability is optimal when pH stays between 7.2-7.4 and dissolved oxygen > 40%.",
        boundary: "Apoptosis triggers when pH drops below 7.15 for > 20 minutes simultaneously with DO dipping below 35%.",
        drivers: [
          { name: "pH Excursion", explanation: "Delayed base addition response", impact: 85 },
          { name: "Dissolved Oxygen Dip", explanation: "Inadequate sparging rate during exponential growth", impact: 65 },
          { name: "Agitation Shear", explanation: "Excessive impeller speed damaging cells", impact: 40 }
        ],
        path: [
          "Retune pH control loop for faster base addition response",
          "Implement cascade DO control linking agitation and sparging",
          "Cap max agitation speed during peak growth phase"
        ]
      },
      {
        id: "pharma-b",
        name: "Formulation out-of-spec excursions",
        envelope: "Content uniformity is achieved when mixing time is > 45 mins at 20 RPM.",
        boundary: "Segregation occurs when mixing time exceeds 60 mins leading to over-blending, or drops below 40 mins.",
        drivers: [
          { name: "Over-blending", explanation: "Extended mixing times causing particle segregation", impact: 80 },
          { name: "Fill Level", explanation: "Blender loaded beyond optimal working volume", impact: 60 },
          { name: "Material Flow", explanation: "Poor flowability of active pharmaceutical ingredient", impact: 50 }
        ],
        path: [
          "Strictly enforce 50-minute maximum mixing time",
          "Limit blender fill volume to 65% of total capacity",
          "Pre-mill API to ensure tighter particle size distribution"
        ]
      }
    ]
  },
  {
    id: "finance",
    name: "Finance & Insurance Risk",
    tagline: "When your risk models keep underperforming in specific market conditions.",
    datasets: [
      {
        id: "fin-a",
        name: "Credit portfolio stress boundary",
        envelope: "Portfolio default rate remains < 2% when VIX < 25 and sector concentration < 15%.",
        boundary: "Defaults cascade when VIX spikes > 30 and specific sector correlations break down.",
        drivers: [
          { name: "Volatility Spike", explanation: "Macro market stress triggering margin calls", impact: 85 },
          { name: "Sector Correlation", explanation: "Previously uncorrelated assets moving together", impact: 70 },
          { name: "Liquidity Drain", explanation: "Inability to exit positions at modeled prices", impact: 55 }
        ],
        path: [
          "Implement dynamic concentration limits based on real-time VIX",
          "Stress test portfolio assuming historical correlations go to 1.0",
          "Maintain higher cash buffers during elevated volatility regimes"
        ]
      },
      {
        id: "fin-b",
        name: "Insurance claims clustering at tail events",
        envelope: "Reserves are adequate for isolated storm events causing < 500 claims/day.",
        boundary: "Capital depletion accelerates when a secondary event occurs within 14 days of a primary tail event.",
        drivers: [
          { name: "Secondary Event Timing", explanation: "Consecutive catastrophes depleting adjuster capacity", impact: 90 },
          { name: "Reinsurance Attachment", explanation: "Losses falling just short of treaty attachment points", impact: 65 },
          { name: "Supply Chain Inflation", explanation: "Post-event surge in repair material costs", impact: 50 }
        ],
        path: [
          "Restructure reinsurance to lower aggregate attachment points",
          "Establish pre-negotiated repair rates with preferred contractor networks",
          "Build predictive models for adjuster deployment based on early weather tracks"
        ]
      }
    ]
  }
];
