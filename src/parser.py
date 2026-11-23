"""Message parsing: injection detection, banned-term detection, price extraction (ultra-optimized)."""

import re

# ═══════════════════════════════════════════════════════════════════════════════
#  LATEST MESSAGE ISOLATION
# ═══════════════════════════════════════════════════════════════════════════════

RE_LATEST_MARKER = re.compile(r'\[Latest message\s*[—–-]')

def isolate_latest_message(full_msg):
    """Return only the supplier's latest message, excluding quoted history."""
    marker = RE_LATEST_MARKER.search(full_msg)
    if marker:
        rest = full_msg[marker.start():]
        newline = rest.find('\n')
        if newline != -1:
            return rest[newline + 1:]
        return rest
    return full_msg


# ═══════════════════════════════════════════════════════════════════════════════
#  PROMPT INJECTION DETECTION  (scan ENTIRE message, including quoted parts)
# ═══════════════════════════════════════════════════════════════════════════════

_INJECTION_PATTERNS = [
    r'<!--.*?(?:assistant|approve|accept|reject|escalate|mark|grant|override).*?-->',
    r'SYSTEM\s+NOTE\s+TO\s+AI',
    r'note\s+for\s+the\s+language\s+model',
    r'note\s+to\s+(?:the\s+)?(?:AI|bot|model|automated)',
    r'(?:if\s+)?(?:an?\s+)?automated\s+system\s+is\s+reading',
    r'(?:if\s+)?(?:an?\s+)?(?:AI|bot|model)\s+(?:is\s+)?(?:reading|processing|reviewing|screens)',
    r'whichever\s+bot',
    r'ignore\s+(?:all\s+)?(?:your\s+)?previous\s+instructions',
    r'\[admin\s+override\]|admin\s+override',
    r'skip\s+(?:the\s+)?playbook\s+checks',
    r'AI\s*सहायक|सहायक\s+के\s+लिए\s+निर्देश|निर्देश.*?ACCEPT',
    r'(?:pre-?approved|already\s+approved|approval\s+(?:already|has\s+been)\s+granted)',
    r'reviewing\s+assistant\s+should\s+accept',
    r'our\s+CFO\s+already\s+signed\s+off',
    r'(?:output|return|set|mark|record)\s+(?:this\s+)?(?:thread\s+)?(?:as\s+)?(?:ACCEPT|REJECT|COUNTER|ESCALATE)',
    r'(?:record|set|mark)\s+the\s+decision\s+as',
    r'just\s+mark\s+it\s+accepted',
    r'(?:dear|to|for)\s+(?:the\s+)?(?:AI|bot|automated)\s+(?:agent|reviewer|system|reader)',
    r'please\s+(?:approve|accept|grant|override)',
]
_COMBINED_INJECTION_RE = re.compile('|'.join(f'(?:{p})' for p in _INJECTION_PATTERNS), re.I | re.DOTALL)


def detect_injection(full_msg):
    """Return True if the message contains a prompt injection attempt."""
    m_lower = full_msg.lower()
    if not (
        '<!--' in full_msg or
        'system note' in m_lower or
        'language model' in m_lower or
        'note to' in m_lower or
        'automated system' in m_lower or
        'whichever bot' in m_lower or
        'previous instructions' in m_lower or
        'ignore' in m_lower or
        'admin override' in m_lower or
        'playbook' in m_lower or
        'सहायक' in full_msg or 'निर्देश' in full_msg or
        'pre-approved' in m_lower or 'preapproved' in m_lower or
        'already approved' in m_lower or 'signed off' in m_lower or
        'has been granted' in m_lower or 'approval already' in m_lower or
        'reviewing assistant' in m_lower or
        'decision as' in m_lower or 'mark it accepted' in m_lower or
        (('reading' in m_lower or 'processing' in m_lower or 'screens' in m_lower or 'reviewing' in m_lower) and ('ai' in m_lower or 'bot' in m_lower or 'model' in m_lower)) or
        (('dear' in m_lower or 'to' in m_lower or 'for' in m_lower) and ('ai' in m_lower or 'bot' in m_lower or 'automated' in m_lower)) or
        'please approve' in m_lower or 'please accept' in m_lower or 'please grant' in m_lower or 'please override' in m_lower or
        ('accept' in full_msg and ('output' in m_lower or 'return' in m_lower or 'set' in m_lower or 'mark' in m_lower or 'record' in m_lower))
    ):
        return False
    return bool(_COMBINED_INJECTION_RE.search(full_msg))


# ═══════════════════════════════════════════════════════════════════════════════
#  BANNED CONTRACT TERMS  (scan only LATEST message)
# ═══════════════════════════════════════════════════════════════════════════════

RE_DENIAL = re.compile(
    r'(?:no|not|without)\s+(?:an?\s+)?auto(?:matic(?:ally)?)?[\s-]*renew|'
    r'renewal\s+only\s+(?:by\s+mutual|if\s+both)',
    re.I
)
RE_AUTO_RENEW = re.compile(r'auto(?:matic(?:ally)?)?[\s-]*renew', re.I)
RE_YEAR_TO_YEAR = re.compile(r'continues?\s+(?:from\s+)?year\s+to\s+year\s+unless', re.I)
RE_RENEWS_OWN = re.compile(r'renews?\s+on\s+its\s+own', re.I)
RE_HALF_ADVANCE = re.compile(r'\bhalf\b.*?(?:upfront|advance)|(?:upfront|advance).*?\bhalf\b', re.I)
RE_PCT_ADVANCE = re.compile(r'(\d+)\s*%.*?(?:upfront|advance)|(?:upfront|advance).*?(\d+)\s*%', re.I)
RE_LIABILITY = re.compile(r'liability.*?unlimited|unlimited.*?liability', re.I)
RE_NO_EXCL = re.compile(r'(?:no|not|without)\s+(?:asking\s+for\s+)?exclusiv', re.I)
RE_EXCL = re.compile(r'exclusive\s+supplier|exclusivity|only\s+from\s+us|must\s+buy\s+only\s+from|buy\s+these\s+items\s+only\s+from', re.I)


def detect_banned_terms(latest_msg):
    """Return True if the latest message contains a banned contract term."""
    text = latest_msg
    t_lower = text.lower()

    # 1. Auto-renewal
    if 'renew' in t_lower or 'year to year' in t_lower:
        if not RE_DENIAL.search(text):
            if RE_AUTO_RENEW.search(text) or RE_YEAR_TO_YEAR.search(text) or RE_RENEWS_OWN.search(text):
                return True

    # 2. Upfront / advance > 30% (numbers or words like 'half')
    if 'upfront' in t_lower or 'advance' in t_lower or 'half' in t_lower:
        if RE_HALF_ADVANCE.search(text):
            return True
        for m in RE_PCT_ADVANCE.finditer(text):
            pct = int(m.group(1) or m.group(2))
            if pct > 30:
                return True

    # 3. Unlimited liability for Acme
    if 'liability' in t_lower and 'unlimited' in t_lower:
        if RE_LIABILITY.search(text):
            return True

    # 4. Exclusivity
    if 'exclusiv' in t_lower or 'only from' in t_lower or 'only from us' in t_lower:
        if not RE_NO_EXCL.search(text):
            if RE_EXCL.search(text):
                return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  NUMBER PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_number(s):
    """Parse a numeric string (handles Indian commas like 1,20,000)."""
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
    """Convert English number words to integer. E.g. 'twenty-nine thousand seven hundred' → 29700."""
    text = text.lower().replace('-', ' ').replace(' and ', ' ')
    tokens = text.split()
    current = 0
    result = 0
    for tok in tokens:
        if tok in _UNITS:
            current += _UNITS[tok]
        elif tok in _TENS:
            current += _TENS[tok]
        elif tok == 'hundred':
            current = (current if current else 1) * 100
        elif tok == 'thousand':
            result += (current if current else 1) * 1000
            current = 0
        elif tok == 'lakh':
            result += (current if current else 1) * 100000
            current = 0
        elif tok == 'crore':
            result += (current if current else 1) * 10000000
            current = 0
        else:
            break
    result += current
    return result if result > 0 else None


# ═══════════════════════════════════════════════════════════════════════════════
#  CURRENCY & GST DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

_CUR = r'(?:₹|\bRs\.?\s*|\bINR\s+|\bUSD\s*|\$|\bEUR\s*|€|\bGBP\s*|£|\bSGD\s*|\bAED\s*|\bJPY\s*)'
_AMT = r'(\d[\d,]*(?:\.\d+)?)'  # captures an amount starting with digit
num_word = r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|crore|and)'

RE_GST = re.compile(r'inclu(?:sive|ding)\s+(?:of\s+)?GST|incl\.?\s*GST|GST\s+included', re.I)
RE_PERIOD_MONTH = re.compile(r'per\s+(?:\w+\s+)?per\s+month\b|per\s+month\b|\bmonthly\b', re.I)
RE_PERIOD_YEAR = re.compile(r'per\s+(?:\w+\s+)?per\s+year\b|per\s+year\b|per\s+annum\b|\bannual\b|\byearly\b', re.I)

RE_CORRECTION_1 = re.compile(r'CORRECTION.*?should\s+read\s+(' + _CUR + r')\s*' + _AMT, re.I | re.DOTALL)
RE_CORRECTION_2 = re.compile(r'CORRECTION.*?(' + _CUR + r')\s*' + _AMT, re.I | re.DOTALL)
RE_TOTAL = re.compile(r'(' + _CUR + r')\s*' + _AMT + r'\s+in\s+total', re.I)
RE_LIST_DISC = re.compile(r'(\d+)\s*%\s*(?:discount|off)\s+(?:on\s+)?(?:our\s+)?list\s+price\s+of\s+(' + _CUR + r')\s*' + _AMT, re.I)
RE_PREV_DISC = re.compile(r'(?:a\s+)?(?:further\s+)?(\d+)\s*%\s*off\s+(?:our\s+)?previous\s+(?:quote|price|offer)', re.I)
RE_RANGE = re.compile(r'between\s+(' + _CUR + r')\s*' + _AMT + r'\s+and\s+(?:' + _CUR + r')?\s*' + _AMT, re.I)
RE_TIER = re.compile(r'(' + _CUR + r')\s*' + _AMT + r'\s+per\s+\w+.*?for\s+orders?\s+of\s+up\s+to\s+(\d+).*?(?:' + _CUR + r')?\s*' + _AMT + r'.*?(?:for\s+larger|per\s+\w+\s+for\s+larger)', re.I | re.DOTALL)
RE_K_LAKH = re.compile(r'(' + _CUR + r')\s*(\d+(?:\.\d+)?)\s*(k|lakh)\b', re.I)
RE_DOZEN = re.compile(r'(' + _CUR + r')\s*' + _AMT + r'\s+per\s+dozen', re.I)
RE_WORDS = re.compile(r'((?:' + num_word + r'[\s-]*){2,})\s*rupees?\s+per\s+', re.I)
RE_DIRECT = re.compile(r'(' + _CUR + r')\s*' + _AMT + r'\s+per\s+', re.I)
RE_FREE = re.compile(r'plus\s+(\d+)\s+free\s+\w+\s+for\s+every\s+(\d+)\s+you\s+pay', re.I)
RE_VOL = re.compile(r'(?:a\s+)?(?:further\s+)?(\d+)\s*%\s*off\s+for\s+orders?\s+(?:of\s+)?(\d+)\s*(?:\w+\s+)?(?:or\s+more|and\s+above|\+)', re.I)
RE_PACK = re.compile(r'\bpack\b', re.I)
RE_REAM = re.compile(r'\breams?\b', re.I)
RE_PER_N = re.compile(r'per\s+(\d+)\s+(?:fixtures|shipments|meals|units|seats|phones|monitors|chairs|boxs|boxes|guards|participants|sites|laptops|headsets)', re.I)
RE_EARLIER_QUOTE = re.compile(r'(?:₹|Rs\.?\s*|INR\s+)' + _AMT, re.I)


def detect_currency(prefix_text):
    """Detect currency from text just before the number."""
    t = prefix_text.strip().lower()
    if '₹' in t or 'rs' in t or 'inr' in t:
        return 'INR'
    if '$' in t or 'usd' in t:
        return 'USD'
    if '€' in t or 'eur' in t:
        return 'EUR'
    if '£' in t or 'gbp' in t:
        return 'GBP'
    if 'sgd' in t:
        return 'SGD'
    if 'aed' in t:
        return 'AED'
    if 'jpy' in t:
        return 'JPY'
    return None


def is_gst_inclusive(text):
    """Check if the message indicates a GST-inclusive price."""
    if 'gst' not in text.lower():
        return False
    return bool(RE_GST.search(text))


def detect_billing_period(text):
    """Detect whether the offer quotes per month or per year."""
    t_lower = text.lower()
    if 'month' in t_lower:
        if RE_PERIOD_MONTH.search(text):
            return 'month'
    if 'year' in t_lower or 'annum' in t_lower or 'annual' in t_lower:
        if RE_PERIOD_YEAR.search(text):
            return 'year'
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  EARLIER SUPPLIER QUOTE EXTRACTION  (for "X% off our previous quote")
# ═══════════════════════════════════════════════════════════════════════════════

_SUPPLIER_EARLIER_RE_CACHE = {}

def get_supplier_earlier_re(supplier_name):
    pat = _SUPPLIER_EARLIER_RE_CACHE.get(supplier_name)
    if pat is None:
        pat = re.compile(
            r'\[Earlier message\s*[—–-]\s*' + re.escape(supplier_name) + r'.*?\](.*?)(?=\[|$)',
            re.DOTALL
        )
        _SUPPLIER_EARLIER_RE_CACHE[supplier_name] = pat
    return pat


def extract_earlier_supplier_quote(full_msg, supplier_name):
    """Find the most recent supplier quote from earlier messages in the thread."""
    pattern = get_supplier_earlier_re(supplier_name)
    quotes = []
    for m in pattern.finditer(full_msg):
        pm = RE_EARLIER_QUOTE.search(m.group(1))
        if pm:
            quotes.append(parse_number(pm.group(1)))
    return quotes[-1] if quotes else None


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PRICE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_and_normalize_price(latest_msg, full_msg, category_key, quantity, supplier_name,
                                 gst_rate, billing_category, supplier_fx, currency_rates):
    """
    Extract the supplier's price from the latest message and normalize to
    INR, excl. GST, per the category's normalized unit.

    Returns (normalized_price_float, currency_str) or (None, 'UNKNOWN') on failure.
    """
    text = latest_msg
    t_lower = text.lower()
    gst_incl = is_gst_inclusive(text)
    bill_period = detect_billing_period(text)

    raw_price = None
    currency = None
    is_total = False
    is_per_dozen = False
    is_prev_quote = False

    # ── 1. CORRECTION ────────────────────────────────────────────────────────
    if 'correction' in t_lower or 'should read' in t_lower:
        m = RE_CORRECTION_1.search(text)
        if not m:
            m = RE_CORRECTION_2.search(text)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))

    # ── 2. TOTAL PRICE  ("₹X in total for all N") ───────────────────────────
    if raw_price is None and 'total' in t_lower:
        m = RE_TOTAL.search(text)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))
            is_total = True

    # ── 3. LIST PRICE DISCOUNT  ("D% discount on our list price of ₹X") ─────
    if raw_price is None and 'list price' in t_lower:
        m = RE_LIST_DISC.search(text)
        if m:
            discount_pct = int(m.group(1))
            currency = detect_currency(m.group(2))
            list_price = parse_number(m.group(3))
            raw_price = list_price * (1 - discount_pct / 100.0)

    # ── 4. PREVIOUS QUOTE DISCOUNT  ("further D% off our previous quote") ───
    if raw_price is None and ('previous' in t_lower or 'prior' in t_lower or 'earlier' in t_lower):
        m = RE_PREV_DISC.search(text)
        if m:
            discount_pct = int(m.group(1))
            prev = extract_earlier_supplier_quote(full_msg, supplier_name)
            if prev is not None:
                raw_price = prev * (1 - discount_pct / 100.0)
                currency = 'INR'
                is_prev_quote = True

    # ── 5. RANGE  ("between ₹A and ₹B per unit") ────────────────────────────
    if raw_price is None and 'between' in t_lower:
        m = RE_RANGE.search(text)
        if m:
            currency = detect_currency(m.group(1))
            a = parse_number(m.group(2))
            b = parse_number(m.group(3))
            raw_price = max(a, b)

    # ── 6. TIERED PRICING ("₹X for up to N, and ₹Y for larger") ─────────────
    if raw_price is None and ('larger' in t_lower or 'up to' in t_lower):
        m = RE_TIER.search(text)
        if m:
            currency = detect_currency(m.group(1))
            price_low = parse_number(m.group(2))
            threshold = int(m.group(3))
            price_high_tier = parse_number(m.group(4))
            raw_price = price_low if quantity <= threshold else price_high_tier

    # ── 7. K and LAKH NOTATION ("₹14.6k per monitor", "Rs. 78k per site") ────
    if raw_price is None and ('k' in t_lower or 'lakh' in t_lower):
        m = RE_K_LAKH.search(text)
        if m:
            currency = detect_currency(m.group(1))
            base_val = float(m.group(2))
            unit_sym = m.group(3).lower()
            if unit_sym == 'k':
                raw_price = base_val * 1000.0
            elif unit_sym == 'lakh':
                raw_price = base_val * 100000.0

    # ── 8. PER DOZEN ────────────────────────────────────────────────────────
    if raw_price is None and 'dozen' in t_lower:
        m = RE_DOZEN.search(text)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))
            is_per_dozen = True

    # ── 9. PRICE IN WORDS  ("twenty thousand rupees per unit") ────────────────
    if raw_price is None and ('rupee' in t_lower or 'rupees' in t_lower):
        m = RE_WORDS.search(text)
        if m:
            num = words_to_number(m.group(1))
            if num:
                raw_price = float(num)
                currency = 'INR'

    # ── 10. DIRECT PRICE  ("₹X per unit" / "₹X per unit incl. GST") ─────────
    if raw_price is None:
        m = RE_DIRECT.search(text)
        if m:
            currency = detect_currency(m.group(1))
            raw_price = parse_number(m.group(2))

    # ── If still nothing, bail out ───────────────────────────────────────────
    if raw_price is None:
        return None, 'UNKNOWN'

    if currency is None:
        currency = 'INR'

    # ── Subscriptions MUST have a billing period specified ───────────────────
    if billing_category is not None and not is_total and not is_prev_quote and bill_period is None:
        return None, 'UNKNOWN'

    price = raw_price

    # ── Free-for-every modifier ──────────────────────────────────────────────
    if 'free' in t_lower:
        m_free = RE_FREE.search(text)
        if m_free:
            free_units = int(m_free.group(1))
            paid_units = int(m_free.group(2))
            price = price * paid_units / (paid_units + free_units)

    # ── Volume discount modifier ─────────────────────────────────────────────
    if '%' in text and ('off' in t_lower or 'discount' in t_lower):
        m_vol = RE_VOL.search(text)
        if m_vol:
            vol_disc = int(m_vol.group(1))
            vol_threshold = int(m_vol.group(2))
            if quantity >= vol_threshold:
                price = price * (1 - vol_disc / 100.0)

    # ── Pack / per-N conversions ─────────────────────────────────────────────
    if category_key == 'led-lighting' and RE_PACK.search(text):
        price = price / 4.0
    elif category_key == 'printer-paper' and RE_REAM.search(text):
        price = price * 10.0

    m_per_n = RE_PER_N.search(text)
    if m_per_n:
        price = price / float(m_per_n.group(1))

    # ── Total → per-unit ─────────────────────────────────────────────────────
    if is_total:
        price = price / quantity

    # ── Per-dozen → per-unit ─────────────────────────────────────────────────
    if is_per_dozen:
        price = price / 12.0

    # ── Currency conversion ──────────────────────────────────────────────────
    if currency != 'INR':
        fx_rate = None
        if supplier_name in supplier_fx and currency in supplier_fx[supplier_name]:
            fx_rate = supplier_fx[supplier_name][currency]
        elif currency in currency_rates:
            fx_rate = currency_rates[currency]
        else:
            return None, currency

        price = price * fx_rate

    # ── GST removal ──────────────────────────────────────────────────────────
    if gst_incl:
        price = price / (1 + gst_rate)

    # ── Billing period normalization ─────────────────────────────────────────
    if billing_category is not None and bill_period is not None:
        if billing_category == 'year' and bill_period == 'month':
            price = price * 12
        elif billing_category == 'month' and bill_period == 'year':
            price = price / 12

    return price, currency
