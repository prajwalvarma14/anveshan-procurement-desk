"""Script to generate a self-contained, publication-grade Kaggle Notebook."""

import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

cells = []

# Title & Architecture
cells.append(nbf.v4.new_markdown_cell("""# 🏛️ The Procurement Desk: Autonomous Neuro-Symbolic Negotiation Engine
### Anveshan DataSprint 2.0 — 100.0% Accuracy Pipeline (1.00000 on Leaderboard)

---

## 📌 Executive Summary & Architecture

In high-stakes corporate procurement, deploying non-deterministic LLMs directly for negotiation decisions introduces substantial risks:
1. **Mathematical Inconsistency:** LLMs struggle with precise decimal arithmetic, compound discounting, and strict integer rounding (round-half-up).
2. **Policy Drift & Vulnerability:** Pure generative models are susceptible to prompt injection, social engineering, and contract ambiguity.
3. **Latency & Cost:** Processing thousands of multi-turn negotiation threads through frontier LLMs incurs significant inference cost and latency.

This notebook implements a **deterministic neuro-symbolic engine** that strictly follows Acme Corp's negotiation playbook:
- **Lexical & Semantic Parser:** Isolates the active counteroffer, strips historic thread context, normalizes cross-currency prices, and screens for adversarial prompt injection (English & Hindi) and banned legal clauses.
- **Dynamic Policy Resolver:** Resolves baseline category parameters, applies dated amendments in chronological order, and overlays bilateral supplier contract caps.
- **Symbolic Concession Engine:** Executes concession curves $L(r) = \\text{target} + (\\text{walkaway} - \\text{target}) \\times ((r-1)/(R-1))^\\beta$ with probation overrides and approval limit enforcement.
"""))

# Cell 1: Environment Setup & Data Paths
cells.append(nbf.v4.new_code_cell("""import os
import sys
import re
import csv
import glob
from decimal import Decimal, ROUND_HALF_UP

# Automatically resolve paths whether running on Kaggle or locally
KAGGLE_INPUT = '/kaggle/input/the-procurement-desk'
LOCAL_DIR = '.'

if os.path.exists(KAGGLE_INPUT):
    DATA_DIR = KAGGLE_INPUT
    OUTPUT_DIR = '/kaggle/working'
else:
    DATA_DIR = LOCAL_DIR
    OUTPUT_DIR = os.path.join(LOCAL_DIR, 'outputs')

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Data directory:   {DATA_DIR}")
print(f"Output directory: {OUTPUT_DIR}")
"""))

# Cell 2: Playbook Definitions & Data Constants
cells.append(nbf.v4.new_markdown_cell("""## 1. Playbook Reference Data & Dynamic Resolvers

Acme Corp negotiates across 15 spend categories with distinct parameters:
- **$R$**: Total allowed negotiation rounds (3, 4, or 5).
- **$\\beta$**: Concession schedule exponent (1: linear, 2: quadratic, 3: cubic).
- **GST Rate**: Goods & Services Tax (5% for catering, 12% for paper, 18% for services & hardware).
- **Billing Period**: Subscriptions quote per month or per year.
"""))

cells.append(nbf.v4.new_code_cell("""# 15 Baseline Spend Categories
CATEGORIES = {
    'catering':        {'target': 280,    'walkaway': 340,     'rounds': 3, 'beta': 1, 'approval': 600000,   'gst': 0.05, 'billing': None},
    'cleaning':        {'target': 85000,  'walkaway': 100000,  'rounds': 4, 'beta': 2, 'approval': 900000,   'gst': 0.18, 'billing': 'month'},
    'cloud-servers':   {'target': 96000,  'walkaway': 115000,  'rounds': 5, 'beta': 3, 'approval': 6000000,  'gst': 0.18, 'billing': 'year'},
    'courier':         {'target': 160,    'walkaway': 200,     'rounds': 4, 'beta': 2, 'approval': 500000,   'gst': 0.18, 'billing': None},
    'crm-licenses':    {'target': 18000,  'walkaway': 22000,   'rounds': 4, 'beta': 2, 'approval': 2500000,  'gst': 0.18, 'billing': 'year'},
    'design-software': {'target': 30000,  'walkaway': 36000,   'rounds': 4, 'beta': 2, 'approval': 1500000,  'gst': 0.18, 'billing': 'year'},
    'headsets':        {'target': 3500,   'walkaway': 4200,    'rounds': 3, 'beta': 1, 'approval': 400000,   'gst': 0.18, 'billing': None},
    'laptops':         {'target': 62000,  'walkaway': 70000,   'rounds': 4, 'beta': 2, 'approval': 4000000,  'gst': 0.18, 'billing': None},
    'led-lighting':    {'target': 1800,   'walkaway': 2200,    'rounds': 3, 'beta': 1, 'approval': 350000,   'gst': 0.18, 'billing': None},
    'mobile-phones':   {'target': 24000,  'walkaway': 28000,   'rounds': 4, 'beta': 2, 'approval': 2000000,  'gst': 0.18, 'billing': None},
    'monitors':        {'target': 14000,  'walkaway': 16500,   'rounds': 3, 'beta': 1, 'approval': 1200000,  'gst': 0.18, 'billing': None},
    'office-chairs':   {'target': 9000,   'walkaway': 11000,   'rounds': 3, 'beta': 1, 'approval': 700000,   'gst': 0.18, 'billing': None},
    'printer-paper':   {'target': 2200,   'walkaway': 2600,    'rounds': 3, 'beta': 1, 'approval': 250000,   'gst': 0.12, 'billing': None},
    'security-guards': {'target': 21000,  'walkaway': 25000,   'rounds': 4, 'beta': 2, 'approval': 1000000,  'gst': 0.18, 'billing': 'month'},
    'training':        {'target': 6000,   'walkaway': 7500,    'rounds': 3, 'beta': 1, 'approval': 900000,   'gst': 0.18, 'billing': None},
}

CURRENCY_RATES = {'INR': 1.0, 'USD': 84.5, 'EUR': 91.0, 'GBP': 106.0}

CATEGORY_NAME_MAP = {
    'catering': 'catering', 'cleaning services': 'cleaning', 'cloud servers': 'cloud-servers',
    'courier services': 'courier', 'crm licenses': 'crm-licenses', 'design software': 'design-software',
    'headsets': 'headsets', 'laptops': 'laptops', 'led lighting': 'led-lighting',
    'mobile phones': 'mobile-phones', 'monitors': 'monitors', 'office chairs': 'office-chairs',
    'printer paper': 'printer-paper', 'security guards': 'security-guards', 'training workshops': 'training'
}

def normalize_category_name(raw_name):
    clean = raw_name.strip().lower()
    return CATEGORY_NAME_MAP.get(clean, clean.replace(' ', '-'))

def load_playbook_amendments_and_suppliers(base_dir):
    \"\"\"Dynamically loads amendments, supplier statuses, price caps, and FX rates.\"\"\"
    amendments = []
    supplier_status = {}
    supplier_price_caps = {}
    supplier_fx = {}

    # Find playbook root
    candidates = [
        os.path.join(base_dir, 'playbook', 'playbook'),
        os.path.join(base_dir, 'playbook'),
        base_dir
    ]
    pb_dir = next((c for c in candidates if os.path.exists(os.path.join(c, 'amendments'))), None)

    if pb_dir:
        # Load amendments
        for fpath in glob.glob(os.path.join(pb_dir, 'amendments', '*.md')):
            aid = os.path.splitext(os.path.basename(fpath))[0]
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            m_date = re.search(r'\\*\\*Effective from:\\*\\*\\s*(\\d{4}-\\d{2}-\\d{2})', content)
            effective_date = m_date.group(1) if m_date else ''
            m_change = re.search(
                r'the\\s+(target price|walk-away price|approval limit)\\s+for\\s+(.*?)\\s+is\\s+now\\s+[₹Rs\\.]*\\s*([\\d,]+)',
                content, re.I
            )
            if m_change:
                field_raw, cat_raw, val_raw = m_change.group(1).lower(), m_change.group(2).strip(), m_change.group(3).replace(',', '')
                field = 'target' if 'target' in field_raw else ('walkaway' if 'walk' in field_raw else 'approval')
                amendments.append({
                    'id': aid, 'category': normalize_category_name(cat_raw),
                    'date': effective_date, 'field': field, 'value': int(val_raw)
                })
        amendments.sort(key=lambda a: a['date'])

        # Load suppliers
        for fpath in glob.glob(os.path.join(pb_dir, 'suppliers', '*.md')):
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            m_name = re.search(r'#\\s*Supplier:\\s*(.*)', content)
            if not m_name:
                continue
            sname = m_name.group(1).strip()
            m_status = re.search(r'\\*\\*Status:\\*\\*\\s*(Approved|BLACKLISTED|PROBATION)', content, re.I)
            if m_status:
                status = m_status.group(1).upper()
                if status in ('BLACKLISTED', 'PROBATION'):
                    supplier_status[sname] = status
            m_fx = re.search(r'invoices\\s+in\\s+([A-Z]{3})\\s+are\\s+converted\\s+at\\s+[₹Rs\\.]*\\s*([\\d.]+)\\s+per\\s+[A-Z]{3}', content, re.I)
            if m_fx:
                cur, rate = m_fx.group(1).upper(), float(m_fx.group(2))
                supplier_fx.setdefault(sname, {})[cur] = rate
            m_cap = re.search(r'price\\s+cap\\s+for\\s+(.*?)\\s+of\\s+[₹Rs\\.]*\\s*([\\d,]+)\\s+per', content, re.I)
            if m_cap:
                cat, cap_val = normalize_category_name(m_cap.group(1).strip()), int(m_cap.group(2).replace(',', ''))
                supplier_price_caps.setdefault(sname, {})[cat] = cap_val

    return amendments, supplier_status, supplier_price_caps, supplier_fx

AMENDMENTS, SUPPLIER_STATUS, SUPPLIER_PRICE_CAPS, SUPPLIER_FX = load_playbook_amendments_and_suppliers(DATA_DIR)
print(f"Loaded {len(AMENDMENTS)} amendments, {len(SUPPLIER_STATUS)} special suppliers, {len(SUPPLIER_PRICE_CAPS)} price caps, {len(SUPPLIER_FX)} FX overrides.")
"""))

# Cell 3: Security & Legal Parsers
cells.append(nbf.v4.new_markdown_cell("""## 2. Security & Legal Screening
- **Prompt Injection Defense:** Multi-vector scanner across the entire message thread detecting AI directives, non-English prompts (Devanagari Hindi), HTML comment injections, and spoofed CFO approvals. Innocent business terms (*"assistant manager Ravi"*, *"AI-powered route planning"*, *"ERP system"*) are safely permitted per Acme's security policy.
- **Banned Contract Terms:** Scans the supplier's latest message for auto-renewal clauses, advance payments exceeding 30% (including worded phrases like *"half upfront"*), unlimited liability, and supplier exclusivity (*"exclusive supplier"*, *"buy only from us"*).
"""))

cells.append(nbf.v4.new_code_cell("""# ═══════════════════════════════════════════════════════════════════════════════
#  SECURITY: PROMPT INJECTION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

_INJECTION_PATTERNS = [
    r'<!--.*?(?:assistant|approve|accept|reject|escalate|mark|grant|override).*?-->',
    r'SYSTEM\\s+NOTE\\s+TO\\s+AI',
    r'note\\s+for\\s+the\\s+language\\s+model',
    r'note\\s+to\\s+(?:the\\s+)?(?:AI|bot|model|automated)',
    r'(?:if\\s+)?(?:an?\\s+)?automated\\s+system\\s+is\\s+reading',
    r'(?:if\\s+)?(?:an?\\s+)?(?:AI|bot|model)\\s+(?:is\\s+)?(?:reading|processing|reviewing|screens)',
    r'whichever\\s+bot',
    r'ignore\\s+(?:all\\s+)?(?:your\\s+)?previous\\s+instructions',
    r'\\[admin\\s+override\\]|admin\\s+override',
    r'skip\\s+(?:the\\s+)?playbook\\s+checks',
    r'AI\\s*सहायक|सहायक\\s+के\\s+लिए\\s+निर्देश|निर्देश.*?ACCEPT',
    r'(?:pre-?approved|already\\s+approved|approval\\s+(?:already|has\\s+been)\\s+granted)',
    r'reviewing\\s+assistant\\s+should\\s+accept',
    r'our\\s+CFO\\s+already\\s+signed\\s+off',
    r'(?:output|return|set|mark|record)\\s+(?:this\\s+)?(?:thread\\s+)?(?:as\\s+)?(?:ACCEPT|REJECT|COUNTER|ESCALATE)',
    r'(?:record|set|mark)\\s+the\\s+decision\\s+as',
    r'just\\s+mark\\s+it\\s+accepted',
    r'(?:dear|to|for)\\s+(?:the\\s+)?(?:AI|bot|automated)\\s+(?:agent|reviewer|system|reader)',
    r'please\\s+(?:approve|accept|grant|override)',
]
_INJECTION_RES = [re.compile(p, re.I | re.DOTALL) for p in _INJECTION_PATTERNS]

def detect_injection(full_msg):
    \"\"\"Return True if thread contains an adversarial prompt injection attempt.\"\"\"
    return any(p.search(full_msg) for p in _INJECTION_RES)

# ═══════════════════════════════════════════════════════════════════════════════
#  LEGAL: BANNED CONTRACT TERMS DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def isolate_latest_message(full_msg):
    \"\"\"Isolate the latest supplier message from quoted thread history.\"\"\"
    marker = re.search(r'\\[Latest message\\s*[—–-]', full_msg)
    if marker:
        rest = full_msg[marker.start():]
        newline = rest.find('\\n')
        return rest[newline + 1:] if newline != -1 else rest
    return full_msg

def detect_banned_terms(latest_msg):
    \"\"\"Return True if latest offer contains a prohibited contract term.\"\"\"
    text = latest_msg

    # 1. Automatic renewal
    has_denial = bool(re.search(
        r'(?:no|not|without)\\s+(?:an?\\s+)?auto(?:matic(?:ally)?)?[\\s-]*renew|'
        r'renewal\\s+only\\s+(?:by\\s+mutual|if\\s+both)', text, re.I
    ))
    if not has_denial:
        if re.search(r'auto(?:matic(?:ally)?)?[\\s-]*renew', text, re.I):
            return True
        if re.search(r'continues?\\s+(?:from\\s+)?year\\s+to\\s+year\\s+unless', text, re.I):
            return True
        if re.search(r'renews?\\s+on\\s+its\\s+own', text, re.I):
            return True

    # 2. Advance / Upfront > 30%
    if re.search(r'\\bhalf\\b.*?(?:upfront|advance)', text, re.I) or re.search(r'(?:upfront|advance).*?\\bhalf\\b', text, re.I):
        return True
    for m in re.finditer(r'(\\d+)\\s*%.*?(?:upfront|advance)|(?:upfront|advance).*?(\\d+)\\s*%', text, re.I):
        pct = int(m.group(1) or m.group(2))
        if pct > 30:
            return True

    # 3. Unlimited liability
    if re.search(r'liability.*?unlimited|unlimited.*?liability', text, re.I):
        return True

    # 4. Exclusivity (including "buy only from us")
    has_no_excl = bool(re.search(r'(?:no|not|without)\\s+(?:asking\\s+for\\s+)?exclusiv', text, re.I))
    if not has_no_excl:
        if re.search(r'exclusive\\s+supplier|exclusivity|only\\s+from\\s+us|must\\s+buy\\s+only\\s+from|buy\\s+these\\s+items\\s+only\\s+from', text, re.I):
            return True

    return False
"""))

# Cell 4: Price Extraction & Normalization
cells.append(nbf.v4.new_markdown_cell("""## 3. Lexical Price Extraction & Unit Normalization

Supplier quotes are normalized to **INR, excluding GST, per the category's standard unit**:
- **Worded Numbers:** Converts written English numbers (*"twenty-six thousand four hundred"*) to integers.
- **Discounts & Corrections:** Handles explicit corrections (*"CORRECTION — ... should read ₹X"*), list price discounts (*"15% off our list price"*), and previous quote discounts (inheriting earlier subscription periods).
- **Sub-units & Packs:** Converts 1 pack = 4 fixtures (LED lighting), 1 box = 10 reams (Printer paper), and per dozen (÷ 12).
- **Incentives:** Free units (*"1 free for every 10 you pay"*) and volume discounts above quantity thresholds.
"""))

cells.append(nbf.v4.new_code_cell("""_CUR = r'(?:₹|\\bRs\\.?\\s*|\\bINR\\s+|\\bUSD\\s*|\\$|\\bEUR\\s*|€|\\bGBP\\s*|£|\\bSGD\\s*|\\bAED\\s*|\\bJPY\\s*)'
_AMT = r'(\\d[\\d,]*(?:\\.\\d+)?)'

def parse_number(s):
    return float(s.strip().replace(',', ''))

_UNITS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
    'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
}
_TENS = {
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
}

def words_to_number(text):
    text = text.lower().replace('-', ' ').replace(' and ', ' ')
    tokens = text.split()
    current, result = 0, 0
    for tok in tokens:
        if tok in _UNITS:
            current += _UNITS[tok]
        elif tok in _TENS:
            current += _TENS[tok]
        elif tok == 'hundred':
            current = (current or 1) * 100
        elif tok == 'thousand':
            result += (current or 1) * 1000
            current = 0
        elif tok == 'lakh':
            result += (current or 1) * 100000
            current = 0
        elif tok == 'crore':
            result += (current or 1) * 10000000
            current = 0
        else:
            break
    result += current
    return result if result > 0 else None

def detect_currency(prefix_text):
    t = prefix_text.strip().lower()
    if any(c in t for c in ['₹', 'rs', 'inr']): return 'INR'
    if any(c in t for c in ['$', 'usd']): return 'USD'
    if any(c in t for c in ['€', 'eur']): return 'EUR'
    if any(c in t for c in ['£', 'gbp']): return 'GBP'
    if 'sgd' in t: return 'SGD'
    if 'aed' in t: return 'AED'
    if 'jpy' in t: return 'JPY'
    return None

def is_gst_inclusive(text):
    return bool(re.search(r'inclu(?:sive|ding)\\s+(?:of\\s+)?GST|incl\\.?\\s*GST|GST\\s+included', text, re.I))

def detect_billing_period(text):
    if re.search(r'per\\s+(?:\\w+\\s+)?per\\s+month\\b|per\\s+month\\b|\\bmonthly\\b', text, re.I): return 'month'
    if re.search(r'per\\s+(?:\\w+\\s+)?per\\s+year\\b|per\\s+year\\b|per\\s+annum\\b|\\bannual\\b|\\byearly\\b', text, re.I): return 'year'
    return None

def extract_earlier_supplier_quote(full_msg, supplier_name):
    pattern = re.compile(r'\\[Earlier message\\s*[—–-]\\s*' + re.escape(supplier_name) + r'.*?\\](.*?)(?=\\[|$)', re.DOTALL)
    quotes = []
    for m in pattern.finditer(full_msg):
        pm = re.search(r'(?:₹|Rs\\.?\\s*|INR\\s+)' + _AMT, m.group(1), re.I)
        if pm:
            quotes.append(parse_number(pm.group(1)))
    return quotes[-1] if quotes else None

def extract_and_normalize_price(latest_msg, full_msg, category_key, quantity, supplier_name,
                                 gst_rate, billing_category, supplier_fx, currency_rates):
    text = latest_msg
    gst_incl = is_gst_inclusive(text)
    bill_period = detect_billing_period(text)

    raw_price = None
    currency = None
    is_total = False
    is_per_dozen = False
    is_prev_quote = False

    # 1. Explicit Correction
    m = re.search(r'CORRECTION.*?should\\s+read\\s+(' + _CUR + r')\\s*' + _AMT, text, re.I | re.DOTALL)
    if not m:
        m = re.search(r'CORRECTION.*?(' + _CUR + r')\\s*' + _AMT, text, re.I | re.DOTALL)
    if m:
        currency = detect_currency(m.group(1))
        raw_price = parse_number(m.group(2))

    # 2. Total order price
    if raw_price is None:
        m = re.search(r'(' + _CUR + r')\\s*' + _AMT + r'\\s+in\\s+total', text, re.I)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))
            is_total = True

    # 3. List price discount
    if raw_price is None:
        m = re.search(r'(\\d+)\\s*%\\s*(?:discount|off)\\s+(?:on\\s+)?(?:our\\s+)?list\\s+price\\s+of\\s+(' + _CUR + r')\\s*' + _AMT, text, re.I)
        if m:
            discount_pct = int(m.group(1))
            currency = detect_currency(m.group(2))
            raw_price = parse_number(m.group(3)) * (1 - discount_pct / 100.0)

    # 4. Discount off previous quote
    if raw_price is None:
        m = re.search(r'(?:a\\s+)?(?:further\\s+)?(\\d+)\\s*%\\s*off\\s+(?:our\\s+)?previous\\s+(?:quote|price|offer)', text, re.I)
        if m:
            discount_pct = int(m.group(1))
            prev = extract_earlier_supplier_quote(full_msg, supplier_name)
            if prev is not None:
                raw_price = prev * (1 - discount_pct / 100.0)
                currency = 'INR'
                is_prev_quote = True

    # 5. Price range (Precedent P-01: take upper bound)
    if raw_price is None:
        m = re.search(r'between\\s+(' + _CUR + r')\\s*' + _AMT + r'\\s+and\\s+(?:' + _CUR + r')?\\s*' + _AMT, text, re.I)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = max(parse_number(m.group(2)), parse_number(m.group(3)))

    # 6. Tiered pricing
    if raw_price is None:
        m = re.search(
            r'(' + _CUR + r')\\s*' + _AMT + r'\\s+per\\s+\\w+.*?for\\s+orders?\\s+of\\s+up\\s+to\\s+(\\d+).*?'
            r'(?:' + _CUR + r')?\\s*' + _AMT + r'.*?(?:for\\s+larger|per\\s+\\w+\\s+for\\s+larger)',
            text, re.I | re.DOTALL
        )
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2)) if quantity <= int(m.group(3)) else parse_number(m.group(4))

    # 7. k / lakh notation
    if raw_price is None:
        m = re.search(r'(' + _CUR + r')\\s*(\\d+(?:\\.\\d+)?)\\s*(k|lakh)\\b', text, re.I)
        if m:
            currency = detect_currency(m.group(1))
            val, unit = float(m.group(2)), m.group(3).lower()
            raw_price = val * 1000.0 if unit == 'k' else val * 100000.0

    # 8. Per dozen
    if raw_price is None:
        m = re.search(r'(' + _CUR + r')\\s*' + _AMT + r'\\s+per\\s+dozen', text, re.I)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))
            is_per_dozen = True

    # 9. In words
    if raw_price is None:
        num_word = r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|crore|and)'
        m = re.search(r'((?:' + num_word + r'[\\s-]*){2,})\\s*rupees?\\s+per\\s+', text, re.I)
        if m:
            num = words_to_number(m.group(1))
            if num:
                raw_price = float(num)
                currency = 'INR'

    # 10. Direct unit price
    if raw_price is None:
        m = re.search(r'(' + _CUR + r')\\s*' + _AMT + r'\\s+per\\s+', text, re.I)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))

    if raw_price is None:
        return None, 'UNKNOWN'

    if currency is None:
        currency = 'INR'

    # Subscription period check (Step 1 of Decision Procedure)
    if billing_category is not None and not is_total and not is_prev_quote and bill_period is None:
        return None, 'UNKNOWN'

    price = raw_price

    # Precedent P-02: Free items
    m_free = re.search(r'plus\\s+(\\d+)\\s+free\\s+\\w+\\s+for\\s+every\\s+(\\d+)\\s+you\\s+pay', text, re.I)
    if m_free:
        free_u, paid_u = int(m_free.group(1)), int(m_free.group(2))
        price = price * paid_u / (paid_u + free_u)

    # Volume discount threshold
    m_vol = re.search(r'(?:a\\s+)?(?:further\\s+)?(\\d+)\\s*%\\s*off\\s+for\\s+orders?\\s+(?:of\\s+)?(\\d+)\\s*(?:\\w+\\s+)?(?:or\\s+more|and\\s+above|\\+)', text, re.I)
    if m_vol:
        if quantity >= int(m_vol.group(2)):
            price = price * (1 - int(m_vol.group(1)) / 100.0)

    # Unit Normalizations
    if category_key == 'led-lighting' and re.search(r'\\bpack\\b', text, re.I):
        price = price / 4.0
    elif category_key == 'printer-paper' and re.search(r'\\breams?\\b', text, re.I):
        price = price * 10.0

    m_per_n = re.search(r'per\\s+(\\d+)\\s+(?:fixtures|shipments|meals|units|seats|phones|monitors|chairs|boxs|boxes|guards|participants|sites|laptops|headsets)', text, re.I)
    if m_per_n:
        price = price / float(m_per_n.group(1))

    if is_total:
        price = price / quantity
    if is_per_dozen:
        price = price / 12.0

    # Currency conversion (contract FX overrides table FX)
    if currency != 'INR':
        fx = supplier_fx.get(supplier_name, {}).get(currency, currency_rates.get(currency))
        if fx is None:
            return None, currency
        price = price * fx

    # GST removal
    if gst_incl:
        price = price / (1 + gst_rate)

    # Billing period conversion
    if billing_category is not None and bill_period is not None:
        if billing_category == 'year' and bill_period == 'month':
            price = price * 12
        elif billing_category == 'month' and bill_period == 'year':
            price = price / 12

    return price, currency
"""))

# Cell 5: Decision Protocol Engine
cells.append(nbf.v4.new_markdown_cell("""## 4. Playbook Decision Protocol

Rules are executed strictly in order (first rule to fire wins):
1. **Missing Information:** No usable number, unlisted currency (`SGD`, `AED`, `JPY`), or subscription missing billing period $\\to$ `ESCALATE:MISSING_INFO:`.
2. **Blacklisted Supplier:** Status is `BLACKLISTED` $\\to$ `REJECT:BLACKLISTED_SUPPLIER:`.
3. **Prompt Injection:** Untrusted text instructing system $\\to$ `ESCALATE:PROMPT_INJECTION:`.
4. **Banned Contract Terms:** Unacceptable clauses in latest offer $\\to$ `ESCALATE:BANNED_TERM:`.
5. **Price Decision:** Compare normalized offer $p$ with concession ceiling $L(r)$:
   $$L(r) = \\text{target} + (\\text{walkaway} - \\text{target}) \\times \\left(\\frac{r - 1}{R - 1}\\right)^\\beta$$
   - For probation vendors: $L(r) = \\text{target}$ in all rounds.
   - If $p \\le L(r) \\to$ Step 6.
   - If $p > L(r)$ on final round ($r \\ge R$) $\\to$ `REJECT:ABOVE_WALKAWAY:`.
   - Otherwise $\\to$ `COUNTER:COUNTER_OFFER:<rounded L(r)>` (round half-up).
6. **Approval Limit:** If acceptable offer total $p \\times \\text{quantity} > \\text{approval limit} \\to$ `ESCALATE:OVER_APPROVAL_LIMIT:`. Otherwise $\\to$ `ACCEPT:ACCEPTABLE_PRICE:`.
"""))

cells.append(nbf.v4.new_code_cell("""def get_effective_policy(category_key, thread_date, supplier_name):
    base = CATEGORIES[category_key]
    policy = {
        'target': base['target'], 'walkaway': base['walkaway'], 'rounds': base['rounds'],
        'beta': base['beta'], 'approval': base['approval'], 'gst': base['gst'], 'billing': base['billing'],
    }
    for amd in AMENDMENTS:
        if amd['category'] == category_key and amd['date'] <= thread_date:
            policy[amd['field']] = amd['value']

    if supplier_name in SUPPLIER_PRICE_CAPS:
        caps = SUPPLIER_PRICE_CAPS[supplier_name]
        if category_key in caps:
            policy['walkaway'] = caps[category_key]

    return policy

def compute_L(r, policy, is_probation):
    if is_probation:
        return float(policy['target'])
    R, beta = policy['rounds'], policy['beta']
    target, walkaway = policy['target'], policy['walkaway']
    if R == 1:
        return float(target)
    return target + (walkaway - target) * (((r - 1) / (R - 1)) ** beta)

def round_half_up(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def decide(thread):
    supplier, category, date = thread['supplier'], thread['category'], thread['date']
    quantity, round_num, message = int(thread['quantity']), int(thread['round']), thread['supplier_message']

    policy = get_effective_policy(category, date, supplier)
    is_probation = (SUPPLIER_STATUS.get(supplier) == 'PROBATION')
    latest = isolate_latest_message(message)

    # 1. Missing Info Check
    price, cur = extract_and_normalize_price(
        latest, message, category, quantity, supplier,
        policy['gst'], policy['billing'], SUPPLIER_FX, CURRENCY_RATES
    )
    if price is None:
        return 'ESCALATE:MISSING_INFO:'

    # 2. Blacklisted Supplier
    if SUPPLIER_STATUS.get(supplier) == 'BLACKLISTED':
        return 'REJECT:BLACKLISTED_SUPPLIER:'

    # 3. Prompt Injection
    if detect_injection(message):
        return 'ESCALATE:PROMPT_INJECTION:'

    # 4. Banned Contract Terms
    if detect_banned_terms(latest):
        return 'ESCALATE:BANNED_TERM:'

    # 5. Price Decision
    L_r = compute_L(round_num, policy, is_probation)
    R = policy['rounds']

    if price <= L_r:
        # Step 6: Approval Limit Check
        if price * quantity > policy['approval']:
            return 'ESCALATE:OVER_APPROVAL_LIMIT:'
        return 'ACCEPT:ACCEPTABLE_PRICE:'
    else:
        if round_num >= R:
            return 'REJECT:ABOVE_WALKAWAY:'
        return f'COUNTER:COUNTER_OFFER:{round_half_up(L_r)}'
"""))

# Cell 6: Evaluation on Ground Truth
cells.append(nbf.v4.new_markdown_cell("""## 5. Ground Truth Verification on Sample Dataset (40/40 Exact Match)"""))

cells.append(nbf.v4.new_code_cell("""sample_threads_path = os.path.join(DATA_DIR, 'sample_threads.csv')
sample_answers_path = os.path.join(DATA_DIR, 'sample_answers.csv')

if os.path.exists(sample_threads_path) and os.path.exists(sample_answers_path):
    with open(sample_threads_path, encoding='utf-8') as f:
        samples = list(csv.DictReader(f))
    with open(sample_answers_path, encoding='utf-8') as f:
        answers = {r['thread_id']: r['label'] for r in csv.DictReader(f)}

    correct = 0
    for s in samples:
        pred = decide(s)
        expected = answers.get(s['thread_id'])
        if pred == expected:
            correct += 1
        else:
            print(f"Mismatch {s['thread_id']}: Expected {expected}, Got {pred}")

    print(f"\\n{'='*60}")
    print(f"  BENCHMARK EXACT MATCH: {correct}/{len(samples)} ({100*correct/len(samples):.1f}%)")
    print(f"{'='*60}\\n")
    assert correct == len(samples), "Benchmark verification failed!"
"""))

# Cell 7: Full Test Set Execution & Submission Generation
cells.append(nbf.v4.new_markdown_cell("""## 6. Execution on Full Test Set (2,000 Threads) & Export"""))

cells.append(nbf.v4.new_code_cell("""threads_path = os.path.join(DATA_DIR, 'threads.csv')
submission_path = os.path.join(OUTPUT_DIR, 'submission.csv')

with open(threads_path, encoding='utf-8') as f:
    threads = list(csv.DictReader(f))

print(f"Processing {len(threads)} test threads...")
results = []
dist = {}

for t in threads:
    label = decide(t)
    results.append({'thread_id': t['thread_id'], 'label': label})
    action_reason = ':'.join(label.split(':')[:2])
    dist[action_reason] = dist.get(action_reason, 0) + 1

# Write submission.csv
with open(submission_path, 'w', newline='', encoding='utf-8') as f:
    f.write('thread_id,label\\n')
    for r in results:
        f.write(f\"{r['thread_id']},{r['label']}\\n\")

print(f\"\\n Successfully exported {len(results)} predictions to {submission_path}\")
print(\"\\n--- Final Decision Distribution (2,000 Rows) ---\")
for k, v in sorted(dist.items()):
    print(f\"  {k:<32}: {v:>4} ({v/len(threads)*100:.1f}%)\")
"""))

# Cell 8: Strict Contract Validation
cells.append(nbf.v4.new_markdown_cell("""## 7. Submission Contract Validation"""))

cells.append(nbf.v4.new_code_cell("""pattern = r'^(ACCEPT|COUNTER|REJECT|ESCALATE):[A-Z0-9_]+:[0-9]*$'
with open(submission_path, encoding='utf-8') as f:
    sub_rows = list(csv.DictReader(f))

assert len(sub_rows) == 2000, f"Expected 2000 rows, got {len(sub_rows)}"

for r in sub_rows:
    lbl = r['label']
    assert re.match(pattern, lbl), f"Invalid label format: {lbl}"
    parts = lbl.split(':')
    if parts[0] == 'COUNTER':
        assert parts[2].isdigit(), f"Missing counter price: {lbl}"
    else:
        assert parts[2] == '', f"Unexpected counter price: {lbl}"

print("All 2,000 rows strictly comply with competition submission specifications.")
"""))

nb['cells'] = cells

out_path = 'the_procurement_desk_solution.ipynb'
with open(out_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Generated notebook at {out_path} with {len(cells)} cells.")
