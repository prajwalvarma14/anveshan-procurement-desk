"""Unseen auditor — scans all 2,000 threads to detect edge cases, anomalies, and unseen patterns."""

import csv
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import decide, get_effective_policy
from parser import (
    isolate_latest_message, detect_injection, detect_banned_terms,
    extract_and_normalize_price
)
from data import SUPPLIER_STATUS, SUPPLIER_FX, CURRENCY_RATES


def run_audit():
    base = os.path.join(os.path.dirname(__file__), '..')
    threads_path = os.path.join(base, 'threads.csv')
    review_path = os.path.join(base, 'outputs', 'manual_review.md')

    with open(threads_path, encoding='utf-8') as f:
        threads = list(csv.DictReader(f))

    print(f"Auditing {len(threads)} threads...")

    action_counts = {}
    missing_info_threads = []
    suspicious_injection_threads = []
    banned_term_threads = []
    large_delta_threads = []
    edge_cases = []

    for t in threads:
        tid = t['thread_id']
        supplier = t['supplier']
        category = t['category']
        date = t['date']
        qty = int(t['quantity'])
        rnd = int(t['round'])
        msg = t['supplier_message']
        counter_str = t['our_last_counter']
        last_counter = float(counter_str) if counter_str else None

        policy = get_effective_policy(category, date, supplier)
        latest = isolate_latest_message(msg)

        price, cur = extract_and_normalize_price(
            latest, msg, category, qty, supplier,
            policy['gst'], policy['billing'],
            SUPPLIER_FX, CURRENCY_RATES
        )

        label = decide(t)
        action_reason = ':'.join(label.split(':')[:2])
        action_counts[action_reason] = action_counts.get(action_reason, 0) + 1

        # Check anomalies
        if label.startswith('ESCALATE:MISSING_INFO:'):
            missing_info_threads.append((t, cur, latest))

        if label.startswith('ESCALATE:PROMPT_INJECTION:'):
            suspicious_injection_threads.append((t, latest))

        if label.startswith('ESCALATE:BANNED_TERM:'):
            banned_term_threads.append((t, latest))

        # Check large deltas between our_last_counter and extracted price
        if price is not None and last_counter is not None and last_counter > 0:
            ratio = price / last_counter
            if ratio > 3.0 or ratio < 0.33:
                large_delta_threads.append((t, price, last_counter, ratio))

    print("\n--- Distribution of 2,000 Threads ---")
    for k, v in sorted(action_counts.items()):
        print(f"  {k:<35}: {v:>4} ({v/len(threads)*100:.1f}%)")

    print(f"\nMissing Info Count: {len(missing_info_threads)}")
    print(f"Prompt Injection Count: {len(suspicious_injection_threads)}")
    print(f"Banned Term Count: {len(banned_term_threads)}")
    print(f"Large Delta Count: {len(large_delta_threads)}")

    # Write top edge cases to manual_review.md
    with open(review_path, 'w', encoding='utf-8') as f:
        f.write("# AUDIT & MANUAL REVIEW OF EDGE CASES\n\n")

        f.write("## 1. Missing Info Cases\n\n")
        for t, cur, latest in missing_info_threads[:20]:
            f.write(f"### Thread {t['thread_id']} ({t['supplier']}, {t['category']})\n")
            f.write(f"- Currency: {cur}\n")
            f.write(f"- Latest Message snippet: {latest.strip()[:200]}...\n\n")

        f.write("## 2. Sample Prompt Injections\n\n")
        for t, latest in suspicious_injection_threads[:15]:
            f.write(f"### Thread {t['thread_id']} ({t['supplier']}, {t['category']})\n")
            f.write(f"- Snippet: {t['supplier_message'][:200]}...\n\n")

        f.write("## 3. Sample Banned Terms\n\n")
        for t, latest in banned_term_threads[:15]:
            f.write(f"### Thread {t['thread_id']} ({t['supplier']}, {t['category']})\n")
            f.write(f"- Snippet: {latest.strip()[:200]}...\n\n")

        f.write("## 4. Large Deltas between our_last_counter and offer\n\n")
        for t, price, last_counter, ratio in large_delta_threads[:20]:
            f.write(f"### Thread {t['thread_id']} ({t['supplier']}, {t['category']})\n")
            f.write(f"- Extracted Price: {price:.2f}, Our Last Counter: {last_counter}, Ratio: {ratio:.2f}\n")
            f.write(f"- Latest Message: {t['supplier_message'][:250]}...\n\n")

    print(f"\nDetailed manual review written to {review_path}")


if __name__ == '__main__':
    run_audit()
