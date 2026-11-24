"""Deep audit script to inspect all 2,000 threads and check every edge case."""

import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from main import load_threads
from engine import decide, get_effective_policy, compute_L, round_half_up
from parser import (
    isolate_latest_message,
    detect_injection,
    detect_banned_terms,
    extract_and_normalize_price,
    detect_currency,
    is_gst_inclusive,
    detect_billing_period
)
from data import CATEGORIES, SUPPLIER_STATUS, SUPPLIER_PRICE_CAPS, SUPPLIER_FX, CURRENCY_RATES

def audit():
    threads = load_threads('threads.csv')
    print(f"Total threads loaded: {len(threads)}")

    # 1. Check MISSING_INFO
    missing_info = [t for t in threads if decide(t) == 'ESCALATE:MISSING_INFO:']
    print(f"\n--- MISSING_INFO Audit ({len(missing_info)} threads) ---")
    reasons = {}
    other_missing = []
    for t in missing_info:
        msg = isolate_latest_message(t['supplier_message'])
        cat = t['category']
        policy = CATEGORIES[cat]
        p, c = extract_and_normalize_price(
            msg, t['supplier_message'], cat, int(t['quantity']), t['supplier'],
            policy['gst'], policy['billing'], SUPPLIER_FX, CURRENCY_RATES
        )
        if c in ('AED', 'SGD', 'JPY'):
            reasons[f'Unlisted currency ({c})'] = reasons.get(f'Unlisted currency ({c})', 0) + 1
        elif 'call' in msg.lower() or 'specs' in msg.lower() or 'pricing will depend' in msg.lower() or 'revert' in msg.lower():
            reasons['No price / Qualitative inquiry'] = reasons.get('No price / Qualitative inquiry', 0) + 1
        elif policy['billing'] is not None and ('month' not in msg.lower() and 'year' not in msg.lower()):
            reasons['Subscription missing billing period'] = reasons.get('Subscription missing billing period', 0) + 1
        else:
            reasons['Other'] = reasons.get('Other', 0) + 1
            other_missing.append((t['thread_id'], t['category'], msg))

    for k, v in sorted(reasons.items()):
        print(f"  {k}: {v}")

    if other_missing:
        print(f"\nPotential Other Missing ({len(other_missing)}):")
        for tid, cat, m in other_missing[:10]:
            print(f"  [{tid}] {cat}: {m.strip().replace(chr(10), ' ')[:120]}")

    # 2. Check BANNED TERMS
    banned = [t for t in threads if decide(t) == 'ESCALATE:BANNED_TERM:']
    print(f"\n--- BANNED_TERM Audit ({len(banned)} threads) ---")
    banned_reasons = {}
    for t in banned:
        msg = isolate_latest_message(t['supplier_message'])
        m_lower = msg.lower()
        if 'renew' in m_lower or 'year to year' in m_lower:
            banned_reasons['Auto-renewal'] = banned_reasons.get('Auto-renewal', 0) + 1
        elif 'advance' in m_lower or 'upfront' in m_lower or 'half' in m_lower:
            banned_reasons['Advance > 30%'] = banned_reasons.get('Advance > 30%', 0) + 1
        elif 'liability' in m_lower:
            banned_reasons['Unlimited liability'] = banned_reasons.get('Unlimited liability', 0) + 1
        elif 'exclusiv' in m_lower or 'only from' in m_lower:
            banned_reasons['Exclusivity'] = banned_reasons.get('Exclusivity', 0) + 1
        else:
            banned_reasons['Other Banned'] = banned_reasons.get('Other Banned', 0) + 1
            print(f"  UNKNOWN BANNED: [{t['thread_id']}] {msg}")

    for k, v in sorted(banned_reasons.items()):
        print(f"  {k}: {v}")

    # 3. Check PROMPT INJECTION
    injections = [t for t in threads if decide(t) == 'ESCALATE:PROMPT_INJECTION:']
    print(f"\n--- PROMPT_INJECTION Audit ({len(injections)} threads) ---")
    inj_types = {}
    for t in injections:
        msg = t['supplier_message']
        m_lower = msg.lower()
        if '<!--' in msg:
            inj_types['HTML comment'] = inj_types.get('HTML comment', 0) + 1
        elif 'सहायक' in msg or 'निर्देश' in msg:
            inj_types['Hindi jailbreak'] = inj_types.get('Hindi jailbreak', 0) + 1
        elif 'system note' in m_lower or 'note to' in m_lower or 'language model' in m_lower:
            inj_types['System note / Directive'] = inj_types.get('System note / Directive', 0) + 1
        elif 'admin override' in m_lower or 'override' in m_lower:
            inj_types['Override / Bypass'] = inj_types.get('Override / Bypass', 0) + 1
        elif 'cfo' in m_lower or 'signed off' in m_lower or 'pre-approved' in m_lower or 'already approved' in m_lower:
            inj_types['Fake approval claim'] = inj_types.get('Fake approval claim', 0) + 1
        elif 'mark' in m_lower or 'accept' in m_lower or 'output' in m_lower or 'record' in m_lower:
            inj_types['Output label tampering'] = inj_types.get('Output label tampering', 0) + 1
        else:
            inj_types['Other Injection'] = inj_types.get('Other Injection', 0) + 1

    for k, v in sorted(inj_types.items()):
        print(f"  {k}: {v}")

    # 4. Check for ANY potential false negative banned terms across non-banned threads
    print(f"\n--- Scanning non-banned threads for hidden banned clauses ---")
    non_banned = [t for t in threads if not decide(t).startswith('ESCALATE:BANNED_TERM') and not decide(t).startswith('REJECT:BLACKLISTED') and not decide(t).startswith('ESCALATE:PROMPT_INJECTION') and not decide(t).startswith('ESCALATE:MISSING_INFO')]
    suspicious = []
    for t in non_banned:
        msg = isolate_latest_message(t['supplier_message'])
        m_lower = msg.lower()
        if 'sole supplier' in m_lower or 'exclusive' in m_lower or 'exclusivity' in m_lower:
            suspicious.append((t['thread_id'], 'exclusivity', msg))
        elif 'upfront' in m_lower or 'advance' in m_lower:
            suspicious.append((t['thread_id'], 'advance', msg))
        elif 'renew' in m_lower:
            suspicious.append((t['thread_id'], 'renew', msg))

    print(f"Suspicious clauses in acceptable/counter/reject threads: {len(suspicious)}")
    for tid, stype, smsg in suspicious[:15]:
        print(f"  [{tid}] Type: {stype} | {smsg.strip().replace(chr(10), ' ')[:120]}")

if __name__ == '__main__':
    audit()

def audit_exclusivity_and_clauses():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Exclusivity and Clauses ---")
    banned_excl = []
    denied_excl = []
    other_excl = []
    for t in threads:
        latest = isolate_latest_message(t['supplier_message'])
        l_lower = latest.lower()
        if 'exclusiv' in l_lower or 'only from' in l_lower:
            if 'not asking for exclusivity' in l_lower or 'we are not asking for exclusivity' in l_lower or 'without asking for exclusivity' in l_lower:
                denied_excl.append(t['thread_id'])
            elif 'exclusive supplier' in l_lower or 'exclusivity' in l_lower or 'only from us' in l_lower:
                banned_excl.append(t['thread_id'])
            else:
                other_excl.append((t['thread_id'], latest.replace('\n', ' ')))

    print(f"Banned exclusivity hits: {len(banned_excl)}")
    print(f"Denied exclusivity hits: {len(denied_excl)}")
    print(f"Other exclusivity hits: {len(other_excl)}")
    for tid, txt in other_excl:
        print(f"  [{tid}] {txt[:120]}")

audit_exclusivity_and_clauses()

def audit_advance_payments():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Advance Payments ---")
    banned_advance = []
    allowed_advance = []
    for t in threads:
        latest = isolate_latest_message(t['supplier_message'])
        l_lower = latest.lower()
        if 'advance' in l_lower or 'upfront' in l_lower or 'half' in l_lower:
            is_banned = False
            if 'half' in l_lower and ('upfront' in l_lower or 'advance' in l_lower):
                is_banned = True
            for m in re.finditer(r'(\d+)\s*%.*?(?:upfront|advance)|(?:upfront|advance).*?(\d+)\s*%', latest, re.I):
                pct = int(m.group(1) or m.group(2))
                if pct > 30:
                    is_banned = True
            if is_banned:
                banned_advance.append(t['thread_id'])
            else:
                allowed_advance.append(t['thread_id'])

    print(f"Banned advance payments (>30% or half): {len(banned_advance)}")
    print(f"Allowed advance payments (<=30%): {len(allowed_advance)}")

audit_advance_payments()

def audit_auto_renewal():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Auto-Renewal ---")
    banned_renew = []
    denied_renew = []
    other_renew = []
    for t in threads:
        latest = isolate_latest_message(t['supplier_message'])
        l_lower = latest.lower()
        if 'renew' in l_lower or 'year to year' in l_lower:
            has_denial = bool(re.search(
                r'(?:no|not|without)\s+(?:an?\s+)?auto(?:matic(?:ally)?)?[\s-]*renew|'
                r'renewal\s+only\s+(?:by\s+mutual|if\s+both)', latest, re.I
            ))
            if has_denial:
                denied_renew.append(t['thread_id'])
            elif re.search(r'auto(?:matic(?:ally)?)?[\s-]*renew', latest, re.I) or re.search(r'continues?\s+(?:from\s+)?year\s+to\s+year\s+unless', latest, re.I) or re.search(r'renews?\s+on\s+its\s+own', latest, re.I):
                banned_renew.append(t['thread_id'])
            else:
                other_renew.append((t['thread_id'], latest.replace('\n', ' ')))

    print(f"Banned auto-renewal: {len(banned_renew)}")
    print(f"Explicitly denied auto-renewal (safe): {len(denied_renew)}")
    print(f"Other renewal mentions: {len(other_renew)}")
    for tid, txt in other_renew[:10]:
        print(f"  [{tid}] {txt[:120]}")

audit_auto_renewal()

def audit_liability():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Liability ---")
    banned_liab = []
    other_liab = []
    for t in threads:
        latest = isolate_latest_message(t['supplier_message'])
        l_lower = latest.lower()
        if 'liability' in l_lower:
            if re.search(r'liability.*?unlimited|unlimited.*?liability', latest, re.I):
                banned_liab.append(t['thread_id'])
            else:
                other_liab.append((t['thread_id'], latest.replace('\n', ' ')))

    print(f"Banned unlimited liability: {len(banned_liab)}")
    print(f"Other liability mentions: {len(other_liab)}")
    for tid, txt in other_liab[:10]:
        print(f"  [{tid}] {txt[:120]}")

audit_liability()

def audit_probation_suppliers():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Probation Suppliers ---")
    probation_threads = [t for t in threads if SUPPLIER_STATUS.get(t['supplier']) == 'PROBATION']
    print(f"Total probation supplier threads: {len(probation_threads)}")
    dist = {}
    for t in probation_threads:
        d = decide(t)
        action_reason = ':'.join(d.split(':')[:2])
        dist[action_reason] = dist.get(action_reason, 0) + 1
        if d.startswith('COUNTER'):
            # check if counter price == target price
            policy = get_effective_policy(t['category'], t['date'], t['supplier'])
            counter_val = int(d.split(':')[2])
            target_val = policy['target']
            if counter_val != target_val:
                print(f"  MISMATCH PROBATION COUNTER: [{t['thread_id']}] Counter: {counter_val}, Target: {target_val}")

    for k, v in sorted(dist.items()):
        print(f"  {k}: {v}")

audit_probation_suppliers()

def audit_approval_limit():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Approval Limit ---")
    near_limit = []
    for t in threads:
        policy = get_effective_policy(t['category'], t['date'], t['supplier'])
        is_probation = (SUPPLIER_STATUS.get(t['supplier']) == 'PROBATION')
        latest = isolate_latest_message(t['supplier_message'])
        price, cur = extract_and_normalize_price(
            latest, t['supplier_message'], t['category'], int(t['quantity']), t['supplier'],
            policy['gst'], policy['billing'], SUPPLIER_FX, CURRENCY_RATES
        )
        if price is not None:
            L_r = compute_L(int(t['round']), policy, is_probation)
            if price <= L_r:
                tot = price * int(t['quantity'])
                app = policy['approval']
                ratio = tot / app
                if 0.98 <= ratio <= 1.02:
                    near_limit.append((t['thread_id'], t['category'], tot, app, ratio))

    print(f"Threads within 2% of approval limit: {len(near_limit)}")
    for tid, cat, tot, app, r in near_limit:
        print(f"  [{tid}] {cat}: Total={tot:.2f}, Approval={app}, Ratio={r:.5f}")

audit_approval_limit()

def audit_prompt_injection_coverage():
    threads = load_threads('threads.csv')
    print("\n--- Detailed Audit of Prompt Injection Coverage ---")
    flagged = 0
    unflagged_suspicious = []
    for t in threads:
        msg = t['supplier_message']
        is_inj = detect_injection(msg)
        if is_inj:
            flagged += 1
        else:
            m_lower = msg.lower()
            if any(w in m_lower for w in ['ignore', 'instruction', 'override', 'jailbreak', 'system note', 'cfo signed', 'pre-approved', 'preapproved']):
                unflagged_suspicious.append((t['thread_id'], msg))

    print(f"Total flagged injections: {flagged}")
    print(f"Unflagged threads containing suspicious words: {len(unflagged_suspicious)}")
    for tid, txt in unflagged_suspicious:
        print(f"  [{tid}] {txt.replace(chr(10), ' ')[:140]}")

audit_prompt_injection_coverage()
