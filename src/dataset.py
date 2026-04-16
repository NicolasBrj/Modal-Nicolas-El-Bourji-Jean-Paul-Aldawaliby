companies = [
    "Nvidia",
    "Apple",
    "Alphabet",
    "Microsoft",
    "Amazon",
    "Broadcom",
    "Meta",
    "Tesla",
    "Oracle",
    "Advanced Micro Devices",
    "JPMorgan Chase",
    "Bank of America",
    "Citigroup",
    "Wells Fargo",
    "Goldman Sachs",
    "Morgan Stanley",
    "BlackRock",
    "American Express",
    "Charles Schwab",
    "Mastercard"
]
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

values_block = "\n".join([f'"{c}"@en' for c in companies])

query = f"""
SELECT DISTINCT ?inputName ?company ?companyLabel ?ticker ?industryLabel ?countryLabel ?exchangeLabel
WHERE {{
  VALUES ?inputName {{
    {values_block}
  }}

  ?company rdfs:label ?inputName .
  ?company wdt:P31 ?instanceOf .

  FILTER(?instanceOf IN (wd:Q4830453, wd:Q6881511, wd:Q891723, wd:Q783794))

  OPTIONAL {{ ?company wdt:P249 ?ticker. }}
  OPTIONAL {{ ?company wdt:P452 ?industry. }}
  OPTIONAL {{ ?company wdt:P17 ?country. }}
  OPTIONAL {{ ?company wdt:P414 ?exchange. }}

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }}
}}
ORDER BY ?inputName
"""

sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

rows = []
for r in results["results"]["bindings"]:
    rows.append({
        "input_name": r["inputName"]["value"],
        "wikidata_id": r["company"]["value"].split("/")[-1],
        "wikidata_label": r.get("companyLabel", {}).get("value"),
        "ticker_wikidata": r.get("ticker", {}).get("value"),
        "industry": r.get("industryLabel", {}).get("value"),
        "country": r.get("countryLabel", {}).get("value"),
        "exchange": r.get("exchangeLabel", {}).get("value"),
    })

df_wikidata = pd.DataFrame(rows)
display(df_wikidata)
from pathlib import Path

df_companies = pd.DataFrame({
    "canonical_name": [
        "Nvidia", "Apple", "Alphabet", "Microsoft", "Amazon", "Broadcom", "Meta", "Tesla", "Oracle", "AMD",
        "JPMorgan Chase", "Bank of America", "Citigroup", "Wells Fargo", "Goldman Sachs", "Morgan Stanley",
        "BlackRock", "American Express", "Charles Schwab", "Mastercard"
    ],
    "ticker": [
        "NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "AVGO", "META", "TSLA", "ORCL", "AMD",
        "JPM", "BAC", "C", "WFC", "GS", "MS", "BLK", "AXP", "SCHW", "MA"
    ],
    "sector": [
        "Tech", "Tech", "Tech", "Tech", "Tech", "Tech", "Tech", "Tech", "Tech", "Tech",
        "Financials", "Financials", "Financials", "Financials", "Financials", "Financials",
        "Financials", "Financials", "Financials", "Financials"
    ]
})

# small normalization to match names
name_map = {
    "Advanced Micro Devices": "AMD"
}

df_wikidata["canonical_name"] = df_wikidata["input_name"].replace(name_map)

df_final = df_companies.merge(
    df_wikidata.drop(columns=["input_name"]).drop_duplicates(subset=["canonical_name"]),
    on="canonical_name",
    how="left"
)

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "companies.csv"
df_final.to_csv(out_path, index=False)

display(df_final)
print(f"Saved to {out_path}")

manual_aliases = {
    "Nvidia": ["Nvidia", "NVIDIA", "NVIDIA Corporation", "NVDA"],
    "Apple": ["Apple", "Apple Inc.", "AAPL"],
    "Alphabet": ["Alphabet", "Alphabet Inc.", "Google", "GOOGL"],
    "Microsoft": ["Microsoft", "Microsoft Corp.", "MSFT"],
    "Amazon": ["Amazon", "Amazon.com", "Amazon.com, Inc.", "AMZN"],
    "Broadcom": ["Broadcom", "Broadcom Inc.", "AVGO"],
    "Meta": ["Meta", "Meta Platforms", "Facebook", "META"],
    "Tesla": ["Tesla", "Tesla Inc.", "TSLA"],
    "Oracle": ["Oracle", "Oracle Corporation", "ORCL"],
    "AMD": ["AMD", "Advanced Micro Devices", "AMD Inc."],
    "JPMorgan Chase": ["JPMorgan Chase", "JPMorgan", "JPM"],
    "Bank of America": ["Bank of America", "BofA", "BAC"],
    "Citigroup": ["Citigroup", "Citi", "C"],
    "Wells Fargo": ["Wells Fargo", "WFC"],
    "Goldman Sachs": ["Goldman Sachs", "Goldman", "GS"],
    "Morgan Stanley": ["Morgan Stanley", "MS"],
    "BlackRock": ["BlackRock", "BLK"],
    "American Express": ["American Express", "AmEx", "AXP"],
    "Charles Schwab": ["Charles Schwab", "SCHW"],
    "Mastercard": ["Mastercard", "Mastercard Incorporated", "MA"],
}

df_final["aliases"] = df_final["canonical_name"].map(lambda x: json.dumps(manual_aliases.get(x, []), ensure_ascii=False))
df_final.to_csv(out_path, index=False)

display(df_final[["canonical_name", "ticker", "wikidata_id", "aliases"]])