"""
Fetch the raw data for the project from SCB (Statistics Sweden) and Riksbanken.

Run from the project root folder:

    python src/fetch_data.py

It saves one CSV file per dataset in data/raw/ and prints a short sanity check
at the end, so you can see that the numbers look right.

Data sources
- SCB Statistikdatabasen, API v2: https://statistikdatabasen.scb.se/api/v2
- Riksbanken SWEA API:            https://api.riksbank.se/swea/v1
"""

import itertools
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

SCB_API = "https://statistikdatabasen.scb.se/api/v2"
RIKSBANK_API = "https://api.riksbank.se/swea/v1"

# data/raw/ next to the src/ folder, no matter where you run the script from
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# Special value for the Region dimension: Stockholms län (code 01)
# + its 26 municipalities (codes 01xx).
STOCKHOLM_COUNTY = "STOCKHOLM_COUNTY"

# ---------------------------------------------------------------------------
# What to fetch from SCB.
# "select" says which values to take for each dimension:
#   "*"              -> all values
#   ["code1", ...]   -> only these codes
#   STOCKHOLM_COUNTY -> Stockholms län + its municipalities
# Dimensions that are not listed get "*" (all values).
# ---------------------------------------------------------------------------
SCB_TABLES = {
    "completed_dwellings_by_tenure": {
        "table_id": "TAB4193",
        "description": "Completed dwellings in new buildings by region, building type "
                       "and tenure (hyresrätt/bostadsrätt/äganderätt). Yearly 1991-",
        "select": {"Region": STOCKHOLM_COUNTY},
    },
    "started_completed_quarterly": {
        "table_id": "TAB4572",
        "description": "Started and completed dwellings by region and building type. "
                       "Quarterly 1975- (no tenure split)",
        "select": {"Region": STOCKHOLM_COUNTY},
    },
    "production_price_by_region": {
        "table_id": "TAB1626",
        "description": "Price per m2 for new multi-family buildings: land, building, "
                       "total. Gross/net. By region (incl. Stor-Stockholm). Yearly 1994-",
        "select": {},
    },
    "production_price_by_tenure": {
        "table_id": "TAB1634",
        "description": "Price per m2 for new multi-family buildings by region "
                       "(metro areas) and tenure. Gross/net. Yearly 1994-",
        "select": {},
    },
    "rents_new_2022_onwards": {
        "table_id": "TAB6417",
        "description": "Rents in new rental buildings by region, number of rooms and "
                       "rent-setting model (incl. 'with investment subsidy'). 2022-",
        "select": {},
    },
    "rents_new_2014_2022": {
        "table_id": "TAB4277",
        "description": "Rents in new rental buildings by region, developer and "
                       "apartment type. 2014-2022 (discontinued series)",
        "select": {},
    },
    "construction_cost_index": {
        "table_id": "TAB6328",
        "description": "Construction cost index for housing, 2021=100. Quarterly 2000-",
        "select": {},
    },
    "disposable_income": {
        "table_id": "TAB1492",
        "description": "Disposable income per household by region and household type, "
                       "age 18+. Mean and median, tkr, fixed prices. Yearly 2011-",
        "select": {"Region": STOCKHOLM_COUNTY, "Alder": ["18+"]},
    },
    "lending_rates_companies": {
        "table_id": "TAB5780",
        "description": "Lending rates from MFI/mortgage institutions to non-financial "
                       "companies, by fixed-rate period. Monthly 1987-",
        "select": {"Referenssektor": ["1"], "Motpartssektor": ["1"]},
    },
}

# Riksbank series (daily values)
RIKSBANK_SERIES = {
    "SECBREPOEFF": "Policy rate (styrränta)",
    "SEMB2YCACOMB": "Swedish mortgage bond, 2 years",
    "SEMB5YCACOMB": "Swedish mortgage bond, 5 years",
    "SEGVB5YC": "Swedish government bond, 5 years",
    "SEGVB10YC": "Swedish government bond, 10 years",
}
RIKSBANK_START = "2010-01-01"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_json(url, retries=3):
    """GET a URL and return the JSON. Waits and retries if the API says 'too many requests'."""
    for attempt in range(retries):
        response = requests.get(url, timeout=60)
        if response.status_code == 429:  # rate limited -> wait and try again
            wait = 10 * (attempt + 1)
            print(f"   Rate limited, waiting {wait} s ...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Gave up after {retries} attempts: {url}")


def ordered_codes(dimension):
    """Return the codes of a json-stat2 dimension in the order of its index."""
    index = dimension["category"]["index"]
    if isinstance(index, list):  # json-stat also allows a plain list
        return index
    return sorted(index, key=index.get)


def jsonstat_to_dataframe(data):
    """
    Turn a json-stat2 response into a 'long' table:
    one row per value, with a code column and a label column per dimension.
    """
    dims = data["id"]
    codes_per_dim = [ordered_codes(data["dimension"][d]) for d in dims]

    rows = []
    # json-stat2 stores values row by row: the last dimension changes fastest,
    # which is exactly the order itertools.product walks through.
    for combo, value in zip(itertools.product(*codes_per_dim), data["value"]):
        row = {}
        for dim, code in zip(dims, combo):
            labels = data["dimension"][dim]["category"].get("label", {})
            row[f"{dim}_code"] = code
            row[dim] = labels.get(code, code)
        row["value"] = value  # None = missing (".." in SCB)
        rows.append(row)
    return pd.DataFrame(rows)


def build_scb_url(table_id, metadata, select):
    """Build the data URL for an SCB v2 table from our 'select' settings."""
    params = [("lang", "sv"), ("outputFormat", "json-stat2")]
    for dim in metadata["id"]:
        wanted = select.get(dim, "*")
        if wanted == STOCKHOLM_COUNTY:
            all_codes = ordered_codes(metadata["dimension"][dim])
            wanted = [c for c in all_codes if c.startswith("01")]
        if isinstance(wanted, list):
            if not wanted:
                raise ValueError(f"{table_id}: no values selected for dimension '{dim}'")
            wanted = ",".join(wanted)
        params.append((f"valueCodes[{dim}]", wanted))
    query = "&".join(f"{quote(k, safe='')}={quote(v, safe='*')}" for k, v in params)
    return f"{SCB_API}/tables/{table_id}/data?{query}"


def fetch_scb_table(table_id, select):
    """Download one SCB table and return it as a DataFrame + its metadata."""
    metadata = get_json(f"{SCB_API}/tables/{table_id}/metadata?lang=sv")
    time.sleep(0.5)  # be nice to the API (max 30 calls per 10 seconds)
    data = get_json(build_scb_url(table_id, metadata, select))
    time.sleep(0.5)
    return jsonstat_to_dataframe(data), data


def fetch_riksbank_series(series_id, start, end):
    """Download daily observations for one Riksbank series."""
    url = f"{RIKSBANK_API}/Observations/{series_id}/{start}/{end}"
    observations = get_json(url)
    df = pd.DataFrame(observations)  # columns: date, value
    df.insert(0, "series_id", series_id)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    log = []

    print("Fetching SCB tables ...")
    for name, spec in SCB_TABLES.items():
        print(f" - {name} ({spec['table_id']})")
        df, data = fetch_scb_table(spec["table_id"], spec["select"])
        path = RAW_DIR / f"scb_{name}.csv"
        df.to_csv(path, index=False)
        log.append({
            "file": path.name,
            "source": f"SCB {spec['table_id']}",
            "description": spec["description"],
            "scb_label": data.get("label"),
            "scb_updated": data.get("updated"),
            "rows": len(df),
            "missing_values": int(df["value"].isna().sum()),
        })

    print("Fetching Riksbank series ...")
    today = date.today().isoformat()
    frames = []
    for series_id, description in RIKSBANK_SERIES.items():
        print(f" - {series_id} ({description})")
        frames.append(fetch_riksbank_series(series_id, RIKSBANK_START, today))
        time.sleep(2)  # Riksbank limits anonymous calls, so go slow
    rates = pd.concat(frames, ignore_index=True)
    rates["description"] = rates["series_id"].map(RIKSBANK_SERIES)
    path = RAW_DIR / "riksbank_interest_rates_daily.csv"
    rates.to_csv(path, index=False)
    log.append({
        "file": path.name,
        "source": "Riksbanken SWEA",
        "description": "Daily interest rates: " + ", ".join(RIKSBANK_SERIES),
        "scb_label": None,
        "scb_updated": None,
        "rows": len(rates),
        "missing_values": int(rates["value"].isna().sum()),
    })

    log_df = pd.DataFrame(log)
    log_df.insert(0, "fetched_on", today)
    log_df.to_csv(RAW_DIR / "_fetch_log.csv", index=False)

    print(f"\nSaved {len(log)} files to {RAW_DIR}\n")
    print(log_df[["file", "rows", "missing_values"]].to_string(index=False))
    sanity_check()


def sanity_check():
    """Print a few numbers we already know, to check the data looks right."""
    print("\nSanity check (compare with the 'expected' value):")

    def check(text, expected, get_value):
        try:
            value = get_value()
            print(f" - {text}: {value}   (expected about {expected})")
        except Exception as error:  # a check should never crash the script
            print(f" - {text}: could not check ({error})")

    def read(name):
        return pd.read_csv(RAW_DIR / name, dtype=str)

    check("Completed rental apartments, Stockholms län 2023", "7797",
          lambda: read("scb_completed_dwellings_by_tenure.csv").query(
              "Region_code == '01' and Hustyp_code == 'FLERBO' "
              "and Upplatelseform_code == '1' and Tid == '2023'")["value"].iloc[0])

    check("Total production price kr/m2, Stor-Stockholm 2024 (net)", "58829",
          lambda: read("scb_production_price_by_region.csv").query(
              "Region_code == '0010' and BruttoNetto_code == '2' "
              "and ContentsCode_code == '000003I6' and Tid == '2024'")["value"].iloc[0])

    check("Rent kr/m2/year with investment subsidy, Stor-Stockholm 2025", "2574",
          lambda: read("scb_rents_new_2022_onwards.csv").query(
              "Region_code == '0010' and Hyresattningsmod_code == '2' "
              "and AntalRum_code == '00' and ContentsCode_code == '000007GJ' "
              "and Tid == '2025'")["value"].iloc[0])

    def mortgage_2023():
        rates = pd.read_csv(RAW_DIR / "riksbank_interest_rates_daily.csv", parse_dates=["date"])
        mask = (rates["series_id"] == "SEMB5YCACOMB") & (rates["date"].dt.year == 2023)
        return round(rates.loc[mask, "value"].mean(), 2)

    check("Average 5y mortgage bond rate 2023, %", "3.69", mortgage_2023)


if __name__ == "__main__":
    main()
