export const SECTORS = [
  {
    id: "data-centers",
    name: "DATA CENTERS & HOSTING",
    tagline: "When your uptime SLA keeps slipping and you can't find the cause.",
    datasets: [
      {
        id: "server-temp",
        name: "Server Thermal Failure Boundary",
        envelope: "System remains stable when server temperature stays below 85°C.",
        boundary: "Thermal failure imminent when temperature exceed 85°C.",
        drivers: [
          { name: "CPU Load", explanation: "High computation cycles generating heat", impact: 85 },
          { name: "Cooling Fan RPM", explanation: "Insufficient airflow for current load", impact: 70 },
          { name: "Ambient Temperature", explanation: "External heat load on rack", impact: 45 }
        ],
        path: [
          "Reduce CPU utilization when temp hits 82°C",
          "Increase rack airflow via perforated tiles",
          "Recalibrate cooling response lag"
        ]
      }
    ]
  },
  {
    id: "plastics",
    name: "PLASTICS / POLYMER / MANUFACTURING",
    tagline: "When your process keeps drifting out of spec and rejects pile up.",
    datasets: [
      {
        id: "wine-quality",
        name: "Process Quality Degradation Boundary",
        envelope: "Quality remains high when physicochemical parameters stay within verified ranges.",
        boundary: "Quality degrades when alcohol content drops below a specific threshold combined with high acidity.",
        drivers: [
          { name: "Alcohol", explanation: "Primary driver of batch quality score", impact: 90 },
          { name: "Volatile Acidity", explanation: "Acidity level impacting taste profile", impact: 65 },
          { name: "Sulphates", explanation: "Preservation agent concentration", impact: 50 }
        ],
        path: [
          "Tighten fermentation temperature control",
          "Implement inline alcohol sensing",
          "Standardize sulphate addition timing"
        ]
      }
    ]
  },
  {
    id: "manufacturing",
    name: "GENERAL MANUFACTURING & OEE",
    tagline: "When downtime keeps happening and the root cause keeps shifting.",
    datasets: [
      {
        id: "predictive-maintenance",
        name: "Machine Failure Boundary (AI4I)",
        envelope: "Machine remains stable when torque and tool wear are within standard limits.",
        boundary: "Failure risk spikes when torque exceeds 50Nm or tool wear crosses 200 min.",
        drivers: [
          { name: "Torque", explanation: "Mechanical stress on the spindle", impact: 85 },
          { name: "Tool Wear", explanation: "Cumulative usage of the cutting edge", impact: 70 },
          { name: "Air Temperature", explanation: "Environmental heat affecting tolerances", impact: 40 }
        ],
        path: [
          "Automate tool change at 180 min wear",
          "Cap torque at 48Nm for high-precision runs",
          "Improve spindle chiller performance"
        ]
      }
    ]
  },
  {
    id: "pharma",
    name: "PHARMA / BIOTECH / TOXICITY",
    tagline: "When batch failures and out-of-spec results threaten your regulatory standing.",
    datasets: [
      {
        id: "water-potability",
        name: "Water Safety Parameter Boundary",
        envelope: "Water remains potable when chemical parameters stay within safety windows.",
        boundary: "Safety threshold breached when pH or hardness deviates from regulatory limits.",
        drivers: [
          { name: "ph", explanation: "Acidity/Alkalinity balance", impact: 80 },
          { name: "Hardness", explanation: "Mineral concentration levels", impact: 60 },
          { name: "Chloramines", explanation: "Disinfection byproduct levels", impact: 45 }
        ],
        path: [
          "Install real-time pH monitoring and dosing",
          "Upgrade reverse osmosis filtration membranes",
          "Optimize chloramine neutralizing schedule"
        ]
      }
    ]
  },
  {
    id: "finance",
    name: "FINANCE & INSURANCE RISK",
    tagline: "When your risk models keep underperforming in specific market conditions.",
    datasets: [
      {
        id: "insurance-claims",
        name: "Insurance Claims Severity Boundary",
        envelope: "Claims remain in the low-severity regime for profiles within the safe envelope.",
        boundary: "Claims severity spikes for policyholders matching high-risk age and BMI profiles.",
        drivers: [
          { name: "smoker", explanation: "Primary lifestyle risk factor", impact: 90 },
          { name: "bmi", explanation: "Physical health indicator", impact: 65 },
          { name: "age", explanation: "Demographic risk variable", impact: 50 }
        ],
        path: [
          "Adjust premiums for high-risk BMI segments",
          "Increase reserves for smokers in specific age bands",
          "Refine underwriting for high-severity clusters"
        ]
      }
    ]
  },
  {
    id: "energy-hvac",
    name: "ENERGY & HVAC",
    tagline: "When energy overruns and environmental violations threaten your bottom line.",
    datasets: [
      {
        id: "energy-demand",
        name: "Facility Air Quality Boundary",
        envelope: "Air quality remains within regulatory limits during normal operations.",
        boundary: "Regulatory breach when pm2.5 levels exceed 100 during low windspeed.",
        drivers: [
          { name: "pm2.5", explanation: "Particulate matter concentration", impact: 95 },
          { name: "Windspeed", explanation: "Atmospheric dispersion factor", impact: 60 },
          { name: "TEMP", explanation: "Temperature affecting air stagnation", impact: 40 }
        ],
        path: [
          "Activate secondary scrubbers when pm2.5 hits 80",
          "Schedule high-emission runs during high wind windows",
          "Install low-level localized air sensors"
        ]
      }
    ]
  },
  {
    id: "logistics",
    name: "LOGISTICS",
    tagline: "When your fulfillment SLAs collapse during peak demand.",
    datasets: [
      {
        id: "logistics-demand",
        name: "Supply Chain Demand Spike Boundary",
        envelope: "Fulfillment SLAs are met when order volume is within standard capacity.",
        boundary: "SLA breach occurs when order quantity exceeds 100 units per transaction.",
        drivers: [
          { name: "Quantity", explanation: "Order volume per transaction", impact: 85 },
          { name: "UnitPrice", explanation: "Value density affecting handling care", impact: 40 },
          { name: "CustomerID", explanation: "Bulk buyer behavior patterns", impact: 30 }
        ],
        path: [
          "Pre-allocate pickers for bulk order windows",
          "Implement automated sorting for high-quantity SKUs",
          "Set dynamic SLA buffers for large orders"
        ]
      }
    ]
  },
  {
    id: "cyber-risk",
    name: "CYBER & SLA RISK",
    tagline: "When network anomalies and breaches threaten your enterprise security.",
    datasets: [
      {
        id: "network-anomaly",
        name: "Network SLA Breach Boundary",
        envelope: "Network remains stable during standard traffic patterns.",
        boundary: "Anomaly detected when traffic parameter combinations trigger intrusion alerts.",
        drivers: [
          { name: "Traffic Volume", explanation: "Total throughput on segment", impact: 80 },
          { name: "Connection Count", explanation: "Simultaneous sessions per host", impact: 70 },
          { name: "Error Rate", explanation: "Failed packet transmissions", impact: 50 }
        ],
        path: [
          "Enable rate limiting on edge routers",
          "Implement zero-trust boundary verification",
          "Automate isolation for anomalous segments"
        ]
      }
    ]
  }
];

