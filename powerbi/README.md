# Power BI report

**The Cost of Building Rentals in Stockholm** – seven report pages (cover, five story pages, closing page)
presented full screen as the final presentation (no PowerPoint). PDF export:
[`The_Cost_of_Building_Rentals_in_Stockholm.pdf`](The_Cost_of_Building_Rentals_in_Stockholm.pdf).
Power BI file (report + data, opens in Power BI Desktop):
[`The_Cost_of_Building_Rentals_in_Stockholm.pbix`](The_Cost_of_Building_Rentals_in_Stockholm.pbix).

- **Data source:** `../data/processed/rental_model_powerbi.xlsx` (Import mode), created by
  `notebooks/02_model.ipynb`. Tables: `validation`, `subsidy_history`, `scenarios`,
  `affordability`, `completions_vs_rate`, `cost_split`.
- **Theme:** `theme_rental_premium.json` (View → Themes → Browse for themes). Navy `#1F3A5F`, teal
  `#14A3A0`, orange `#F2994A`, red `#E15759`, white cards with rounded corners and a soft shadow on a
  `#EEF2F7` background, Segoe UI Semibold.
- **Sliders (pages 3–4):** interest rate, investment subsidy and land price filter the `scenarios` and
  `affordability` tables. Default view: 2.75 % / 0 kr/m² / Outer suburb (today's level).
- **Screenshots:** `screenshots/` – one image per page, taken in full-screen view.
  `model_validation.png` shows the model vs actual rents 2022–2025 (a page removed from the final
  presentation to keep it short; the validation is described in the main README).

| Page | Story |
|---|---|
| 1. The problem | Too few rentals are built – and building follows the interest rate with a 3-year lag |
| 2. Why so expensive? | Costs have quadrupled since 1994, and land is the hidden driver |
| 3. What would it take? | Test the tools yourself – who decides each one |
| 4. Who can afford it? | Only two-income households – singles are priced out |
| 5. The answer | With three tools she pays 30 % of her income, not 68 % |
