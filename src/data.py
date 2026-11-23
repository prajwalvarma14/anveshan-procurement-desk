"""Reference data for The Procurement Desk — categories, suppliers, amendments, currencies."""

import os
from loaders import load_amendments, load_suppliers

# ── Categories (Fixed baseline spend categories) ─────────────────────────────
CATEGORIES = {
    'catering':        {'target': 280,    'walkaway': 340,     'rounds': 3, 'beta': 1, 'approval': 600000,   'gst': 0.05, 'billing': None},
    'cleaning':        {'target': 85000,  'walkaway': 100000,  'rounds': 4, 'beta': 2, 'approval': 900000,   'gst': 0.18, 'billing': 'month'},
    'cloud-servers':   {'target': 96000,  'walkaway': 115000,  'rounds': 5, 'beta': 3, 'approval': 6000000,  'gst': 0.18, 'billing': 'year'},
    'courier':         {'target': 160,    'walkaway': 200,     'rounds': 4, 'beta': 2, 'approval': 500000,   'gst': 0.18, 'billing': None},
    'crm-licenses':    {'target': 18000,  'walkaway': 22000,   'rounds': 4, 'beta': 2, 'approval': 2500000,  'gst': 0.18, 'billing': 'year'},
    'design-software': {'target': 30000,  'walkaway': 36000,   'rounds': 4, 'beta': 2, 'approval': 1500000,  'gst': 0.18, 'billing': 'year'},
    'headsets':        {'target': 3500,   'walkaway': 4200,    'rounds': 3, 'beta': 1, 'approval': 400000,   'gst': 0.18, 'billing': None},
    'laptops':         {'target': 62000,  'walkaway': 70000,   'rounds': 4, 'beta': 2, 'approval': 4000000,  'gst': 0.18, 'billing': None},
    'led-lighting':    {'target': 1800,   'walkaway': 2200,    'rounds': 3, 'beta': 1, 'approval': 350000,   'gst': 0.18, 'billing': None},
    'mobile-phones':   {'target': 24000,  'walkaway': 28000,   'rounds': 4, 'beta': 2, 'approval': 2000000,  'gst': 0.18, 'billing': None},
    'monitors':        {'target': 14000,  'walkaway': 16500,   'rounds': 3, 'beta': 1, 'approval': 1200000,  'gst': 0.18, 'billing': None},
    'office-chairs':   {'target': 9000,   'walkaway': 11000,   'rounds': 3, 'beta': 1, 'approval': 700000,   'gst': 0.18, 'billing': None},
    'printer-paper':   {'target': 2200,   'walkaway': 2600,    'rounds': 3, 'beta': 1, 'approval': 250000,   'gst': 0.12, 'billing': None},
    'security-guards': {'target': 21000,  'walkaway': 25000,   'rounds': 4, 'beta': 2, 'approval': 1000000,  'gst': 0.18, 'billing': 'month'},
    'training':        {'target': 6000,   'walkaway': 7500,    'rounds': 3, 'beta': 1, 'approval': 900000,   'gst': 0.18, 'billing': None},
}

# ── Standard currency conversion table ───────────────────────────────────────
CURRENCY_RATES = {
    'INR': 1,
    'USD': 84.5,
    'EUR': 91,
    'GBP': 106,
}

KNOWN_CURRENCIES = {'INR', 'USD', 'EUR', 'GBP'}

# ── Dynamic Loading from Playbook Directory ──────────────────────────────────
_playbook_dir = os.path.join(os.path.dirname(__file__), '..', 'playbook', 'playbook')

AMENDMENTS = load_amendments(_playbook_dir)
SUPPLIER_STATUS, SUPPLIER_PRICE_CAPS, SUPPLIER_FX = load_suppliers(_playbook_dir)
