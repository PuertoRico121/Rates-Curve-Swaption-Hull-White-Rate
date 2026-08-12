"""Shared utilities for the analyst-level rates calibration project.

The project deliberately uses synthetic quotes and a single-curve EUR-style setup.
It is designed to demonstrate workflow and model judgement, not to reproduce a
production multi-curve rates stack.
"""
from pathlib import Path
import math
import pandas as pd
import QuantLib as ql

EVALUATION_DATE = ql.Date(15, ql.January, 2026)
CALENDAR = ql.TARGET()
SETTLEMENT_DAYS = 2
SETTLEMENT_DATE = CALENDAR.advance(EVALUATION_DATE, SETTLEMENT_DAYS, ql.Days)

DEPOSIT_QUOTES = [
    ("1M", ql.Period(1, ql.Months), 0.0210),
    ("3M", ql.Period(3, ql.Months), 0.0215),
    ("6M", ql.Period(6, ql.Months), 0.0220),
]

SWAP_QUOTES = [
    ("1Y", ql.Period(1, ql.Years), 0.0225),
    ("2Y", ql.Period(2, ql.Years), 0.0230),
    ("3Y", ql.Period(3, ql.Years), 0.0235),
    ("5Y", ql.Period(5, ql.Years), 0.0245),
    ("7Y", ql.Period(7, ql.Years), 0.0252),
    ("10Y", ql.Period(10, ql.Years), 0.0260),
]

SWAPTION_VOLS = [
    # expiry, underlying swap tenor, Black-style ATM volatility
    ("1Y", "1Y", ql.Period(1, ql.Years), ql.Period(1, ql.Years), 0.235),
    ("1Y", "2Y", ql.Period(1, ql.Years), ql.Period(2, ql.Years), 0.230),
    ("1Y", "5Y", ql.Period(1, ql.Years), ql.Period(5, ql.Years), 0.223),
    ("1Y", "10Y", ql.Period(1, ql.Years), ql.Period(10, ql.Years), 0.218),
    ("2Y", "1Y", ql.Period(2, ql.Years), ql.Period(1, ql.Years), 0.232),
    ("2Y", "2Y", ql.Period(2, ql.Years), ql.Period(2, ql.Years), 0.227),
    ("2Y", "5Y", ql.Period(2, ql.Years), ql.Period(5, ql.Years), 0.220),
    ("2Y", "10Y", ql.Period(2, ql.Years), ql.Period(10, ql.Years), 0.215),
    ("5Y", "1Y", ql.Period(5, ql.Years), ql.Period(1, ql.Years), 0.224),
    ("5Y", "2Y", ql.Period(5, ql.Years), ql.Period(2, ql.Years), 0.219),
    ("5Y", "5Y", ql.Period(5, ql.Years), ql.Period(5, ql.Years), 0.213),
    ("5Y", "10Y", ql.Period(5, ql.Years), ql.Period(10, ql.Years), 0.208),
]

CURVE_GRID = [
    ("3M", ql.Period(3, ql.Months)),
    ("6M", ql.Period(6, ql.Months)),
    ("1Y", ql.Period(1, ql.Years)),
    ("2Y", ql.Period(2, ql.Years)),
    ("3Y", ql.Period(3, ql.Years)),
    ("5Y", ql.Period(5, ql.Years)),
    ("7Y", ql.Period(7, ql.Years)),
    ("10Y", ql.Period(10, ql.Years)),
]


def set_evaluation_date():
    ql.Settings.instance().evaluationDate = EVALUATION_DATE


def build_curve(rate_shift=0.0):
    """Bootstrap a simple deposit + swap curve.

    Parameters
    ----------
    rate_shift : float
        Parallel shift applied to every input quote in absolute rate terms.
        Example: +0.001 = +10 bp.
    """
    set_evaluation_date()
    deposit_dc = ql.Actual360()
    fixed_dc = ql.Thirty360(ql.Thirty360.European)
    floating_index = ql.Euribor6M()

    helpers = []
    meta = []

    for label, tenor, quote in DEPOSIT_QUOTES:
        q = quote + rate_shift
        helper = ql.DepositRateHelper(
            ql.QuoteHandle(ql.SimpleQuote(q)),
            tenor,
            SETTLEMENT_DAYS,
            CALENDAR,
            ql.ModifiedFollowing,
            True,
            deposit_dc,
        )
        helpers.append(helper)
        meta.append({"instrument": "Deposit", "tenor": label, "market_quote": q, "helper": helper})

    for label, tenor, quote in SWAP_QUOTES:
        q = quote + rate_shift
        helper = ql.SwapRateHelper(
            ql.QuoteHandle(ql.SimpleQuote(q)),
            tenor,
            CALENDAR,
            ql.Annual,
            ql.Unadjusted,
            fixed_dc,
            floating_index,
            ql.QuoteHandle(),
            ql.Period(0, ql.Days),
        )
        helpers.append(helper)
        meta.append({"instrument": "Swap", "tenor": label, "market_quote": q, "helper": helper})

    curve_dc = ql.Actual365Fixed()
    curve = ql.PiecewiseFlatForward(SETTLEMENT_DATE, helpers, curve_dc)
    curve.enableExtrapolation()

    # Trigger lazy bootstrap now rather than at the first later query.
    _ = curve.discount(curve.maxDate())
    handle = ql.YieldTermStructureHandle(curve)
    return curve, handle, meta


def curve_snapshot(curve):
    """Return discount factors, continuous zero rates and 6M simple forwards."""
    dc = ql.Actual365Fixed()
    rows = []
    ref = curve.referenceDate()
    for label, tenor in CURVE_GRID:
        d = CALENDAR.advance(ref, tenor, ql.ModifiedFollowing)
        d2 = CALENDAR.advance(d, ql.Period(6, ql.Months), ql.ModifiedFollowing)
        rows.append({
            "tenor": label,
            "date": d.ISO(),
            "discount_factor": curve.discount(d),
            "zero_rate": curve.zeroRate(d, dc, ql.Continuous, ql.Annual).rate(),
            "fwd_6m": curve.forwardRate(d, d2, dc, ql.Simple).rate(),
        })
    return pd.DataFrame(rows)


def curve_repricing_table(meta):
    """Check that the bootstrap reproduces the input quotes."""
    rows = []
    for item in meta:
        helper = item["helper"]
        implied = helper.impliedQuote()
        market = item["market_quote"]
        rows.append({
            "instrument": item["instrument"],
            "tenor": item["tenor"],
            "market_quote": market,
            "implied_quote": implied,
            "error_bp": (implied - market) * 1e4,
        })
    return pd.DataFrame(rows)


def swaption_vol_table(vol_shift=0.0):
    rows = []
    for ex_label, ten_label, _, _, vol in SWAPTION_VOLS:
        rows.append({"expiry": ex_label, "tenor": ten_label, "vol": vol + vol_shift})
    return pd.DataFrame(rows)


def build_swaption_helpers(curve_handle, vol_shift=0.0):
    """Create ATM swaption calibration helpers from the synthetic vol matrix."""
    set_evaluation_date()
    index = ql.Euribor6M(curve_handle)
    helpers, meta = [], []
    for ex_label, ten_label, expiry, length, vol in SWAPTION_VOLS:
        v = vol + vol_shift
        helper = ql.SwaptionHelper(
            expiry,
            length,
            ql.QuoteHandle(ql.SimpleQuote(v)),
            index,
            index.tenor(),
            index.dayCounter(),
            index.dayCounter(),
            curve_handle,
        )
        helpers.append(helper)
        meta.append({"expiry": ex_label, "tenor": ten_label, "market_vol": v, "helper": helper})
    return helpers, meta


def helper_market_value(helper, market_vol):
    """Return helper market value with a compatibility fallback."""
    if hasattr(helper, "marketValue"):
        return helper.marketValue()
    if hasattr(helper, "blackPrice"):
        return helper.blackPrice(market_vol)
    return float("nan")


def swaption_market_table(meta):
    rows = []
    for item in meta:
        helper = item["helper"]
        rows.append({
            "swaption": f'{item["expiry"]}x{item["tenor"]}',
            "expiry": item["expiry"],
            "tenor": item["tenor"],
            "market_vol": item["market_vol"],
            "market_value": helper_market_value(helper, item["market_vol"]),
        })
    return pd.DataFrame(rows)


def calibrate_hull_white(curve_handle, helpers, simplex_step=0.05):
    """Calibrate one-factor Hull-White (a, sigma) to swaption helpers."""
    model = ql.HullWhite(curve_handle)
    engine = ql.JamshidianSwaptionEngine(model)
    for h in helpers:
        h.setPricingEngine(engine)

    method = ql.Simplex(simplex_step)
    end_criteria = ql.EndCriteria(1000, 250, 1e-7, 1e-7, 1e-7)
    model.calibrate(helpers, method, end_criteria)
    return model


def calibration_table(model, meta):
    """Compare market targets with model values and model-implied vols."""
    engine = ql.JamshidianSwaptionEngine(model)
    rows = []
    for item in meta:
        h = item["helper"]
        h.setPricingEngine(engine)
        market_vol = item["market_vol"]
        market_value = helper_market_value(h, market_vol)
        model_value = h.modelValue()
        implied_vol = h.impliedVolatility(model_value, 1e-6, 1000, 1e-4, 2.0)
        rel_error = (model_value - market_value) / market_value if market_value else float("nan")
        rows.append({
            "swaption": f'{item["expiry"]}x{item["tenor"]}',
            "market_vol": market_vol,
            "model_implied_vol": implied_vol,
            "vol_error_bp": (implied_vol - market_vol) * 1e4,
            "market_value": market_value,
            "model_value": model_value,
            "relative_price_error": rel_error,
        })
    return pd.DataFrame(rows)


def make_european_swaption(curve_handle, option_years=2, swap_years=5, notional=1_000_000, strike=None):
    """Construct a simple European payer swaption and its underlying vanilla swap."""
    set_evaluation_date()
    index = ql.Euribor6M(curve_handle)
    fixed_dc = ql.Thirty360(ql.Thirty360.European)
    float_dc = index.dayCounter()
    fixed_tenor = ql.Period(1, ql.Years)
    float_tenor = ql.Period(6, ql.Months)
    fixed_conv = ql.Unadjusted
    float_conv = ql.ModifiedFollowing

    swap_start = CALENDAR.advance(SETTLEMENT_DATE, ql.Period(option_years, ql.Years), float_conv)
    swap_end = CALENDAR.advance(swap_start, ql.Period(swap_years, ql.Years), float_conv)

    fixed_schedule = ql.Schedule(
        swap_start, swap_end, fixed_tenor, CALENDAR,
        fixed_conv, fixed_conv, ql.DateGeneration.Forward, False
    )
    float_schedule = ql.Schedule(
        swap_start, swap_end, float_tenor, CALENDAR,
        float_conv, float_conv, ql.DateGeneration.Forward, False
    )

    discount_engine = ql.DiscountingSwapEngine(curve_handle)
    dummy = ql.VanillaSwap(
        ql.Swap.Payer, notional,
        fixed_schedule, 0.0, fixed_dc,
        float_schedule, index, 0.0, float_dc,
    )
    dummy.setPricingEngine(discount_engine)
    atm_rate = dummy.fairRate()
    used_strike = atm_rate if strike is None else strike

    underlying = ql.VanillaSwap(
        ql.Swap.Payer, notional,
        fixed_schedule, used_strike, fixed_dc,
        float_schedule, index, 0.0, float_dc,
    )
    underlying.setPricingEngine(discount_engine)

    exercise_date = CALENDAR.advance(swap_start, -SETTLEMENT_DAYS, ql.Days, float_conv)
    swaption = ql.Swaption(underlying, ql.EuropeanExercise(exercise_date))
    return swaption, underlying, atm_rate, used_strike


def price_swaption_hw(swaption, model):
    swaption.setPricingEngine(ql.JamshidianSwaptionEngine(model))
    return swaption.NPV()


def calibration_summary(table):
    return pd.Series({
        "mean_abs_vol_error_bp": table["vol_error_bp"].abs().mean(),
        "max_abs_vol_error_bp": table["vol_error_bp"].abs().max(),
        "mean_abs_relative_price_error": table["relative_price_error"].abs().mean(),
    })
