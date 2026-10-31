# create_db.py : ลบ clinic.db เก่า แล้วสร้างใหม่จาก clinic_db.sql
#   จากนั้นเติมตารางออกตรวจล่วงหน้า DAYS_AHEAD วัน (แพทย์ทุกคน ทุกวัน วันละ 12 ช่อง)
# ใช้รีเซ็ตข้อมูลก่อน Demo ทุกครั้ง  วิธีรัน: python create_db.py

import sqlite3
import os
from datetime import date, timedelta

# จำนวนวันที่เปิดให้จองล่วงหน้า นับจากวันนี้ (0 = วันนี้ ... 30 = อีก 30 วัน)
DAYS_AHEAD = 30

# เวลาเริ่มของช่องตรวจ ช่องละ 30 นาที: เช้า 09:00-12:00 บ่าย 13:00-16:00 พักเที่ยง 12:00-13:00
SLOT_TIMES = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
              '13:00', '13:30', '14:00', '14:30', '15:00', '15:30']

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

#รันคำสั่งทั้งไฟล์ในครั้งเดียว (สร้างตาราง + ใส่ข้อมูลตัวอย่าง รวมช่องเวลาตัวอย่าง 50 ช่อง schedule_id 1-50)
cursor.executescript(sql_script)

#เติมช่องเวลาออกตรวจล่วงหน้า: วันนี้ถึงอีก DAYS_AHEAD วัน แพทย์ทุกคน ทุกวัน (รวมเสาร์-อาทิตย์)
# เตรียมรายการ (doctor_id, work_date, slot_time) ด้วยลูป แล้วส่งให้ executemany ทีเดียว
cursor.execute('SELECT doctor_id FROM doctors ORDER BY doctor_id')
doctor_ids = [row[0] for row in cursor.fetchall()]
new_slots = []
for day in range(DAYS_AHEAD + 1):
    work_date = (date.today() + timedelta(days=day)).isoformat()
    for doctor_id in doctor_ids:
        for slot_time in SLOT_TIMES:
            new_slots.append((doctor_id, work_date, slot_time))

# INSERT OR IGNORE: ช่องที่มีอยู่แล้วในข้อมูลตัวอย่างจะชน UNIQUE (doctor_id, work_date, slot_time) แล้วถูกข้ามไป
# ช่องตัวอย่างจึงคง schedule_id เดิม คิวตัวอย่างอ้างช่องเดิมได้ถูกต้อง ช่องใหม่ได้ schedule_id ต่อจาก 50
cursor.executemany('''INSERT OR IGNORE INTO schedules (doctor_id, work_date, slot_time)
                      VALUES (?, ?, ?)''', new_slots)
added = cursor.rowcount

# Commit your changes in the database
conn.commit()
print("สร้าง clinic.db ใหม่เรียบร้อย")
print("เติมช่องเวลาล่วงหน้า " + str(DAYS_AHEAD) + " วัน: เตรียม " + str(len(new_slots)) + " ช่อง เพิ่มใหม่ "
      + str(added) + " ช่อง (มีอยู่แล้วในข้อมูลตัวอย่าง " + str(len(new_slots) - added) + " ช่อง)")
print()

#ตรวจจำนวนแถวของแต่ละตาราง
# ผลที่ควรได้ (DAYS_AHEAD = 30): departments 5, doctors 10, patients 15, schedules 3739, appointments 30, treatments 15
#   schedules 3739 = ช่องตัวอย่าง 50 + ช่องใหม่ 3689 (31 วัน x แพทย์ 10 คน x 12 ช่อง = 3720 ช่อง ซ้ำกับช่องตัวอย่าง 31 ช่อง)
cursor.execute('''SELECT 'departments', COUNT(*) FROM departments
                  UNION ALL SELECT 'doctors', COUNT(*) FROM doctors
                  UNION ALL SELECT 'patients', COUNT(*) FROM patients
                  UNION ALL SELECT 'schedules', COUNT(*) FROM schedules
                  UNION ALL SELECT 'appointments', COUNT(*) FROM appointments
                  UNION ALL SELECT 'treatments', COUNT(*) FROM treatments''')
print("จำนวนแถวในแต่ละตาราง")
for row in cursor.fetchall():
    print("  " + row[0] + ": " + str(row[1]))

#ช่วงวันที่ของช่องเวลา
# ผลที่ควรได้: ทั้งหมดตั้งแต่ 200 วันก่อน (ประวัติการรักษา) ถึงอีก 30 วัน / ช่องที่จองได้ตั้งแต่วันนี้ถึงอีก 30 วัน
cursor.execute('SELECT MIN(work_date), MAX(work_date) FROM schedules')
row = cursor.fetchone()
print("ช่วงวันที่ของช่องเวลาทั้งหมด: " + row[0] + " ถึง " + row[1])
cursor.execute('''SELECT MIN(work_date), MAX(work_date), COUNT(*) FROM schedules
                  WHERE work_date >= date('now', 'localtime')''')
row = cursor.fetchone()
print("ช่องเวลาตั้งแต่วันนี้: " + row[0] + " ถึง " + row[1] + " (" + str(row[2]) + " ช่อง)")

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
