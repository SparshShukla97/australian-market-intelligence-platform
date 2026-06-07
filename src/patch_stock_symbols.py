"""
patch_stock_symbols.py

Patches ALL articles in MongoDB with the latest stock ticker mappings.
Runs after mongodb_storage.py to ensure older articles are also updated.

The main pipeline only enriches the current batch — this script fills the gap
by updating every article in MongoDB that is missing a ticker but should have one.

Usage:
    PYTHONPATH=src python src/patch_stock_symbols.py
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

TICKER_MAP = {
    # Global tech
    "microsoft":                "MSFT",
    "meta":                     "META",
    "amazon":                   "AMZN",
    "amazon bedrock":           "AMZN",
    "amazon web services":      "AMZN",
    "aws":                      "AMZN",
    "alphabet":                 "GOOGL",
    "google":                   "GOOGL",
    "apple":                    "AAPL",
    "nvidia":                   "NVDA",
    "atlassian":                "TEAM",
    "cisco":                    "CSCO",
    "intel":                    "INTC",
    "oracle":                   "ORCL",
    "salesforce":               "CRM",
    "slack":                    "CRM",
    "linkedin":                 "MSFT",
    "shopify":                  "SHOP",
    "dxc technology":           "DXC",
    "dxc":                      "DXC",
    "amadeus":                  "AMS.MC",
    "sap":                      "SAP",
    "servicenow":               "NOW",
    "palantir":                 "PLTR",
    "ford":                     "F",
    "ford motor company":       "F",
    # ASX-listed
    "macquarie bank":           "MQG.AX",
    "macquarie group":          "MQG.AX",
    "macquarie":                "MQG.AX",
    "telstra":                  "TLS.AX",
    "woolworths":               "WOW.AX",
    "woolworths group":         "WOW.AX",
    "coles":                    "COL.AX",
    "coles group":              "COL.AX",
    "bhp":                      "BHP.AX",
    "commonwealth bank":        "CBA.AX",
    "cba":                      "CBA.AX",
    "nab":                      "NAB.AX",
    "national australia bank":  "NAB.AX",
    "anz":                      "ANZ.AX",
    "westpac":                  "WBC.AX",
    "wesfarmers":               "WES.AX",
    "bunnings":                 "WES.AX",
    "seek":                     "SEK.AX",
    "rea group":                "REA.AX",
    "xero":                     "XRO.AX",
    "nextdc":                   "NXT.AX",
    "sigma":                    "CWN.AX",
    "chemist warehouse":        "CWN.AX",
    "accent group":             "AX1.AX",
    "endeavour":                "EDV.AX",
    "hmc capital":              "HMC.AX",
    "domain":                   "DHG.AX",
    "qantas":                   "QAN.AX",
    "rio tinto":                "RIO.AX",
    "woodside":                 "WDS.AX",
    "origin energy":            "ORG.AX",
    "amp":                      "AMP.AX",
    "apa group":                "APA.AX",
    "apa":                      "APA.AX",
    "neoen":                    "APA.AX",
    "news corp":                "NWS",
    "nine entertainment":       "NEC.AX",
}


def main():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    col    = client["australian_market_intelligence"]["articles"]

    updated = 0
    total   = col.count_documents({})

    for doc in col.find({}, {"_id": 1, "primary_company": 1, "stock_symbol": 1}):
        company = str(doc.get("primary_company", "")).strip()
        current = str(doc.get("stock_symbol",    "")).strip()

        ticker = TICKER_MAP.get(company.lower(), "")

        # Update if we now know the ticker AND it isn't already set correctly
        if ticker and current in ("", "nan", "None") and ticker != current:
            col.update_one(
                {"_id": doc["_id"]},
                {"$set": {"stock_symbol": ticker, "stock_chart_available": True}},
            )
            updated += 1

    print(f"  Patched {updated} / {total} articles with missing stock symbols")


if __name__ == "__main__":
    main()
