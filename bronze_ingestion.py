import os
import json
import jaydebeapi
import pandas as pd
from datetime import datetime

# 1. JDBC va Drayver sozlamalari
server_ip = "5.189.143.4"
port = "3306"
database = "ignition"
username = "ignition_user"
password = "demo123"

jdbc_url = f"jdbc:mariadb://{server_ip}:{port}/{database}?useSSL=false"
driver_class = "org.mariadb.jdbc.Driver"
jar_path = "./mariadb-java-client-3.5.8.jar"

# Biznes jadvallari
business_tables = ["customers", "orders", "products", "order_items", "customer_updates"]

# Bronze qatlam joylashadigan papka
bronze_base_path = "./bronze"
os.makedirs(bronze_base_path, exist_ok=True)

# Phase 3: Metadata ro'yxati
metadata_records = []

print("=== BRONZE INGESTION & METADATA REPORTING BOSHLANDI ===")

try:
    conn = jaydebeapi.connect(driver_class, jdbc_url, [username, password], jar_path)
    print("[MUVAFFAQIYAT] MariaDB-ga JDBC ulanish o'rnatildi.\n")

    for table in business_tables:
        extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[JARAYON] {table} jadvali yuklanmoqda...")
        
        try:
            # Ma'lumotni o'qish
            query = f"SELECT * FROM `{table}`"
            df = pd.read_sql(query, conn)
            
            # Metadata hisoblash (Phase 3 uchun yangi ustunlar)
            record_count = len(df)
            column_count = len(df.columns)  # Ustunlar sonini aniqlash (YANGI)
            load_status = "SUCCESS"
            error_message = None
            
            # Bronze qatlamga yozish
            df["ingested_at"] = pd.Timestamp.now()
            output_path = os.path.join(bronze_base_path, table)
            os.makedirs(output_path, exist_ok=True)
            df.to_parquet(os.path.join(output_path, f"{table}.parquet"), index=False)
            
            print(f"[OK] {table} yozildi. Qatorlar: {record_count}, Ustunlar: {column_count}")

        except Exception as table_err:
            load_status = "FAILED"
            record_count = 0
            column_count = 0
            error_message = str(table_err)
            print(f"[XATOLIK] {table} jadvalida muammo: {error_message}")

        # Phase 3 talablariga mos Metric ma'lumotlarini yig'ish
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

# --- PHASE 3: METADATA EXPORT BO'LIMI ---
# 1. JSON formatida saqlash
json_log_path = "./metadata_report.json"
with open(json_log_path, "w", encoding="utf-8") as json_file:
    json.dump(metadata_records, json_file, indent=4, ensure_ascii=False)

# 2. CSV formatida saqlash (YANGI)
csv_log_path = "./metadata_report.csv"
metadata_df = pd.DataFrame(metadata_records)
metadata_df.to_csv(csv_log_path, index=False, encoding="utf-8")

print("\n=== PHASE 3: METADATA REPORTING YAKUNLANDI ===")
print(f"-> JSON hisobot: {json_log_path}")
print(f"-> CSV hisobot: {csv_log_path}")
