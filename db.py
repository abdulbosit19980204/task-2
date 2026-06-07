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

        #
        
        # --- FAYLGA YOZISH BO'LIMI ---
        # 'w' rejimi faylni yangidan ochadi (agar bor bo'lsa ichini tozalaydi)
        # encoding='utf-8' o'zbekcha yoki maxsus belgilarni to'g'ri yozish uchun shart
        with open("db_report.txt", "w", encoding="utf-8") as file:
            # Fayl sarlavhasi
            file.write("=========================================\n")
            file.write("       MARIADB MA'LUMOTLAR BAZASI HISOBOTI\n")
            file.write("=========================================\n\n")
            
            # Tizim ma'lumotlari
            file.write(f"Ulanish holati: Muvaffaqiyatli\n")
            file.write(f"MariaDB Versiyasi: {db_version}\n")
            file.write(f"Jami jadvallar soni: {len(tables)}\n\n")
            
            # Jadvallar ro'yxati
            file.write("Jadvallar ro'yxati:\n")
            file.write("-----------------------------------------\n")
            for index, table in enumerate(tables, start=1):
                file.write(f"{index}. {table[0]}\n")
            
            file.write("-----------------------------------------\n")
            file.write("Hisobot yakunlandi.\n")
            
        print("Hisobot 'db_report.txt' fayliga muvaffaqiyatli yozildi!")

except Exception as e:
    print(f"Xatolik yuz berdi: {e}")

finally:
    connection.close()
