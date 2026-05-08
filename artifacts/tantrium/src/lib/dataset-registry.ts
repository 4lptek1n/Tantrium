export interface DatasetEntry {
  id: string;
  name: string;
  sector: string;
  url?: string;
  difficulty: "auto-fetch" | "manual-upload" | "demo-only";
  manualNote?: string;
  problem: string;
  financialImpact: string;
  tantriumOutput: string;
  sourceLink?: string;
  suggestedTargetCol?: string;
  suggestedThreshold?: number;
  suggestedDirection?: "above" | "below";
  expectedColumns?: string[];
}

export const DATASET_REGISTRY: DatasetEntry[] = [
  // SECTOR 1: DATA CENTERS & HOSTING
  {
    id: "server-temp",
    name: "Server Thermal Failure Boundary",
    sector: "DATA CENTERS & HOSTING",
    url: "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/machine_temperature_system_failure.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "value",
    suggestedThreshold: 85,
    suggestedDirection: "above",
    expectedColumns: ["timestamp", "value"],
    problem: "A server machine's temperature is recorded continuously. Find the thermal boundary where failure becomes imminent.",
    financialImpact: "Unplanned server downtime costs $5,000–$500,000 per hour in lost revenue and SLA penalties. Thermal failures are the #1 preventable cause.",
    tantriumOutput: "Exact temperature threshold preceding failure, the time-lag window, safe operating range, and a cooling response protocol.",
    sourceLink: "https://github.com/numenta/NAB"
  },
  {
    id: "appliances-energy",
    name: "Facility Energy Demand Boundary",
    sector: "DATA CENTERS & HOSTING",
    url: "https://raw.githubusercontent.com/LuisM78/Appliances-energy-prediction-data/master/energydata_complete.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "Appliances",
    suggestedThreshold: 300,
    suggestedDirection: "above",
    expectedColumns: ["date", "Appliances", "lights", "T1", "RH_1", "T_out", "RH_out", "Windspeed"],
    problem: "Facility appliance energy consumption is logged by the minute. Identify the demand regime boundary where consumption breaks into a runaway pattern.",
    financialImpact: "Energy overruns in data centers typically add 15–40% to operating costs. Identifying the break point allows load scheduling that prevents peak-tier billing.",
    tantriumOutput: "The load threshold where energy consumption enters an unstable regime, top environmental drivers, and a scheduling policy to stay in the safe envelope.",
    sourceLink: "https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction"
  },
  // SECTOR 2: PLASTICS / POLYMER / MANUFACTURING
  {
    id: "wine-quality",
    name: "Process Quality Degradation Boundary",
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/winequality-red.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "quality",
    suggestedThreshold: 6,
    suggestedDirection: "below",
    expectedColumns: ["fixed acidity","volatile acidity","citric acid","residual sugar","chlorides","free sulfur dioxide","total sulfur dioxide","density","pH","sulphates","alcohol","quality"],
    problem: "Production batch quality scores are logged with physicochemical sensor readings. Find the parameter boundary below which product quality fails to meet specification.",
    financialImpact: "Out-of-spec batches in manufacturing generate reject costs of 3–12% of production value. Early boundary detection eliminates late-stage quality failures.",
    tantriumOutput: "The physicochemical combination that pushes product quality below spec, ranked failure drivers, and the parameter windows that define the safe production envelope.",
    sourceLink: "https://archive.ics.uci.edu/dataset/186/wine+quality"
  },
  {
    id: "secom",
    name: "Semiconductor Yield Failure Boundary",
    sector: "PLASTICS / POLYMER / MANUFACTURING",
    difficulty: "manual-upload",
    manualNote: "Download the SECOM dataset from UCI ML Repository (591 sensor columns, ~1500 runs). Upload the features CSV file.",
    sourceLink: "https://archive.ics.uci.edu/dataset/179/secom",
    problem: "591 process sensors are recorded per semiconductor production run. Find which sensor combinations predict out-of-spec yield failures.",
    financialImpact: "Semiconductor yield losses cost $10,000–$500,000 per failed production run. Every 1% yield improvement represents millions in recovered output.",
    tantriumOutput: "The top sensor signal combinations that predict failure, the boundary values for each, and a process control checklist targeting the safe operating window."
  },
  // SECTOR 3: GENERAL MANUFACTURING & OEE
  {
    id: "predictive-maintenance",
    name: "Machine Failure Boundary (AI4I)",
    sector: "GENERAL MANUFACTURING & OEE",
    difficulty: "manual-upload",
    manualNote: "Download the AI4I 2020 Predictive Maintenance dataset from UCI ML Repository. It is a CSV with columns: UDI, Product ID, Type, Air temperature [K], Process temperature [K], Rotational speed [rpm], Torque [Nm], Tool wear [min], Machine failure, and failure mode columns.",
    sourceLink: "https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset",
    suggestedTargetCol: "Machine failure",
    suggestedThreshold: 1,
    suggestedDirection: "above",
    expectedColumns: ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]", "Machine failure"],
    problem: "10,000 machining operations are logged with temperature, torque, rotational speed, and tool wear. Find the exact parameter boundary where machine failure rate transitions from negligible to significant.",
    financialImpact: "Unplanned manufacturing downtime costs $260,000 per hour on average. Predictive boundary detection reduces unplanned stoppages by 30–50%.",
    tantriumOutput: "The torque/temperature boundary where failure risk crosses the critical threshold, top 3 failure drivers, and an operating envelope for each machine parameter."
  },
  {
    id: "energy-efficiency",
    name: "Building OEE / Energy Efficiency Boundary",
    sector: "GENERAL MANUFACTURING & OEE",
    difficulty: "manual-upload",
    manualNote: "Download the UCI Energy Efficiency dataset (Heating/Cooling Load prediction). Upload the CSV.",
    sourceLink: "https://archive.ics.uci.edu/dataset/242/energy+efficiency",
    problem: "Building configurations are measured against heating and cooling loads. Find the design parameter boundary where energy demand becomes inefficient.",
    financialImpact: "Buildings operating outside their efficiency boundary consume 25–60% excess energy. Identifying the break point enables retrofitting decisions worth $50,000–$2M per facility.",
    tantriumOutput: "The building configuration threshold where energy load breaks into the inefficient regime, top design drivers, and recommended operational adjustments."
  },
  // SECTOR 4: PHARMA / BIOTECH / TOXICITY
  {
    id: "water-potability",
    name: "Water Safety Parameter Boundary",
    sector: "PHARMA / BIOTECH / TOXICITY",
    url: "https://raw.githubusercontent.com/MainakRepositor/Datasets/master/water_potability.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "Potability",
    suggestedThreshold: 1,
    suggestedDirection: "above",
    expectedColumns: ["ph","Hardness","Solids","Chloramines","Sulfate","Conductivity","Organic_carbon","Trihalomethanes","Turbidity","Potability"],
    problem: "Water samples are tested across 9 chemical parameters. Determine which parameter combinations push a sample outside safe potability limits.",
    financialImpact: "Water quality failures in pharmaceutical manufacturing or municipal supply trigger regulatory shutdowns and liability exposure of $1M–$50M per incident.",
    tantriumOutput: "The chemical parameter boundary where water fails safety thresholds, ranked driver parameters, and the safe operating window for each.",
    sourceLink: "https://www.kaggle.com/datasets/adityakadiwal/water-potability"
  },
  {
    id: "heart-failure",
    name: "Clinical Risk Threshold Boundary",
    sector: "PHARMA / BIOTECH / TOXICITY",
    url: "https://raw.githubusercontent.com/dsrscientist/dataset1/master/heart.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "target",
    suggestedThreshold: 1,
    suggestedDirection: "above",
    expectedColumns: ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal","target"],
    problem: "Clinical indicators from cardiac patients are recorded alongside adverse outcomes. Find the diagnostic boundary where risk of a cardiac event transitions from manageable to critical.",
    financialImpact: "Missed cardiac events drive malpractice claims averaging $500,000 and regulatory exposure for pharma/insurance companies. Early risk stratification reduces liability and intervention costs.",
    tantriumOutput: "The clinical parameter boundary where adverse outcome risk crosses the critical threshold, top 3 diagnostic drivers, and a risk stratification protocol.",
    sourceLink: "https://archive.ics.uci.edu/dataset/45/heart+disease"
  },
  // SECTOR 5: FINANCE & INSURANCE RISK
  {
    id: "insurance-claims",
    name: "Insurance Claims Severity Boundary",
    sector: "FINANCE & INSURANCE RISK",
    url: "https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/insurance.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "charges",
    suggestedThreshold: 15000,
    suggestedDirection: "above",
    expectedColumns: ["age","sex","bmi","children","smoker","region","charges"],
    problem: "Policyholder profiles are logged against annual insurance charges. Find the profile boundary where claims costs break into the high-severity regime.",
    financialImpact: "High-severity claimants in the top 10% of a portfolio generate 40–60% of total claims costs. Boundary identification enables repricing and reserve adjustment worth millions.",
    tantriumOutput: "The policyholder profile threshold where claims enter the high-severity regime, top cost drivers, and a risk segmentation framework for the safe vs at-risk population.",
    sourceLink: "https://www.kaggle.com/datasets/mirichoi0218/insurance"
  },
  {
    id: "german-credit",
    name: "Credit Default Risk Boundary",
    sector: "FINANCE & INSURANCE RISK",
    difficulty: "manual-upload",
    manualNote: "Download the Statlog (German Credit Data) dataset from UCI ML Repository. Upload the processed CSV with column headers.",
    sourceLink: "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
    suggestedTargetCol: "class",
    suggestedThreshold: 2,
    suggestedDirection: "above",
    problem: "Loan applicants are profiled across 20 financial and personal attributes. Find the credit feature boundary where default risk transitions from acceptable to operationally critical.",
    financialImpact: "Each 1% increase in portfolio default rate costs a mid-sized lender $2M–$20M annually. Boundary-based credit policy tightening is directly measurable in P&L.",
    tantriumOutput: "The credit profile boundary where default probability crosses the risk tolerance threshold, top 3 drivers, and a credit policy adjustment targeting the safe applicant envelope."
  },
  // SECTOR 6: ENERGY & HVAC
  {
    id: "energy-demand",
    name: "Facility Air Quality Boundary",
    sector: "ENERGY & HVAC",
    url: "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pollution.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "pm2.5",
    suggestedThreshold: 100,
    suggestedDirection: "above",
    expectedColumns: ["No","year","month","day","hour","pm2.5","DEWP","TEMP","PRES","cbwd","Iws","Is","Ir"],
    problem: "Hourly environmental readings from an industrial facility track pollution levels against weather and operational parameters. Find the operational boundary where air quality breaks into a regulatory risk zone.",
    financialImpact: "EPA violations for air quality exceedances carry fines of $25,000–$100,000 per day plus remediation costs. Boundary-aware operations prevent regulatory exposure.",
    tantriumOutput: "The operational parameter combination that drives pollution above regulatory thresholds, top environmental drivers, and the safe operating window.",
    sourceLink: "https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data"
  },
  // SECTOR 7: LOGISTICS
  {
    id: "logistics-demand",
    name: "Supply Chain Demand Spike Boundary",
    sector: "LOGISTICS",
    difficulty: "manual-upload",
    manualNote: "Download the 'Online Retail' dataset from UCI ML Repository (transactions CSV). Upload the cleaned CSV with columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.",
    sourceLink: "https://archive.ics.uci.edu/dataset/352/online+retail",
    suggestedTargetCol: "Quantity",
    suggestedThreshold: 100,
    suggestedDirection: "above",
    problem: "Retail transaction quantities are logged by SKU and date. Find the order volume boundary above which fulfillment systems consistently fail to meet SLA commitments.",
    financialImpact: "Logistics SLA failures cost 2–5% of contract value in penalties and 15–30% customer churn. Demand boundary detection enables pre-emptive capacity allocation.",
    tantriumOutput: "The order volume threshold where fulfillment SLAs break, demand pattern drivers, and an inventory buffer policy targeting the safe throughput envelope."
  },
  // SECTOR 8: CYBER & SLA RISK
  {
    id: "network-anomaly",
    name: "Network SLA Breach Boundary",
    sector: "CYBER & SLA RISK",
    difficulty: "manual-upload",
    manualNote: "Download the KDD Cup 1999 or NSL-KDD network intrusion dataset. Upload the CSV with connection features.",
    sourceLink: "https://www.unb.ca/cic/datasets/nsl.html",
    suggestedTargetCol: "label",
    suggestedThreshold: 1,
    suggestedDirection: "above",
    problem: "Network connection attributes are logged continuously. Find the traffic parameter combination where the network transitions from normal operation to anomalous/SLA-threatening behavior.",
    financialImpact: "Network SLA breaches cost enterprise operators $100,000–$5M per incident in penalties, remediation, and reputational damage. Early boundary detection cuts mean-time-to-detect by 70%.",
    tantriumOutput: "The connection parameter boundary where anomalous behavior begins, top traffic drivers of boundary breach, and a network policy targeting the safe operating envelope."
  },
  // FUNCTION TEST
  {
    id: "iris-test",
    name: "Engine Verification (Iris Dataset)",
    sector: "FUNCTION TEST",
    url: "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "petal_length",
    suggestedThreshold: 4.0,
    suggestedDirection: "above",
    problem: "Standard benchmark dataset. Use this to verify the analysis engine is producing correct outputs before running on production data.",
    financialImpact: "N/A — verification only.",
    tantriumOutput: "Verifiable correlation outputs that can be cross-checked against published petal length analysis results."
  },
  {
    id: "diamonds",
    name: "Product Pricing Anomaly Boundary",
    sector: "FINANCE & INSURANCE RISK",
    url: "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/diamonds.csv",
    difficulty: "auto-fetch",
    suggestedTargetCol: "price",
    suggestedThreshold: 5000,
    suggestedDirection: "above",
    expectedColumns: ["carat","cut","color","clarity","depth","table","price","x","y","z"],
    problem: "Product attributes and prices are logged across 53,000 items. Find the physical characteristic boundary where pricing breaks into the premium regime.",
    financialImpact: "Mis-priced inventory in commodity markets costs 5–15% of revenue. Boundary-aware pricing models capture margin that generic regression misses.",
    tantriumOutput: "The attribute combination threshold where pricing enters the premium regime, top value drivers, and the attribute windows defining the standard vs premium boundary.",
    sourceLink: "https://ggplot2.tidyverse.org/reference/diamonds.html"
  }
];
