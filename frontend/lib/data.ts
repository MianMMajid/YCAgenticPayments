import {
  Activity,
  BadgeCheck,
  Banknote,
  Blocks,
  Building2,
  ClipboardCheck,
  FileSearch,
  FileText,
  Landmark,
  MapPinned,
  ShieldCheck,
  Workflow,
} from "lucide-react";

export const deals = [
  {
    name: "567 Guilford Avenue",
    market: "Baltimore, MD",
    phase: "Diligence",
    risk: "Medium",
    value: "$395k",
  },
  {
    name: "123 Monument Street",
    market: "Baltimore, MD",
    phase: "Offer Draft",
    risk: "Low",
    value: "$370k",
  },
  {
    name: "914 Fort Avenue",
    market: "Baltimore, MD",
    phase: "Risk Review",
    risk: "High",
    value: "$425k",
  },
];

export const metrics = [
  { label: "Active workflows", value: "18", detail: "6 need review" },
  { label: "Median cycle", value: "9.4d", detail: "from offer to clear" },
  { label: "Grounded claims", value: "94%", detail: "source-backed" },
  { label: "Pending payments", value: "$1.9k", detail: "4 milestones" },
];

export const workflowSteps = [
  {
    title: "Ingest deal room",
    owner: "Document agent",
    state: "Complete",
    detail: "17 files indexed across leases, inspection, appraisal, permits, and offer package.",
  },
  {
    title: "Extract diligence facts",
    owner: "Extraction graph",
    state: "Complete",
    detail: "Purchase price, contingencies, flood zone, valuation delta, and title exceptions normalized.",
  },
  {
    title: "Resolve contradictions",
    owner: "Reasoning agent",
    state: "Review",
    detail: "Tax assessment conflicts with RentCast value range and requires expert confirmation.",
  },
  {
    title: "Prepare escrow release",
    owner: "Escrow orchestrator",
    state: "Blocked",
    detail: "Inspection and appraisal reports need approval before payment release.",
  },
];

export const documents = [
  {
    name: "Draft PSA v4.pdf",
    type: "Purchase agreement",
    status: "Parsed",
    citations: 12,
    issue: "Closing date and earnest money verified",
  },
  {
    name: "Inspection report.pdf",
    type: "Inspection",
    status: "Needs review",
    citations: 8,
    issue: "Electrical panel exception requires buyer approval",
  },
  {
    name: "Baltimore zoning extract.pdf",
    type: "Zoning",
    status: "Parsed",
    citations: 6,
    issue: "Residential use appears conforming",
  },
  {
    name: "Appraisal worksheet.xlsx",
    type: "Financial model",
    status: "Waiting",
    citations: 0,
    issue: "Awaiting lender file",
  },
];

export const escrowMilestones = [
  { label: "Initiated", value: "Complete", icon: Building2 },
  { label: "Funded", value: "Complete", icon: Banknote },
  { label: "Verifications", value: "In review", icon: FileSearch },
  { label: "Settlement", value: "Pending", icon: Landmark },
];

export const agents = [
  {
    name: "Title Search Agent",
    task: "Review title exceptions",
    state: "Approved",
    tool: "LandAmerica",
    icon: ShieldCheck,
  },
  {
    name: "Inspection Agent",
    task: "Classify repair exposure",
    state: "Review",
    tool: "AmeriSpec",
    icon: ClipboardCheck,
  },
  {
    name: "Appraisal Agent",
    task: "Validate valuation band",
    state: "Running",
    tool: "CoreLogic",
    icon: Activity,
  },
  {
    name: "Lending Agent",
    task: "Confirm conditions",
    state: "Queued",
    tool: "Fannie Mae",
    icon: FileText,
  },
];

export const traceEvents = [
  {
    time: "09:42",
    title: "Retrieved comparable sales",
    body: "Pulled three recent comps within 0.8 miles and normalized for beds, baths, and finished sqft.",
  },
  {
    time: "09:44",
    title: "Cited zoning record",
    body: "Matched parcel to residential zoning extract and flagged no current non-conforming use.",
  },
  {
    time: "09:47",
    title: "Raised expert question",
    body: "Inspection notes mention knob-and-tube remnants; agent asked reviewer to confirm remediation scope.",
  },
];

export const navigation = [
  { label: "Deals", icon: Blocks },
  { label: "Diligence", icon: FileSearch },
  { label: "Escrow", icon: Workflow },
  { label: "Map", icon: MapPinned },
  { label: "Trust", icon: BadgeCheck },
];
