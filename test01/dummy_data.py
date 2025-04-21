import mysql.connector
from datetime import datetime
import random
import time

# DB 연결
db = mysql.connector.connect(
    host="10.10.10.113",
    user="root",
    password="1234",
    database="tp_dht11_db",
    autocommit=True
)

cursor = db.cursor()

print("✅ 더미 데이터 실시간 삽입 시작 (1초 간격)... 중지하려면 Ctrl + C")

try:
    while True:
        now = datetime.now()

        temperature = round(random.uniform(24.0, 28.0), 1)
        humidity = round(random.uniform(40.0, 60.0), 1)

        cursor.execute("""
            INSERT INTO measured_value (time, temperature, humidity)
            VALUES (%s, %s, %s)
        """, (now.strftime("%Y-%m-%d %H:%M:%S"), temperature, humidity))

        print(f"입력 → 시간: {now.strftime('%H:%M:%S')}, 온도: {temperature}, 습도: {humidity}")

        time.sleep(1)  # 1초 대기

except KeyboardInterrupt:
    print("\n⛔ 중지됨 (사용자 인터럽트)")

finally:
    cursor.close()
    db.close()
    print("🔌 DB 연결 종료")