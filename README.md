# The Cost of Building Rentals in Stockholm

What rent does a newly built rental apartment in Stockholm need to break even, how much do
interest rates and the state investment subsidy affect it, and can ordinary households afford it?

Individual project – Hyper Island, Data Analyst (DA27), autumn 2026.

## Project structure

```
rental-housing-stockholm/
├── data/
│   ├── raw/          # data exactly as downloaded from the APIs (created by fetch_data.py)
│   └── processed/    # cleaned data used by the model and Power BI
├── notebooks/        # exploration and analysis (Jupyter)
├── src/
│   └── fetch_data.py # downloads all raw data from SCB and Riksbanken
├── requirements.txt
└── README.md
```

## Getting started

```bash
# 1. Create and activate a virtual environment (once)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install packages
pip install -r requirements.txt

# 3. Download the raw data (takes about a minute)
python src/fetch_data.py
```

The script saves one CSV per dataset in `data/raw/`, a log of what was fetched
(`_fetch_log.csv`) and prints a sanity check comparing a few values with known figures.

## Data sources

| File in `data/raw/` | Source | Content |
|---|---|---|
| `scb_completed_dwellings_by_tenure.csv` | SCB TAB4193 | Completed dwellings by tenure (rental/co-op), Stockholms län + municipalities, 1991– |
| `scb_started_completed_quarterly.csv` | SCB TAB4572 | Started and completed dwellings per quarter, 1975– |
| `scb_production_price_by_region.csv` | SCB TAB1626 | Production price per m² (land, building, total), gross/net, Stor-Stockholm, 1994– |
| `scb_production_price_by_tenure.csv` | SCB TAB1634 | Production price per m² by tenure, metropolitan areas, 1994– |
| `scb_rents_new_2022_onwards.csv` | SCB TAB6417 | Rents in new rentals by rent-setting model (incl. with investment subsidy), 2022– |
| `scb_rents_new_2014_2022.csv` | SCB TAB4277 | Rents in new rentals, 2014–2022 (discontinued series) |
| `scb_construction_cost_index.csv` | SCB TAB6328 | Construction cost index for housing, 2021=100, quarterly |
| `scb_disposable_income.csv` | SCB TAB1492 | Disposable household income by household type, mean/median |
| `scb_lending_rates_companies.csv` | SCB TAB5780 | Lending rates to non-financial companies, monthly |
| `riksbank_interest_rates_daily.csv` | Riksbanken SWEA | Policy rate, mortgage bonds (2y, 5y), government bonds (5y, 10y), daily |

APIs: [SCB Statistikdatabasen API v2](https://statistikdatabasen.scb.se/api/v2) ·
[Riksbanken SWEA API](https://api.riksbank.se/swea/v1)

## Notes on the data

- SCB production prices are **regional averages** for projects completed each year, so they
  depend on where building happened that year. Location is modelled as scenarios instead.
- "Netto" production price appears to be after deduction of state investment subsidy; "brutto" before.
- "Stor-Stockholm" in SCB = the 26 municipalities of Stockholms län.
- Missing values in SCB tables (`..`) are stored as empty cells.
