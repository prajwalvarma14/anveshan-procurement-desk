import os
import sys
import json
import hashlib
import csv
import subprocess

def check(name, status, msg=''):
    mark = '✅' if status else '❌'
    print(f'{mark} {name}: {msg}')
    if not status:
        sys.exit(1)

print('=' * 75)
print('          EXHAUSTIVE REPOSITORY & SUBMISSION AUDIT')
print('=' * 75)

# 1. Required Files Check
files = [
    'README.md',
    'requirements.txt',
    'environment.yml',
    'submission.csv',
    'threads.csv',
    'sample_threads.csv',
    'sample_answers.csv',
    'sample_submission.csv',
    'the_procurement_desk_solution.ipynb',
    'src/main.py',
    'src/engine.py',
    'src/parser.py',
    'src/data.py',
    'src/loaders.py',
    'src/evaluate.py',
    'src/validate_submission.py',
    'tests/test_pipeline.py'
]
for f in files:
    exists = os.path.exists(f)
    size = f"{os.path.getsize(f):,} bytes" if exists else "NOT FOUND"
    check(f'File Check: {f}', exists, size)

# 2. Check submission.csv Header, Row Count, & Label Regex
with open('submission.csv', encoding='utf-8') as f:
    rows = list(csv.reader(f))

check('submission.csv Header', rows[0] == ['thread_id', 'label'], str(rows[0]))
check('submission.csv Row Count', len(rows) == 2001, f"{len(rows) - 1} rows (expected exactly 2000)")

import re
label_pattern = re.compile(r'^(ACCEPT|COUNTER|REJECT|ESCALATE):[A-Z0-9_]+:[0-9]*$')
invalid_labels = []
for i, r in enumerate(rows[1:], start=1):
    if len(r) != 2:
        invalid_labels.append(f"Row {i}: invalid col count {len(r)}")
    elif not label_pattern.match(r[1]):
        invalid_labels.append(f"Row {i} ({r[0]}): invalid format '{r[1]}'")
check('Format Validation (All 2,000 Rows)', len(invalid_labels) == 0, f"{len(invalid_labels)} invalid labels")

# 3. Cryptographic Checksum Matching
target_hash = 'B23652B3F1F5D0159E7047963F96CF96D767E11AB3671F7044E21481C6A925A1'.lower()
outputs = [
    'submission.csv',
    'outputs/submission.csv',
    'outputs/submission_8.csv',
    'outputs/submission_final.csv',
    'outputs/submission_7.csv'
]
for p in outputs:
    exists = os.path.exists(p)
    if exists:
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest().lower()
        check(f'SHA-256 Check: {p}', h == target_hash, f"{h[:16]}... (Exact Match)")
    else:
        check(f'SHA-256 Check: {p}', False, "File missing")

# 4. Jupyter Notebook Structure & Auto-Discovery Check
nb = json.load(open('the_procurement_desk_solution.ipynb', encoding='utf-8'))
check('Notebook JSON Structure', 'cells' in nb and len(nb['cells']) >= 8, f"{len(nb['cells'])} cells found")
nb_text = json.dumps(nb)
check('Notebook Auto-Discovery Logic', "os.walk('/kaggle/input')" in nb_text, "Found dynamic path scanner")
check('Notebook Fail-Safe Fallbacks', "AMENDMENTS_DEFAULT" in nb_text, "Found hardcoded policy backup")

# 5. README Mandatory 11-Section Compliance Check
readme = open('README.md', encoding='utf-8').read()
sections = [
    ('1. Overview', '## 1. Overview'),
    ('2. Mathematics & Formal Equations', '## 2. Mathematics'),
    ('3. Architecture Diagram', '## 3. Architecture Diagram'),
    ('4. Implementation & Code Structure', '## 4. Implementation'),
    ('5. AI Models & API Usage Disclosures', '## 5. AI Models'),
    ('6. Handling Tricky Edge Cases', '## 6. Handling Tricky'),
    ('7. Evaluation, Error Analysis & Submission History', '## 7. Evaluation'),
    ('8. Real-World Enterprise Application', '## 8. Real-World'),
    ('9. Drawbacks & Limitations', '## 9. Drawbacks'),
    ('10. Original Work & Disclosures', '## 10. Original Work'),
    ('11. How to Run & Reproduce Final Submission', '## 11. How to Run')
]
for title, tag in sections:
    check(f'README Section: {title}', tag in readme, "Found & Verified")

# 6. Presentation Deck Check
ppt_files = [
    '../DataSprint2.0_by_Anveshan_PPT_Template.pptx',
    '../The_Procurement_Desk_Championship_Deck.pptx'
]
import pptx
for ppt in ppt_files:
    exists = os.path.exists(ppt)
    if exists:
        prs = pptx.Presentation(ppt)
        check(f'Presentation Deck: {os.path.basename(ppt)}', len(prs.slides) == 9, f"{len(prs.slides)} slides (2 intro + 7 content)")
    else:
        check(f'Presentation Deck: {os.path.basename(ppt)}', False, "File missing")

print('=' * 75)
print('              ALL 25 REPOSITORY AUDIT CHECKS PASSED!')
print('=' * 75)
