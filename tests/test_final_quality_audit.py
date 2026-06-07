import json
import pandas as pd


INPUT_PATH = "output/final_production_articles.csv"


GENERIC_BAD_COMPANIES = {
    "Federal Court",
    "Supreme Court",
    "Big Tech",
    "Agency",
    "Cyber",
    "Technology",
    "NRF",
    "ABA",
    "ANU",
}


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value)


def is_empty(value):
    return safe_text(value).strip() == ""


def audit_row(row):
    issues = []

    title = safe_text(row.get("title"))
    category = safe_text(row.get("category_requested"))
    primary_company = safe_text(row.get("primary_company"))
    event_type = safe_text(row.get("event_type"))
    sentiment = safe_text(row.get("sentiment"))
    relevance_score = row.get("relevance_score")
    polished_summary = safe_text(row.get("polished_summary"))
    key_insight = safe_text(row.get("key_insight"))
    strategic_importance = safe_text(row.get("strategic_importance"))

    if is_empty(primary_company):
        issues.append("Missing primary company")

    if primary_company in GENERIC_BAD_COMPANIES:
        issues.append(f"Suspicious primary company: {primary_company}")

    if is_empty(event_type):
        issues.append("Missing event type")

    if is_empty(sentiment):
        issues.append("Missing sentiment")

    if pd.isna(relevance_score):
        issues.append("Missing relevance score")
    else:
        try:
            score = int(relevance_score)
            if score < 1 or score > 5:
                issues.append(f"Invalid relevance score: {score}")
        except Exception:
            issues.append(f"Invalid relevance score format: {relevance_score}")

    if is_empty(polished_summary):
        issues.append("Missing polished summary")

    if is_empty(key_insight):
        issues.append("Missing key insight")

    if is_empty(strategic_importance):
        issues.append("Missing strategic importance")

    if category == "Technology":
        tech_words = ["ai", "cloud", "cyber", "software", "data", "digital", "tech", "automation"]
        if not any(word in title.lower() or word in polished_summary.lower() for word in tech_words):
            issues.append("Possible category mismatch: Technology")

    if category == "Energy":
        energy_words = ["energy", "solar", "battery", "grid", "renewable", "wind", "gas", "power"]
        if not any(word in title.lower() or word in polished_summary.lower() for word in energy_words):
            issues.append("Possible category mismatch: Energy")

    if category == "Retail":
        retail_words = ["retail", "store", "consumer", "sales", "brand", "shopping", "ecommerce"]
        if not any(word in title.lower() or word in polished_summary.lower() for word in retail_words):
            issues.append("Possible category mismatch: Retail")

    return issues


def main():
    df = pd.read_csv(INPUT_PATH)

    audit_results = []

    for index, row in df.iterrows():
        issues = audit_row(row)

        audit_results.append(
            {
                "row": index,
                "title": row.get("title"),
                "category": row.get("category_requested"),
                "primary_company": row.get("primary_company"),
                "event_type": row.get("event_type"),
                "sentiment": row.get("sentiment"),
                "relevance_score": row.get("relevance_score"),
                "issues": issues,
                "issue_count": len(issues),
            }
        )

    audit_df = pd.DataFrame(audit_results)

    print("\nQUALITY AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total articles checked: {len(audit_df)}")
    print(f"Articles with issues: {(audit_df['issue_count'] > 0).sum()}")
    print(f"Articles clean: {(audit_df['issue_count'] == 0).sum()}")

    print("\nARTICLES WITH ISSUES")
    print("=" * 80)

    problem_rows = audit_df[audit_df["issue_count"] > 0]

    if problem_rows.empty:
        print("No issues found.")
    else:
        for _, row in problem_rows.iterrows():
            print("\n" + "-" * 80)
            print("ROW:", row["row"])
            print("TITLE:", row["title"])
            print("CATEGORY:", row["category"])
            print("PRIMARY COMPANY:", row["primary_company"])
            print("EVENT TYPE:", row["event_type"])
            print("SENTIMENT:", row["sentiment"])
            print("RELEVANCE:", row["relevance_score"])
            print("ISSUES:")
            for issue in row["issues"]:
                print(f"- {issue}")

    audit_df["issues"] = audit_df["issues"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    audit_df.to_csv("output/final_quality_audit.csv", index=False)

    print("\nSaved audit report to: output/final_quality_audit.csv")


if __name__ == "__main__":
    main()