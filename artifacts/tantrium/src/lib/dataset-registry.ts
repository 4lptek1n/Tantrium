export interface DatasetEntry {
  id: string;
  name: string;
  sector: string;
  url?: string;
  corsReliable: boolean;
  manualNote?: string;
  problem: string;
  suggestedTargetCol?: string;
  suggestedThreshold?: number;
  suggestedDirection?: "above" | "below";
  expectedColumns?: string[];
}

export const DATASET_REGISTRY: DatasetEntry[] = [
  // SECTOR: DATA CENTERS & HOSTING
  {
    id: "appliances-energy",
    name: "Appliances Energy Prediction",
    sector: "DATA CENTERS & HOSTING",
    url: "https://raw.githubusercontent.com/LuisM78/Appliances-energy-prediction-data/master/energydata_complete.csv",
    corsReliable: true,
    problem: "At what energy load does appliance consumption break into an unstable high-consumption regime?",
    suggestedTargetCol: "Appliances",
    suggestedThreshold: 300,
    suggestedDirection: "above",
    expectedColumns: ["date", "Appliances", "lights", "T1", "RH_1", "T_out", "RH_out", "Windspeed"]
  },
  {
    id: "server-farm-power",
    name: "Server Farm Power Demand",
    sector: "DATA CENTERS & HOSTING",
    url: "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/machine_temperature_system_failure.csv",
    corsReliable: true,
    problem: "Identify the temperature threshold where machine failure becomes imminent in a server environment.",
    suggestedTargetCol: "value",
    suggestedThreshold: 85,
    suggestedDirection: "above"
  },
  {
    id: "network-traffic",
    name: "Network Traffic Anomaly (CICIDS)",
    sector: "DATA CENTERS & HOSTING",
    corsReliable: false,
    manualNote: "Download from https://www.unb.ca/cic/datasets/ids-2018.html and upload the CSV.",
    problem: "Find the traffic volume boundary where network intrusion patterns emerge."
  },

  // SECTOR: PLASTICS / POLYMER / MANUFACTURING
  {
    id: "steel-faults",
    name: "Steel Plates Surface Faults",
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/steel_faults.csv",
    corsReliable: false,
    manualNote: "Download from UCI ML Repository: Steel Plates Faults dataset",
    problem: "Determine which surface geometry parameters drive fault classification beyond acceptable limits."
  },
  {
    id: "injection-molding",
    name: "Injection Molding Sensor Data",
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    corsReliable: false,
    manualNote: "Download from a plastics dataset source.",
    problem: "Identify the boundary where pressure/temperature variance leads to part defects."
  },
  {
    id: "secom",
    name: "Semiconductor Manufacturing (SECOM)",
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    corsReliable: false,
    manualNote: "Download SECOM dataset from UCI ML Repository. 591 sensor readings per run.",
    problem: "Which sensor signals reliably predict out-of-spec production runs?"
  },

  // SECTOR: GENERAL MANUFACTURING & OEE
  {
    id: "predictive-maintenance",
    name: "AI4I 2020 Predictive Maintenance",
    sector: "GENERAL MANUFACTURING & OEE",
    url: "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv",
    corsReliable: false,
    manualNote: "Download from UCI: https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset",
    problem: "Find the exact torque/temperature combination where machine failure rate crosses from negligible to significant."
  },
  {
    id: "traffic-volume",
    name: "Metro Interstate Traffic Volume",
    sector: "GENERAL MANUFACTURING & OEE",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/Metro_Interstate_Traffic_Volume.csv",
    corsReliable: false,
    problem: "Identify traffic throughput thresholds that predict operational congestion events."
  },
  {
    id: "bike-sharing",
    name: "Bike Sharing Demand",
    sector: "GENERAL MANUFACTURING & OEE",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/hour.csv",
    corsReliable: false,
    problem: "Find the demand level boundary where system capacity constraints activate."
  },

  // SECTOR: PHARMA / BIOTECH / TOXICITY
  {
    id: "water-quality",
    name: "Water Quality (Potability)",
    sector: "PHARMA / BIOTECH / TOXICITY",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/water_potability.csv",
    corsReliable: false,
    problem: "Determine which chemical parameter combinations push water quality outside safe boundaries."
  },
  {
    id: "wine-quality",
    name: "Wine Quality Boundary",
    sector: "PHARMA / BIOTECH / TOXICITY",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/winequality-red.csv",
    corsReliable: false,
    problem: "Find the physicochemical boundary where wine quality degrades below acceptable product standards."
  },
  {
    id: "heart-failure",
    name: "Heart Failure Clinical Records",
    sector: "PHARMA / BIOTECH / TOXICITY",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/heart.csv",
    corsReliable: false,
    problem: "Which clinical indicators reach a boundary that reliably predicts adverse outcomes?"
  },

  // SECTOR: FINANCE & INSURANCE RISK
  {
    id: "german-credit",
    name: "German Credit Risk",
    sector: "FINANCE & INSURANCE RISK",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/german_credit.csv",
    corsReliable: false,
    problem: "Identify the credit feature boundary where default risk transitions from manageable to critical."
  },
  {
    id: "insurance-claims",
    name: "Insurance Claims Severity",
    sector: "FINANCE & INSURANCE RISK",
    url: "https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/insurance.csv",
    corsReliable: true,
    problem: "Find the policyholder profile threshold where claims costs break into the high-severity regime.",
    suggestedTargetCol: "charges",
    suggestedThreshold: 15000,
    suggestedDirection: "above"
  },
  {
    id: "loan-default",
    name: "Loan Default Prediction",
    sector: "FINANCE & INSURANCE RISK",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/loan_data.csv",
    corsReliable: false,
    problem: "Determine the debt-to-income boundary beyond which default probability exceeds operational tolerance."
  },

  {
    id: "iris-test",
    name: "Iris (Quick Function Test)",
    sector: "Function Test",
    url: "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
    corsReliable: true,
    problem: "Simple verification dataset — confirm the analysis engine is working correctly before running on production data.",
    suggestedTargetCol: "petal_length",
    suggestedThreshold: 4.0,
    suggestedDirection: "above"
  }
];
