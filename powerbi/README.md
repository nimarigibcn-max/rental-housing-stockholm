# Power BI report

**The Cost of Building Rentals in Stockholm** – six report pages presented full screen as the final
presentation (no PowerPoint).

- **Data source:** `../data/processed/rental_model_powerbi.xlsx` (Import mode), created by
  `notebooks/02_model.ipynb`. Tables: `validation`, `subsidy_history`, `scenarios`,
  `affordability`, `completions_vs_rate`, `cost_split`.
- **Theme:** `theme_rental_premium.json` (View → Themes → Browse for themes). Navy `#1F3A5F`, teal
  `#14A3A0`, orange `#F2994A`, red `#E15759`, white cards with rounded corners and a soft shadow on a
  `#EEF2F7` background, Segoe UI Semibold.
- **Sliders (pages 4–5):** interest rate, investment subsidy and land price filter the `scenarios` and
  `affordability` tables. Default view: 2.75 % / 0 kr/m² / Average land price (today's level).
- **Screenshots:** `screenshots/` – one image per page, taken in full-screen view.

| Page | Story |
|---|---|
| 1. The problem | Too few rentals are built – and building follows the interest rate with a 3-year lag |
| 2. Why so expensive? | Costs have quadrupled since 1994, and land is the hidden driver |
| 3. Can we trust the model? | The model matches real rents 2022–24; in 2025 a 1 900 kr/month gap opens |
| 4. What would it take? | Test the levers yourself – who decides each one |
| 5. Who can afford it? | Only two-income households – singles are priced out |
| 6. The answer | Cheaper land, a targeted subsidy and housing allowance – together |
