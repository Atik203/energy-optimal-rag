/**
 * Site content and every number used on the site.
 *
 * The project record is the source of truth. Each group below names the
 * documents it was transcribed from. No value here is estimated, modelled,
 * or invented for presentation. Where a value is absent from the record, it
 * is omitted or marked TBD.
 *
 * Key documents:
 * - README.md
 * - ROADMAP.md
 * - docs/IMPLEMENTATION_PLAN.md
 * - docs/MEASUREMENT.md
 * - docs/DATA_CARD.md
 * - docs/PILOT_EVIDENCE.md
 * - docs/RISKS.md
 * - docs/DECISIONS.md
 * - docs/proposal.md
 * - prereg/PREREGISTRATION.md
 *
 * Claim boundary: post-pilot MARGINAL, public scaffold v0.1.0, no
 * confirmatory results, preregistration not frozen. Every pilot value is
 * labelled pilot in the UI. The 2 pp static claim is dead. The 5 pp result
 * is a pilot signal, not certified. The 78.8% oracle gain is an upper bound.
 */

export type ClaimStatus = "supported" | "dead" | "rejected" | "upper-bound" | "signal" | "pending";

export const project = {
  name: "Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation",
  shortName: "G2",
  siteName: "Energy Observatory",
  version: "0.1.0",
  status: "post-pilot MARGINAL",
  statusDetail: "Public scaffold. No confirmatory results. Preregistration not frozen.",
  updated: "2026-11-14",
  repo: "https://github.com/Atik203/energy-optimal-rag",
  author: "Atikur Rahaman and contributors",
  citationVersion: "0.1.0",
  citationDate: "2026-11-09",
  licenseCode: "MIT",
  licenseDocs: "CC BY 4.0",
  licenseData: "CC BY-SA 4.0",
} as const;

/* Course and team — EEE 4261 Green Computing, Section C. Sadman Ifaz is
   from Section E; the remaining team is Section C. */

export const course = {
  code: "EEE 4261",
  name: "Green Computing",
  section: "C",
  label: "EEE 4261 · Green Computing · Section C",
} as const;

export const team = [
  { name: "Md. Atikur Rahaman", id: "0112310298", section: "C" },
  { name: "Md. Sarowar Alam Sourov", id: "0112310302", section: "C" },
  { name: "Pratay Paul", id: "0112310163", section: "C" },
  { name: "Sadman Ifaz", id: "0112230873", section: "E" },
  { name: "Jayed Bin Khalid", id: "0112230880", section: "C" },
] as const;

/* ------------------------------------------------------------------ */
/* Claim boundary — README.md §Status, ROADMAP.md §1.2–1.3             */
/* ------------------------------------------------------------------ */

export const claimBoundary = {
  notClaimed: [
    "A universal k* across datasets, readers, retrievers, or hardware.",
    "A \u201c2 pp optimal\u201d retrieval depth. The 2 pp decision rule is dead at the current power.",
    "A \u201c5 pp certified\u201d result before the powered rerun.",
    "A learned-policy gain. The 78.8% oracle is a hindsight upper bound.",
    "Carbon optimality beyond constant-factor reporting.",
    "Generalization to frontier readers, dense retrievers, or full NQ.",
    "An energy or hardware-generalization claim from the optional H200 64k accuracy-only check.",
    "A Llama 3B or 16k context result as part of H7 or G5.",
  ],
  mayClaim: [
    "The energy-depth tradeoff is real and steep under the pilot conditions.",
    "The affine energy model and the context-side share are measurable and stable in the pilot.",
    "The identity is a useful diagnostic at an interior optimum and flags over-retrieval at high k.",
    "At a 5 pp EM margin, k = 4 is non-inferior in the pilot and saves energy \u2014 pilot evidence, not a certified result.",
    "Query-conditional depth is a promising direction; 78.8% is an oracle upper bound, not a policy result.",
  ],
  nextClaim:
    "At a pre-specified 5 percentage-point EM non-inferiority margin, an interior depth (k = 4) retains accuracy while saving roughly 69% of GPU energy per correct answer relative to k = 32, and a query-conditional policy captures a material fraction of the adaptive oracle gap at matched accuracy.",
  nextClaimNote: "This is the defensible next claim if the powered rerun supports it. It is not yet established.",
  prohibitedLanguage: [
    "\u201cOptimal depth\u201d without a dataset, reader, margin, and hardware qualifier.",
    "\u201cCertified\u201d before the freeze and the powered rerun.",
    "\u201cLearned-policy gain\u201d from the oracle computation.",
  ],
} as const;

/* ------------------------------------------------------------------ */
/* Pilot — README.md, ROADMAP.md §1.1, docs/MEASUREMENT.md,             */
/* docs/IMPLEMENTATION_PLAN.md §3–7, docs/PILOT_EVIDENCE.md,           */
/* docs/proposal.md, prereg/PREREGISTRATION.md §1                       */
/* ------------------------------------------------------------------ */

export const pilot = {
  dataset: "SQuAD v1.1 dev",
  questions: 200,
  depths: [0, 1, 2, 4, 8, 16, 32],
  generations: 1400,
  gpu: "RTX 3060 Laptop 6 GB",
  reader: "qwen3.5:4b",
  quantization: "Q4",
  readerContext: "4096 context",
  retriever: "BM25 top-32",
  passages: 45651,
  contexts: 20958,
  chunkWords: 70,
  meanPassageWords: 53.4,
  energy: {
    e1: 45.5,
    e4: 48.3,
    e32: 157.1,
    span: 3.45,
  },
  fit: {
    a: 15.74,
    b: 2.283,
    r2: 0.999,
    formula: "J(k) = 15.74 + 2.283k",
  },
  energyMeans: {
    j1: 17.98,
    j4: 25.1,
    j32: 89.55,
  },
  accuracy: {
    a1: 0.395,
    a4: 0.52,
    a32: 0.57,
    plateauLow: 0.52,
    plateauHigh: 0.535,
    plateauFrom: 4,
    plateauTo: 16,
  },
  contextShare: {
    at2: 36.3,
    at32: 85.1,
  },
  retrievalShare: {
    min: 3.5,
    max: 17.3,
    minAt: 32,
    maxAt: 1,
  },
  identity: {
    at2: { gap: 0.044, ci: [-0.05, 0.128] as const },
    at32: { gap: 0.7 },
  },
  repeatCv: { k: 8, median: 3.8, max: 9.24 },
  scoringSensitivity: {
    interiorK: 16,
    savingsPct: 42.5,
    gold: "Von Miller",
    prediction: "Denver linebacker Von Miller",
  },
  static2pp: {
    kStar: 32,
    pOptimal: 0.61,
    threshold: 0.8,
    status: "DEAD" as const,
  },
  fivePp: {
    k: 4,
    savings: 69.3,
    nStar: 876,
    pReported: 0.537,
    status: "pilot signal, not certified" as const,
  },
  oracle: { gain: 78.8, status: "upper bound" as const },
  recall: {
    depths: [1, 2, 4, 8, 16, 32],
    goldContext: [63.0, 71.0, 77.5, 81.0, 83.5, 88.0],
    goldAnswer: [58.0, 67.5, 75.5, 80.5, 84.0, 88.5],
  },
  blockFactors: [
    { k: 0, factor: 1.041 },
    { k: 1, factor: 1.1 },
    { k: 2, factor: 1.188 },
    { k: 4, factor: 1.128 },
    { k: 8, factor: 1.118 },
    { k: 16, factor: 1.081 },
    { k: 32, factor: 1.073 },
  ],
  idle: { preW: 15.56, preCv: 10.4, postW: 17.63, postCv: 15.9 },
  cpuProxy: { watts: 20, seconds: 0.149, joules: 3.11 },
  thermal: {
    tempStartC: 71.9,
    tempEndC: 88.4,
    clockStartMhz: 1657,
    clockEndMhz: 1003,
    powerStartW: 82.5,
    powerEndW: 54.2,
  },
  nonce: { prefillWithoutMs: 247, prefillWithMs: 710 },
  mdeAt200: "4\u20135 pp",
  sweepKj: 49.6,
  nStar: [
    { k: 4, n: 876 },
    { k: 8, n: 1000 },
    { k: 16, n: 1489 },
  ],
  savingsAt: { queries: 10000, kj: 566, calibrationShareOfSavingPct: 8.8 },
  calibrationShareAt100kPct: 0.9,
} as const;

/* ------------------------------------------------------------------ */
/* Pilot table — docs/proposal.md Appendix A, README.md §Status         */
/* ------------------------------------------------------------------ */

export const pilotTable: Array<{
  quantity: string;
  value: string;
  status: ClaimStatus;
  note: string;
}> = [
  {
    quantity: "Energy per correct answer",
    value: "E(32) 157.1 vs E(1) 45.5 J/correct \u00b7 3.45\u00d7",
    status: "supported",
    note: "Steep under pilot conditions; not a universal law.",
  },
  {
    quantity: "Affine energy fit",
    value: "J(k) = 15.74 + 2.283k J \u00b7 R\u00b2 = 0.9990",
    status: "supported",
    note: "Affine on this grid; not a law.",
  },
  {
    quantity: "Accuracy",
    value: "A_EM 0.395 \u2192 0.570; flat 0.520\u20130.535 at k = 4\u201316",
    status: "supported",
    note: "Strict EM; reader-limited.",
  },
  {
    quantity: "Context-side share",
    value: "36.3% at k = 2 \u2192 85.1% at k = 32",
    status: "supported",
    note: "Retrieval-only proxy share: 3.5%\u201317.3%.",
  },
  {
    quantity: "Identity at k = 2",
    value: "+0.044 \u00b7 95% CI [\u22120.050, +0.128]",
    status: "supported",
    note: "Interval includes zero; local diagnostic.",
  },
  {
    quantity: "Identity at k = 32",
    value: "+0.700",
    status: "rejected",
    note: "Rejected: flags over-retrieval.",
  },
  {
    quantity: "Repeat CV at k = 8",
    value: "median 3.80% \u00b7 max 9.24%",
    status: "supported",
    note: "Three blocks of 20 identical queries.",
  },
  {
    quantity: "Static 2 pp claim",
    value: "k* = 32 (boundary) \u00b7 P(k* optimal) = 0.61 < 0.8",
    status: "dead",
    note: "Power/margin failure. Do not resurrect.",
  },
  {
    quantity: "5 pp margin at k = 4",
    value: "69.3% savings \u00b7 N* = 876 \u00b7 P = .537",
    status: "signal",
    note: "Pilot signal, not certified. Needs the powered rerun.",
  },
  {
    quantity: "Adaptive oracle",
    value: "78.8% gain at matched accuracy",
    status: "upper-bound",
    note: "Hindsight upper bound; no learned policy.",
  },
];

/* ------------------------------------------------------------------ */
/* Survived / died board — README.md §Status, ROADMAP.md §1.1           */
/* ------------------------------------------------------------------ */

export const survivalClaims: Array<{
  status: ClaimStatus;
  claim: string;
  evidence: string;
  note: string;
}> = [
  {
    status: "supported",
    claim: "Energy per correct answer rises steeply with depth",
    evidence: "E(32) 157.1 vs E(1) 45.5 J/correct \u2192 3.45\u00d7",
    note: "Pilot",
  },
  {
    status: "supported",
    claim: "Energy is affine in depth on this grid",
    evidence: "J(k) = 15.74 + 2.283k J \u00b7 R\u00b2 = 0.9990",
    note: "Pilot",
  },
  {
    status: "supported",
    claim: "Accuracy rises then plateaus",
    evidence: "A_EM 0.395 \u2192 0.570 \u00b7 flat 0.520\u20130.535 at k = 4\u201316",
    note: "Pilot",
  },
  {
    status: "supported",
    claim: "Context-side energy dominates at high depth",
    evidence: "36.3% at k = 2 \u2192 85.1% at k = 32",
    note: "Pilot",
  },
  {
    status: "supported",
    claim: "The identity holds at the interior optimum",
    evidence: "+0.044 at k = 2 \u00b7 95% CI [\u22120.050, +0.128]",
    note: "Pilot",
  },
  {
    status: "supported",
    claim: "The measurement is repeatable",
    evidence: "Repeat CV median 3.80% \u00b7 max 9.24%",
    note: "Pilot",
  },
  {
    status: "dead",
    claim: "A static 2 pp-optimal depth",
    evidence: "k* = 32 boundary \u00b7 P(k* optimal) = 0.61 < 0.8",
    note: "DEAD",
  },
  {
    status: "rejected",
    claim: "The identity certifies high-k behaviour",
    evidence: "Gap +0.700 at k = 32 \u00b7 32 passages is over-retrieval",
    note: "Rejected",
  },
  {
    status: "upper-bound",
    claim: "Query-conditional oracle gain",
    evidence: "78.8% at matched accuracy",
    note: "Upper bound only",
  },
  {
    status: "signal",
    claim: "5 pp non-inferiority at k = 4",
    evidence: "69.3% savings \u00b7 N* = 876 \u00b7 P = .537",
    note: "Pilot signal",
  },
];

/* ------------------------------------------------------------------ */
/* Powered rerun — README.md §The powered rerun, prereg §3–6,          */
/* docs/IMPLEMENTATION_PLAN.md §5, §8–9                               */
/* ------------------------------------------------------------------ */

export const rerun = {
  primary: {
    dataset: "SQuAD v1.1 dev",
    n: 1000,
    depths: [0, 1, 2, 4, 8, 16, 32],
    reader: "qwen3.5:4b",
    retriever: "BM25 top-32",
    seed: 20261115,
    marginPp: 5,
    referenceK: 32,
    candidateK: 4,
    minSavingsPct: 20,
    secondaryMarginPp: 2,
    alpha: 0.05,
    bootstrap: 10000,
  },
  replication: {
    n: 500,
    reader: "Qwen2.5-1.5B-Instruct",
    dataset: "SQuAD v1.1 dev",
    depths: [0, 1, 2, 4, 8, 16, 32],
  },
  readerPanel: {
    n: 500,
    reader: "Llama 3.2 3B Instruct",
    quantization: "Q4_K_M",
    context: 4096,
    dataset: "SQuAD v1.1 dev",
    depths: [0, 1, 2, 4, 8, 16, 32],
    sameIdsAs: "Qwen2.5-1.5B replication",
    status: "exploratory",
    note: "Direction-only; not part of H7 or G5.",
  },
  contextProbe: {
    n: 200,
    reader: "Qwen3.5-4B",
    quantization: "Q4",
    context: 16384,
    controlContext: 4096,
    depths: [32, 48, 64],
    hardware: "RTX 3060 Laptop 6 GB",
    status: "planned diagnostic",
    note: "16k allocation; k<=64 is ~6k tokens, not a 16k prompt. Requires 100% GPU.",
  },
  optionalH200: {
    hardware: "H200 MIG 1g.18gb (18 GB)",
    reader: "Qwen3.5-4B",
    context: 65536,
    mode: "accuracy-only",
    energyClaim: false,
    status: "optional, not run",
  },
  hotpot: {
    n: 500,
    dataset: "HotpotQA distractor dev",
    depths: [0, 1, 2, 4, 8, 10],
    retriever: "BM25 top-10",
    paragraphs: 10,
    goldParagraphs: 2,
    distractors: 8,
  },
  boundary: {
    n: 200,
    depths: [32, 48, 64],
    retriever: "BM25 top-64",
    contextCheck: "8k context budget for k=64; separate 16k probe",
  },
  taxes: {
    n: 150,
    depths: [0, 1, 2, 4, 8, 16, 32],
    fixedPct: 20,
    perPassagePct: 20,
    rangePct: "10\u201330%",
    fixedJ: 3.148,
    perPassageJ: 0.457,
  },
  policy: {
    train: 600,
    validation: 200,
    test: 200,
    seed: 20261115,
    gateOracleGainPct: 20,
    gateCapturePct: 50,
  },
  power: {
    discordant: 0.08,
    sd: 0.283,
    seAt1000: "0.9 pp",
    mdeAt200: "5.0 pp",
    mdeAt500: "3.1 pp",
    mdeAt1000: "2.2 pp",
    halfWidthAt1000: "1.8 pp",
    powerAt0: ">0.99",
    powerAt1: "0.998",
    powerAt2: "0.96",
    powerAt3: "0.72",
  },
} as const;

/* ------------------------------------------------------------------ */
/* Hypotheses — prereg/PREREGISTRATION.md §2                           */
/* ------------------------------------------------------------------ */

export const hypotheses: Array<{
  id: string;
  statement: string;
  type: string;
}> = [
  {
    id: "H1",
    statement:
      "Energy is affine in depth: J(k) = a + bk with b > 0 and R\u00b2 \u2265 0.95 on SQuAD, and the affine fit is not rejected by a lack-of-fit check at the 5% level.",
    type: "Confirmatory",
  },
  {
    id: "H2",
    statement:
      "At a 5 pp EM non-inferiority margin, k = 4 is non-inferior to k = 32 on SQuAD at n = 1,000, with at least 20% energy savings.",
    type: "Primary",
  },
  {
    id: "H3",
    statement:
      "At the selected interior depth, the optimal-depth identity gap \u03b5_J \u2212 \u03b5_A has a 95% bootstrap interval that includes zero.",
    type: "Confirmatory",
  },
  {
    id: "H4",
    statement:
      "The context-side energy share S(k) lies in [0.10, 0.70] at the selected depth and increases with k.",
    type: "Confirmatory",
  },
  {
    id: "H5",
    statement:
      "The oracle query-conditional gain is at least 20%, and a learned policy captures at least 50% of it at matched accuracy on 200 held-out questions.",
    type: "Confirmatory (adaptive)",
  },
  {
    id: "H6",
    statement:
      "A fixed energy tax increases k*; a per-passage energy tax decreases k*, with the accuracy gate held fixed.",
    type: "Confirmatory (causal)",
  },
  {
    id: "H7",
    statement:
      "The direction of H2 replicates on Qwen2.5-1.5B-Instruct (n = 500) or HotpotQA distractor (n = 500).",
    type: "Confirmatory (replication)",
  },
];

/* ------------------------------------------------------------------ */
/* Gates — ROADMAP.md §4, docs/IMPLEMENTATION_PLAN.md §12              */
/* ------------------------------------------------------------------ */

export const gates = {
  kill: [
    {
      id: "K1",
      criterion: "Relative energy effect < 10%",
      pilot: "PASS (245% effect)",
      action: "If it fires on the rerun, stop the depth story; report the null.",
      status: "pass" as const,
    },
    {
      id: "K2",
      criterion: "k* at boundary {0, K_max}",
      pilot: "FAIL (k* = 32)",
      action: "Extend the grid once (16k probe); if still boundary, reframe as \u201cdon't over-retrieve.\u201d",
      status: "fail" as const,
    },
    {
      id: "K3",
      criterion: "P(k* optimal) < 0.8",
      pilot: "FAIL (0.61)",
      action: "Increase n or repeats once; if it persists, drop static certification.",
      status: "fail" as const,
    },
    {
      id: "K4",
      criterion: "Context share < 5% and flat",
      pilot: "PASS (36\u201385%)",
      action: "If it fires, the lever is generation, not depth; reframe.",
      status: "pass" as const,
    },
    {
      id: "K5",
      criterion: "k* spans > 1 depth across bootstrap/datasets",
      pilot: "FAIL (span 3)",
      action: "Pivot to query-conditional policy; do not claim a population k*.",
      status: "fail" as const,
    },
    {
      id: "K6",
      criterion: "Oracle gain < 15%",
      pilot: "PASS (78.8%)",
      action: "If it fires on held-out policy evaluation, kill the adaptive component.",
      status: "pass" as const,
    },
    {
      id: "K7",
      criterion: "Repeat CV > 20% or MDE > observed effect",
      pilot: "PASS (3.80% median)",
      action: "Fix measurement (more repeats, wall meter); do not interpret the curve.",
      status: "pass" as const,
    },
  ],
  go: [
    {
      id: "G1",
      criterion:
        "5 pp non-inferiority at an interior k, with \u2265 20% energy savings vs k = 32.",
    },
    {
      id: "G2",
      criterion:
        "Upper confidence bound on accuracy loss \u2264 5 pp, and bootstrap P(k* optimal) \u2265 0.8 for the 5 pp selection.",
    },
    {
      id: "G3",
      criterion:
        "Context-side share at the selected k in [0.10, 0.70], and the share varies with k.",
    },
    {
      id: "G4",
      criterion:
        "Oracle gain \u2265 20%, and a learned policy captures \u2265 50% of it at matched accuracy.",
    },
    {
      id: "G5",
      criterion: "Replication on the 1.5B reader or HotpotQA.",
    },
  ],
} as const;

/* ------------------------------------------------------------------ */
/* Phases — ROADMAP.md §2                                              */
/* ------------------------------------------------------------------ */

export const phases: Array<{
  id: string;
  weeks: string;
  name: string;
  goal: string;
  outputs: string;
  exit: string;
}> = [
  {
    id: "P0",
    weeks: "Week 1",
    name: "Scaffold and golden reproduction",
    goal: "Prove the harness before producing new evidence.",
    outputs:
      "Repository, CI, environment lock, config schema, CLI validation, data manifest, 200-question golden reproduction, measurement harness checks.",
    exit:
      "Golden E(k) within 10% of the pilot at each depth; K7 passes; validate is clean.",
  },
  {
    id: "P1",
    weeks: "Weeks 2\u20133",
    name: "Powered SQuAD rerun",
    goal: "Decide whether the paper has a static policy result.",
    outputs:
      "n = 1,000 \u00d7 7 depths, frozen prereg, raw ledger, primary 5 pp non-inferiority analysis.",
    exit: "G1 or a documented failure; K1\u2013K7 adjudicated; freeze respected.",
  },
  {
    id: "P2",
    weeks: "Weeks 4\u20136",
    name: "External validity and causal test",
    goal: "Stress the result with one confirmatory replication reader, one exploratory reader, a distractor dataset, depth/context probes, and energy taxes.",
    outputs:
      "Qwen2.5-1.5B replication (n = 500) and Llama 3.2 3B exploratory reader (n = 500), HotpotQA distractor (n = 500, k \u2264 10), boundary probe (n = 200, 8k), 16k context-budget probe (n = 200), fixed and per-passage taxes; optional H200 accuracy-only check, not run.",
    exit: "G5 replication; tax signs match Corollary 1; boundary probe resolves; exploratory arms reported without gates.",
  },
  {
    id: "P3",
    weeks: "Weeks 7\u201310",
    name: "Query-conditional policy",
    goal: "Test whether adaptivity is real, not just a ceiling.",
    outputs:
      "Feature set, policy model, 600/200/200 split, matched-accuracy evaluation, oracle gap capture.",
    exit: "G4: oracle gain \u2265 20% and policy captures \u2265 50% at matched accuracy, or a documented negative.",
  },
  {
    id: "P4",
    weeks: "Weeks 11\u201314",
    name: "Theory validation and sensitivity",
    goal: "Test the identity, the comparative statics, and the dependence on scoring and margin.",
    outputs:
      "Identity tests across datasets and readers, certification-cost curves, margin sensitivity, distractor counterexample check, robustness to scoring rule.",
    exit: "Theory report; identity and comparative statics either supported or revised.",
  },
  {
    id: "P5",
    weeks: "Weeks 15\u201318",
    name: "Paper",
    goal: "Write a decision-theory and causal-measurement paper, not a curve paper.",
    outputs:
      "Manuscript draft, supplement, figures, tables, claims-evidence map.",
    exit: "Internal review; every number traces to runs/<run_id>/raw.csv.",
  },
  {
    id: "P6",
    weeks: "Weeks 19\u201320",
    name: "Buffer and release",
    goal: "Make the result reproducible off the original machine.",
    outputs:
      "Camera-ready fixes, reproducibility package, Zenodo DOI, data card, release tag.",
    exit: "Clean-room reproduction on a second machine; archive deposited.",
  },
];

/* ------------------------------------------------------------------ */
/* Budget — ROADMAP.md §5                                              */
/* ------------------------------------------------------------------ */

export const budget = {
  items: [
    { item: "GPU compute", cost: "$0", note: "Local RTX 3060 Laptop 6 GB; optional H200 check is accuracy-only." },
    { item: "Electricity", cost: "~$2", note: "15\u201320 GPU-hours at ~100 W plus host overhead; indicative, not metered billing." },
    { item: "Plug-in wall meter", cost: "$25", note: "Cross-check on a 30-query subset per condition." },
    { item: "USB backup drive", cost: "$10", note: "Cold backup of raw runs, manifest, and checksums." },
    { item: "Contingency", cost: "$10", note: "Replacement fan/thermal paste or a spare SSD." },
    { item: "Total", cost: "\u2264 $47", note: "Hard cap. No rental, no paid API, no cloud inference." },
  ],
  computeHours: "15\u201320 local GPU-hours (incl. ~1.2\u20131.7 exploratory)",
  storage: "~5 GB on E: for raw data, processed parquet, run CSVs, and figures.",
  team: "3\u20134 people \u00b7 20 weeks",
} as const;

/* ------------------------------------------------------------------ */
/* Deliverables — ROADMAP.md §6                                        */
/* ------------------------------------------------------------------ */

export const deliverables = [
  "Open harness (MIT): installable rag_energy package, CLI, configs, and scripts.",
  "Frozen dataset IDs and manifest with versions, licenses, and SHA-256 checksums.",
  "Raw energy ledger: per-query CSV per run and the aggregated tracked ledger.",
  "Analysis scripts: reproducible bootstrap, non-inferiority, identity, policy, and power calculations.",
  "Preregistration and amendments.",
  "Paper draft and supplement, with every number mapped in artifacts/claims_evidence.csv.",
  "Reproducibility package: environment lock, model digests, config hashes, data checksums, clean-room script, Zenodo DOI.",
  "Data card covering provenance, sampling, licensing, and limits.",
  "Measurement protocol and runbook.",
  "Risk log, reviewed at every phase gate.",
];

/* ------------------------------------------------------------------ */
/* Risks — docs/RISKS.md                                               */
/* ------------------------------------------------------------------ */

export const risks: Array<{
  id: string;
  risk: string;
  likelihood: string;
  impact: string;
  mitigation: string;
}> = [
  {
    id: "R1",
    risk: "Strict EM vs lenient scoring decides the green verdict",
    likelihood: "High",
    impact: "High",
    mitigation:
      "Pre-register EM primary; report lenient span and F1 \u2265 0.5; require the qualitative conclusion to survive all three.",
  },
  {
    id: "R2",
    risk: "Reader strength / SQuAD saturation flattens the accuracy curve",
    likelihood: "Medium",
    impact: "High",
    mitigation: "1.5B and exploratory Llama 3B replication; 16k context probe; HotpotQA; reader-conditional results; no universal claim.",
  },
  {
    id: "R3",
    risk: "Single corpus / single retriever limits external validity",
    likelihood: "High",
    impact: "Medium",
    mitigation: "HotpotQA distractor; recall@k; state the boundary in every claim.",
  },
  {
    id: "R4",
    risk: "Thermal throttling changes the energy curve over the run",
    likelihood: "High",
    impact: "Medium",
    mitigation:
      "Randomize k within question; log temperature and clock; steady-state block calibration; first-50 sensitivity.",
  },
  {
    id: "R5",
    risk: "NVML coarse resolution makes per-query joules look precise",
    likelihood: "High",
    impact: "Medium",
    mitigation: "20-query blocks; repeat CV; wall-meter cross-check; sensor caveat in every table.",
  },
  {
    id: "R6",
    risk: "Ollama prefix cache confounds depth with request order",
    likelihood: "Medium",
    impact: "High",
    mitigation: "Unique 10-hex nonce per request; verify prefill times; invalidate rows without a nonce.",
  },
  {
    id: "R7",
    risk: "Energy noise swamps the effect",
    likelihood: "Medium",
    impact: "High",
    mitigation: "Idle subtraction; blocks; repeats; bootstrap; pre-registered MDE; wall meter.",
  },
  {
    id: "R8",
    risk: "Adaptive policy overfits 600 training questions",
    likelihood: "High",
    impact: "High",
    mitigation: "Strict 600/200/200 split; simple model; no test tuning; learning curve; feature-free baseline.",
  },
  {
    id: "R9",
    risk: "A binding gate defeats the tax test",
    likelihood: "Medium",
    impact: "High",
    mitigation: "Run taxes at a mid-accuracy gate as well; pre-register both; report gated and unconstrained optima.",
  },
  {
    id: "R10",
    risk: "Data licensing violation from redistributing text",
    likelihood: "Low",
    impact: "High",
    mitigation: "No raw text; release IDs, checksums, predictions, aggregates only; CC BY-SA notice.",
  },
  {
    id: "R11",
    risk: "Schedule slip on a 20-week plan",
    likelihood: "Medium",
    impact: "Medium",
    mitigation: "P6 buffer; drop the optional H200 check first, then the 16k probe or Llama 3B panel, before the boundary/1.5B; never drop the primary.",
  },
  {
    id: "R12",
    risk: "Scope creep into a universal-k* or carbon paper",
    likelihood: "Medium",
    impact: "Medium",
    mitigation: "Claim boundary in README/ROADMAP; out-of-scope list; amendment required for a new claim.",
  },
  {
    id: "R13",
    risk: "Model or dependency drift breaks reproduction",
    likelihood: "Medium",
    impact: "Medium",
    mitigation: "Lock file on target; model digest; config hash in registry; clean-room reproduction in P6.",
  },
  {
    id: "R14",
    risk: "Secret leak in a commit or run log",
    likelihood: "Low",
    impact: "High",
    mitigation: ".gitignore; secret scan before each push; private reporting; no tokens in configs.",
  },
  {
    id: "R15",
    risk: "Reader/model shopping creates a false replication",
    likelihood: "Medium",
    impact: "High",
    mitigation: "Pre-specify the exploratory panel; report all readers; no post-outcome promotion; H7/G5 unchanged.",
  },
  {
    id: "R16",
    risk: "16k context OOM or CPU offload invalidates the probe",
    likelihood: "Medium",
    impact: "High",
    mitigation: "Require 100% GPU and >300 MB headroom; record prompt tokens; reject truncation; report the hardware limit.",
  },
  {
    id: "R17",
    risk: "Cross-hardware divergence is mistaken for replication",
    likelihood: "Medium",
    impact: "High",
    mitigation: "H200 is accuracy-only; report hardware class; never pool with RTX 3060 energy.",
  },
  {
    id: "R18",
    risk: "Llama license or model-store growth",
    likelihood: "Low",
    impact: "Medium",
    mitigation: "Use the gated Llama 3.2 Community License; do not redistribute weights; record the digest; keep Q4 under storage limits.",
  },
];

/* ------------------------------------------------------------------ */
/* Decisions — docs/DECISIONS.md                                       */
/* ------------------------------------------------------------------ */

export const decisions = [
  {
    id: "D-001",
    date: "2026-11-09",
    title: "Repository name is energy-optimal-rag",
    summary:
      "Name states the object (retrieval depth) and the objective (energy), not the method (certification).",
    status: "accepted",
  },
  {
    id: "D-002",
    date: "2026-11-09",
    title: "All project storage stays on E:",
    summary:
      "Code, data, runs, and artifacts live under E:\\PROJECT\\energy-optimal-rag; the USB backup is the only off-volume copy.",
    status: "accepted",
  },
  {
    id: "D-003",
    date: "2026-11-09",
    title: "The static 2 pp claim is dead",
    summary:
      "The pilot selected k* = 32 at the boundary with P(k* optimal) = 0.61. The 2 pp margin remains only as an estimation target.",
    status: "accepted",
  },
  {
    id: "D-004",
    date: "2026-11-09",
    title: "5 pp non-inferiority is the primary decision",
    summary:
      "One-sided 5 pp EM non-inferiority at k = 4 vs k = 32, requiring at least 20% savings. No '5 pp certified' language before the rerun.",
    status: "accepted",
  },
  {
    id: "D-005",
    date: "2026-11-09",
    title: "Compute is local-only",
    summary:
      "No GPU rental, no paid API, no cloud inference. Cash cap: $47.",
    status: "accepted",
  },
  {
    id: "D-006",
    date: "2026-11-09",
    title: "No raw data, model weights, or secrets in the repository",
    summary:
      "Track the manifest, registry, ledger, and claims map only. Raw text, weights, run directories, and credentials stay out.",
    status: "accepted",
  },
  {
    id: "D-007",
    date: "2026-11-09",
    title: "The 78.8% oracle gain is an upper bound, not a result",
    summary:
      "In the pilot, the oracle chooses the cheapest correct depth with hindsight. No policy was trained. Reporting it as a learned-policy gain would be fabrication.",
    status: "accepted",
  },
  {
    id: "D-008",
    date: "2026-11-09",
    title: "prereg-freeze-v1 precedes the P1 confirmatory analysis",
    summary:
      "The freeze tag predates the new accuracy data. The analysis records the prereg hash and refuses on mismatch.",
    status: "accepted (pending freeze)",
  },
  {
    id: "D-009",
    date: "2026-11-11",
    title: "One analysis population and failure rule",
    summary:
      "A valid row requires a nonce, a completed request, and a clean power window. A failed or empty generation is a wrong answer and is retained. Descriptive statistics use every valid row at depth k; the primary paired test uses valid rows at both k = 4 and k = 32.",
    status: "accepted",
  },
  {
    id: "D-010",
    date: "2026-11-11",
    title: "5 pp pilot is a signal, not a certification",
    summary:
      "Use “pilot signal — not certified.” The proposal reports P = .537 for the 5 pp selection. The rerun must report the non-inferiority test and the selection probability separately. No “G2 passed” language.",
    status: "accepted",
  },
  {
    id: "D-011",
    date: "2026-11-11",
    title: "Pilot evidence is transcribed, not reproducible in-repo",
    summary:
      "The pilot raw CSVs are not in the repository. Every pilot claim is recorded in docs/PILOT_EVIDENCE.md and indexed in artifacts/claims_evidence.csv with run_id=pilot. A re-run is new evidence, not a reproduction.",
    status: "accepted",
  },
  {
    id: "D-012",
    date: "2026-11-14",
    title: "Third reader is exploratory; H7/G5 stay fixed",
    summary:
      "Llama 3.2 3B uses the same 500 SQuAD IDs as the 1.5B replication, 4k Q4, direction-only. It does not satisfy or change H7 or G5; no gate and no post-outcome promotion.",
    status: "accepted",
  },
  {
    id: "D-013",
    date: "2026-11-14",
    title: "Boundary context fix and diagnostic context probe",
    summary:
      "The boundary grid uses 8k so k=64 is not truncated. A separate Qwen3.5-4B 16k context-budget probe has a 4k control and is diagnostic, not a new k*. H200 is accuracy-only with no energy claim.",
    status: "accepted",
  },
];

/* ------------------------------------------------------------------ */
/* Theory — docs/IMPLEMENTATION_PLAN.md §10, docs/proposal.md §12      */
/* ------------------------------------------------------------------ */

export const theory = {
  assumptions: [
    {
      id: "A1",
      text: "Coverage: A(k) = 1 \u2212 (1 \u2212 A\u2080)(1 \u2212 p)^k, with A\u2080 \u2208 [0,1) and p \u2208 (0,1]. Each passage independently supplies the needed evidence with probability p. Stylized, not universal.",
    },
    {
      id: "A2",
      text: "Energy: J(k) = a + bk with a, b > 0. The pilot supports this (R\u00b2 = 0.9990) but rejects A1's global fit.",
    },
  ],
  theorems: [
    {
      id: "Theorem 1",
      title: "The optimal-depth identity",
      formula: "kJ\u2032(k) / J(k) = kA\u2032(k) / A(k)",
      body:
        "At an interior optimum, the energy elasticity equals the accuracy elasticity. The identity is scale-free and falsifiable, but local: the pilot validates it at k = 2 and rejects it as a global claim.",
      pilot:
        "Gap +0.044 at k = 2, 95% CI [\u22120.050, +0.128]. Gap +0.700 at k = 32.",
    },
    {
      id: "Theorem 2",
      title: "The price of static depth",
      formula: "E(static) / E(oracle) \u2192 1 + bK/a",
      body:
        "For any static depth there is a query mixture on which it is arbitrarily worse than a query-conditional policy at equal accuracy. An impossibility result, not a claim that a learned policy attains it.",
      pilot: "Motivates the oracle ceiling and the policy experiment; no learned policy exists yet.",
    },
    {
      id: "Theorem 3",
      title: "The certification threshold",
      formula: "N* = C_cert / [A(k*)(E(k\u2080) \u2212 E(k*))]",
      body:
        "Calibration beats a default only when the deployment is long enough to repay the sweep. Finding the depth is itself an energy purchase.",
      pilot:
        "Pilot sweep cost 49.6 kJ; N* = 876 for k = 4, 1,000 for k = 8, 1,489 for k = 16. Descriptive, not a deployment guarantee.",
    },
  ],
  counterexample: {
    setup: "a = 1, b = 0.02, K = {0,1,2,4}, A = (0.6, 0.9, 0.7, 1.0)",
    energies: "E = (1.667, 1.133, 1.486, 1.080)",
    lesson:
      "A local minimum at k = 1 and a lower global minimum at k = 4. A greedy policy stops at 1 and misses 4. Certification must search globally, or the method must test monotonicity and rerank/compress first.",
  },
  coverageFit: { a0: 0.324, p: 0.0218, r2: 0.332 },
  falsification: [
    "A wrong tax sign falsifies the affine/split model.",
    "An identity gap excluding zero at every interior depth falsifies the diagnostic.",
    "A non-monotone SQuAD curve falsifies global unimodality, though not the local identity.",
    "A policy capturing no material oracle fraction falsifies the practical value of adaptivity.",
  ],
} as const;

/* ------------------------------------------------------------------ */
/* Measurement — docs/MEASUREMENT.md, docs/IMPLEMENTATION_PLAN.md §7   */
/* ------------------------------------------------------------------ */

export const measurement = {
  decomposition: "J_k(q) = J_ret_k(q) + J_pre_k(q) + J_dec_k(q) + J_fix(q)",
  components: [
    {
      symbol: "J_ret",
      label: "Retrieval",
      body: "BM25 scoring, index lookup, and fetch. CPU proxy: wall time \u00d7 20 W single-thread active-above-idle.",
    },
    {
      symbol: "J_pre",
      label: "Prefill",
      body: "Prefill of the query plus k passages. Captured by NVML; the dominant term at high depth.",
    },
    {
      symbol: "J_dec",
      label: "Decode",
      body: "Decoding of the answer. Captured by NVML.",
    },
    {
      symbol: "J_fix",
      label: "Fixed",
      body: "Amortized model load and fixed per-query overhead. Partly captured by NVML.",
    },
  ],
  sensor: {
    library: "pynvml (nvidia-ml-py)",
    field: "power.draw",
    cadence: "100 ms",
    also: "utilization.gpu, memory.used, temperature.gpu, clocks.sm",
    caveat:
      "The 100 ms cadence is a sampling label. On the pilot laptop the driver updates power.draw coarsely, approximately once per second. Treat per-query energy as a paired observation, not a 100 ms precision measurement.",
  },
  integration: "J_gpu_raw(q) = max(0, trapz(power, time) \u2212 idle_power_w \u00d7 duration_s)",
  blockFormula:
    "factor_k = J_block_k / \u03a3_i J_gpu_raw(q_i, k)\nJ_gpu_calibrated(q, k) = factor_k \u00d7 J_gpu_raw(q, k)",
  controls: [
    {
      title: "Idle subtraction",
      value: "15.56 W",
      detail: "60 s pre-run baseline, CV 10.4%. Post-run 17.63 W, CV 15.9%.",
    },
    {
      title: "Block calibration",
      value: "20 queries",
      detail: "Back-to-back queries per depth. Pilot factors 1.041\u20131.188; largest at k = 2.",
    },
    {
      title: "Prefix-cache control",
      value: "10-hex nonce",
      detail: "A k = 32 request after k = 16 cut prefill from 710 ms to 247 ms. The nonce prevents reuse.",
    },
    {
      title: "Thermal control",
      value: "71.9 \u2192 88.4 \u00b0C",
      detail: "SM clock 1657 \u2192 1003 MHz; mean power 82.5 \u2192 54.2 W. Energy was stable.",
    },
    {
      title: "Repeatability",
      value: "3.80% median",
      detail: "Three blocks of 20 identical queries at k = 8; max CV 9.24%.",
    },
    {
      title: "Wall meter",
      value: "30-query subset",
      detail: "Whole-system cross-check. A factor far from 1 is reported, not hidden.",
    },
  ],
  derived: [
    "A(k) = mean(C_k), C_k \u2208 {0,1}",
    "J(k) = mean(J_k), joules per query",
    "E(k) = J(k) / A(k), as a ratio of sums",
    "S(k) = (J_ret + J_pre) / J(k), context-side share",
    "S_r(k) = J_ret / J(k), retrieval-only share",
    "\u03b5_J(k) = k J\u2032(k) / J(k), from the fitted affine model",
    "\u03b5_A(k) = k A\u2032(k) / A(k), from finite differences",
    "N* = C_cert / [A(k*)(E(k\u2080) \u2212 E(k*))]",
  ],
  checklist:
    "Every energy table states the sensor, cadence, idle baseline and its CV, block factors, repeat CV, CPU proxy watts, wall-meter factor, GPU model, driver, power mode, and reader/model digest.",
} as const;

/* ------------------------------------------------------------------ */
/* Data — docs/DATA_CARD.md                                            */
/* ------------------------------------------------------------------ */

export const datasets = {
  squad: {
    name: "SQuAD v1.1 dev",
    role: "Primary controlled QA",
    upstreamQuestions: 10570,
    upstreamContexts: 20958,
    usedPrimary: 1000,
    usedReplication: 500,
    usedBoundary: 200,
    corpus: "20,958 contexts \u2192 45,651 70-word passages",
    retriever: "BM25 Okapi, top-32",
    license: "CC BY-SA 4.0",
    primaryMetric: "Normalized EM",
    secondaryMetrics: "Lenient span, token F1 \u2265 0.5",
    meanPassageWords: 53.4,
    goldOutsideCapPct: 12,
    note:
      "The closed corpus isolates depth: changing k changes how much evidence reaches the reader, not which corpus is searched. That is a strength for mechanism and a weakness for external validity.",
    recallNote:
      "About 12% of questions have gold evidence outside the top-32 cap, which caps accuracy at 0.88 and adds a final jump at k = 32 that a full-corpus retriever would not show.",
  },
  hotpot: {
    name: "HotpotQA distractor dev",
    role: "Multi-hop / distractor stress",
    upstreamQuestions: 7405,
    used: 500,
    paragraphs: 10,
    goldParagraphs: 2,
    distractors: 8,
    corpus: "10 paragraphs per question; no pooling across questions",
    retriever: "BM25 Okapi, top-10",
    depths: [0, 1, 2, 4, 8, 10],
    license: "CC BY-SA 4.0",
    primaryMetric: "Normalized EM",
    note:
      "It is the cheapest available stress test for multi-hop evidence and distractor-induced non-monotonicity. The Theorem 1 unimodality assumption is most likely to fail here.",
    recallNote:
      "BM25 over 10 paragraphs is a weak retriever for multi-hop questions. The condition is a stress test, not a leaderboard entry.",
  },
  processing: [
    "Normalization: lowercase, strip punctuation and articles, collapse whitespace.",
    "Chunking: whitespace tokens, 70 words, no overlap (SQuAD); whole paragraphs (HotpotQA).",
    "Seed 20261115 for sampling and the deterministic policy split.",
    "Policy split 600 / 200 / 200 by SHA-256 of seed:question_id.",
    "No test-set tuning. The test split is evaluated once.",
    "Raw and processed text live in data/raw/ and data/processed/, both git-ignored.",
  ],
  limits: [
    "One closed corpus and one multi-hop distractor set; no open-domain NQ or fullwiki run.",
    "BM25 only in the primary condition; no dense retriever.",
    "English only.",
    "One 4B primary reader, one 1.5B confirmatory replication reader, and one exploratory 3B reader; no frontier model.",
    "SQuAD is saturated for strong readers; the pilot's 4B reader is the binding constraint. The Llama 3B panel is a reader-family check, not a universal depth.",
    "The 16k context-budget probe is a separate diagnostic on the same laptop GPU; 16k fits at 100% GPU, while 32k offloads to CPU.",
    "The energy measurements are from one laptop GPU, not a datacenter. The optional H200 64k check is accuracy-only with no power telemetry.",
  ],
} as const;

/* ------------------------------------------------------------------ */
/* Scoring, policy, taxes — docs/IMPLEMENTATION_PLAN.md §6, §8–9,      */
/* prereg/PREREGISTRATION.md §4–5                                     */
/* ------------------------------------------------------------------ */

export const scoring = [
  {
    id: "Primary",
    rule: "Normalized EM",
    detail: "Lowercase, strip punctuation and articles, collapse whitespace.",
  },
  {
    id: "Secondary",
    rule: "Lenient span match",
    detail: "Normalized gold appears in a short prediction.",
  },
  {
    id: "Secondary",
    rule: "Token F1 \u2265 0.5",
    detail: "The qualitative conclusion must survive all three rules, or the dependence is reported.",
  },
] as const;

export const policy = {
  features: [
    "BM25 top score",
    "Second score",
    "Score gap",
    "Mean and standard deviation",
    "Score entropy",
    "Number of positive scores",
    "Question length",
    "Question type",
  ],
  model: "Cost-sensitive classifier or shallow decision tree predicting the cheapest depth whose predicted correctness clears the gate.",
  evaluation:
    "Evaluate at matched accuracy against the best static k; report the fraction of the oracle gap captured on the same held-out questions.",
  split:
    "600 train / 200 validation / 200 test by SHA-256 of seed:question_id. These are target counts; hashed assignment can produce slightly different realized counts, which are reported. No test-set tuning.",
  guardrails: [
    "No gold answer, post-generation signal, or depth label enters the features.",
    "Validation selects the model and operating point; test is touched once.",
    "A policy that captures < 50% is a reported negative; the static result can stand without it.",
  ],
} as const;

export const taxes = {
  fixed: {
    label: "Fixed tax",
    change: "Adds 10\u201330% of a = 15.74 J before generation; configured at 3.148 J (20%).",
    prediction: "k* increases.",
  },
  perPassage: {
    label: "Per-passage tax",
    change: "Adds 10\u201330% of b = 2.283 J per retrieved passage; configured at 0.457 J (20%).",
    prediction: "k* decreases.",
  },
  design:
    "150 questions per condition, the same seven depths, and a mid-accuracy gate where the optimum is interior. Gated and unconstrained optima are both reported.",
  falsification:
    "A wrong tax sign falsifies the affine/split model. Because a binding gate can mask movement, the mid-accuracy condition is pre-registered, not post-hoc.",
} as const;

/* ------------------------------------------------------------------ */
/* Prior work — docs/proposal.md §5                                    */
/* ------------------------------------------------------------------ */

export const priorWork = [
  {
    work: "Pan et al. \u00b7 NeurIPS 2025 MLForSys",
    optimize: "Accuracy\u2013energy landscape",
    relation:
      "Reports that \u2264 3% accuracy differences span up to 20.2\u00d7 energy. No E(k) = J/correct, gated k*, policy, or calibration decision; workshop, cloud models.",
  },
  {
    work: "Hwang \u00b7 OpenReview, 2026",
    optimize: "Tokens",
    relation:
      "Adapts depth/context from query difficulty for lower token cost. Unrefereed; no joules, k*, or guarantee.",
  },
  {
    work: "Hashemi et al. \u00b7 arXiv:2510.15719",
    optimize: "Latency",
    relation:
      "Cost-aware RL reports ~16\u201320% lower latency. Optimizes latency, not joules; no k* or guarantee.",
  },
  {
    work: "Feric et al. \u00b7 RAGMark, arXiv:2609.05760",
    optimize: "Per-stage power",
    relation:
      "Benchmarks per-stage power and reports up to 66% lower energy from context reduction. Does not measure joules per correct answer or certify a depth.",
  },
  {
    work: "Song et al. \u00b7 ECML PKDD 2026",
    optimize: "Retrieval quality",
    relation:
      "Tail-Aware Adaptive-k adapts k for retrieval quality. No joules-per-correct-answer estimand.",
  },
  {
    work: "Taguchi et al. \u00b7 EMNLP 2025",
    optimize: "Tokens",
    relation:
      "Adaptive-k for long-context QA without tuning or iteration. Optimizes tokens/context, not energy per correct answer.",
  },
  {
    work: "Gao et al. \u00b7 Token Arena, arXiv:2605.00300",
    optimize: "Joules per correct answer",
    relation:
      "Reports joules per correct answer at endpoint granularity but does not optimize retrieval depth.",
  },
];

export const contributions = [
  {
    title: "Gated estimand",
    body:
      "E(k) = E[J_k] / E[C_k], total joules over total correct answers, with a pre-registered accuracy floor. The gate stops the ratio from rewarding cheap failure.",
  },
  {
    title: "Optimal-depth identity",
    body:
      "At an interior optimum, kJ\u2032/J = kA\u2032/A. For affine energy the left side is the variable energy share \u2014 a scale-free, falsifiable local diagnostic.",
  },
  {
    title: "Price-of-static-depth bound",
    body:
      "For any static depth there is a query mixture on which it is arbitrarily worse than a query-conditional policy at equal accuracy.",
  },
  {
    title: "Certification-cost threshold",
    body:
      "Calibration beats a default only when N > N* = C_cert / [A(k*)(E(k\u2080) \u2212 E(k*))]. Finding the depth is itself an energy purchase.",
  },
  {
    title: "Causal energy-tax test",
    body:
      "A fixed dummy computation raises a; a per-passage one raises b, with reader, prompt, passages, and answers unchanged. The predicted signs are falsifiable.",
  },
  {
    title: "Learned adaptive policy",
    body:
      "A small cost-sensitive model uses cheap pre-generation features and is tested once on held-out questions at matched accuracy.",
  },
];

export const priorWorkNote =
  "Search to 8 November 2026; re-run before submission. We do not claim the metric, adaptive depth, or bandit machinery as new. The combination \u2014 gated E(k), identity, static-depth bound, N*, causal split test \u2014 is absent from the papers found.";

/* ------------------------------------------------------------------ */
/* References — docs/proposal.md §19                                   */
/* ------------------------------------------------------------------ */

export const references = {
  priorWork: [
    {
      id: "R1",
      text: "Lewis, P., et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.",
    },
    {
      id: "R2",
      text: "Jeong, S., et al. Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity. NAACL 2024, pp. 7036\u20137050. DOI 10.18653/v1/2024.naacl-long.389.",
    },
    {
      id: "R3",
      text: "Pan, M., et al. Towards Automatically Optimizing Retrieval Augmented AI Systems. NeurIPS 2025 MLForSys Workshop. OpenReview an17DUVvuS.",
    },
    {
      id: "R4",
      text: "Hwang, M. Query Complexity\u2013Aware Adaptive Retrieval for Cost-Efficient Retrieval-Augmented Generation. OpenReview direct upload, 2026. ObkC4BCAFt.",
    },
    {
      id: "R5",
      text: "Hashemi, H., R\u00fchle, V., Rajmohan, S. Cost-Aware Retrieval-Augmentation Reasoning Models with Adaptive Retrieval Depth. arXiv:2510.15719, 2025.",
    },
    {
      id: "R6",
      text: "Feric, Z., et al. RAGMark: A Comprehensive Framework for Benchmarking Retrieval-Augmented Generation Systems. arXiv:2609.05760, 2026.",
    },
    {
      id: "R7",
      text: "Song, Z., et al. Tail-Aware Adaptive-k: Query-Adaptive Context Selection for Retrieval-Augmented Generation. ECML PKDD 2026, LNCS LNAI 16944, pp. 193\u2013209. DOI 10.1007/978-3-032-37667-1_12.",
    },
    {
      id: "R8",
      text: "Taguchi, C., Maekawa, S., Bhutani, N. Efficient Context Selection for Long-Context QA: No Tuning, No Iteration, Just Adaptive-k. EMNLP 2025, pp. 20105\u201320130. DOI 10.18653/v1/2025.emnlp-main.1017.",
    },
    {
      id: "R9",
      text: "Gao, Y., Wang, M., Yu, Y. L. Token Arena: A Continuous Benchmark Unifying Energy and Cognition in AI Inference. arXiv:2605.00300, 2026.",
    },
  ],
  dataTools: [
    {
      id: "D1",
      text: "Rajpurkar, P., et al. SQuAD: 100,000+ Questions for Machine Comprehension of Text. EMNLP 2016, pp. 2383\u20132392. DOI 10.18653/v1/D16-1264.",
    },
    {
      id: "D2",
      text: "Yang, Z., et al. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. EMNLP 2018. DOI 10.18653/v1/D18-1259.",
    },
    {
      id: "D3",
      text: "Robertson, S., Zaragoza, H. The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval 3(4), 333\u2013389, 2009. DOI 10.1561/1500000019.",
    },
  ],
} as const;

/* ------------------------------------------------------------------ */
/* Site navigation                                                     */
/* ------------------------------------------------------------------ */

export const navItems = [
  { href: "/research", label: "Research", index: "01" },
  { href: "/method", label: "Method", index: "02" },
  { href: "/results", label: "Results", index: "03" },
  { href: "/roadmap", label: "Roadmap", index: "04" },
  { href: "/about", label: "About", index: "05" },
] as const;
