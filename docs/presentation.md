# Presentation Script — Energy-Optimal Retrieval Depth in RAG

**Course:** EEE 4261 — Green Computing, Section C  
**Deck:** 12 slides (11 presented + 1 reference slide)  
**Total target:** 9 minutes 20 seconds (safe for an 8–10 minute slot)  
**Buffer:** about 40 seconds for handoffs and pauses

> [!NOTE]
> এই script-এ `[স্লাইড ২]` মানে ওই স্লাইডে যাওয়া। বড় বাক্যগুলো ভেঙে ভেঙে বলবেন। সংখ্যাগুলো বলার পরে এক সেকেন্ড থামবেন।

---

## 1. কে কোন স্লাইড বলবে

| ক্রম | সদস্য | স্লাইড | বিষয় | সময় |
|---:|---|---|---|---:|
| 1 | **Pratay Paul** | 1–3 | Title + Introduction & Problem Statement + Motivation & Research Gap | 2:15 |
| 2 | **Md. Sarowar Alam Sourov** | 4–5 | Objectives & Scope + Dataset | 1:50 |
| 3 | **Md. Atikur Rahaman** | 6–7 | Proposed Method + Methodology Flow | 1:50 |
| 4 | **Sadman Ifaz** | 8–9 | Experimental Setup + Analysis & Gates | 1:45 |
| 5 | **Jayed Bin Khalid** | 10–11 | Expected Results + Applications, Risks & Conclusion | 1:40 |

**Slide 12 — References:** কেউ উপস্থাপন করবে না। প্রশ্নের সময় দরকার হলে দেখানো যাবে।

### Time check

| সময় | কী হবে |
|---:|---|
| 0:00 | Pratay শুরু করবে |
| 2:15 | Sourov শুরু করবে |
| 4:05 | Atik শুরু করবে |
| 5:55 | Sadman শুরু করবে |
| 7:40 | Jayed শুরু করবে |
| 9:20 | শেষ |
| 9:20–10:00 | প্রশ্ন-উত্তর শুরু |

---

## 2. Pratay Paul — 2:15

### Slide 1 — Title (0:00–0:25)

[স্লাইড ১]

শুভ দিন, স্যার। আমি প্রতয় পল। আমাদের টিমের পক্ষ থেকে আপনাদের স্বাগতম। আমাদের টিমে আছেন আতিকুর, সারোয়ার, সাদমান, জায়েদ এবং আমি।

আমাদের প্রজেক্টের নাম: **Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation**।

সহজ ভাষায়: RAG-এ আমরা কতগুলো passage পড়ব, সেটা এমনভাবে বাছাই করতে চাই যাতে **প্রতি সঠিক উত্তরের energy cost সবচেয়ে কম** হয়।

### Slide 2 — Introduction & Problem Statement (0:25–1:25)

[স্লাইড ২]

RAG-এর ধাপগুলো দেখুন। প্রথমে প্রশ্ন আসে। তারপর BM25 দিয়ে কিছু passage খোঁজা হয়। এরপর k-টি passage reader-কে দেওয়া হয়। Reader মানে যে model passage পড়ে উত্তর তৈরি করে। শেষে উত্তর আসে।

এখানে **k হলো retrieval depth** — অর্থাৎ reader কতগুলো passage দেখবে।

More passages মানে বেশি evidence। Accuracy বাড়তে পারে, কিন্তু energy খরচও বাড়ে। Fewer passages মানে energy কম, কিন্তু উত্তর ভুল হতে পারে। তাই শুধু accuracy বা শুধু energy দেখলে সঠিক depth পাওয়া যায় না।

আমরা মাপি: **E(k) = ΣJ_k / ΣC_k**।

এখানে **J_k** হলো depth k-তে এক প্রশ্নের energy; **C_k** হলো ১ যদি উত্তর সঠিক হয়, ০ যদি ভুল হয়; **Σ** হলো সব প্রশ্নের যোগফল। সহজভাবে: **মোট energy ÷ মোট সঠিক উত্তর**।

আমরা k বাছাই করি একটি **accuracy floor**-এর নিচে না গিয়ে। ৫ accuracy point মানে ৫ percentage point, সংক্ষেপে **pp**।

### Slide 3 — Motivation & Research Gap (1:25–2:15)

[স্লাইড ৩]

Motivation: pilot study-তে **k=32**-এ প্রতি সঠিক উত্তরের energy **k=1**-এর তুলনায় **3.45 গুণ** বেশি। k=32-এ energy-এর **85.1%** যায় passage পড়ার পেছনে। Accuracy 4 থেকে 16 passage পর্যন্ত প্রায় flat থাকে। আর 5 pp margin-এ **k=4**-এ savings **69.3%**। এগুলো early result, final নয়।

এই table-এ দেখুন: static top-k শুধু accuracy দেখে; adaptive-k token বা latency দেখে; energy benchmark শুধু power বা energy দেখে। কিন্তু কেউ একসাথে **energy per correct answer, accuracy floor, break-even, আর policy** দেখে না। এটাই আমাদের research gap।

[হ্যান্ডঅফ] এখন সারোয়ার আলম সৌরভ Objectives ও Dataset নিয়ে বলবেন।

---

## 3. Md. Sarowar Alam Sourov — 1:50

### Slide 4 — Objectives & Scope (2:15–3:10)

[স্লাইড ৪]

ধন্যবাদ। আমি সারোয়ার আলম সৌরভ।

আমাদের তিনটি প্রশ্ন।

**এক: Static depth।** কোন k-তে E(k) সবচেয়ে কম, যদি k=32-এর থেকে 5 pp-এর বেশি accuracy না কমি? এটি H1–H4 এবং H7 replication পরীক্ষা করে।

**দুই: Adaptivity।** প্রতিটি প্রশ্নের জন্য আলাদা k বেছে নিলে কি best static depth-এর সমান accuracy রাখা যায়? এটি H5।

**তিন: Cause and cost।** Energy tax দিলে k* predicted দিকে যায় কি না, আর measurement sweep তার energy ফেরত দেয় কি না? এটি H6, আর N* break-even।

**H1–H7** হলো সাতটি hypothesis। **H মানে hypothesis** — একটি পরীক্ষামূলক statement, যার clear pass/fail rule আছে।

আমরা 5 pp rule, ≥20% savings, energy–accuracy link, passage share, policy, এবং tax signs পরীক্ষা করব। আমরা universal k*, 2 pp optimum, বা rerun-এর আগে certified 5 pp result claim করব না।

### Slide 5 — Dataset (3:10–4:05)

[স্লাইড ৫]

প্রথম dataset: **SQuAD** — Stanford Question Answering Dataset — v1.1 dev। এতে 10,570 প্রশ্ন, 20,958 context, এবং 45,651 passage আছে। আমরা BM25 top-32 ব্যবহার করব।

আমাদের primary run 1,000 প্রশ্ন, replication 500, boundary 200। Metric exact match; license CC BY-SA 4.0।

দ্বিতীয় dataset: **HotpotQA** — multi-hop question answering dataset। distractor version-এ 7,405 প্রশ্ন; আমরা 500 ব্যবহার করব। প্রতি প্রশ্নে 10 paragraph: 2 gold + 8 distractor। k = 0, 1, 2, 4, 8, 10; BM25 top-10।

SQuAD depth isolate করে; HotpotQA multi-hop ও distractor stress test করে।

[হ্যান্ডঅফ] এখন আতিকুর রাহামান Proposed Method ও Methodology Flow নিয়ে বলবেন।

---

## 4. Md. Atikur Rahaman — 1:50

### Slide 6 — Proposed Method (4:05–5:10)

[স্লাইড ৬]

ধন্যবাদ। আমি আতিকুর রাহামান।

Method-এ চারটি idea।

**এক: Energy per correct answer।** E(k) = ΣJ_k / ΣC_k, accuracy floor দিয়ে gated। Read as: total energy ÷ total correct answers।

**দুই: Energy–accuracy link।** k J′(k) / J(k) = k A′(k) / A(k)। Best depth-এ energy ও accuracy একই percentage-এ বদলায়। J′ ও A′ হলো rate of change।

**তিন: Break-even।** N* = C_cert / [A(k*)(E(k₀) − E(k*))]। N* মানে কতগুলো প্রশ্নের পরে sweep-এর energy সাশ্রয় তার খরচের চেয়ে বেশি। C_cert হলো sweep energy, k₀ default depth, k* best depth।

**চার: Energy-cost test।** Fixed cost (a) k* বাড়ায়; per-passage cost (b) k* কমায়। উল্টো sign হলে model ভুল।

Baseline হলো একটাই fixed top-k, শুধু accuracy বা speed দেখে tune করা। আমাদের proposal হলো accuracy floor-এর মধ্যে energy per correct answer দিয়ে depth বাছাই করা।

### Slide 7 — Methodology Flow (5:10–5:55)

[স্লাইড ৭]

এই slide-এ experiment-এর flow।

উপরে pipeline: Prepare SQuAD ও HotpotQA → Index BM25 → Sweep ৭টি depth → Measure NVML ও block → Score exact match ও bootstrap → Analyze E(k), N*, policy।

নিচে decision flow: Freeze plan → Small re-run 200 প্রশ্ন → Full re-run 1,000 × 7 → Checkpoints G1–G5 ও K1–K7 → More tests: replication, policy, theory।

মূল কথা: **run হলো measurement, checkpoint হলো decision**।

[হ্যান্ডঅফ] এখন সাদমান ইফাজ Experimental Setup ও Analysis-এর Gates নিয়ে বলবেন।

---

## 5. Sadman Ifaz — 1:45

### Slide 8 — Experimental Setup (5:55–6:50)

[স্লাইড ৮]

ধন্যবাদ। আমি সাদমান ইফাজ।

Setup-এ runs: SQuAD 1,000 × 7; Qwen2.5-1.5B 500 × 7; HotpotQA 500 × 6; boundary 200 × 3; taxes 150 × 2।

Measurement: NVML প্রতি 100 ms-এ power পড়ে। 60 সেকেন্ড idle baseline; 20 প্রশ্নের block; প্রতিটি request-এ unique code, যাতে cached prompt না আসে; heat ও speed log; wall meter; repeat block।

Decision: k=4, k=32-এর থেকে 5 pp-এর বেশি খারাপ নয় — এটা **non-inferiority, NI**; অন্তত 20% energy savings; 5% one-sided false-positive limit; 10,000 resamples। 2-point rule শুধু estimate।

Budget: **15–20 GPU hours**, RTX 3060 6 GB, একসাথে একটাই job, wall power, screen off।

### Slide 9 — Analysis & Gates (6:50–7:40)

[স্লাইড ৯]

এখন Analysis ও Gates।

**G মানে go** — checkpoint pass হলে এগিয়ে যাব। **K মানে stop/reframe** — fail হলে report করে claim বদলাব। **H মানে hypothesis** — পরীক্ষার statement।

Main decision: k=4, k=32-এর থেকে 5 pp-এর বেশি খারাপ নয়, এবং অন্তত 20% energy savings। Formula: **A(4) − A(32) > −5 pp · savings ≥ 20%**। 5% one-sided false-positive limit, 10,000 resamples। P(k*) হলো সম্ভাবনা যে বাছাই করা depth-টাই সত্যিই সবচেয়ে ভালো।

Go gates: G1 5-point rule + ≥20%; G2 upper confidence bound ≤5 points এবং P(k*) ≥ 0.8; G3 energy on passages 10–70%; G4 best-possible gain ≥20%, policy ≥50%; G5 replication।

Stop gates: K1 energy effect <10%; K2 best depth boundary-তে; K3 P(k*) < 0.8; K4 energy on passages <5%; K5 best depth 1-এর বেশি নড়ে; K6 best-possible gain <15%; K7 repeat error >20%।

কোনো checkpoint fail করলে আমরা সেটা report করি এবং claim বদলাই।

[হ্যান্ডঅফ] এখন জায়েদ বিন খালিদ Expected Results ও Conclusion নিয়ে বলবেন।

---

## 6. Jayed Bin Khalid — 1:40

### Slide 10 — Expected Results (7:40–8:25)

[স্লাইড ১০]

ধন্যবাদ। আমি জায়েদ বিন খালিদ।

Expected results:

- **H1** — energy linear: R² ≥ 0.95 এবং lack-of-fit test 5%-এ fail না করলে pass।
- **H2** — main decision: k=4 5 pp-এর মধ্যে এবং ≥20% savings।
- **H3–H4** — 95% confidence range-এ 0 থাকবে; energy share on passages 10–70% এবং বাড়বে।
- **H5–H6** — best-possible gain ≥20%, policy ≥50%, fixed cost k* বাড়াবে, per-passage cost কমাবে।
- **H7** — Qwen2.5-1.5B বা HotpotQA-তে replication।

Null result-ও result।

### Slide 11 — Applications, Risks & Conclusion (8:25–9:20)

[স্লাইড ১১]

Applications: green RAG serving ও capacity planning; ছোট GPU ও edge device; energy-aware benchmark; accuracy-margin policy; open harness।

Risks: exact match vs lenient scoring; reader strength ও এক dataset; GPU heat ও power sensor limit; cached prompt ও policy overfitting; budget 15–20 GPU hours, ≤$47।

আমাদের proposal তিনটি:

1. Accuracy floor-এর মধ্যে energy per correct answer দিয়ে depth বাছাই।
2. Energy cost দিয়ে causal test।
3. প্রতি প্রশ্নে আলাদা depth বেছে নেওয়া policy, matched accuracy-তে।

আমরা 1,000 প্রশ্নের study চালিয়ে result report করতে চাই — positive বা null।

ধন্যবাদ, স্যার। প্রশ্ন থাকলে আমরা উত্তর দিতে প্রস্তুত।

---

# Q&A — স্যারের সম্ভাব্য প্রশ্ন ও বাংলা উত্তর

> [!TIP]
> উত্তর শুরু করার আগে এক সেকেন্ড থামুন। তারপর প্রথম বাক্যে সরাসরি উত্তর দিন। বিস্তারিত লাগলে স্লাইডে ফিরে যান।

## A. Basic definitions

### ১. `k` কী?

**উত্তর:** `k` হলো retrieval depth — reader-কে কতগুলো passage দেওয়া হচ্ছে। `k=4` মানে reader ৪টি passage দেখছে; `k=32` মানে ৩২টি passage দেখছে। স্লাইড ২-এ এটি দেখানো আছে।

### ২. `E(k)` কী?

**উত্তর:** `E(k)` হলো প্রতি সঠিক উত্তরের energy। এটি মোট energy-কে মোট সঠিক উত্তর দিয়ে ভাগ করে। সহজভাবে: **total energy ÷ total correct answers**। স্লাইড ২ ও ৬-এ সূত্রটি আছে।

### ৩. `J_k` ও `C_k` কী?

**উত্তর:** `J_k` হলো depth `k`-তে এক প্রশ্নের energy। `C_k` হলো ১ যদি উত্তর সঠিক হয়, ০ যদি ভুল হয়। `Σ` মানে সব প্রশ্নের যোগফল।

### ৪. `pp` কী?

**উত্তর:** `pp` মানে **percentage point**। ৫ pp মানে ৫ accuracy point — এটি ৫% relative নয়। উদাহরণ: accuracy ৮০% থেকে ৭৫% হলে ৫ pp কমে।

### ৫. `EM` কী?

**উত্তর:** `EM` মানে **exact match**। Predicted answer এবং gold answer হুবহু মিললে ১, না মিললে ০। আমাদের primary metric exact match।

### ৬. `NI` কী?

**উত্তর:** `NI` মানে **non-inferiority** — অর্থাৎ নতুনটি পুরোনোটির চেয়ে নির্দিষ্ট margin-এর বেশি খারাপ নয়। এখানে `k=4`, `k=32`-এর থেকে ৫ pp-এর বেশি খারাপ না হলে NI pass।

### ৭. `P(k*)` কী?

**উত্তর:** `P(k*)` হলো bootstrap probability যে আমরা বাছাই করা depth-টাই সত্যিই সবচেয়ে ভালো। G2-তে `P(k*) ≥ 0.8` দরকার; K3-তে `P(k*) < 0.8` হলে stop/reframe।

### ৮. `R²` কী?

**উত্তর:** `R²` হলো goodness of fit — model data-কে কতটা ভালোভাবে ব্যাখ্যা করছে। H1-এ `R² ≥ 0.95` এবং lack-of-fit test ৫%-এ fail না করলে pass।

### ৯. `N*` কী?

**উত্তর:** `N*` হলো break-even প্রশ্নের সংখ্যা — কতগুলো প্রশ্নের পরে measurement sweep-এর energy সাশ্রয় তার খরচের চেয়ে বেশি হয়। স্লাইড ৬-এ সূত্রটি আছে।

### ১০. `C_cert`, `k₀`, `k*` কী?

**উত্তর:** `C_cert` হলো sweep-এর energy cost। `k₀` হলো default depth। `k*` হলো selected বা best depth।

### ১১. `a` ও `b` কী?

**উত্তর:** Energy model `J(k) = a + bk`-তে `a` হলো fixed cost, `b` হলো per-passage cost। Fixed cost বাড়লে `k*` বাড়ে; per-passage cost বাড়লে `k*` কমে। উল্টো sign হলে model ভুল।

## B. Gates and hypotheses

### ১২. `G1–G5` কী?

**উত্তর:** এগুলো **go gates** — pass হলে পরের ধাপে যাব।

- G1: ৫ pp non-inferiority + ≥20% energy savings
- G2: upper confidence bound ≤5 pp এবং `P(k*) ≥ 0.8`
- G3: energy on passages 10–70%
- G4: best-possible gain ≥20%, policy capture ≥50%
- G5: Qwen2.5-1.5B বা HotpotQA-তে replication

### ১৩. `K1–K7` কী?

**উত্তর:** এগুলো **stop/reframe gates** — fail হলে result report করব এবং claim বদলাব।

- K1: energy effect <10%
- K2: best depth boundary-তে
- K3: `P(k*) < 0.8`
- K4: energy on passages <5%
- K5: best depth ১-এর বেশি নড়ে
- K6: best-possible gain <15%
- K7: repeat error >20%

### ১৪. `H1–H7` কী?

**উত্তর:** সাতটি hypothesis:

- H1: energy depth-এ affine
- H2: ৫ pp primary decision
- H3: optimal-depth identity
- H4: passage-energy share
- H5: query-conditional policy
- H6: energy-tax signs
- H7: replication

প্রতিটির pass/fail rule স্লাইড ১০-এ আছে।

### ১৫. `H` কী?

**উত্তর:** `H` মানে **hypothesis** — একটি পরীক্ষামূলক statement, যার clear pass/fail rule আছে। যেমন H2 বলে `k=4` কি `k=32`-এর থেকে ৫ pp-এর বেশি খারাপ নয়।

### ১৬. `G` ও `K` কী?

**উত্তর:** `G` মানে **go** — checkpoint pass হলে এগিয়ে যাব। `K` মানে **stop/reframe** — fail হলে report করে claim বদলাব। স্লাইড ৯-এ এটি লেখা আছে।

## C. Project design

### ১৭. প্রাইমারি reader কোনটি? কেন Qwen2.5-1.5B?

**উত্তর:** প্রাইমারি reader **Qwen3.5-4B** — এটি local Ollama-তে Q4, 4096 context-এ installed। Replication reader **Qwen2.5-1.5B-Instruct** — ভিন্ন family ও size, তাই external validity বেশি। একই 4B দিয়ে করলে সেটা replication নয়, repeat হতো।

### ১৮. `5 pp` কেন, `2 pp` নয়?

**উত্তর:** `2 pp` static claim-টি dead — pilot-এ `P(k*)=0.61`, যা G2-এর 0.8-এর নিচে। তাই 2 pp শুধু estimation target, hypothesis নয়। `5 pp` হলো pre-registered primary margin, সঙ্গে ≥20% savings। এটি এখনো pilot signal, certified result নয়।

### ১৯. `69.3%` কী?

**উত্তর:** Pilot study-তে ৫ pp margin-এ `k=4`-এ `k=32`-এর তুলনায় energy savings 69.3%। এটি early result — powered rerun-এ যাচাই করতে হবে।

### ২০. `78.8%` কী?

**উত্তর:** এটি pilot-এর **oracle upper bound** — matched accuracy-তে সবচেয়ে ভালো সম্ভাব্য gain। কোনো learned policy এখনো train করা হয়নি, তাই এটি learned-policy result নয়। H5/G4 এই upper bound-এর দিকে তাকায়।

### ২১. Universal `k*` আছে কি?

**উত্তর:** না। Optimal depth নির্ভর করে reader, dataset, accuracy floor, এবং energy cost-এর উপর। আমরা universal `k*` claim করি না; আমরা একটি **decision rule** estimate করি।

### ২২. `k=4` কি `k*`?

**উত্তর:** না। `k=4` হলো ৫ pp rule-এর pre-registered candidate। `k*` হলো estimated best depth। Pilot-এ `k*` boundary-তে ছিল এবং `P(k*)=0.61`; final rerun-এ এটি estimate হবে।

### ২৩. Gate fail করলে কী হবে?

**উত্তর:** আমরা result report করব এবং claim বদলাব। K1–K4 ও K6 kill/reframe; K5 ও K7 measurement/framing fix করার সুযোগ। Negative result-ও একটি result।

### ২৪. কেন SQuAD ও HotpotQA?

**উত্তর:** SQuAD-এর closed corpus depth isolate করে — retriever বদলায় না, শুধু `k` বদলায়। HotpotQA multi-hop reasoning ও distractors যোগ করে, তাই external validity stress test হয়।

### ২৫. কেন BM25?

**উত্তর:** BM25 হলো একটি fixed lexical retriever — Best Matching 25। এটি fixed রাখলে depth-এর effect পরিষ্কার দেখা যায়। Retriever বদলালে depth-এর সঙ্গে retrieval quality মিশে যেত।

### ২৬. `n=1,000` কেন?

**উত্তর:** ৫ pp decision-এর precision ও power-এর জন্য primary run `n=1,000`। Pilot `n=200` accuracy-এর জন্য underpowered ছিল। Replication 500, boundary 200।

### ২৭. `20%` savings কেন?

**উত্তর:** G1-এর practical threshold হলো `k=32`-এর তুলনায় অন্তত ২০% energy savings। কম savings হলে depth বদলানোর engineering benefit প্রশ্নবিদ্ধ।

### ২৮. Measurement কীভাবে করবেন?

**উত্তর:** NVML প্রতি 100 ms-এ GPU power পড়ে। 60 সেকেন্ড idle baseline নিই; 20 প্রশ্নের block-এ measure করি; প্রতিটি request-এ unique code দিই যাতে cached prompt না আসে; wall meter দিয়ে total energy check করি; heat ও speed log করি; একটি block repeat করি noise দেখতে।

### ২৯. `10,000 bootstrap` কেন?

**উত্তর:** Paired accuracy ও energy-এর uncertainty estimate করতে এবং `P(k*)` বের করতে 10,000 bootstrap resamples ব্যবহার করি।

### ৩০. `5% one-sided` কেন?

**উত্তর:** Non-inferiority test-এ one-sided alpha 0.05 ব্যবহার করি — অর্থাৎ 95% confidence level-এ `k=4` যে ৫ pp-এর বেশি খারাপ নয়, সেটি পরীক্ষা করি।

## D. Scope and limitations

### ৩১. Carbon optimality বলছেন কি?

**উত্তর:** না। আমরা GPU energy মাপি, carbon নয়। Carbon নির্ভর করে grid mix-এর উপর; এটি আমাদের current scope-এর বাইরে।

### ৩২. Frontier model, dense retriever, full Natural Questions — এগুলো কি cover করছেন?

**উত্তর:** না। আমাদের scope হলো SQuAD, HotpotQA, BM25, Qwen3.5-4B এবং Qwen2.5-1.5B। Frontier/dense/full NQ generalization future work।

### ৩৩. সবচেয়ে বড় risk কী?

**উত্তর:** চারটি 주요 risk: scoring rule (exact match vs lenient), reader strength ও এক dataset, GPU heat/power sensor limit, এবং cached prompt/policy overfitting। এগুলোর mitigation স্লাইড ১১-এ আছে।

### ৩৪. Budget কত?

**উত্তর:** 15–20 GPU hours, local RTX 3060 6 GB, একসাথে একটাই job। Cash budget ≤$47।

### ৩৫. Novelty কী?

**উত্তর:** Prior work আলাদাভাবে accuracy, token/latency, বা energy দেখে। আমরা একসাথে দেখি: **gated E(k)** (energy per correct answer under accuracy floor), **causal energy taxes**, **break-even N***, এবং **query-conditional policy at matched accuracy**।

---

# Quick number sheet — প্রশ্নের সময়

| Item | Value |
|---|---:|
| SQuAD questions | 10,570 |
| SQuAD passages | 45,651 |
| HotpotQA questions | 7,405 |
| HotpotQA used | 500 |
| Primary run | 1,000 × 7 |
| Replication | 500 × 7 |
| HotpotQA run | 500 × 6 |
| Boundary | 200 × 3 |
| Taxes | 150 × 2 |
| Energy span | 3.45× |
| Context share at k=32 | 85.1% |
| Pilot savings at k=4 | 69.3% |
| Oracle upper bound | 78.8% |
| 2 pp claim | dead |
| 5 pp result | pilot signal, not certified |
| Bootstrap | 10,000 |
| Alpha | 0.05, one-sided |
| GPU budget | 15–20 hours |
| Cash budget | ≤$47 |

---

# Equations বলার সহজ উপায়

| Equation | বলবেন |
|---|---|
| `E(k) = ΣJ_k / ΣC_k` | “ই অফ কে সমান মোট জে কে ভাগ মোট সি কে” — অথবা “মোট energy ভাগ মোট সঠিক উত্তর” |
| `k J′(k)/J(k) = k A′(k)/A(k)` | “কে জে প্রাইম অফ কে ভাগ জে অফ কে, সমান কে এ প্রাইম অফ কে ভাগ এ অফ কে” |
| `N* = C_cert / [A(k*)(E(k₀) − E(k*))]` | “এন স্টার সমান সি সার্ট ভাগ, এ অফ কে স্টার গুণ ই অফ কে জিরো মাইনাস ই অফ কে স্টার” |
| `A(4) − A(32) > −5 pp` | “এ অফ ফোর মাইনাস এ অফ থার্টি-টু, মাইনাস ফাইভ পিপি-এর চেয়ে বড়” |

---

# শেষ পরামর্শ

- প্রতি স্লাইডে কমপক্ষে **একটি সংখ্যা** বলবেন — এতে শিক্ষক বুঝবেন কাজটি সুনির্দিষ্ট।
- `k`, `E(k)`, `pp`, `NI`, `P(k*)` — এই পাঁচটি শব্দ প্রতিটি সদস্য জানবেন।
- কোনো প্রশ্নের উত্তর না জানলে বলবেন: **“স্যার, এটি আমাদের current scope-এর বাইরে; আমরা এটি future work হিসেবে দেখছি।”**
- সময় কম হলে প্রতিটি speaker শেষের ১–২টি বাক্য বাদ দেবে, কিন্তু সংখ্যা ও gate-এর নাম বাদ দেবে না।
