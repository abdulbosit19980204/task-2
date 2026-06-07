import findspark
findspark.init()

import os
import json
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

# 1. Spark Session-ni JDBC drayver bilan ishga tushirish
# 'mariadb-java-client-3.5.8.jar' fayli kod bilan bitta papkada bo'lishi kerak
spark = SparkSession.builder \
    .appName("MariaDB-to-Bronze-Ingestion") \
    .config("spark.jars", "mariadb-java-client-3.5.8.jar") \
    .getOrCreate()

# 2. MariaDB JDBC ulanish sozlamalari
jdbc_url = "jdbc:mariadb://5.189.143.4:3306/ignition?useSSL=false"
connection_properties = {
    "user": "ignition_user",
    "password": "demo123",
    "driver": "org.mariadb.jdbc.Driver"
}

# Biznes jadvallari ro'yxati (Topshiriq talabi bo'yicha)
business_tables = ["customers", "orders", "products", "order_items"]

# Bronze qatlam joylashadigan papka (Lokal)
bronze_base_path = "./bronze"
os.makedirs(bronze_base_path, exist_ok=True)

# Yuklash natijalari (Metadata) uchun ro'yxat
ingestion_logs = []

print("=== BRONZE QATLAMGA MA'LUMOTLARNI YUKLASH BOSHLANDI ===")

# 3. Jadvallarni sikl (loop) orqali o'qish va yozish
for table in business_tables:
    extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[MUTAAXASSIS] {table} jadvali o'qilmoqda...")
    
    try:
        # JDBC orqali ma'lumotni Spark DataFrame-ga o'qish
        df = spark.read.jdbc(url=jdbc_url, table=table, properties=connection_properties)
        
        # Data Engineer amaliyoti: Ma'lumotga yuklangan vaqtini (Ingestion Timestamp) qo'shish
        df_with_meta = df.withColumn("ingested_at", current_timestamp())
        
        # Sxema (Schema) ma'lumotini matn ko'rinishida olish
        schema_json = df.schema.json()
        
        # Qatorlar sonini hisoblash
        record_count = df.count()
        
        # 4. Bronze formatda (Parquet) saqlash
        # Hamma jadval o'z papkasiga yoziladi (Masalan: bronze/customers)
        output_path = os.path.join(bronze_base_path, table)
        
        # 'overwrite' - agar papka bo'lsa o'chirib qayta yozadi
        df_with_meta.write.mode("overwrite").parquet(output_path)
        
        load_status = "SUCCESS"
        error_message = None
        print(f"[MUVAFFIQIYAT] {table} muvaffaqiyatli yuklandi. Qatorlar: {record_count}")

    except Exception as e:
        load_status = "FAILED"
        record_count = 0
        schema_json = None
        error_message = str(e)
        print(f"[XATOLIK] {table} jadvalida muammo: {error_message}")

    # Log ma'lumotlarini yig'ish
    ingestion_logs.append({
        "table_name": table,
        "record_count": record_count,
        "extraction_timestamp": extraction_time,
        "load_status": load_status,
        "error_message": error_message,
        "schema": json.loads(schema_json) if schema_json else None
    })

# 5. Output / Metadata hisobotini saqlash (JSON formatida log yuritish)
log_file_path = "./bronze_ingestion_summary.json"
with open(log_file_path, "w", encoding="utf-8") as log_file:
    json.dump(ingestion_logs, log_file, indent=4, ensure_ascii=False)

print("\n=== JARAYON YAKUNLANDI ===")
print(f"Barcha loglar va sxema ma'lumotlari '{log_file_path}' fayliga yozildi.")

# Spark sessiyani yopish
spark.stop()
