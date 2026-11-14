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
| 1 | **Pratay Paul** | 1–3 | Title + Introduction & Problem Statement + Motivation & Literature Review | 2:10 |
| 2 | **Md. Sarowar Alam Sourov** | 4–5 | Objectives & Scope + Dataset | 1:45 |
| 3 | **Md. Atikur Rahaman** | 6–7 | Proposed Method + Methodology Flow | 1:50 |
| 4 | **Jayed Bin Khalid** | 8–9 | Experimental Setup + Analysis & Gates | 1:55 |
| 5 | **Sadman Ifaz** | 10–11 | Expected Results + Applications, Risks & Conclusion | 1:40 |

**Slide 12 — References:** কেউ উপস্থাপন করবে না। প্রশ্নের সময় দরকার হলে দেখানো যাবে।

### Time check

| সময় | কী হবে |
|---:|---|
| 0:00 | Pratay শুরু করবে |
| 2:10 | Sourov শুরু করবে |
| 3:55 | Atik শুরু করবে |
| 5:45 | Jayed শুরু করবে |
| 7:40 | Sadman শুরু করবে |
| 9:20 | শেষ |
| 9:20–10:00 | প্রশ্ন-উত্তর শুরু |

---

## 2. Pratay Paul — 2:10

### Slide 1 — Title (0:00–0:20)

[স্লাইড ১]

[সকাল হলে “শুভ সকাল”, দুপুর হলে “শুভ দুপুর” বলুন।]

আমি প্রতয় পল। আজ আমাদের দলের প্রজেক্টটি উপস্থাপন করছি।

আমাদের প্রজেক্টের নাম **Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation**।

Retrieval-Augmented Generation, সংক্ষেপে RAG, এমন পদ্ধতি যেখানে মডেল উত্তর দেওয়ার আগে প্রাসঙ্গিক লেখা খুঁজে নিয়ে ব্যবহার করে।

আমাদের প্রশ্ন হলো: কতগুলো passage দিলে উত্তর ঠিক থাকে, অথচ energy খরচ কম হয়?

### Slide 2 — Introduction & Problem Statement (0:20–1:05)

[স্লাইড ২]

প্রথমে প্রশ্ন আসে। BM25, অর্থাৎ Best Matching 25, প্রাসঙ্গিক passage খোঁজে। Reader model-কে k-টি passage দিলে সে সেগুলো পড়ে উত্তর তৈরি করে।

এখানে **k হলো retrieval depth**—reader-কে দেওয়া passage-এর সংখ্যা।

বেশি passage accuracy বাড়াতে পারে, তবে energy-ও বাড়ে। কম passage energy বাঁচায়, কিন্তু দরকারি তথ্য বাদ পড়তে পারে। তাই শুধু accuracy বা শুধু energy দেখে depth বাছাই করা যায় না।

আমরা **E(k) = ΣJ_k / ΣC_k** দিয়ে প্রতি সঠিক উত্তরের energy মাপি।

**J_k** হলো depth k-তে এক প্রশ্নের energy; **C_k** হলো সঠিক হলে ১, ভুল হলে ০; আর **Σ** মানে সব প্রশ্নের যোগফল। সহজভাবে, মোট energy ভাগ মোট সঠিক উত্তর।

আমরা k=32-এর তুলনায় accuracy loss ৫ percentage point-এর মধ্যে রেখে E(k) কমাতে চাই। Percentage point-কে সংক্ষেপে **pp** বলি।

### Slide 3 — Motivation & Literature Review (1:05–2:10)

[স্লাইড ৩]

Pilot-এ k=32-এ প্রতি সঠিক উত্তরের energy k=1-এর **3.45 গুণ** ছিল। k=32-এ retrieval ও passage processing-সহ context-side share ছিল **85.1%**। k=4–16-এ accuracy ছিল **52%–53.5%**।

৫ pp margin-এ pilot analysis k=4 বেছে নিয়েছিল, যা k=32-এর তুলনায় প্রতি সঠিক উত্তরের energy **69.3%** বাঁচায়। এগুলো pilot result, চূড়ান্ত নয়।

Literature review-তে কয়েকটি ধারা আছে। Lewis et al. RAG-এর ভিত্তি স্থাপন করেন; Jeong, Hwang, Hashemi, Song ও Taguchi query অনুযায়ী retrieval বদলান; Pan, RAGMark ও Token Arena RAG-এর energy মাপে। Token Arena-তেই modeled joules per correct answer আছে, তাই metric নিজে নতুন নয়। আমাদের gap হলো measured energy দিয়ে accuracy limit-এর মধ্যে k বাছাই, break-even cost, causal tax test, এবং matched-accuracy policy একসঙ্গে পরীক্ষা করা।

[হ্যান্ডঅফ] এখন সারোয়ার আলম সৌরভ Objectives ও Dataset নিয়ে বলবেন।

---

## 3. Md. Sarowar Alam Sourov — 1:45

### Slide 4 — Objectives & Scope (2:10–3:05)

[স্লাইড ৪]

ধন্যবাদ। আমি সারোয়ার আলম সৌরভ। আমাদের তিনটি প্রশ্ন।

**এক: Static depth।** k=32-এর তুলনায় accuracy loss ৫ pp-এর মধ্যে রেখে কোন k-তে E(k) সবচেয়ে কম? এতে H1–H4 পরীক্ষা হবে; H7-তে অন্য reader বা dataset-এ একই দিকের ফল আসে কি না দেখব।

**দুই: Adaptivity।** প্রতি প্রশ্নে আলাদা k বেছে নিয়ে best static depth-এর সমান accuracy রাখা যায় কি না—এটি H5।

**তিন: কারণ ও খরচ।** Fixed বা প্রতি-passage energy cost দিলে k* কীভাবে বদলায়, তা H6 পরীক্ষা করে। Sweep-এর energy খরচ কত প্রশ্নে পুষিয়ে যায়, তা N* বলে।

H1–H7 হলো সাতটি পরীক্ষামূলক বক্তব্য; H মানে hypothesis। আমরা ৫ pp rule, ≥20% সাশ্রয়, energy–accuracy সম্পর্ক, context share, policy ও cost effect পরীক্ষা করব। একটি universal best depth claim করছি না। ২ pp শুধু estimate; ৫ pp-এর ফল powered rerun-এর আগে pilot signal।

### Slide 5 — Dataset (3:05–3:55)

[স্লাইড ৫]

প্রথম dataset **SQuAD**, অর্থাৎ Stanford Question Answering Dataset v1.1 dev। এতে 10,570টি প্রশ্ন, 20,958টি context, এবং 45,651টি passage আছে। Retriever BM25 top-32।

Primary run-এ 1,000টি, reader replication-এ 500টি, আর boundary test-এ 200টি প্রশ্ন থাকবে। Primary metric normalized exact match।

দ্বিতীয় dataset **HotpotQA**। Distractor version-এ 7,405টি প্রশ্ন আছে; আমরা 500টি নেব। প্রতি প্রশ্নে 10টি paragraph—2টি gold, 8টি distractor। k হবে 0, 1, 2, 4, 8, 10; retriever BM25 top-10।

SQuAD-এ একই corpus রেখে depth-এর প্রভাব দেখি। HotpotQA-তে multi-hop evidence ও distractor থাকে, তাই এটি stress test।

[হ্যান্ডঅফ] এখন আতিকুর রহমান Proposed Method ও Methodology Flow ব্যাখ্যা করবেন।

---

## 4. Md. Atikur Rahaman — 1:50

### Slide 6 — Proposed Method (3:55–4:55)

[স্লাইড ৬]

ধন্যবাদ। আমি আতিকুর রহমান।

আমাদের method-এ চারটি অংশ।

**এক:** accuracy limit-এর মধ্যে E(k), অর্থাৎ মোট energy ভাগ মোট সঠিক উত্তর, কমানো।

**দুই:** interior optimum-এ energy ও accuracy-র শতকরা পরিবর্তনের হার সমান কি না দেখা। J′ ও A′ হলো k বদলালে তাদের পরিবর্তনের হার।

**তিন:** N* দিয়ে sweep-এর break-even প্রশ্নসংখ্যা বের করা। C_cert হলো sweep energy; k₀ default depth; k* হলো বাছাই করা depth।

**চার:** Accuracy gate একই রেখে fixed cost বাড়ালে k* বাড়ে, প্রতি-passage cost বাড়ালে কমে কি না পরীক্ষা করা।

Baseline-এ সবার জন্য একই top-k। আমাদের প্রস্তাব accuracy limit রেখে energy per correct answer দিয়ে depth বেছে নেয়।

### Slide 7 — Methodology Flow (4:55–5:45)

[স্লাইড ৭]

এই স্লাইডে study workflow। Primary SQuAD run-এ 7টি depth, HotpotQA-তে 6টি। এরপর NVML ও block calibration-এ energy মাপি, normalized exact match score করি, তারপর paired NI test, bootstrap, E(k), N*, ও policy বিশ্লেষণ করি।

নিচে: 200 প্রশ্নের P0 check, P1-এর আগে plan freeze, 1,000 প্রশ্নের full run, gate review, তারপর replication, tax, policy ও theory test।

মূল কথা: **run measurement দেয়; checkpoint বলে আমরা এগোব কি না।**

[হ্যান্ডঅফ] এখন জায়েদ বিন খালিদ Experimental Setup এবং Analysis-এর gate-গুলো ব্যাখ্যা করবেন।

---

## 5. Jayed Bin Khalid — 1:55

### Slide 8 — Experimental Setup (5:45–6:40)

[স্লাইড ৮]

ধন্যবাদ। আমি জায়েদ বিন খালিদ।

Run plan: SQuAD 1,000 × 7 depth; replication 2 × 500 × 7 — Qwen2.5-1.5B এবং exploratory Llama 3.2 3B; HotpotQA 500 × 6; boundary test 200 × 3; 16k context probe 200 × 3; energy-tax test 150 × 2 condition। Policy split-এর target 600 train, 200 validation, 200 test।

NVML প্রতি 100 মিলিসেকেন্ডে power sample করে, কিন্তু এই laptop-এ sensor reading প্রায় প্রতি এক সেকেন্ডে update হয়। তাই 100 মিলিসেকেন্ড sampling মানে 100 মিলিসেকেন্ডের sensor precision নয়।

60 সেকেন্ডের idle baseline বাদ দিয়ে 20-query block calibrate করব। Unique code cache reuse কমায়। Temperature ও clock log করব, block repeat করব, এবং 30-query subset-এ wall meter ব্যবহার করব।

H2 pass করতে paired one-sided 5% test-এর lower bound −5 pp-এর ওপরে এবং energy saving অন্তত 20% হতে হবে। Energy uncertainty-র জন্য 10,000 paired bootstrap নেব। 2 pp শুধু estimate করব।

Budget **15–20 GPU hours**। RTX 3060 6 GB-তে একবারে একটি job; wall power, screen off।

### Slide 9 — Analysis & Gates (6:40–7:40)

[স্লাইড ৯]

এখন Analysis ও Gates।

**G মানে go**—pass হলে এগোব। **K মানে stop/reframe**—fail হলে ফল report করে claim বদলাব। **H মানে hypothesis**, অর্থাৎ পরীক্ষার বক্তব্য।

Main decision: k=4-এর accuracy loss 5 pp-এর বেশি নয়, আর energy per correct answer-এ সাশ্রয় অন্তত 20%। `P(k*)` হলো 10,000 bootstrap sample-এর কত অংশে ওই depth-টি accuracy gate মেনে best হয়—সত্যিই best হওয়ার নিশ্চয়তা নয়।

G1–G2 static সিদ্ধান্ত ও stability দেখে; G3 context-side share; G4 oracle gain ≥20% হলে policy matched accuracy-তে তার ≥50% ধরে কি না; G5 replication।

K1–K7 ছোট effect, boundary বা unstable best depth, কম context share বা oracle gain, এবং noisy measurement ধরার জন্য। নির্দিষ্ট threshold স্লাইডে আছে।

কোনো checkpoint fail করলে সেটি লুকাব না—report করব এবং claim সীমিত বা বদলাব।

[হ্যান্ডঅফ] এখন সাদমান ইফাজ Expected Results ও Conclusion নিয়ে বলবেন।

---

## 6. Sadman Ifaz — 1:40

### Slide 10 — Expected Results (7:40–8:25)

[স্লাইড ১০]

ধন্যবাদ। আমি সাদমান ইফাজ।

H1 থেকে H7 পর্যন্ত আমাদের pass/fail নিয়মগুলো এই স্লাইডে আছে।

- **H1:** `J(k)=a+bk`-তে `b>0`, `R²≥0.95`, এবং 5% lack-of-fit test-এ fit বাতিল হয় না।
- **H2:** paired one-sided test-এর lower bound −5 pp-এর ওপরে, energy saving অন্তত 20%।
- **H3–H4:** identity-gap interval-এ 0; selected depth-এ context share 10–70% এবং k-এর সঙ্গে বাড়ে।
- **H5–H6:** oracle gain অন্তত 20%; policy matched accuracy-তে তার অন্তত অর্ধেক ধরে; fixed ও per-passage cost k* প্রত্যাশিত দিকে সরায়।
- **H7:** H2-এর দিক Qwen2.5-1.5B বা HotpotQA-তে মেলে কি না। Llama 3.2 3B আলাদা exploratory reader panel; এটি H7 বা G5 নয় এবং এর কোনো gate নেই।

কোনো hypothesis সমর্থন না পেলেও সেটি report করব। Null result-ও ফল।

### Slide 11 — Applications, Risks & Conclusion (8:25–9:20)

[স্লাইড ১১]

এই ফল energy-aware RAG serving, capacity planning, ছোট GPU ও edge device-এর নকশায় কাজে লাগতে পারে। Reusable code প্রকাশেরও পরিকল্পনা আছে।

প্রধান ঝুঁকি হলো scoring rule, সীমিত reader ও dataset, GPU heat ও sensor-এর সীমা, এবং cache বা policy overfitting। Budget 15–20 GPU hours; মোট cash cap 47 dollar।

আমাদের প্রস্তাব তিনটি:

1. Accuracy limit মেনে প্রতি সঠিক উত্তরের energy দিয়ে depth বাছাই।
2. Energy cost বদলে best depth-এর ওপর তার causal effect পরীক্ষা।
3. প্রতিটি প্রশ্নের জন্য আলাদা depth বেছে নেওয়া policy-কে একই accuracy-তে পরীক্ষা।

আমরা 1,000 প্রশ্নের study চালিয়ে ফল positive বা null—যাই হোক—report করতে চাই।

ধন্যবাদ, স্যার। এখন আপনাদের প্রশ্নের উত্তর দেব।

---

# Q&A — স্যারের সম্ভাব্য প্রশ্ন ও বাংলা উত্তর

> [!TIP]
> উত্তর শুরু করার আগে এক সেকেন্ড থামুন। তারপর প্রথম বাক্যে সরাসরি উত্তর দিন। বিস্তারিত লাগলে স্লাইডে ফিরে যান।

## A. প্রাথমিক ধারণা

### ১. `k` কী?

**উত্তর:** `k` হলো retrieval depth—reader-কে দেওয়া passage-এর সংখ্যা। `k=4` হলে reader ৪টি passage পায়; `k=32` হলে ৩২টি পায়।

### ২. `E(k)` কী?

**উত্তর:** `E(k)` হলো প্রতি সঠিক উত্তরের energy। সব প্রশ্নে খরচ হওয়া মোট energy-কে সঠিক উত্তরের মোট সংখ্যা দিয়ে ভাগ করি। তাই এটি per-query ratio-র গড় নয়; এটি মোট energy ভাগ মোট সঠিক উত্তর।

### ৩. `J_k` ও `C_k` কী?

**উত্তর:** `J_k` হলো depth `k`-তে একটি প্রশ্নের energy। `C_k` হলো correctness indicator—সঠিক হলে ১, ভুল হলে ০। `Σ` মানে সব প্রশ্নের যোগফল।

### ৪. `pp` কী?

**উত্তর:** `pp` মানে **percentage point**। Accuracy ৮০% থেকে ৭৫% হলে কমে ৫ pp। এটি ৫% relative decrease নয়।

### ৫. `EM` কী?

**উত্তর:** `EM` মানে **exact match**। Normalization-এর পরে model-এর উত্তরটি gold answer-এর সঙ্গে পুরো মিললে ১, না মিললে ০। এটিই আমাদের primary metric।

### ৬. `NI` কী?

**উত্তর:** `NI` মানে **non-inferiority**—নতুন পদ্ধতি নির্ধারিত margin-এর বেশি খারাপ নয়। এখানে `k=4`-এর accuracy `k=32`-এর চেয়ে ৫ pp-এর বেশি কম নয়—এটি শুধু observed difference দেখে বলা যাবে না; paired one-sided test-ও pass করতে হবে।

### ৭. `P(k*)` কী?

**উত্তর:** `P(k*)` হলো 10,000 bootstrap resample-এর যে অংশে ওই depth-টি accuracy gate মেনে সবচেয়ে কম energy দেয়। এটি “সত্যিই best হওয়ার সম্ভাবনা” নয়। G2-তে এই অংশ অন্তত 0.8 হতে হবে।

### ৮. `R²` কী?

**উত্তর:** `R²` হলো fit quality—সরলরেখাটি data-র সঙ্গে কতটা মেলে। H1 pass করতে `R² ≥ 0.95` এবং ৫% lack-of-fit test-এ fit বাতিল না হওয়া দরকার।

### ৯. `N*` কী?

**উত্তর:** `N*` হলো break-even question count—কতটি query-র পরে sweep চালাতে খরচ হওয়া energy, বেছে নেওয়া depth-এর মাধ্যমে সাশ্রয় হওয়া energy দিয়ে পুষিয়ে যায়।

### ১০. `C_cert`, `k₀`, `k*` কী?

**উত্তর:** `C_cert` হলো depth খুঁজতে sweep-এর মোট energy cost। `k₀` হলো default depth, আর `k*` হলো accuracy gate মেনে সবচেয়ে কম energy দেওয়া depth।

### ১১. `a` ও `b` কী?

**উত্তর:** `J(k)=a+bk`-তে `a` হলো fixed energy cost, আর `b` হলো প্রতি passage যোগ হলে বাড়তি energy। আমাদের prediction হলো: fixed cost বাড়ালে `k*` বাড়বে; প্রতি-passage cost বাড়ালে `k*` কমবে।

## B. Gate ও hypothesis

### ১২. `G1–G5` কী?

**উত্তর:** এগুলো **go gate**—শর্ত পূরণ হলে পরের ধাপে যাব।

- G1: `k=32`-এর তুলনায় interior depth-এ ৫ pp non-inferiority এবং ≥20% energy savings
- G2: accuracy loss-এর upper confidence bound ≤5 pp এবং `P(k*) ≥ 0.8`
- G3: selected depth-এ context-side share 10–70%, এবং depth বদলালে share-ও বদলায়
- G4: oracle gain ≥20%, policy matched accuracy-তে তার ≥50% পায়
- G5: Qwen2.5-1.5B reader অথবা HotpotQA-তে replication

### ১৩. `K1–K7` কী?

**উত্তর:** এগুলো **stop/reframe gate**—শর্ত fail হলে ফলটি report করব এবং claim সীমিত বা বদলাব।

- K1: energy effect <10%
- K2: best depth boundary-তে
- K3: `P(k*) < 0.8`
- K4: context-side share <5% এবং depth-এর সঙ্গে বাড়ে না
- K5: bootstrap sample বা dataset বদলালে best depth ১-এর বেশি depth জুড়ে ছড়ায়
- K6: best-possible gain <15%
- K7: repeat coefficient of variation (CV) >20% অথবা minimum detectable effect (MDE), observed effect-এর চেয়ে বড়

### ১৪. `H1–H7` কী?

**উত্তর:** সাতটি পরীক্ষামূলক বক্তব্য:

- H1: প্রতি query-র energy depth-এর সঙ্গে positive slope-এ affine line মেনে বাড়ে; `R² ≥ 0.95` এবং ৫% lack-of-fit test-এ fit বাতিল হয় না।
- H2: `k=4`-এর paired ৫ pp non-inferiority test pass করে এবং ≥20% সাশ্রয় দেয়।
- H3: নির্বাচিত interior depth-এ energy–accuracy identity gap-এর 95% interval-এ 0 থাকে।
- H4: selected depth-এ context-side share 10–70% এবং depth বাড়লে share বাড়ে।
- H5: 200 held-out প্রশ্নে learned policy matched accuracy-তে oracle gain-এর অন্তত অর্ধেক ধরে।
- H6: accuracy gate একই রেখে fixed cost বাড়ালে `k*` বাড়ে, প্রতি-passage cost বাড়ালে `k*` কমে।
- H7: H2-এর দিক Qwen2.5-1.5B বা HotpotQA-তে মেলে।

প্রতিটির pass/fail rule স্লাইড ১০-এ আছে।

### ১৫. `H` কী?

**উত্তর:** `H` মানে **hypothesis**—আমরা যে বক্তব্যটি data দিয়ে পরীক্ষা করব। যেমন H2 পরীক্ষা করে `k=4`-এর accuracy `k=32`-এর চেয়ে ৫ pp-এর বেশি কম কি না, এবং energy সাশ্রয় অন্তত ২০% কি না।

### ১৬. `G` ও `K` কী?

**উত্তর:** `G` মানে **go**—শর্ত পূরণ হলে এগোব। `K` মানে **stop/reframe**—শর্ত পূরণ না হলে ফল report করে claim বদলাব।

## C. Project-এর নকশা

### ১৭. প্রাইমারি reader কোনটি? কেন Qwen2.5-1.5B?

**উত্তর:** Primary reader হলো **Qwen3.5-4B**, local Ollama-তে Q4 quantization ও 4096-token context-সহ। Replication-এ **Qwen2.5-1.5B-Instruct** নেব, কারণ এটি ভিন্ন generation ও size-এর reader। একই 4B আবার চালালে সেটি repeat হতো, cross-reader replication নয়।

### ১৮. `5 pp` কেন, `2 pp` নয়?

**উত্তর:** ২ pp-কে decision threshold ধরে best depth certify করার claim আমরা বাদ দিয়েছি। Pilot-এ ২ pp gate-এ `k*=32` boundary-তে ছিল এবং `P(k*)=0.61`, যা G2-এর 0.8-এর নিচে। ২ pp এখন শুধু estimate করব। ৫ pp হলো planned primary margin; সঙ্গে অন্তত ২০% সাশ্রয়ও লাগবে। Pilot-এর ৫ pp ফল signal, certification নয়।

### ১৯. `69.3%` কী?

**উত্তর:** Pilot-এ ৫ pp margin-এ `k=4` বেছে নেওয়া হয়েছিল। `k=32`-এর তুলনায় প্রতি সঠিক উত্তরের energy-তে সাশ্রয় ছিল 69.3%। এটি pilot signal; 1,000-প্রশ্নের run-এ যাচাই করতে হবে।

### ২০. `78.8%` কী?

**উত্তর:** 78.8% হলো pilot-এর **oracle upper bound**—একই accuracy রেখে hindsight-এ প্রতিটি প্রশ্নের জন্য সেরা depth বেছে নিলে যে gain পাওয়া যেত। কোনো learned policy এখনো test করা হয়নি, তাই 78.8% policy-র result নয়। H5/G4 পরীক্ষা করবে learned policy এই gain-এর কতটা ধরতে পারে।

### ২১. Universal `k*` আছে কি?

**উত্তর:** না। Best depth reader, dataset, accuracy limit ও energy cost-এর ওপর নির্ভর করতে পারে। তাই আমরা সবার জন্য একটিমাত্র `k*` বলি না; পরিস্থিতি অনুযায়ী depth বাছাইয়ের decision rule পরীক্ষা করি।

### ২২. `k=4` কি `k*`?

**উত্তর:** `k=4` হলো primary test-এর নির্ধারিত candidate; `k*` হলো accuracy gate মেনে সবচেয়ে কম energy দেওয়া estimated depth। ২ pp gate-এ pilot `k*=32` বেছে নিয়েছিল, `P(k*)=0.61`। ৫ pp gate-এ `k=4`-এর pilot selection probability ছিল `0.537`। তাই `k=4`-কে universal best বলা যাবে না।

### ২৩. Gate fail করলে কী হবে?

**উত্তর:** Gate fail করলে ফলটি report করব; threshold বদলে pass করানোর চেষ্টা করব না। K1–K4 ও K6 claim stop বা reframe করতে পারে। K5 ও K7 আগে measurement বা framing ঠিক করার সুযোগ দেয়। Negative result-ও report হবে।

### ২৪. কেন SQuAD ও HotpotQA?

**উত্তর:** SQuAD-এ corpus স্থির থাকে, তাই একই retriever রেখে শুধু `k` বদলে depth-এর প্রভাব দেখা যায়। HotpotQA-তে multi-hop প্রশ্ন ও distractor আছে; এটি অন্য ধরনের কঠিন প্রশ্নে পদ্ধতিটি পরীক্ষা করে।

### ২৫. কেন BM25?

**উত্তর:** BM25 হলো fixed keyword-based retriever। এটিকে একই রাখলে `k` বদলানোর প্রভাব আলাদা করে দেখা যায়। Retriever-ও বদলালে depth-এর সঙ্গে retrieval-এর প্রভাব মিশে যেত।

### ২৬. `n=1,000` কেন?

**উত্তর:** Primary run-এ 1,000টি প্রশ্ন রাখা হয়েছে, যাতে ৫ pp non-inferiority test-এর জন্য বেশি precision ও power থাকে। 200-প্রশ্নের pilot-এ ২ pp margin certify করার মতো power ছিল না। Replication-এ 500, boundary test-এ 200টি প্রশ্ন।

### ২৭. `20%` savings কেন?

**উত্তর:** আমাদের পরিকল্পনায় `k=32`-এর তুলনায় অন্তত ২০% energy savings-কে G1-এর শর্ত ধরা হয়েছে। শুধু accuracy ধরে রাখলেই হবে না; energy-তেও এই ন্যূনতম সাশ্রয় দেখাতে হবে।

### ২৮. Measurement কীভাবে করবেন?

**উত্তর:** NVML প্রতি 100 ms-এ power sample করে, কিন্তু এই laptop-এ sensor reading প্রায় প্রতি এক সেকেন্ডে update হয়। তাই 100 ms sampling-কে 100 ms precision বলা যাবে না। আমরা 60 সেকেন্ডের idle baseline বাদ দিই, 20-query block দিয়ে energy calibrate করি, unique code দিয়ে prefix-cache reuse কমাই, temperature ও clock log করি, এবং 30-query subset-এ wall meter দিয়ে পুরো system-এর energy cross-check করি।

### ২৯. `10,000 bootstrap` কেন?

**উত্তর:** প্রশ্নগুলোকে paired unit ধরে 10,000 বার bootstrap resample করি। এতে energy ও accuracy-র uncertainty এবং কোন depth কতবার best হয়েছে, তা হিসাব করা যায়।

### ৩০. `5% one-sided` কেন?

**উত্তর:** Paired one-sided non-inferiority test-এ `α=0.05` ব্যবহার করি। `k=4` ও `k=32`-এর accuracy difference-এর one-sided 95% lower bound −5 pp-এর ওপরে হলে non-inferiority সমর্থিত হয়।

## D. Scope ও সীমাবদ্ধতা

### ৩১. Carbon optimality বলছেন কি?

**উত্তর:** না। আমরা GPU energy মাপি, carbon emission নয়। Carbon হিসাব করতে electricity grid-এর emission factor লাগবে; সেটি এই study-র scope-এর বাইরে।

### ৩২. Frontier model, dense retriever, full Natural Questions — এগুলো কি cover করছেন?

**উত্তর:** না। আমাদের scope হলো SQuAD ও HotpotQA, BM25, Qwen3.5-4B এবং Qwen2.5-1.5B। Frontier model, dense retriever, বা পুরো Natural Questions dataset-এ generalization পরীক্ষা করছি না।

### ৩৩. সবচেয়ে বড় risk কী?

**উত্তর:** প্রধান ঝুঁকি চারটি: exact-match ও lenient scoring-এ ভিন্ন ফল, reader ও dataset-এর সীমিত পরিসর, GPU heat ও power sensor-এর সীমা, এবং cache বা policy overfitting। স্লাইড ১১-তে এগুলো দেখানো আছে।

### ৩৪. Budget কত?

**উত্তর:** Local RTX 3060 6 GB-তে মোট 15–20 GPU hours, একবারে একটি job। মোট cash budget সর্বোচ্চ 47 dollar।

### ৩৫. Novelty কী?

**উত্তর:** আমাদের contribution হলো একই study-তে চারটি বিষয় দেখা: accuracy limit-সহ energy per correct answer, energy cost বদলানোর causal test, sweep-এর break-even query count, এবং matched accuracy-তে query-conditional policy। এই সমন্বয়টি আমাদের পর্যালোচিত prior work-এ পাইনি।

### ৩৬. এই flow diagram-টাই কি journal paper-এর পুরো flow?

**উত্তর:** না। এটি study workflow ও planned gates-এর overview, paper-এর section-by-section flow নয়। Journal-এর methods overview figure হিসেবে ব্যবহার করা যাবে, তবে actual runs, dataset-specific depth grid, calibration, paired test ও bootstrap দেখিয়ে update করতে হবে। P0 check-এর পরে P1-এর আগে plan freeze হবে। Planned run-কে completed result হিসেবে দেখানো যাবে না।

### ৩৭. কেন Llama 3.2 3B?

**উত্তর:** এটি ভিন্ন family-এর 3B reader, Q4-এ 6 GB GPU-তে 4k context-এ চলে। এটি reader-family robustness দেখার exploratory panel; primary বা H7 replication নয়। Llama-এর quantized version-এর validated context 8k, তাই এটি 16k probe-এ ব্যবহার করছি না।

### ৩৮. Llama কি H7 বা G5 পূরণ করে?

**উত্তর:** না। H7 আগের মতোই Qwen2.5-1.5B অথবা HotpotQA; G5-ও অপরিবর্তিত। Llama আলাদা exploratory arm—কোনো gate নেই, 5 pp certify করে না, এবং ফল দেখার পরে H7/G5-এ যোগ করা যাবে না।

### ৩৯. 16k context probe-এ কী হচ্ছে?

**উত্তর:** এটি Qwen3.5-4B-এর 16k `num_ctx` allocation-এর diagnostic, 200 boundary প্রশ্নে `k=32/48/64` এবং একটি `k=32 @ 4096` control। 70-word passage-এ `k≤64` আসলে প্রায় 6k token, তাই এটি “16k-token prompt” নয়। 100% GPU residency লাগবে; CPU offload হলে hardware limit report করব।

### ৪০. H200 ব্যবহার করা যাবে?

**উত্তর:** শুধু optional accuracy-only 64k check-এর জন্য; H200 MIG slice-এ per-instance power reading নেই, তাই energy বা E(k) claim করা যাবে না। H200-এর ফল RTX 3060-এর সঙ্গে pool করা যাবে না।

### ৪১. অনেক model test করবেন না কেন?

**উত্তর:** প্রতিটি reader-এ 500 × 7 generation লাগে, আর model বাড়ালে selection ও multiple-comparison risk বাড়ে। একটি exploratory Llama panel আর একটি context probe-ই প্রশ্নটির জন্য যথেষ্ট; বেশি model মানে ভালো science নয়।

---

# References: প্রশ্ন এলে কী বলবেন

এই নোটগুলো 9 মিনিট 20 সেকেন্ডের মূল বক্তৃতায় পড়ার দরকার নেই। স্যার কোনো citation সম্পর্কে জানতে চাইলে ১–২টি বাক্য বলুন।

### 1. Lewis et al. (2020) — RAG-এর ভিত্তি

এই কাজটি language model-এর নিজস্ব জ্ঞানের সঙ্গে বাইরের document থেকে আনা তথ্য যুক্ত করে RAG পদ্ধতি প্রস্তাব করে। এটি RAG-এর মূল ধারণা, তবে energy অনুযায়ী retrieval depth বাছাই করে না।

### 2. Jeong et al. (2024) — Adaptive-RAG

এই পদ্ধতি প্রশ্নের complexity দেখে no retrieval, একবার retrieval, বা iterative retrieval বেছে নেয়। এটি adaptive retrieval-এর গুরুত্বপূর্ণ উদাহরণ, তবে GPU joules per correct answer-কে সিদ্ধান্তের metric হিসেবে পরীক্ষা করে না।

### 3. Pan et al. (2025) — RAG configuration ও energy

তারা দেখিয়েছেন, কাছাকাছি accuracy-র RAG configuration-গুলোর energy cost অনেক ভিন্ন হতে পারে। কাজটি energy–accuracy trade-off দেখায়, কিন্তু pre-set accuracy margin-এর অধীনে retrieval depth-এর break-even সিদ্ধান্ত দেয় না।

### 4. Hwang (2026) — Query Complexity-Aware Adaptive Retrieval

এই OpenReview direct upload-এ query complexity দেখে retrieval depth ও context ব্যবহার বদলানো হয়, যাতে retrieval ও token cost কমে। এটি peer-reviewed conference paper নয়।

### 5. Hashemi et al. (2025) — Cost-Aware Adaptive Retrieval Depth

তারা reasoning model-এর জন্য reinforcement learning-ভিত্তিক cost-aware adaptive retrieval পরীক্ষা করেছেন। তাদের abstract-এ latency কমা ও exact-match accuracy বাড়ার কথা আছে; আমাদের মতো GPU energy per correct answer gate নেই।

### 6. Feric et al. (2026) — RAGMark

RAGMark হলো RAG system benchmark, যা latency, GPU use, memory, power ও answer quality-সহ বিভিন্ন stage মাপে। এটি energy benchmarking-এর প্রয়োজন দেখায়, কিন্তু আমাদের study-এর accuracy-gated retrieval-depth decision নয়।

### 7. Song et al. (2026) — Tail-Aware Adaptive-k

এই পদ্ধতি similarity score-এর tail দেখে প্রতিটি query-র জন্য adaptive cutoff বেছে নেয়। Springer/Crossref-এ online publication 2026 এবং print citation year 2027; slide-এ ECML PKDD conference year 2026 রাখা হয়েছে।

### 8. Taguchi et al. (2025) — Just Adaptive-k

তারা long-context question answering-এর জন্য tuning বা iterative prompting ছাড়াই context size বেছে নেওয়ার পদ্ধতি দেন। কাজটি context selection-এ প্রাসঙ্গিক, কিন্তু energy-calibrated depth decision নয়।

### 9. Gao et al. (2026) — Token Arena

Token Arena বিভিন্ন model-serving endpoint benchmark করে এবং modeled energy-সহ joules per correct answer মেট্রিকও দেয়। তাই আমাদের metric নিজে নতুন নয়; Token Arena retrieval depth-এর accuracy-gated সিদ্ধান্তটি পরীক্ষা করে না।

### 10. Rajpurkar et al. (2016) — SQuAD

SQuAD হলো Wikipedia passage-ভিত্তিক extractive question-answering dataset; উত্তরের text passage থেকে নেওয়া হয়। আমাদের study-তে SQuAD-কে primary dataset হিসেবে ব্যবহার করি।

### 11. Yang et al. (2018) — HotpotQA

HotpotQA multi-hop প্রশ্ন ও supporting-fact annotation-সহ তৈরি করা হয়েছে। আমরা distractor version নিই, যেখানে প্রতি প্রশ্নে 2টি gold ও 8টি distractor paragraph থাকে।

### 12. Robertson & Zaragoza (2009) — BM25

এই survey probabilistic relevance framework ব্যাখ্যা করে এবং BM25-এর ধারণা ও বিকাশ নিয়ে আলোচনা করে। আমাদের পরীক্ষায় BM25 fixed রাখি, যাতে retrieval depth বদলানোর প্রভাব আলাদা করে দেখা যায়।

---

# Model notes — প্রশ্ন এলে

- **Qwen3.5-4B:** primary reader, Q4, 4096 context; the 16k probe uses Q4 at 16384.
- **Qwen2.5-1.5B-Instruct:** confirmatory H7 replication, fp16, 4096 context.
- **Llama 3.2 3B Instruct:** exploratory reader, Q4_K_M, 4096 context; Llama 3.2 Community License; quantized variant has an 8k validated ceiling.
- **H200 MIG 1g.18gb:** optional 64k accuracy-only check; no per-instance power telemetry, so no energy claim.

---

# Quick number sheet — প্রশ্নের সময়

| Item | Value |
|---|---:|
| SQuAD questions | 10,570 |
| SQuAD passages | 45,651 |
| HotpotQA questions | 7,405 |
| HotpotQA used | 500 |
| Primary run | 1,000 × 7 |
| Replication | 2 × 500 × 7 |
| HotpotQA run | 500 × 6 |
| Boundary | 200 × 3 (8k) |
| Context probe | 200 × 3 (16k) |
| Taxes | 150 × 2 |
| Policy split target | 600 / 200 / 200 |
| Energy span | 3.45× |
| Context share at k=32 | 85.1% |
| Pilot savings at k=4 | 69.3% |
| Oracle upper bound | 78.8% |
| 2 pp decision claim | বাদ; estimation only |
| 5 pp result | pilot signal, not certified |
| Bootstrap | 10,000 |
| Alpha | 0.05, one-sided |
| Local GPU budget | 15–20 hours (+~1.2–1.7 exploratory) |
| H200 | optional 64k accuracy-only; no energy |
| Cash budget | ≤$47 |

---

# Equations বলার সহজ উপায়

| Equation | বলবেন |
|---|---|
| `E(k) = ΣJ_k / ΣC_k` | “ই অফ কে: সব প্রশ্নের মোট energy ভাগ মোট সঠিক উত্তর।” |
| `k J′(k)/J(k) = k A′(k)/A(k)` | “এই সমীকরণে interior optimum-এ energy ও accuracy-র শতকরা পরিবর্তনের হার সমান।” |
| `N* = C_cert / [A(k*)(E(k₀) − E(k*))]` | “এন স্টার: sweep-এর energy cost ভাগ, best depth-এর accuracy গুণ প্রতি query-তে সাশ্রয় হওয়া energy।” |
| `A(4) − A(32) > −5 pp` | “চার passage-এর accuracy থেকে বত্রিশ passage-এর accuracy বাদ দিলে ফল মাইনাস পাঁচ pp-এর চেয়ে বড় হতে হবে।” |

---

# শেষ পরামর্শ

- প্রতি স্লাইডে কমপক্ষে **একটি সংখ্যা** বলবেন — এতে শিক্ষক বুঝবেন কাজটি সুনির্দিষ্ট।
- `k`, `E(k)`, `pp`, `NI`, `P(k*)` — এই পাঁচটি ধারণা প্রতিটি সদস্য বুঝে বলবেন।
- কোনো প্রশ্নের উত্তর না জানলে বলবেন: **“স্যার, বিষয়টি আমাদের এই study-র scope-এর বাইরে; আমরা এটিকে future work হিসেবে দেখছি।”**
- সময় কম হলে প্রতিটি speaker শেষের ১–২টি বাক্য বাদ দেবে, কিন্তু সংখ্যা ও gate-এর নাম বাদ দেবে না।
