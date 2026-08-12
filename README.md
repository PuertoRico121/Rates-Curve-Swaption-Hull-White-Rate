# Yield Curve, Swaption Calibration and Hull–White Pricing

## Overview

This project builds a compact interest-rate derivatives workflow in Python using QuantLib. It connects three core tasks commonly found in rates trading, structuring, quantitative research, and model validation:

1. **Interest-rate curve construction**
2. **Swaption volatility calibration**
3. **Hull–White pricing and sensitivity analysis**

The project is designed as a practical end-to-end example rather than a full production pricing system. It shows how market rate inputs can be transformed into a calibrated stochastic interest-rate model and then used for derivative valuation and risk analysis.

Sample market inputs are used so the workflow is reproducible. The same structure can be adapted to observed market quotes from trading or market-data systems.

---

## Project Workflow

### 1. Market Data and Yield Curve Construction

The first stage converts short-term rate and swap quotes into a continuous term structure.

The workflow covers:

- deposit / short-rate inputs
- swap-rate inputs across multiple maturities
- curve bootstrapping
- discount factors
- zero rates
- forward rates
- repricing checks against the original market instruments

The output is a calibrated interest-rate curve that can be used consistently for discounting, forward-rate estimation, and derivative pricing.

---

### 2. Swaption Market Instruments

The project then introduces an ATM swaption volatility matrix across several option expiries and underlying swap tenors.

For each calibration instrument, the workflow links:

- swaption expiry
- swap tenor
- market implied volatility
- market price
- model price
- calibration error

This provides the market targets used to calibrate the interest-rate model.

---

### 3. Hull–White Model Calibration

A one-factor Hull–White short-rate model is calibrated to the swaption market instruments.

The model estimates two main parameters:

- **Mean reversion (`a`)** — controls how quickly short rates tend to revert
- **Volatility (`sigma`)** — controls the magnitude of short-rate uncertainty

Calibration minimizes the difference between model values and market swaption values.

The project reports the calibrated parameters and compares model prices against market prices across the calibration set.

This also illustrates an important practical point: a simple one-factor model may fit some regions of the swaption matrix better than others, so calibration quality must be evaluated rather than assumed.

---

### 4. Swaption Pricing

After calibration, the Hull–White model is used to price interest-rate options.

The main example is a **European swaption**, allowing the project to connect:

**market rates → yield curve → volatility inputs → model calibration → derivative valuation**

The pricing stage demonstrates how a calibrated stochastic-rate model can be used as part of a front-office or risk analytics workflow.

---

### 5. Validation and Sensitivity Analysis

The final stage tests how model outputs respond to changes in assumptions and market conditions.

Examples include:

- upward and downward yield-curve shifts
- swaption volatility changes
- changes in Hull–White mean reversion
- changes in Hull–White volatility
- comparison of market and model prices
- calibration residual analysis

These tests help identify which inputs drive valuation changes and where model fit may be weaker.

---

## Business Applications

### Rates Trading

Rates trading desks rely on consistent curves and pricing models to value positions and understand their exposure to movements in interest rates and volatility.

A workflow like this can support:

- pricing rate options
- comparing model values with market levels
- monitoring sensitivity to curve and volatility moves
- analysing nonlinear interest-rate risk
- testing alternative model assumptions

---

### Structuring

Structured-rates desks use quantitative models when designing and evaluating products whose payoff depends on future interest rates.

Curve construction and stochastic-rate modelling can support:

- evaluating structured-note economics
- testing alternative maturities and payoff structures
- analysing sensitivity to rate and volatility assumptions
- estimating fair value
- discussing pricing and risk trade-offs with trading and sales teams

---

### Quantitative Research and Front-Office Analytics

A rates quant may maintain analytical libraries used by traders and structurers.

The components in this project represent a simplified version of that workflow:

- constructing market-consistent curves
- creating calibration instruments
- calibrating stochastic models
- pricing derivatives
- producing model diagnostics and sensitivities

In a production environment, these components would typically be integrated with larger market-data, pricing, risk, and P&L systems.

---

### Model Validation and Valuation Control

Independent risk and valuation teams may use similar techniques to assess whether model outputs remain consistent with observable market information.

Possible applications include:

- independent repricing
- benchmark-model comparison
- calibration-error analysis
- parameter sensitivity testing
- stress testing
- identifying model limitations
- investigating valuation differences

---

## Repository Structure

```text
rates_curve_swaption_hw/
│
├── 00_setup_and_market_data.ipynb
├── 01_yield_curve_bootstrap.ipynb
├── 02_swaption_market_and_helpers.ipynb
├── 03_hull_white_calibration.ipynb
├── 04_european_swaption_pricing.ipynb
├── 05_validation_and_sensitivity.ipynb
│
├── src/
│   └── rates_project.py
│
├── requirements.txt
└── README.md
```

The notebooks are intended to be followed sequentially from market inputs through model calibration, pricing, and validation.

---

## Technology

- Python
- QuantLib
- NumPy
- pandas
- Matplotlib

---

## Scope

This project intentionally focuses on a relatively simple rates modelling workflow.

It does not attempt to build a full production multi-curve framework or implement more advanced models such as SABR or the LIBOR Market Model. Instead, it focuses on the core mechanics connecting curve construction, swaption calibration, stochastic interest-rate modelling, derivative pricing, and model validation.
