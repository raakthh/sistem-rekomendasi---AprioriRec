"""
Test pipeline end-to-end tanpa server Flask.
Jalankan: python tests/test_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from utils.preprocessor import DataPreprocessor
from models.apriori_engine import AprioriEngine

DATASET = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "online_retail_II.xlsx")

def test_preprocessor():
    print("\n=== TEST: DataPreprocessor ===")
    p = DataPreprocessor(DATASET, sheet_name="Year 2010-2011")
    p.run_pipeline()

    stats = p.get_stats()
    print(f"Transaksi: {stats['total_transactions']:,}")
    print(f"Produk   : {stats['total_products']:,}")
    print(f"Matrix   : {p.transaction_df.shape}")
    assert p.transaction_df is not None, "Transaction matrix kosong!"
    return p

def test_apriori(preprocessor):
    print("\n=== TEST: AprioriEngine ===")
    engine = AprioriEngine(
        min_support=0.02,
        min_confidence=0.3,
        min_lift=1.0,
        max_len=3,
    )
    engine.run_pipeline(preprocessor.transaction_df)

    summary = engine.get_summary()
    print(f"Itemsets : {summary['frequent_itemsets_count']:,}")
    print(f"Rules    : {summary['rules_count']:,}")
    print(f"Avg Lift : {summary['rules_stats'].get('avg_lift', 0):.2f}")
    assert summary["rules_count"] > 0, "Tidak ada rules terbentuk!"
    return engine

def test_recommendations(engine):
    print("\n=== TEST: Rekomendasi ===")
    # Ambil produk dari top itemset
    top = engine.get_popular_combos(top_n=1)
    if top:
        sample_items = top[0]["items"][:1]
        recs = engine.get_recommendations(sample_items, top_n=5)
        print(f"Query : {sample_items}")
        print(f"Rekomendasi ({len(recs)}):")
        for r in recs:
            print(f"  - {r['product']} | lift={r['lift']} conf={r['confidence']}")
    else:
        print("Tidak ada popular combos ditemukan.")

def test_popular_combos(engine):
    print("\n=== TEST: Popular Combos ===")
    combos = engine.get_popular_combos(top_n=5)
    for c in combos:
        print(f"  {c['items']} → support {c['frequency_pct']}")

if __name__ == "__main__":
    p = test_preprocessor()
    e = test_apriori(p)
    test_popular_combos(e)
    test_recommendations(e)
    print("\n✅ Semua test berhasil!")
