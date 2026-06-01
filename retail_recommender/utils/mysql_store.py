"""
MySQL Integration (Opsional)
Simpan rules ke database agar tidak perlu re-train setiap startup.

Aktifkan dengan menambahkan MYSQL_* ke .env
Install: pip install mysql-connector-python
"""

import os
import logging
import json

logger = logging.getLogger(__name__)


def get_connection():
    """Buat koneksi MySQL dari environment variables."""
    try:
        import mysql.connector

        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DB", "retail_recommender"),
        )
    except ImportError:
        raise RuntimeError(
            "mysql-connector-python tidak terinstall. "
            "Jalankan: pip install mysql-connector-python"
        )


DDL = """
CREATE TABLE IF NOT EXISTS association_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    antecedents JSON NOT NULL,
    consequents JSON NOT NULL,
    support FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    lift FLOAT NOT NULL,
    conviction FLOAT,
    rule_strength FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_lift (lift DESC),
    INDEX idx_confidence (confidence DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS frequent_itemsets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    itemset JSON NOT NULL,
    support FLOAT NOT NULL,
    length INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_support (support DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def save_rules(rules_df, itemsets_df):
    """Simpan hasil Apriori ke MySQL."""
    conn = get_connection()
    cursor = conn.cursor()

    # DDL
    for stmt in DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            cursor.execute(s)

    # Truncate lama
    cursor.execute("TRUNCATE TABLE association_rules")
    cursor.execute("TRUNCATE TABLE frequent_itemsets")

    # Insert rules
    rule_rows = [
        (
            json.dumps(sorted(row["antecedents"])),
            json.dumps(sorted(row["consequents"])),
            float(row["support"]),
            float(row["confidence"]),
            float(row["lift"]),
            float(row.get("conviction", 0)),
            float(row["rule_strength"]),
        )
        for _, row in rules_df.iterrows()
    ]
    cursor.executemany(
        """INSERT INTO association_rules
           (antecedents, consequents, support, confidence, lift, conviction, rule_strength)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        rule_rows,
    )

    # Insert itemsets
    itemset_rows = [
        (json.dumps(sorted(row["itemsets"])), float(row["support"]), int(row["length"]))
        for _, row in itemsets_df.iterrows()
    ]
    cursor.executemany(
        "INSERT INTO frequent_itemsets (itemset, support, length) VALUES (%s, %s, %s)",
        itemset_rows,
    )

    conn.commit()
    logger.info(
        f"Tersimpan ke MySQL: {len(rule_rows)} rules, {len(itemset_rows)} itemsets"
    )
    cursor.close()
    conn.close()


def load_rules():
    """Muat rules dari MySQL (jika ada)."""
    import pandas as pd

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM association_rules ORDER BY lift DESC")
    rows = cursor.fetchall()

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["antecedents"] = df["antecedents"].apply(json.loads)
    df["consequents"] = df["consequents"].apply(json.loads)

    cursor.close()
    conn.close()
    logger.info(f"Dimuat dari MySQL: {len(df)} rules")
    return df
