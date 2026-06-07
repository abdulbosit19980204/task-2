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
        # 1. Versiyani olish
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        db_version = version[0]
        
        # 2. Jadvallar ro'yxatini olish
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        # Jadvallar haqida ma'lumot yig'ish uchun ro'yxat
        table_counts = []
        
        print("Jadvallardagi qatorlar soni hisoblanmoqda, kuting...")
        
        # Har bir jadval uchun COUNT(*) so'rovini bajarish
        for table in tables:
            table_name = table[0]
            
            # Xavfsiz dinamik SQL so'rovi (Jadval nomini f-string orqali qo'shamiz)
            count_query = f"SELECT COUNT(*) FROM `{table_name}`;"
            cursor.execute(count_query)
            
            row_count = cursor.fetchone()[0]
            table_counts.append((table_name, row_count))
        
        # --- FAYLGA YOZISH BO'LIMI ---
        with open("db_report_with_counts.txt", "w", encoding="utf-8") as file:
            # Fayl sarlavhasi
            file.write("==================================================\n")
            file.write("       MARIADB MA'LUMOTLAR BAZASI TO'LIQ HISOBOTI\n")
            file.write("==================================================\n\n")
            
            # Tizim ma'lumotlari
            file.write(f"Ulanish holati: Muvaffaqiyatli\n")
            file.write(f"MariaDB Versiyasi: {db_version}\n")
            file.write(f"Jami jadvallar soni: {len(tables)}\n\n")
            
            # Jadvallar va qatorlar soni ro'yxati (Chiroyli formatda)
            file.write(f"{'№':<4} | {'Jadval nomi':<45} | {'Qatorlar soni':<15}\n")
            file.write("-" * 72 + "\n")
            
            for index, (name, count) in enumerate(table_counts, start=1):
                # {name:<45} matnni chapdan 45 ta belgi joyga chiroyli tekislab beradi
                file.write(f"{index:<4} | {name:<45} | {count:<15,}\n")
            
            file.write("-" * 72 + "\n")
            file.write("Hisobot yakunlandi.\n")
            
        print("Kengaytirilgan hisobot 'db_report_with_counts.txt' fayliga yozildi!")

except Exception as e:
    print(f"Xatolik yuz berdi: {e}")

finally:
    connection.close()
