"""Dynamic loader for Acme Playbook files."""

import os
import glob
import re

CATEGORY_NAME_MAP = {
    'catering': 'catering',
    'cleaning services': 'cleaning',
    'cloud servers': 'cloud-servers',
    'courier services': 'courier',
    'crm licenses': 'crm-licenses',
    'design software': 'design-software',
    'headsets': 'headsets',
    'laptops': 'laptops',
    'led lighting': 'led-lighting',
    'mobile phones': 'mobile-phones',
    'monitors': 'monitors',
    'office chairs': 'office-chairs',
    'printer paper': 'printer-paper',
    'security guards': 'security-guards',
    'training workshops': 'training',
}

def normalize_category_name(raw_name):
    clean = raw_name.strip().lower()
    return CATEGORY_NAME_MAP.get(clean, clean.replace(' ', '-'))


def load_amendments(playbook_dir):
    """Load and parse all amendment markdown files."""
    amendments = []
    pattern = os.path.join(playbook_dir, 'amendments', '*.md')
    for fpath in glob.glob(pattern):
        aid = os.path.splitext(os.path.basename(fpath))[0]
        with open(fpath, encoding='utf-8') as f:
            content = f.read()

        m_date = re.search(r'\*\*Effective from:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
        effective_date = m_date.group(1) if m_date else ''

        # Pattern: the (target price|walk-away price|approval limit) for (.*?) is now ₹([\d,]+)
        m_change = re.search(
            r'the\s+(target price|walk-away price|approval limit)\s+for\s+(.*?)\s+is\s+now\s+[₹Rs\.]*\s*([\d,]+)',
            content, re.I
        )
        if m_change:
            field_raw = m_change.group(1).lower()
            cat_raw = m_change.group(2).strip()
            val_raw = m_change.group(3).replace(',', '')

            if 'target' in field_raw:
                field = 'target'
            elif 'walk' in field_raw:
                field = 'walkaway'
            else:
                field = 'approval'

            cat = normalize_category_name(cat_raw)
            val = int(val_raw)

            amendments.append({
                'id': aid,
                'category': cat,
                'date': effective_date,
                'field': field,
                'value': val
            })

    # Sort amendments by effective date ascending
    amendments.sort(key=lambda a: a['date'])
    return amendments


def load_suppliers(playbook_dir):
    """Load supplier statuses, price caps, and FX rates."""
    supplier_status = {}
    supplier_price_caps = {}
    supplier_fx = {}

    pattern = os.path.join(playbook_dir, 'suppliers', '*.md')
    for fpath in glob.glob(pattern):
        with open(fpath, encoding='utf-8') as f:
            content = f.read()

        # Supplier Name: # Supplier: Name
        m_name = re.search(r'#\s*Supplier:\s*(.*)', content)
        if not m_name:
            continue
        sname = m_name.group(1).strip()

        # Status: Approved / BLACKLISTED / PROBATION
        m_status = re.search(r'\*\*Status:\*\*\s*(Approved|BLACKLISTED|PROBATION)', content, re.I)
        if m_status:
            status = m_status.group(1).upper()
            if status in ('BLACKLISTED', 'PROBATION'):
                supplier_status[sname] = status

        # Contract FX: invoices in (USD|EUR|GBP) are converted at ₹([\d.]+) per (USD|EUR|GBP)
        m_fx = re.search(r'invoices\s+in\s+([A-Z]{3})\s+are\s+converted\s+at\s+[₹Rs\.]*\s*([\d.]+)\s+per\s+[A-Z]{3}', content, re.I)
        if m_fx:
            cur = m_fx.group(1).upper()
            rate = float(m_fx.group(2))
            if sname not in supplier_fx:
                supplier_fx[sname] = {}
            supplier_fx[sname][cur] = rate

        # Contract Price Cap: price cap for (.*?) of ₹([\d,]+) per
        m_cap = re.search(r'price\s+cap\s+for\s+(.*?)\s+of\s+[₹Rs\.]*\s*([\d,]+)\s+per', content, re.I)
        if m_cap:
            cat_raw = m_cap.group(1).strip()
            cat = normalize_category_name(cat_raw)
            cap_val = int(m_cap.group(2).replace(',', ''))
            if sname not in supplier_price_caps:
                supplier_price_caps[sname] = {}
            supplier_price_caps[sname][cat] = cap_val

    return supplier_status, supplier_price_caps, supplier_fx
