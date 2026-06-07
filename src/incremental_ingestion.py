import os
import json
import jaydebeapi
import pandas as pd
from datetime import datetime

# ==========================================
# 1. DINAMIK YO'LLAR (KOD src/ ICHIDA TURGANI UCHUN)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Bitta yuqori papkaga chiqib, tegishli papkalarga ulanamiz
JAR_PATH = os.path.join(BASE_DIR, "..", "drivers", "mariadb-java-client-3.5.8.jar")
BRONZE_BASE_PATH = os.path.join(BASE_DIR, "..", "data", "bronze")
WATERMARK_FILE = os.path.join(BASE_DIR, "..", "metadata", "watermarks.json")

# Papkalarni avtomatik xavfsiz yaratish
os.makedirs(os.path.dirname(JAR_PATH), exist_ok=True)
os.makedirs(BRONZE_BASE_PATH, exist_ok=True)
os.makedirs(os.path.dirname(WATERMARK_FILE), exist_ok=True)

# ==========================================
# 2. JDBC SOZLAMALARI VA KONFIGURATSIYA
# ==========================================
jdbc_url = "jdbc:mariadb://5.189.143.4:3306/ignition?useSSL=false"
connection_params = ["ignition_user", "demo123"]
driver_class = "org.mariadb.jdbc.Driver"

tables_config = {
    "customers": {"type": "timestamp", "column": "updated_at", "default": "1970-01-01 00:00:00"},
    "customer_updates": {"type": "timestamp", "column": "updated_at", "default": "1970-01-01 00:00:00"},
    "orders": {"type": "timestamp", "column": "updated_at", "default": "1970-01-01 00:00:00"},
    "order_items": {"type": "identity", "column": "order_item_id", "default": 0}
}

# 3. Watermark holatlarini yuklash
if os.path.exists(WATERMARK_FILE):
    with open(WATERMARK_FILE, "r") as f:
        current_watermarks = json.load(f)
else:
    current_watermarks = {}

for t, cfg in tables_config.items():
    if t not in current_watermarks:
        current_watermarks[t] = cfg["default"]

print("=== INKREMENTAL EXTRACTION (PHASE 4) BOSHLANDI ===")

# ==========================================
# 4. EXTRACTION VA INGESTION PROSESI
# ==========================================
try:
    if not os.path.exists(JAR_PATH):
        raise FileNotFoundError(f"JDBC Driver topilmadi! Joylashtiring: {JAR_PATH}")

    # TO'G'RILANDI: jar_path= kalit so'zi olib tashlandi, to'g'ridan-to'g'ri 4-argument bo'lib o'tdi
    conn = jaydebeapi.connect(driver_class, jdbc_url, connection_params, JAR_PATH)
    
    for table, cfg in tables_config.items():
        last_val = current_watermarks[table]
        col = cfg["column"]
        
        if cfg["type"] == "timestamp":
            query = f"SELECT * FROM `{table}` WHERE `{col}` > '{last_val}'"
        else:
            query = f"SELECT * FROM `{table}` WHERE `{col}` > {last_val}"
            
        print(f"[PROCESS] {table} uchun so'rov yuborilmoqda (Watermark: > {last_val})...")
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        data = cursor.fetchall()
        cursor.close()
        
        records_fetched = len(data)
        
        if records_fetched > 0:
            df = pd.DataFrame(data, columns=columns)
            df["ingested_at"] = pd.Timestamp.now()
            
            output_path = os.path.join(BRONZE_BASE_PATH, table)
            os.makedirs(output_path, exist_ok=True)
            
            file_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            parquet_file_path = os.path.join(output_path, f"{table}_{file_ts}.parquet")
            df.to_parquet(parquet_file_path, index=False)
            
            # 5. Yangi Watermark qiymatini hisoblash
            if cfg["type"] == "timestamp":
                max_val = df[col].astype(str).max()
                if "." in max_val:
                    max_val = max_val.split(".")[0]
                new_watermark = max_val
            else:
                new_watermark = int(df[col].max())
                
            current_watermarks[table] = new_watermark
            print(f"[SUCCESS] {table} dan {records_fetched} yangi qator yuklandi. Yangi Watermark: {new_watermark}")
        else:
            print(f"[SKIP] {table} jadvalida yangi ma'lumot yo'q.")
            
    with open(WATERMARK_FILE, "w") as f:
        json.dump(current_watermarks, f, indent=4)
        
except Exception as e:
    print(f"[CRITICAL ERROR] Jarayonda xatolik: {e}")
finally:
    if 'conn' in locals():
        conn.close()

print("=== INKREMENTAL YUKLASH YAKUNLANDI ===")
