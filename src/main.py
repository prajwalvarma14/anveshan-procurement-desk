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
    out_dir = os.path.join(base, 'outputs')
    os.makedirs(out_dir, exist_ok=True)

    print(f'Streaming threads from {threads_path}...')
    action_counts = {}
    invalid = 0
    results = []

    with open(threads_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        cols = {name: i for i, name in enumerate(next(reader))}
        tid_i, sup_i, cat_i, date_i = cols['thread_id'], cols['supplier'], cols['category'], cols['date']
        qty_i, rnd_i, msg_i = cols['quantity'], cols['round'], cols['supplier_message']

        for i, row in enumerate(reader):
            t = {
                'thread_id': row[tid_i], 'supplier': row[sup_i], 'category': row[cat_i],
                'date': row[date_i], 'quantity': row[qty_i], 'round': row[rnd_i],
                'supplier_message': row[msg_i]
            }
            label = decide(t)

            if not validate_label(label):
                print(f'  ⚠ INVALID label for {row[tid_i]}: {label}')
                invalid += 1

            action_reason = ':'.join(label.split(':')[:2])
            action_counts[action_reason] = action_counts.get(action_reason, 0) + 1
            results.append({'thread_id': row[tid_i], 'label': label})

            if (i + 1) % 500 == 0:
                print(f'  Processed {i+1} threads...')

    target_files = [
        'submission.csv',
        'submission_final.csv',
        'submission_7.csv',
        'submission_8.csv'
    ]

    for fname in target_files:
        fpath = os.path.join(out_dir, fname)
        try:
            write_submission(results, fpath)
            print(f'  ✅ Written {len(results)} rows to {fpath}')
        except PermissionError:
            print(f'  ℹ Note: {fpath} is locked by another process.')

    root_sub = os.path.join(base, 'submission.csv')
    try:
        write_submission(results, root_sub)
        print(f'  ✅ Written {len(results)} rows to {root_sub}')
    except PermissionError:
        print(f'  ℹ Note: {root_sub} is locked by another process.')

    print(f'\n  Distribution of ACTION:REASON:')
    for key in sorted(action_counts.keys()):
        print(f'    {key}: {action_counts[key]}')

    if invalid:
        print(f'\n  ⚠ {invalid} invalid labels detected!')
    else:
        print(f'\n  ✅ All {len(results)} labels pass format validation.')


if __name__ == '__main__':
    main()
