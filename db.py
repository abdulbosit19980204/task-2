import pymysql

# Bazaga ulanish sozlamalari
connection = pymysql.connect(
    host='5.189.143.4',
    port=3306,
    user='ignition_user',
    password='demo123',
    database='ignition',
    ssl_disabled=True # --ssl=0 degani
)

try:
    with connection.cursor() as cursor:
        # Oddiy test so'rovi
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
       
        print(f"Ulanish muvaffaqiyatli! MariaDB versiyasi: {version[0]}")
        
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Jadvalar:")
        for table in tables:
            print(f"  - {table[0]}")
finally:
    connection.close()
