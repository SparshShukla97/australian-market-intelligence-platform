"""
run_full_pipeline.py

Master pipeline orchestrator for Australian Market Intelligence.

Runs the complete pipeline in order:
  Step 1 — Fetch + NLP all 6 categories
  Step 2 — Entity extraction (NER)
  Step 3 — GPT fallback for low-confidence articles
  Step 4 — AI insights (summaries, key insight, why it matters)
  Step 5 — Company enrichment (logos, stock symbols)
  Step 6 — MongoDB upsert (insert new, update existing)

Usage:
    cd /path/to/australian_market_intelligence
    PYTHONPATH=src python src/run_full_pipeline.py
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

import pandas as pd

from main import run_category_pipeline


# ─────────────────────────────────────────────
# Always run from project root, regardless of
# where this script was invoked from.
# This ensures "output/..." paths never
# accidentally resolve to "src/output/...".
# ─────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)


# ─────────────────────────────────────────────
# Logging — writes to both console and file
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("pipeline")


# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
CATEGORIES = [
    "Technology",

    "Energy",
    "Retail",
    "Property",
    "Policy_Economy",
]

OUTPUT_DIR = "output"
ALL_CATEGORIES_CSV = os.path.join(OUTPUT_DIR, "final_all_categories_articles.csv")

# Downstream scripts run in this exact order
DOWNSTREAM_STEPS = [
    ("STEP 2 — Entity Extraction (NER)",        "src/enrich_articles.py"),
    ("STEP 3 — GPT Fallback",                   "src/apply_gpt_fallback.py"),
    ("STEP 4 — AI Insights Generation",         "src/enrich_all_articles.py"),
    ("STEP 5 — Company Enrichment",             "src/company_enrichment.py"),
    ("STEP 6 — MongoDB Upsert",                 "src/mongodb_storage.py"),
    ("STEP 7 — Patch Stock Symbols (all docs)", "src/patch_stock_symbols.py"),
    ("STEP 8 — Company Hero Images (Wikipedia)", "src/company_image_enrichment.py"),
]


# ─────────────────────────────────────────────
# Step 1: Fetch all categories
# ─────────────────────────────────────────────
def step_fetch_all_categories():
    """
    Runs the RSS fetch + scrape + NLP pipeline for every category.
    Combines results, deduplicates by URL, saves to CSV.
    Returns True on success, False if nothing was collected.
    """
    log.info("=" * 60)
    log.info("STEP 1 — Fetching articles across all categories")
    log.info("=" * 60)

    all_dataframes = []

    for category in CATEGORIES:
        log.info(f"  → Running: {category}")
        try:
            df = run_category_pipeline(category)

            if df is not None and not df.empty:
                log.info(f"  ✅ {category}: {len(df)} articles collected")
                all_dataframes.append(df)
            else:
                log.warning(f"  ⚠️  {category}: no articles found, skipping")

        except Exception as e:
            log.error(f"  ❌ {category}: failed — {e}")

    if not all_dataframes:
        log.error("  No articles collected from any category. Aborting.")
        return False

    # Combine all categories into one DataFrame
    combined = pd.concat(all_dataframes, ignore_index=True)
    before_dedup = len(combined)

    # Remove cross-category duplicates by URL
    combined = combined.drop_duplicates(subset=["url"])
    after_dedup = len(combined)
    removed = before_dedup - after_dedup

    log.info(f"\n  Total: {before_dedup} articles → {after_dedup} after removing {removed} duplicates")

    # Save for downstream scripts to pick up
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    combined.to_csv(ALL_CATEGORIES_CSV, index=False)
    log.info(f"  Saved: {ALL_CATEGORIES_CSV}\n")

    return True


# ─────────────────────────────────────────────
# Run a downstream script as a subprocess
# ─────────────────────────────────────────────
def run_script(step_name, script_path):
    """
    Runs a pipeline script in a subprocess.
    Uses the same Python interpreter and sets PYTHONPATH=src.
    Returns True on success, False on failure.
    """
    log.info("=" * 60)
    log.info(step_name)
    log.info("=" * 60)
    log.info(f"  → Running: {os.path.basename(script_path)}")

    # Pass the src directory on PYTHONPATH so all imports resolve
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath("src")

    result = subprocess.run(
        [sys.executable, script_path],
        env=env,
        capture_output=True,
        text=True,
    )

    # Print any output from the script
    for line in result.stdout.strip().splitlines():
        if line.strip():
            log.info(f"     {line.strip()}")

    if result.returncode != 0:
        log.error(f"  ❌ Failed:\n{result.stderr.strip()}")
        return False

    log.info(f"  ✅ {os.path.basename(script_path)} completed\n")
    return True


# ─────────────────────────────────────────────
# Master pipeline runner
# ─────────────────────────────────────────────
def run_full_pipeline():
    """
    Runs the complete end-to-end pipeline.
    Returns True if all steps succeeded, False if any step failed.
    """
    start_time = time.time()
    run_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log.info("\n" + "═" * 60)
    log.info(f"  PIPELINE START  —  {run_id}")
    log.info("═" * 60 + "\n")

    # Step 1: Fetch + NLP all categories
    if not step_fetch_all_categories():
        log.error("Pipeline aborted at Step 1.\n")
        return False

    # Steps 2–6: Enrich, score, store
    for step_name, script_path in DOWNSTREAM_STEPS:
        if not run_script(step_name, script_path):
            log.error(f"Pipeline aborted at: {step_name}\n")
            return False

    # Done
    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)

    log.info("═" * 60)
    log.info(f"  PIPELINE COMPLETE  —  finished in {minutes}m {seconds}s")
    log.info("═" * 60 + "\n")

    return True


if __name__ == "__main__":
    success = run_full_pipeline()
    sys.exit(0 if success else 1)
