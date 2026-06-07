import os
import json
import jaydebeapi
import pandas as pd
from datetime import datetime

# ==========================================
# 1. DINAMIK YO'LLAR (KOD src/ ICHIDA TURGANI UCHUN)
# ==========================================
# Kod bajarilayotgan faylning joylashgan papkasi (task_2/src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Bitta yuqori papkaga (task_2/) chiqib, tegishli papkalarga ulanamiz
JAR_PATH = os.path.join(BASE_DIR, "..", "drivers", "mariadb-java-client-3.5.8.jar")
BRONZE_BASE_PATH = os.path.join(BASE_DIR, "..", "data", "bronze")
METADATA_DIR = os.path.join(BASE_DIR, "..", "metadata")

# Tizim ishlashi uchun kerakli barcha papkalarni xavfsiz yaratish
os.makedirs(os.path.dirname(JAR_PATH), exist_ok=True)
os.makedirs(BRONZE_BASE_PATH, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Hisobotlar chiqadigan aniq yakuniy fayl yo'llari
JSON_LOG_PATH = os.path.join(METADATA_DIR, "metadata_report.json")
CSV_LOG_PATH = os.path.join(METADATA_DIR, "metadata_report.csv")

# ==========================================
# 2. JDBC VA BAZA SOZLAMALARI
# ==========================================
server_ip = "5.189.143.4"
port = "3306"
database = "ignition"
username = "ignition_user"
password = "demo123"

jdbc_url = f"jdbc:mariadb://{server_ip}:{port}/{database}?useSSL=false"
driver_class = "org.mariadb.jdbc.Driver"
connection_params = [username, password]

# Biznes jadvallari
business_tables = ["customers", "orders", "products", "order_items", "customer_updates"]

# Phase 3: Metadata ro'yxati
metadata_records = []

print("=== BRONZE INGESTION & METADATA REPORTING BOSHLANDI ===")

# ==========================================
# 3. DATA EXTRACTION VA METADATA GENERATION
# ==========================================
try:
    # Drayver borligini tekshirish (Data Engineer oltin qoidasi)
    if not os.path.exists(JAR_PATH):
        raise FileNotFoundError(f"JDBC Driver topilmadi! Iltimos uni quyidagi yo'lga joylang: {JAR_PATH}")

    # TO'G'RILANDI: jar_path= kalit so'zi olib tashlandi, to'g'ridan-to'g'ri 4-argument bo'lib o'tdi
    conn = jaydebeapi.connect(driver_class, jdbc_url, connection_params, JAR_PATH)
    print("[MUVAFFAQIYAT] MariaDB-ga JDBC ulanish o'rnatildi.\n")

    for table in business_tables:
        extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[JARAYON] {table} jadvali yuklanmoqda...")
        
        try:
            # UserWarning va format xatolarining oldini olish uchun toza cursor ishlatamiz
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM `{table}`")
            
            # Ustun nomlarini olish
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            data = cursor.fetchall()
            cursor.close()
            
            # DataFrame shakliga keltirish
            df = pd.DataFrame(data, columns=columns)
            
            # Metadata ko'rsatkichlarini hisoblash
            record_count = len(df)
            column_count = len(df.columns)
            load_status = "SUCCESS"
            error_message = None
            
            # Bronze qatlamga yozish mantiqi
            df["ingested_at"] = pd.Timestamp.now()
            output_path = os.path.join(BRONZE_BASE_PATH, table)
            os.makedirs(output_path, exist_ok=True)
            
            # Full Refresh yoki boshlang'ich yuklash uchun Parquet fayl nomi
            parquet_file_path = os.path.join(output_path, f"{table}.parquet")
            df.to_parquet(parquet_file_path, index=False)
            
            print(f"[OK] {table} yozildi. Qatorlar: {record_count}, Ustunlar: {column_count}")

        except Exception as table_err:
            load_status = "FAILED"
            record_count = 0
            column_count = 0
            error_message = str(table_err)
            print(f"[XATOLIK] {table} jadvalida muammo: {error_message}")

        # Phase 3 talablariga mos keluvchi metrikalarni yig'ish
        metadata_records.append({
            "Table Name": table,
            "Record Count": record_count,
            "Column Count": column_count,
            "Load Time": extraction_time,
            "Load Status": load_status,
            "Error Message": error_message
        })

except Exception as conn_err:
    print(f"[KRITIK XATO] JDBC ulanishida muammo: {conn_err}")

finally:
    if 'conn' in locals():
        conn.close()

# ==========================================
# 4. PHASE 3: METADATA EXPORT BO'LIMI
# ==========================================
# 1. JSON formatida saqlash
with open(JSON_LOG_PATH, "w", encoding="utf-8") as json_file:
    json.dump(metadata_records, json_file, indent=4, ensure_ascii=False)

# 2. CSV formatida saqlash
metadata_df = pd.DataFrame(metadata_records)
metadata_df.to_csv(CSV_LOG_PATH, index=False, encoding="utf-8")

print("\n=== PHASE 3: METADATA REPORTING YAKUNLANDI ===")
print(f"-> JSON hisobot: {JSON_LOG_PATH}")
print(f"-> CSV hisobot: {CSV_LOG_PATH}")
