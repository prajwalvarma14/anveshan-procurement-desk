"""Validate submission CSV against strict competition requirements."""

import csv
import os
import re
import sys


def validate(submission_path, sample_sub_path):
    print(f"Validating {submission_path} against {sample_sub_path}...")
    errors = []

    if not os.path.exists(submission_path):
        return False, [f"File not found: {submission_path}"]

    with open(sample_sub_path, encoding='utf-8') as f:
        sample_rows = list(csv.DictReader(f))
    expected_ids = [r['thread_id'] for r in sample_rows]
    expected_count = len(expected_ids)

    with open(submission_path, encoding='utf-8') as f:
        reader = list(csv.DictReader(f))

    # 1. Row count check
    if len(reader) != expected_count:
        errors.append(f"Row count mismatch: expected {expected_count}, got {len(reader)}")

    # 2. Header check
    if reader and list(reader[0].keys()) != ['thread_id', 'label']:
        errors.append(f"Header mismatch: expected ['thread_id', 'label'], got {list(reader[0].keys())}")

    # 3. Thread ID exact match and order
    actual_ids = [r['thread_id'] for r in reader]
    if actual_ids != expected_ids:
        errors.append("thread_id column does not match sample_submission.csv order or IDs")

    # 4. Strict label format regex
    label_pattern = re.compile(r'^(ACCEPT|COUNTER|REJECT|ESCALATE):[A-Z0-9_]+:[0-9]*$')
    valid_reasons = {
        'ACCEPT': {'ACCEPTABLE_PRICE'},
        'COUNTER': {'COUNTER_OFFER'},
        'REJECT': {'ABOVE_WALKAWAY', 'BLACKLISTED_SUPPLIER'},
        'ESCALATE': {'MISSING_INFO', 'PROMPT_INJECTION', 'BANNED_TERM', 'OVER_APPROVAL_LIMIT'},
    }

    for idx, row in enumerate(reader):
        tid = row.get('thread_id', f'Row {idx}')
        label = row.get('label', '')

        if not label_pattern.match(label):
            errors.append(f"[{tid}] Invalid label format: {label!r}")
            continue

        parts = label.split(':')
        action, reason, price = parts[0], parts[1], parts[2]

        if reason not in valid_reasons.get(action, set()):
            errors.append(f"[{tid}] Invalid action-reason combination: {action}:{reason}")

        if action == 'COUNTER':
            if not price.isdigit() or int(price) <= 0:
                errors.append(f"[{tid}] COUNTER requires positive integer price, got: {price!r}")
        else:
            if price != '':
                errors.append(f"[{tid}] {action} must have empty price with trailing colon, got: {price!r}")

    if errors:
        print(f"❌ Validation FAILED with {len(errors)} errors (showing first 10):")
        for err in errors[:10]:
            print(f"  - {err}")
        return False, errors

    print(f"✅ Validation PASSED! All {len(reader)} rows meet strict submission contract.")
    return True, []


if __name__ == '__main__':
    base = os.path.join(os.path.dirname(__file__), '..')
    sub_path = os.path.join(base, 'outputs', 'submission.csv')
    sample_path = os.path.join(base, 'sample_submission.csv')
    ok, _ = validate(sub_path, sample_path)
    sys.exit(0 if ok else 1)
