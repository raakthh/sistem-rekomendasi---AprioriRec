# 🛍️ Retail Recommender — Sistem Rekomendasi Produk Berbasis Apriori

Backend Flask untuk sistem rekomendasi produk marketplace menggunakan algoritma **Apriori Association Rules Mining** pada dataset Online Retail II.

---

## 📐 Arsitektur Metodologi

```
Dataset (online_retail_II.xlsx)
         │
         ▼
[1] Data Preprocessing
    - Load Excel (pandas)
    - Hapus null (Description, Customer ID)
    - Hapus transaksi cancel (Invoice ~"C*")
    - Filter Quantity & Price ≤ 0
         │
         ▼
[2] Transformasi Transaksi
    - Group by Invoice
    - One-hot encoding (Invoice × Produk matrix)
    - Filter produk populer (top-500 by frequency)
         │
         ▼
[3] Pembentukan Frequent Itemsets
    - Algoritma Apriori (mlxtend)
    - min_support = 0.02  (default)
    - max_len = 4 item
         │
         ▼
[4] Perhitungan Metrics
    - Support = P(A ∩ B)
    - Confidence = P(B|A) = P(A ∩ B) / P(A)
    - Lift = Confidence / P(B)
    - Conviction = (1 - P(B)) / (1 - Confidence)
         │
         ▼
[5] Pembentukan Association Rules
    - min_confidence = 0.3
    - min_lift = 1.0
    - Ranking by: lift → confidence → support
         │
         ▼
[6] Output Rekomendasi
    - REST API Flask
    - Cache lookup O(1) per query
    - Siap integrasi frontend
```

---

## 🗂️ Struktur Project

```
retail_recommender/
├── run.py                      # Entry point
├── requirements.txt
├── .env.example                # Template environment variables
│
├── app/
│   ├── __init__.py             # Flask factory
│   ├── model_manager.py        # Singleton state: preprocessor + engine
│   └── routes/
│       ├── health.py           # GET /api/health
│       ├── recommend.py        # POST /api/recommend/products
│       ├── products.py         # GET  /api/products/
│       └── analytics.py        # GET  /api/analytics/summary
│
├── models/
│   └── apriori_engine.py       # Algoritma Apriori + rules + rekomendasi
│
├── utils/
│   ├── preprocessor.py         # Load → Clean → Transform pipeline
│   └── mysql_store.py          # Opsional: simpan rules ke MySQL
│
├── data/
│   └── online_retail_II.xlsx   # Dataset
│
└── tests/
    └── test_pipeline.py        # Test end-to-end tanpa server
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env sesuai kebutuhan
```

### 3. Jalankan Server
```bash
python run.py
```

> ⏳ Startup memakan ~2-3 menit untuk load + training Apriori.
> Monitor progress di terminal log.

---

## 📡 API Reference

### Health Check
```
GET /api/health
```
```json
{
  "status": "ok",
  "model_ready": true,
  "model_summary": {
    "frequent_itemsets_count": 243,
    "rules_count": 68,
    "parameters": { "min_support": 0.02, ... }
  }
}
```

---

### 🎯 Rekomendasi Produk (Utama)
```
POST /api/recommend/products
Content-Type: application/json

{
  "products": ["JUMBO BAG PINK POLKADOT"],
  "top_n": 10
}
```
```json
{
  "query_products": ["JUMBO BAG PINK POLKADOT"],
  "recommendations": [
    {
      "product": "JUMBO BAG RED RETROSPOT",
      "confidence": 0.6269,
      "lift": 7.26,
      "support": 0.0295,
      "rule_strength": 4.55,
      "reason": "Sangat sering dibeli bersama"
    }
  ],
  "total": 1
}
```

---

### 🔗 Produk Sering Dibeli Bersama
```
GET /api/recommend/combos?top_n=20
```

### 📋 Top Association Rules
```
GET /api/recommend/rules?top_n=50&min_lift=2.0&min_confidence=0.4
```

### 🔍 Similar Products (GET shortcut)
```
GET /api/recommend/similar/JUMBO BAG PINK POLKADOT?top_n=5
```

---

### Katalog Produk
```
GET /api/products/?page=1&per_page=50&q=BAG
GET /api/products/top?top_n=20
GET /api/products/search?q=HEART&limit=10
```

### Analytics
```
GET /api/analytics/summary
GET /api/analytics/sales-by-country?top_n=15
GET /api/analytics/sales-trend
GET /api/analytics/itemset-distribution
```

---

## ⚙️ Parameter Apriori

| Parameter | Default | Keterangan |
|---|---|---|
| `MIN_SUPPORT` | 0.02 | Minimum 2% transaksi mengandung itemset |
| `MIN_CONFIDENCE` | 0.3 | Minimum 30% kemungkinan membeli produk B jika beli A |
| `MIN_LIFT` | 1.0 | Lift > 1 = lebih baik dari random |
| `MAX_LEN` | 4 | Maksimum ukuran itemset |

Ubah di `.env` untuk trade-off kecepatan vs kualitas rules.

---

## 🗄️ MySQL (Opsional)

Aktifkan di `.env`:
```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=retail_recommender
```

Install driver: `pip install mysql-connector-python`

Kegunaan: simpan rules hasil training → server restart lebih cepat karena tidak perlu re-train.

---

## 🔌 Integrasi Frontend

Response API dirancang siap pakai untuk React / Vue / Next.js:

```javascript
// Contoh: fetch rekomendasi saat user tambah ke keranjang
async function getRecommendations(cartItems) {
  const res = await fetch('http://localhost:5000/api/recommend/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ products: cartItems, top_n: 6 })
  });
  const data = await res.json();
  return data.recommendations; // Array produk rekomendasi
}
```

CORS sudah diaktifkan untuk semua origin (development). Batasi di production.

---

## 📊 Hasil dari Dataset Online Retail II

- **541.910** baris data → **397.885** setelah cleaning (26.6% dihapus)
- **18.532** invoice unik diproses
- **500** produk populer dalam matrix transaksi
- **68+ association rules** terbentuk (avg lift ~11x)
- Rata-rata waktu response API: **< 50ms**
