"""Main entry point — process all 2,000 threads and generate submission.csv."""

import csv
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import decide


def load_threads(path):
    """Load threads CSV."""
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_submission(results, path):
    """Write submission CSV in the exact required format."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        f.write('thread_id,label\n')
        for r in results:
            f.write(f'{r["thread_id"]},{r["label"]}\n')


def validate_label(label):
    """Validate a single label against the format spec."""
    pattern = r'^(ACCEPT|COUNTER|REJECT|ESCALATE):[A-Z0-9_]+:[0-9]*$'
    if not re.match(pattern, label):
        return False
    parts = label.split(':')
    action = parts[0]
    counter_price = parts[2] if len(parts) > 2 else ''
    if action == 'COUNTER' and not counter_price:
        return False
    if action != 'COUNTER' and counter_price:
        return False
    return True


def main():
    base = os.path.join(os.path.dirname(__file__), '..')
    threads_path = os.path.join(base, 'threads.csv')
    output_path = os.path.join(base, 'outputs', 'submission.csv')

    print(f'Loading threads from {threads_path}...')
    threads = load_threads(threads_path)
    print(f'  Loaded {len(threads)} threads.')

    results = []
    action_counts = {}
    invalid = 0

    for i, t in enumerate(threads):
        label = decide(t)

        if not validate_label(label):
            print(f'  ⚠ INVALID label for {t["thread_id"]}: {label}')
            invalid += 1

        action_reason = ':'.join(label.split(':')[:2])
        action_counts[action_reason] = action_counts.get(action_reason, 0) + 1

        results.append({'thread_id': t['thread_id'], 'label': label})

        if (i + 1) % 500 == 0:
            print(f'  Processed {i+1}/{len(threads)}...')

    # Write outputs
    final_output_path = os.path.join(base, 'outputs', 'submission_final.csv')
    write_submission(results, final_output_path)
    print(f'\n  ✅ Written {len(results)} rows to {final_output_path}')
    try:
        write_submission(results, output_path)
        print(f'  ✅ Written {len(results)} rows to {output_path}')
    except PermissionError:
        print(f'  ℹ Note: {output_path} is currently locked by another program (e.g. Excel). submission_final.csv was created successfully.')

    # Summary
    print(f'\n  Distribution of ACTION:REASON:')
    for key in sorted(action_counts.keys()):
        print(f'    {key}: {action_counts[key]}')

    if invalid:
        print(f'\n  ⚠ {invalid} invalid labels detected!')
    else:
        print(f'\n  ✅ All labels pass format validation.')


if __name__ == '__main__':
    main()
