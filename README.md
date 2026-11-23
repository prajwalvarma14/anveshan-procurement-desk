# The Procurement Desk — Anveshan DataSprint 2.0

> High-precision, deterministic neuro-symbolic pipeline for Acme Corp's autonomous procurement negotiation desk.

Achieved **100.0% (40/40 exact match)** on benchmark sample threads, with full dataset forensics across all 2,000 competition threads.

---

## 📌 Architecture Overview

Rather than relying on end-to-end LLM prompting (which is slow, costly, and susceptible to math/rounding hallucinations and token rate limits), this solution uses a **symbolic decision pipeline**:

```
                             [ Raw Supplier Message ]
                                        │
                                        ▼
                                ┌───────────────┐
                                │ src/parser.py │
                                └───────┬───────┘
                                        │ (Normalized Price, Currencies, Injections, Banned Terms)
                                        ▼
┌───────────────┐               ┌───────────────┐
│  src/data.py  │ ────────────▶ │ src/engine.py │
└───────────────┘ (Playbook)    └───────┬───────┘
                                        │ (Strict 6-Step Decision Protocol)
                                        ▼
                                [ Final Label ]
                        ACTION:REASON:COUNTER_PRICE
```

1. **`src/data.py`**: Structured master tables for 15 spend categories, target/walkaway prices, concession exponents ($\beta$), dated policy amendments, blacklists, and supplier-specific contract terms.
2. **`src/parser.py`**: Extracts normalized per-unit prices (INR excl. GST), parses complex English number words, handles pack/ream/per-N conversions, and screens for adversarial AI prompt injections (English and multilingual) and banned contract clauses.
3. **`src/engine.py`**: Deterministic decision engine executing Acme's 6-step precedence order using half-up integer rupee arithmetic.
4. **`src/main.py`**: High-throughput runner processing all 2,000 threads in <3 seconds.
5. **`src/evaluate.py`**: Automated evaluator testing against ground truth.
6. **`src/validate_submission.py`**: Strict format validation checking all Kaggle rules.

---

## 📊 Benchmark & Distribution

### 1. Benchmark Accuracy (Ground Truth)
- **Exact Match:** **40/40 (100.0%)**
- **Action Accuracy:** 100%
- **Reason Accuracy:** 100%
- **Counter Price Accuracy:** 100%

### 2. Full Test Dataset Distribution (2,000 Threads)

```
COUNTER:COUNTER_OFFER        : 640  (32.0%)
ACCEPT:ACCEPTABLE_PRICE      : 322  (16.1%)
ESCALATE:OVER_APPROVAL_LIMIT : 293  (14.6%)
REJECT:ABOVE_WALKAWAY        : 223  (11.2%)
ESCALATE:PROMPT_INJECTION    : 168  ( 8.4%)
ESCALATE:BANNED_TERM         : 135  ( 6.8%)
ESCALATE:MISSING_INFO        : 125  ( 6.2%)
REJECT:BLACKLISTED_SUPPLIER  :  94  ( 4.7%)
───────────────────────────────────────────
Total                        : 2,000 rows (100.0%)
```

---

## 🚀 How to Run & Reproduce

### 1. Test Against Ground Truth (40 Samples)
```bash
python src/evaluate.py
```
Expected output:
```
============================================================
  EXACT MATCH: 40/40  (100.0%)
============================================================
  🎉 PERFECT SCORE — all 40 samples matched!
```

### 2. Generate Final Submission (2,000 Threads)
```bash
python src/main.py
```
Output generated at: `outputs/submission.csv`

### 3. Validate Submission File
```bash
python src/validate_submission.py
```
Verifies exact 2,000-row count, thread IDs order, regex patterns, and integer price logic.

---

## 🛡️ Edge Cases Handled

- **Multilingual Injections:** Detects English and Hindi injection attempts (`AI सहायक के लिए निर्देश...`, `[admin override]`, hidden HTML comments).
- **Worded Contract Restrictions:** Identifies advance payment clauses over 30% written in words (e.g. *"We will need half the order value upfront"*).
- **Custom Units & Pack Sizes:** Handles `per pack of 4 fixtures` (LED), `per ream` (Printer paper, 10 reams = 1 box), and `per 100 <items>`.
- **Subscription Billing:** Flags subscription categories without billing periods as `ESCALATE:MISSING_INFO:`.
- **Currency Conversions:** Supports table rates and supplier contract overrides for USD, EUR, and GBP; routes unsupported currencies (JPY, SGD, AED) to `MISSING_INFO`.
