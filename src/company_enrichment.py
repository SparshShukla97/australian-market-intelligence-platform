import pandas as pd
import os
import re


INPUT_PATH = "output/final_production_articles.csv"
OUTPUT_PATH = "output/final_company_enriched_articles.csv"


def generate_company_slug(company_name: str) -> str:
    if not company_name:
        return ""

    slug = company_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "", slug)

    return slug


def generate_logo_url(company_name: str) -> str:
    """
    Generate a logo URL using Clearbit's free Logo API.
    Format: https://logo.clearbit.com/{domain}
    Returns empty string if company name is missing.
    """
    slug = generate_company_slug(company_name)

    if not slug:
        return ""

    return f"https://logo.clearbit.com/{slug}.com"


def detect_stock_symbol(company_name: str) -> str:
    """
    Returns a stock ticker for the company, or empty string if private/unknown.
    Lookup is case-insensitive. Covers ASX, NASDAQ, NYSE and major global exchanges.
    """
    known_symbols = {
        # ── Global Tech ──────────────────────────────────────────
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
        "slack":                    "CRM",         # Owned by Salesforce
        "linkedin":                 "MSFT",        # Owned by Microsoft
        "shopify":                  "SHOP",
        "dxc technology":           "DXC",
        "dxc":                      "DXC",
        "amadeus":                  "AMS.MC",
        "sap":                      "SAP",
        "servicenow":               "NOW",
        "palantir":                 "PLTR",
        "openai":                   "",            # Private
        "anthropic":                "",            # Private
        "canva":                    "",            # Private
        "airwallex":                "",            # Private
        "psiquantum":               "",            # Private
        # ── ASX-Listed (Australia) ────────────────────────────────
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
        "bunnings":                 "WES.AX",      # Bunnings owned by Wesfarmers
        "seek":                     "SEK.AX",
        "rea group":                "REA.AX",
        "xero":                     "XRO.AX",
        "nextdc":                   "NXT.AX",
        "sigma":                    "CWN.AX",      # Sigma merged with Chemist Warehouse → CWN
        "chemist warehouse":        "CWN.AX",
        "accent group":             "AX1.AX",
        "endeavour":                "EDV.AX",
        "hmc capital":              "HMC.AX",
        "domain":                   "DHG.AX",
        "car group":                "CAR.AX",
        "realestate.com.au":        "REA.AX",
        "iag":                      "IAG.AX",
        "insurance australia group":"IAG.AX",
        "qantas":                   "QAN.AX",
        "rio tinto":                "RIO.AX",
        "woodside":                 "WDS.AX",
        "origin energy":            "ORG.AX",
        "amp":                      "AMP.AX",
        "apa group":                "APA.AX",
        "apa":                      "APA.AX",
        "neoen":                    "APA.AX",      # Neoen acquired by APA Group 2024
        "nine entertainment":       "NEC.AX",
        "news corp":                "NWS",
        "vocus":                    "",            # Privatised 2021
        # Private AU companies
        "liquid instruments":       "",
        "procurepro":               "",
        "buildpass":                "",
        "venturecrowd":             "",
        "fishburners":              "",
        "unlockd":                  "",
    }

    # Case-insensitive lookup
    return known_symbols.get(company_name.lower().strip(), "")


def enrich_company_data(article):
    company = str(article.get("primary_company", "")).strip()

    logo_url = generate_logo_url(company)
    stock_symbol = detect_stock_symbol(company)

    article["company_logo_url"] = logo_url
    article["stock_symbol"] = stock_symbol
    article["stock_chart_available"] = bool(stock_symbol)
    article["company_website"] = ""

    return article


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH)

    enriched_rows = []

    for _, row in df.iterrows():
        article = row.to_dict()
        enriched_article = enrich_company_data(article)
        enriched_rows.append(enriched_article)

    output_df = pd.DataFrame(enriched_rows)

    output_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved company-enriched articles to: {OUTPUT_PATH}")

    print(
        output_df[
            [
                "title",
                "primary_company",
                "company_logo_url",
                "stock_symbol",
                "stock_chart_available",
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()