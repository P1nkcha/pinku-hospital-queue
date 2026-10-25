# create_db.py : ลบ clinic.db เก่า แล้วสร้างใหม่จาก clinic_db.sql
# ใช้รีเซ็ตข้อมูลก่อน Demo ทุกครั้ง  วิธีรัน: python create_db.py

import sqlite3
import os

# หาตำแหน่งไฟล์จากโฟลเดอร์ที่ไฟล์นี้อยู่ จะได้ไม่สร้าง clinic.db ผิดโฟลเดอร์
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clinic.db')
SQL_PATH = os.path.join(BASE_DIR, 'clinic_db.sql')

#ลบไฟล์ฐานข้อมูลเก่า (ถ้ามี)
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print("ลบ clinic.db เดิมแล้ว")
    except PermissionError:
        # บน Windows ถ้า DB Browser ยังเปิดไฟล์อยู่ จะลบไม่ได้
        print("ลบ clinic.db ไม่ได้ เพราะมีโปรแกรมเปิดไฟล์อยู่ ให้ปิด DB Browser for SQLite แล้วรันใหม่")
        raise SystemExit

#อ่านคำสั่ง SQL ทั้งไฟล์ (utf-8-sig อ่านได้ทั้งไฟล์ UTF-8 ธรรมดาและแบบมี BOM)
with open(SQL_PATH, 'r', encoding='utf-8-sig') as f:
    sql_script = f.read()

#Connecting to sqlite (ถ้ายังไม่มีไฟล์ จะสร้าง clinic.db ให้ใหม่)
conn = sqlite3.connect(DB_PATH)

#Creating a cursor object using the cursor() method
cursor = conn.cursor()

#เปิดการตรวจ foreign key
cursor.execute("PRAGMA foreign_keys = ON")

#รันคำสั่งทั้งไฟล์ในครั้งเดียว (สร้างตาราง + ใส่ข้อมูลตัวอย่าง)
cursor.executescript(sql_script)

# Commit your changes in the database
conn.commit()
print("สร้าง clinic.db ใหม่เรียบร้อย")
print()

#ตรวจจำนวนแถวของแต่ละตาราง
# ผลที่ควรได้: departments 5, doctors 10, patients 15, schedules 50, appointments 30, treatments 15
cursor.execute('''SELECT 'departments', COUNT(*) FROM departments
                  UNION ALL SELECT 'doctors', COUNT(*) FROM doctors
                  UNION ALL SELECT 'patients', COUNT(*) FROM patients
                  UNION ALL SELECT 'schedules', COUNT(*) FROM schedules
                  UNION ALL SELECT 'appointments', COUNT(*) FROM appointments
                  UNION ALL SELECT 'treatments', COUNT(*) FROM treatments''')
print("จำนวนแถวในแต่ละตาราง")
for row in cursor.fetchall():
    print("  " + row[0] + ": " + str(row[1]))

#นับคิวแยกตามสถานะ
# ผลที่ควรได้: ตรวจแล้ว 15, จองแล้ว 12, ยกเลิก 3
cursor.execute('''SELECT status, COUNT(*) FROM appointments
                  GROUP BY status ORDER BY COUNT(*) DESC''')
print("จำนวนคิวแยกตามสถานะ")
for row in cursor.fetchall():
    print("  " + row[0] + ": " + str(row[1]))

#คิวของวันนี้ (นับทุกสถานะ)
# ผลที่ควรได้: 7 คิว
cursor.execute('''SELECT date('now', 'localtime'), COUNT(*)
                  FROM appointments
                  JOIN schedules ON appointments.schedule_id = schedules.schedule_id
                  WHERE schedules.work_date = date('now', 'localtime')''')
row = cursor.fetchone()
print("คิวของวันนี้ (" + row[0] + "): " + str(row[1]) + " คิว")

#คิวที่ตรวจแล้วแต่ยังไม่มีผลการรักษา (ทุกคิวที่ตรวจแล้วต้องมีแถวใน treatments)
# ผลที่ควรได้: 0 คิว
cursor.execute('''SELECT COUNT(*)
                  FROM appointments
                  LEFT JOIN treatments ON treatments.appt_id = appointments.appt_id
                  WHERE appointments.status = 'ตรวจแล้ว' AND treatments.treatment_id IS NULL''')
print("คิวที่ตรวจแล้วแต่ยังไม่มีผลการรักษา: " + str(cursor.fetchone()[0]) + " คิว")

#Closing the connection
conn.close()
