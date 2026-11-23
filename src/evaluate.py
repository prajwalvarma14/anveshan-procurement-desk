"""Evaluate the pipeline against the 40 sample threads."""

import csv
import os
import sys

# Ensure imports work when run from src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import decide


def load_csv(path):
    """Load a CSV into a list of dicts."""
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    base = os.path.join(os.path.dirname(__file__), '..')

    # Load sample threads and answers
    threads = load_csv(os.path.join(base, 'sample_threads.csv'))
    answers_rows = load_csv(os.path.join(base, 'sample_answers.csv'))
    answers = {r['thread_id']: r['label'] for r in answers_rows}

    correct = 0
    total = len(threads)
    mismatches = []

    for t in threads:
        tid = t['thread_id']
        predicted = decide(t)
        expected = answers.get(tid, '???')

        if predicted == expected:
            correct += 1
        else:
            mismatches.append((tid, expected, predicted))

    print(f'\n{"="*60}')
    print(f'  EXACT MATCH: {correct}/{total}  ({100*correct/total:.1f}%)')
    print(f'{"="*60}')

    if mismatches:
        print(f'\n  MISMATCHES ({len(mismatches)}):')
        print(f'  {"Thread":<10} {"Expected":<40} {"Got":<40}')
        print(f'  {"-"*10} {"-"*40} {"-"*40}')
        for tid, exp, got in mismatches:
            print(f'  {tid:<10} {exp:<40} {got:<40}')

            # Component breakdown
            e_parts = exp.split(':')
            g_parts = got.split(':')
            diffs = []
            labels = ['ACTION', 'REASON', 'PRICE']
            for i, lbl in enumerate(labels):
                ev = e_parts[i] if i < len(e_parts) else ''
                gv = g_parts[i] if i < len(g_parts) else ''
                if ev != gv:
                    diffs.append(f'{lbl}: {gv!r} should be {ev!r}')
            if diffs:
                print(f'           → {"; ".join(diffs)}')
    else:
        print('\n  🎉 PERFECT SCORE — all 40 samples matched!')

    print()
    return correct == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
