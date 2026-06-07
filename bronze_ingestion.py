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

# JDBC Connection URL
jdbc_url = f"jdbc:mariadb://{server_ip}:{port}/{database}?useSSL=false"
driver_class = "org.mariadb.jdbc.Driver"
jar_path = "./mariadb-java-client-3.5.8.jar"  # Siz yuklab olgan fayl nomi

# Biznes jadvallari
business_tables = ["customers", "orders", "products", "order_items"]

# Bronze qatlam joylashadigan papka
bronze_base_path = "./bronze"
os.makedirs(bronze_base_path, exist_ok=True)

ingestion_logs = []

print("=== BRONZE QATLAMGA (JDBC + PANDAS) YUKLASH BOSHLANDI ===")

# 2. JDBC orqali ulanishni ochish
try:
    conn = jaydebeapi.connect(
        driver_class,
        jdbc_url,
        [username, password],
        jar_path
    )
    print("[MUVAFFAQIYAT] MariaDB-ga JDBC orqali ulanish o'rnatildi.\n")

    # 3. Jadvallarni sikl orqali o'qish
    for table in business_tables:
        extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[JARAYON] {table} jadvali yuklanmoqda...")
        
        try:
            # SQL so'rovi orqali ma'lumotni o'qish
            query = f"SELECT * FROM `{table}`"
            df = pd.read_sql(query, conn)
            
            # Data Engineer amaliyoti: Yuklangan vaqtini qo'shish (Ingestion Timestamp)
            df["ingested_at"] = pd.Timestamp.now()
            
            # Sxema (Schema) ma'lumotini olish (Ustun nomi va turi)
            schema_info = df.dtypes.astype(str).to_dict()
            
            # Qatorlar soni
            record_count = len(df)
            
            # 4. Bronze formatda (Parquet) saqlash
            output_path = os.path.join(bronze_base_path, table)
            os.makedirs(output_path, exist_ok=True)
            
            # Parquet fayl ko'rinishida yozish
            df.to_parquet(os.path.join(output_path, f"{table}.parquet"), index=False)
            
            load_status = "SUCCESS"
            error_message = None
            print(f"[OK] {table} muvaffaqiyatli yozildi. Qatorlar: {record_count}")

        except Exception as table_err:
            load_status = "FAILED"
            record_count = 0
            schema_info = None
            error_message = str(table_err)
            print(f"[XATOLIK] {table} jadvalida muammo: {error_message}")

        # Log yig'ish
        ingestion_logs.append({
            "table_name": table,
            "record_count": record_count,
            "extraction_timestamp": extraction_time,
            "load_status": load_status,
            "error_message": error_message,
            "schema_info": schema_info
        })

except Exception as conn_err:
    print(f"[KRITIK XATO] JDBC ulanishida muammo: {conn_err}")

finally:
    # Ulanishni yopish
    if 'conn' in locals():
        conn.close()

# 5. Output JSON Log hisobotini saqlash
log_file_path = "./bronze_ingestion_summary.json"
with open(log_file_path, "w", encoding="utf-8") as log_file:
    json.dump(ingestion_logs, log_file, indent=4, ensure_ascii=False)

print("\n=== JARAYON YAKUNLANDI ===")
print(f"Barcha loglar va sxemalar '{log_file_path}' fayliga yozildi.")
