"""Decision engine — implements the playbook's decision procedure."""

from decimal import Decimal, ROUND_HALF_UP

try:
    from data import CATEGORIES, AMENDMENTS, SUPPLIER_STATUS, SUPPLIER_PRICE_CAPS, SUPPLIER_FX, CURRENCY_RATES
    from parser import (
        isolate_latest_message, detect_injection, detect_banned_terms,
        extract_and_normalize_price,
    )
except ImportError:
    from src.data import CATEGORIES, AMENDMENTS, SUPPLIER_STATUS, SUPPLIER_PRICE_CAPS, SUPPLIER_FX, CURRENCY_RATES
    from src.parser import (
        isolate_latest_message, detect_injection, detect_banned_terms,
        extract_and_normalize_price,
    )


_POLICY_CACHE = {}

def get_effective_policy(category_key, thread_date, supplier_name):
    """
    Build the effective policy for a thread by starting from the category
    base, applying amendments up to the thread date, then supplier contract
    overrides. Results are cached for ultra-fast lookup.
    """
    cache_key = (category_key, thread_date, supplier_name)
    if cache_key in _POLICY_CACHE:
        return _POLICY_CACHE[cache_key]

    base = CATEGORIES[category_key]
    policy = {
        'target':   base['target'],
        'walkaway': base['walkaway'],
        'rounds':   base['rounds'],
        'beta':     base['beta'],
        'approval': base['approval'],
        'gst':      base['gst'],
        'billing':  base['billing'],
    }

    # Apply amendments in chronological order (AMENDMENTS is pre-sorted)
    for amd in AMENDMENTS:
        if amd['category'] == category_key and amd['date'] <= thread_date:
            policy[amd['field']] = amd['value']

    # Supplier contract price cap (replaces walkaway for that category)
    if supplier_name in SUPPLIER_PRICE_CAPS:
        caps = SUPPLIER_PRICE_CAPS[supplier_name]
        if category_key in caps:
            policy['walkaway'] = caps[category_key]

    _POLICY_CACHE[cache_key] = policy
    return policy


def compute_L(r, policy, is_probation):
    """
    Compute the concession level L(r).
    For probation suppliers: L(r) = target (no concessions) for all rounds.
    Otherwise: L(r) = target + (walkaway - target) * ((r-1)/(R-1))^beta
    """
    if is_probation:
        return float(policy['target'])

    R = policy['rounds']
    beta = policy['beta']
    target = policy['target']
    walkaway = policy['walkaway']

    if R == 1:
        return float(target)
    ratio = (r - 1) / (R - 1)
    return target + (walkaway - target) * (ratio ** beta)


def round_half_up(value):
    """Round to nearest integer, 0.5 rounds up."""
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def decide(thread):
    """
    Main decision function.  Takes a thread dict (from CSV) and returns
    the label string, e.g. 'ACCEPT:ACCEPTABLE_PRICE:' or 'COUNTER:COUNTER_OFFER:21000'.
    """
    supplier   = thread['supplier']
    category   = thread['category']
    date       = thread['date']
    quantity   = int(thread['quantity'])
    round_num  = int(thread['round'])
    message    = thread['supplier_message']

    # Build effective policy
    policy = get_effective_policy(category, date, supplier)
    is_probation = SUPPLIER_STATUS.get(supplier) == 'PROBATION'

    # Isolate latest message for some checks
    latest = isolate_latest_message(message)

    # ── Step 1: Extract price (to check for MISSING_INFO) ────────────────────
    price, cur = extract_and_normalize_price(
        latest, message, category, quantity, supplier,
        policy['gst'], policy['billing'],
        SUPPLIER_FX, CURRENCY_RATES,
    )
    has_price = price is not None

    # Check for truly unknown currency
    if not has_price:
        # price is None → MISSING_INFO
        return 'ESCALATE:MISSING_INFO:'

    # ── Step 2: Blacklisted supplier ─────────────────────────────────────────
    if SUPPLIER_STATUS.get(supplier) == 'BLACKLISTED':
        return 'REJECT:BLACKLISTED_SUPPLIER:'

    # ── Step 3: Prompt injection ─────────────────────────────────────────────
    if detect_injection(message):
        return 'ESCALATE:PROMPT_INJECTION:'

    # ── Step 4: Banned contract terms ────────────────────────────────────────
    if detect_banned_terms(latest):
        return 'ESCALATE:BANNED_TERM:'

    # ── Step 5: Price decision ───────────────────────────────────────────────
    p = price
    L_r = compute_L(round_num, policy, is_probation)
    R = policy['rounds']

    if p <= L_r:
        # Price is acceptable → check approval limit
        total_cost = p * quantity
        if total_cost > policy['approval']:
            return 'ESCALATE:OVER_APPROVAL_LIMIT:'
        return 'ACCEPT:ACCEPTABLE_PRICE:'
    else:
        if round_num >= R:
            return 'REJECT:ABOVE_WALKAWAY:'
        counter = round_half_up(L_r)
        return f'COUNTER:COUNTER_OFFER:{counter}'
