import pymysql

# Bazaga ulanish sozlamalari
connection = pymysql.connect(
    host='5.189.143.4',
    port=3306,
    user='ignition_user',
    password='demo123',
    database='ignition',
    ssl_disabled=True
)

try:
    with connection.cursor() as cursor:
        # 1. Baza versiyasini olish
        cursor.execute("SELECT VERSION();")
        db_version = cursor.fetchone()[0]

        # 2. Baza ichidagi barcha ustunlar sxemasini, turlarini va Primary Keylarini bitta so'rovda olish
        schema_query = """
            SELECT 
                TABLE_NAME, 
                COLUMN_NAME, 
                DATA_TYPE, 
                COLUMN_TYPE, 
                COLUMN_KEY
            FROM 
                information_schema.columns 
            WHERE 
                table_schema = 'ignition'
            ORDER BY 
                TABLE_NAME, ORDINAL_POSITION;
        """
        cursor.execute(schema_query)
        columns_data = cursor.fetchall()

        # 3. Har bir jadvalning qatorlar sonini (Row Count) aniq hisoblab chiqish
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        table_rows = {}
        print("Jadvallardagi qatorlar soni aniqlanmoqda...")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            table_rows[table_name] = cursor.fetchone()[0]

        # 4. Ma'lumotlarni guruhlash (Jadval nomi -> Ustunlar ro'yxati)
        db_structure = {}
        for row in columns_data:
            t_name, c_name, d_type, c_type, c_key = row
            if t_name not in db_structure:
                db_structure[t_name] = []
            
            # Agar ustun Primary Key bo'lsa belgi qo'yamiz
            is_pk = "Ha (PK)" if c_key == "PRI" else "Yo'q"
            
            db_structure[t_name].append({
                "column": c_name,
                "type": c_type, # To'liq turi (masalan: varchar(255) yoki int(11))
                "pk": is_pk
            })

        # --- FAYLGA YOZISH BO'LIMI ---
        with open("source_system_analysis.txt", "w", encoding="utf-8") as file:
            file.write("=================================================================\n")
            file.write("         MARIADB BAZASI METAMA'LUMOTLARI (SCHEMA) HISOBOTI\n")
            file.write("=================================================================\n\n")
            
            file.write(f"Ma'lumotlar bazasi: ignition\n")
            file.write(f"MariaDB Versiyasi:  {db_version}\n")
            file.write(f"Jami jadvallar:     {len(tables)} ta\n")
            file.write("=================================================================\n\n")

            # Har bir jadval uchun blok yaratamiz
            for index, (t_name, columns) in enumerate(db_structure.items(), start=1):
                file.write(f"{index}. JADVAL NOMI: {t_name}\n")
                file.write(f"   Qatorlar soni (Row Count): {table_rows.get(t_name, 0):,}\n")
                file.write(f"   Ustunlar strukturasi:\n")
                
                # Sarlavha paneli
                file.write(f"   {'   Ustun nomi':<30} | {'Ma\'lumot turi':<20} | {'Primary Key':<12}\n")
                file.write(f"   " + "-" * 68 + "\n")
                
                # Har bir ustun haqida ma'lumot
                for col in columns:
                    file.write(f"      {col['column']:<27} | {col['type']:<20} | {col['pk']:<12}\n")
                
                file.write("\n" + "=" * 65 + "\n\n")

        print("To'liq sxema hisoboti 'source_system_analysis.txt' fayliga muvaffaqiyatli yozildi!")

except Exception as e:
    print(f"Xatolik yuz berdi: {e}")

finally:
    connection.close()
