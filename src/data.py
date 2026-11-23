"""Reference data for The Procurement Desk — categories, suppliers, amendments, currencies."""

# ── Categories ───────────────────────────────────────────────────────────────
# billing: None = non-subscription; 'month'/'year' = expected billing period
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

# ── Amendments (sorted by effective_date) ────────────────────────────────────
AMENDMENTS = [
    {'id': 'AMD-03', 'category': 'printer-paper',   'date': '2026-09-10', 'field': 'walkaway',  'value': 2720},
    {'id': 'AMD-04', 'category': 'cleaning',         'date': '2026-09-18', 'field': 'approval',  'value': 680000},
    {'id': 'AMD-05', 'category': 'mobile-phones',    'date': '2026-09-19', 'field': 'approval',  'value': 2500000},
    {'id': 'AMD-01', 'category': 'courier',           'date': '2026-10-14', 'field': 'approval',  'value': 620000},
    {'id': 'AMD-06', 'category': 'security-guards',  'date': '2026-10-18', 'field': 'walkaway',  'value': 26550},
    {'id': 'AMD-02', 'category': 'monitors',          'date': '2026-11-01', 'field': 'target',    'value': 13790},
    {'id': 'AMD-09', 'category': 'printer-paper',    'date': '2026-12-01', 'field': 'walkaway',  'value': 2770},
    {'id': 'AMD-08', 'category': 'crm-licenses',     'date': '2026-12-05', 'field': 'approval',  'value': 1880000},
    {'id': 'AMD-07', 'category': 'crm-licenses',     'date': '2026-12-08', 'field': 'approval',  'value': 3120000},
]

# ── Supplier status ──────────────────────────────────────────────────────────
SUPPLIER_STATUS = {
    'Arvind Office Supplies':   'BLACKLISTED',
    'Everbright Lighting':      'BLACKLISTED',
    'Saffron Kitchens':         'BLACKLISTED',
    'Banyan Guarding':          'PROBATION',
    'GreenLeaf Facility Care':  'PROBATION',
    'Jade Express':             'PROBATION',
    'Vertex Mobile':            'PROBATION',
}
# All other suppliers are 'APPROVED' (default)

# ── Supplier contract price caps (replace walkaway for that category) ────────
SUPPLIER_PRICE_CAPS = {
    'Deccan Logistics':       {'monitors': 17700},
    'Indus Paper Mills':      {'courier': 200},
    'Jupiter Devices':        {'design-software': 37500},
    'Monsoon Foods':          {'training': 8100},
    'Northstar Facilities':   {'mobile-phones': 29000},
    'Quartz Software':        {'mobile-phones': 29400},
}

# ── Supplier contract FX overrides ───────────────────────────────────────────
SUPPLIER_FX = {
    'Fjord Design Tools':  {'GBP': 105},
    'Nimbus Hosting':      {'USD': 83},
    'Redwood Couriers':    {'EUR': 90.5},
    'Xenon Displays':      {'EUR': 90.5},
}

# ── Standard currency conversion table ───────────────────────────────────────
CURRENCY_RATES = {
    'INR': 1,
    'USD': 84.5,
    'EUR': 91,
    'GBP': 106,
}

# Supported currencies (anything else → MISSING_INFO)
KNOWN_CURRENCIES = {'INR', 'USD', 'EUR', 'GBP'}
