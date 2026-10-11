"""Business assumptions for Fieldcraft, the fictional B2B SaaS company."""

from dataclasses import dataclass
from datetime import date

DEFAULT_START = date(2024, 1, 1)
DEFAULT_END = date(2026, 9, 30)

TRIAL_DAYS = 14
INTERNAL_DOMAIN = "fieldcraft.io"


@dataclass(frozen=True)
class Plan:
    plan_id: str
    tier: int
    # Monthly list price in minor units per currency; annual = 10x monthly (two months free).
    prices: dict[str, int]


PLANS: dict[str, Plan] = {
    "starter": Plan("starter", 1, {"USD": 2900, "EUR": 2700, "GBP": 2300}),
    "pro": Plan("pro", 2, {"USD": 7900, "EUR": 7300, "GBP": 6200}),
    "business": Plan("business", 3, {"USD": 19900, "EUR": 18500, "GBP": 15700}),
}
PLAN_BY_TIER = {p.tier: p for p in PLANS.values()}

# New Pro subscriptions pay the new price from this date; existing ones are grandfathered.
PRO_PRICE_CHANGE_DATE = date(2025, 7, 1)
PRO_NEW_PRICES = {"USD": 8900, "EUR": 8200, "GBP": 6900}

ANNUAL_MONTHS_CHARGED = 10

# country -> (currency, signup weight)
COUNTRIES: dict[str, tuple[str, float]] = {
    "US": ("USD", 0.34),
    "CA": ("USD", 0.06),
    "AU": ("USD", 0.05),
    "GB": ("GBP", 0.13),
    "DE": ("EUR", 0.10),
    "FR": ("EUR", 0.07),
    "NL": ("EUR", 0.05),
    "ES": ("EUR", 0.05),
    "IT": ("EUR", 0.05),
    "IE": ("EUR", 0.03),
    "GR": ("EUR", 0.04),
    "SE": ("EUR", 0.03),
}

# channel -> (signup weight, trial-to-paid base rate)
CHANNELS: dict[str, tuple[float, float]] = {
    "organic": (0.30, 0.16),
    "paid_search": (0.22, 0.14),
    "paid_social": (0.12, 0.08),
    "linkedin": (0.08, 0.18),
    "partner": (0.15, 0.20),
    "referral": (0.08, 0.25),
    "direct": (0.05, 0.15),
}

# company size -> (signup weight, conversion multiplier, plan weights starter/pro/business)
COMPANY_SIZES: dict[str, tuple[float, float, tuple[float, float, float]]] = {
    "1-10": (0.55, 1.0, (0.70, 0.27, 0.03)),
    "11-50": (0.30, 1.1, (0.35, 0.50, 0.15)),
    "51-200": (0.12, 1.3, (0.10, 0.45, 0.45)),
    "201+": (0.03, 1.5, (0.02, 0.28, 0.70)),
}

ANNUAL_SHARE = 0.25
MONTHLY_CHURN = {"starter": 0.040, "pro": 0.028, "business": 0.017}
EARLY_TENURE_CHURN_MULTIPLIER = 1.6  # first 3 months
ANNUAL_RENEWAL_CHURN = 0.15
MONTHLY_UPGRADE = 0.020
MONTHLY_DOWNGRADE = 0.008
REACTIVATION_RATE = 0.08

# Paid campaigns per ad platform: (campaign_id, campaign_name, signup share within channel)
CAMPAIGNS: dict[str, list[tuple[str, str, float]]] = {
    "paid_search": [
        ("gads_1001", "search_brand_global", 0.35),
        ("gads_1002", "search_nonbrand_us", 0.35),
        ("gads_1003", "search_nonbrand_eu", 0.20),
        ("gads_1004", "search_competitor", 0.10),
    ],
    "paid_social": [
        ("meta_2001", "prospecting_lookalike", 0.55),
        ("meta_2002", "retargeting_site_visitors", 0.45),
    ],
    "linkedin": [
        ("li_3001", "ops_managers_us", 0.6),
        ("li_3002", "ops_managers_eu", 0.4),
    ],
}

# campaign_id -> (signups per click, click-through rate, cost per click in platform currency)
CAMPAIGN_ECONOMICS: dict[str, tuple[float, float, float]] = {
    "gads_1001": (0.12, 0.080, 1.2),
    "gads_1002": (0.04, 0.050, 4.5),
    "gads_1003": (0.035, 0.045, 3.8),
    "gads_1004": (0.03, 0.030, 6.0),
    "meta_2001": (0.02, 0.012, 0.9),
    "meta_2002": (0.05, 0.020, 1.4),
    "li_3001": (0.030, 0.006, 7.0),
    "li_3002": (0.025, 0.005, 6.5),
}

# How the web analytics tool groups our channels, and its session-to-signup rate.
WEB_CHANNEL_GROUPS: dict[str, tuple[str, float]] = {
    "organic": ("Organic Search", 0.012),
    "paid_search": ("Paid Search", 0.030),
    "paid_social": ("Paid Social", 0.015),
    "linkedin": ("Paid Social", 0.015),
    "partner": ("Affiliates", 0.040),
    "referral": ("Referral", 0.050),
    "direct": ("Direct", 0.020),
}

UTM_BY_CHANNEL: dict[str, tuple[str | None, str | None]] = {
    "organic": ("google", "organic"),
    "paid_search": ("google", "cpc"),
    "paid_social": ("facebook", "paid_social"),
    "linkedin": ("linkedin", "paid_social"),
    "partner": (None, "affiliate"),  # utm_source is the network name
    "referral": ("customer_referral", "referral"),
    "direct": (None, None),
}

AFFILIATE_NETWORKS = {"affinet": 0.45, "linkloop": 0.35, "refera": 0.20}
# Networks earn 1.5x the first month's revenue per referred paying customer.
AFFILIATE_COMMISSION_MONTHS = 1.5

CRM_OWNERS = [
    ("own_01", "Alex Turner", "smb"),
    ("own_02", "Bea Lindqvist", "smb"),
    ("own_03", "Chris Okafor", "mid_market"),
    ("own_04", "Dana Ruiz", "mid_market"),
    ("own_05", "Elena Papadaki", "enterprise"),
    ("own_06", "Femi Adeyemi", "enterprise"),
]
