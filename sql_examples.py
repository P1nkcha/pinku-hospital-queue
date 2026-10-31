# sql_examples.py : ตัวอย่างคำสั่ง SQL ของระบบจองคิวคลินิก
# รันทีละคำสั่ง แล้วพิมพ์คำสั่งและผลลัพธ์ออกมาให้เห็น
#
# วิธีใช้:  python create_db.py  แล้วตามด้วย  python sql_examples.py
#   - ต้องเริ่มจากข้อมูลชุดตั้งต้นเสมอ ผลจึงจะตรงกับคอมเมนต์ "ผลที่ควรได้"
#   - ไฟล์นี้แก้ข้อมูลจริงใน clinic.db  ก่อน Demo โปรแกรม ให้รัน python create_db.py อีกครั้ง
#
# ตัวอย่างทั้งหมด 10 ข้อ
#   1-5  SELECT แบบ JOIN
#   6    UPDATE ยกเลิกคิว (และลองยกเลิกซ้ำ)
#   7    INSERT จองช่องเดิมใหม่หลังยกเลิก (และลองจองช่องที่มีคนจองแล้ว)
#   8    UPDATE แก้เบอร์โทรผู้ป่วย (และลองใช้เบอร์ซ้ำ)
#   9    DELETE ลบช่องเวลาที่ไม่มีใครจอง
#   10   DELETE ลองลบผู้ป่วยที่มีคิวแล้ว (ติด foreign key)

import sqlite3
import os

# True = หยุดรอให้กด Enter ก่อนไปตัวอย่างถัดไป (เหมาะตอนนำเสนอ)
# False = รันรวดเดียวจนจบ
PAUSE = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clinic.db')


# ---------------------------------------------------------------------
# ฟังก์ชันช่วยพิมพ์ผล
# ---------------------------------------------------------------------

def title(text):
    # พิมพ์หัวข้อของแต่ละตัวอย่าง
    print()
    print("=" * 70)
    print(text)
    print("=" * 70)


def show_sql(sql, params=()):
    # พิมพ์คำสั่ง SQL และค่าที่ส่งแทน ? ให้ผู้ฟังเห็น
    print("SQL:")
    print(sql)
    if params:
        print("ค่าที่แทน ? :", params)


def print_rows(cursor):
    # พิมพ์ผลของ SELECT : ชื่อคอลัมน์ แล้วตามด้วยข้อมูลทีละแถว
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    print("-> ผลลัพธ์")
    print("   " + " | ".join(columns))
    for row in rows:
        print("   " + " | ".join(str(value) for value in row))
    print("   (" + str(len(rows)) + " แถว)")


def run_select(cursor, sql, params=()):
    # รัน SELECT แล้วพิมพ์ทั้งคำสั่งและผลลัพธ์
    show_sql(sql, params)
    cursor.execute(sql, params)
    print_rows(cursor)


def wait():
    # หยุดรอกด Enter (ถ้า PAUSE = True)
    if PAUSE:
        input("\n... กด Enter เพื่อไปตัวอย่างถัดไป ...")


# ---------------------------------------------------------------------
# เริ่มโปรแกรม
# ---------------------------------------------------------------------

if not os.path.exists(DB_PATH):
    print("ไม่พบ clinic.db  ให้รัน python create_db.py ก่อน")
    raise SystemExit

#Connecting to sqlite
conn = sqlite3.connect(DB_PATH)

#เปิดการตรวจ foreign key ทุกครั้งที่เชื่อมต่อ (ถ้าไม่เปิด ตัวอย่างที่ 10 จะลบผู้ป่วยได้)
conn.execute("PRAGMA foreign_keys = ON")

#Creating a cursor object using the cursor() method
cursor = conn.cursor()


# =====================================================================
# ตัวอย่างที่ 1 : SELECT JOIN 5 ตาราง - คิวของวันนี้ พร้อมชื่อผู้ป่วย แพทย์ และแผนก
# ใช้ตอนเปิดดูคิวประจำวัน
# ผลที่ควรได้: 7 แถว เรียงตามเวลา (จองแล้ว 6 คิว + ยกเลิก 1 คิว คือคิวของธีรเดช 10:00)
# =====================================================================
title("ตัวอย่างที่ 1/10 : คิวของวันนี้ (JOIN 5 ตาราง)")
sql = '''SELECT a.appt_id, s.slot_time, p.patient_name, d.doctor_name, dp.dept_name, a.status
    FROM appointments a
    JOIN patients p     ON a.patient_id  = p.patient_id
    JOIN schedules s    ON a.schedule_id = s.schedule_id
    JOIN doctors d      ON s.doctor_id   = d.doctor_id
    JOIN departments dp ON d.dept_id     = dp.dept_id
    WHERE s.work_date = date('now', 'localtime')
    ORDER BY s.slot_time, d.doctor_id'''
run_select(cursor, sql)
wait()


# =====================================================================
# ตัวอย่างที่ 2 : SELECT LEFT JOIN + GROUP BY - จำนวนคิวของแพทย์แต่ละคน (ไม่นับคิวที่ยกเลิก)
# ใช้ LEFT JOIN เพื่อให้แพทย์ที่ยังไม่มีคิวแสดงด้วย (นับได้ 0)
# ผลที่ควรได้: 10 แถว  นพ.ประวิทย์ มากสุด 6 คิว  พญ.รัตนา น้อยสุด 0 คิว  รวมทุกคน 27 คิว (นับคิวย้อนหลังที่ตรวจแล้วด้วย)
# =====================================================================
title("ตัวอย่างที่ 2/10 : จำนวนคิวของแพทย์แต่ละคน")
sql = '''SELECT d.doctor_name, dp.dept_name, COUNT(a.appt_id) AS total_appts
    FROM doctors d
    JOIN departments dp    ON d.dept_id = dp.dept_id
    LEFT JOIN schedules s  ON s.doctor_id = d.doctor_id
    LEFT JOIN appointments a ON a.schedule_id = s.schedule_id
                            AND a.status <> 'ยกเลิก'
    GROUP BY d.doctor_id
    ORDER BY total_appts DESC, d.doctor_id'''
run_select(cursor, sql)
wait()


# =====================================================================
# ตัวอย่างที่ 3 : SELECT LEFT JOIN - ช่องเวลาที่ยังว่างของ พญ.กมลวรรณ (doctor_id 2) วันพรุ่งนี้
# หน้า "จองคิว" ใช้คำสั่งแบบเดียวกันนี้ และตัดช่องของวันนี้ที่เลยเวลาปัจจุบันออกอีกชั้น
# ช่องว่าง = ไม่มีคิวที่ยังไม่ยกเลิก (a.appt_id IS NULL)
# กรองแพทย์ 1 คนและวันเดียว เพราะตารางออกตรวจมีล่วงหน้า 30 วัน ถ้าไม่กรองผลจะยาวหลายร้อยแถว
# ผลที่ควรได้: 11 แถว (09:30 ถึง 15:30)  ไม่มี 09:00 เพราะคิว 14 จองไว้  และมี 09:30 เพราะคิว 17 ถูกยกเลิกไปแล้ว
# =====================================================================
title("ตัวอย่างที่ 3/10 : ช่องเวลาที่ยังว่าง พญ.กมลวรรณ วันพรุ่งนี้")
sql = '''SELECT s.schedule_id, s.work_date, s.slot_time, d.doctor_name
    FROM schedules s
    JOIN doctors d ON s.doctor_id = d.doctor_id
    LEFT JOIN appointments a ON a.schedule_id = s.schedule_id
                            AND a.status <> 'ยกเลิก'
    WHERE s.doctor_id = ?
      AND s.work_date = date('now', 'localtime', '+1 day')
      AND a.appt_id IS NULL
    ORDER BY s.slot_time'''
run_select(cursor, sql, (2,))
wait()


# =====================================================================
# ตัวอย่างที่ 4 : SELECT JOIN - ประวัติคิวทั้งหมดของผู้ป่วย ค้นด้วยเบอร์โทร
# เป็นการค้นหาแบบเดียวกับหน้า "ค้นหาและจัดการคิว"
# ผลที่ควรได้: 2 แถวของสมหญิง (พรุ่งนี้ จองแล้ว / เมื่อวานซืน ตรวจแล้ว) เรียงวันใหม่ก่อน
# =====================================================================
title("ตัวอย่างที่ 4/10 : ประวัติคิวของผู้ป่วย ค้นด้วยเบอร์โทร")
sql = '''SELECT a.appt_id, p.patient_name, s.work_date, s.slot_time, d.doctor_name, a.status
    FROM appointments a
    JOIN patients p  ON a.patient_id  = p.patient_id
    JOIN schedules s ON a.schedule_id = s.schedule_id
    JOIN doctors d   ON s.doctor_id   = d.doctor_id
    WHERE p.phone = ?
    ORDER BY s.work_date DESC, s.slot_time'''
run_select(cursor, sql, ('0812345678',))
wait()


# =====================================================================
# ตัวอย่างที่ 5 : SELECT JOIN + LIKE - ค้นหาคิวด้วยชื่อผู้ป่วยบางส่วน
# % คือ "ตัวอักษรอะไรก็ได้" จึงหาชื่อที่มีคำว่า "สม" อยู่ตรงไหนก็ได้
# เอา % ไปต่อกับ "ค่า" ที่ส่งแทน ? ไม่ได้ต่อเข้าไปในคำสั่ง SQL จึงยังปลอดภัย
# ผลที่ควรได้: 4 แถว (สมหญิง 2 คิว, สมศักดิ์ 2 คิว)
# =====================================================================
title("ตัวอย่างที่ 5/10 : ค้นหาคิวด้วยชื่อบางส่วน")
keyword = 'สม'
sql = '''SELECT a.appt_id, p.patient_name, s.work_date, s.slot_time, d.doctor_name, a.status
    FROM appointments a
    JOIN patients p  ON a.patient_id  = p.patient_id
    JOIN schedules s ON a.schedule_id = s.schedule_id
    JOIN doctors d   ON s.doctor_id   = d.doctor_id
    WHERE p.patient_name LIKE ?
    ORDER BY s.work_date, s.slot_time'''
run_select(cursor, sql, ('%' + keyword + '%',))
wait()


# =====================================================================
# ตัวอย่างที่ 6 : UPDATE - ยกเลิกคิวที่ 7 (วิภาวรรณ วันนี้ 09:00)
# ยกเลิกไม่ลบแถว แค่เปลี่ยน status เพื่อเก็บประวัติ
# เงื่อนไข status = 'จองแล้ว' ทำให้คิวที่ตรวจแล้วหรือยกเลิกแล้ว ยกเลิกซ้ำไม่ได้
# =====================================================================
title("ตัวอย่างที่ 6/10 : UPDATE ยกเลิกคิว")
appt_id = 7

# 6.1 ก่อนแก้: SELECT ด้วยเงื่อนไขเดียวกับ UPDATE
# ผลที่ควรได้: 1 แถว status = จองแล้ว
print("[ก่อน UPDATE]")
sql = '''SELECT appt_id, patient_id, schedule_id, status
    FROM appointments
    WHERE appt_id = ? AND status = 'จองแล้ว' '''
run_select(cursor, sql, (appt_id,))

# 6.2 UPDATE
# ผลที่ควรได้: แก้ไป 1 แถว
print()
print("[รัน UPDATE]")
sql = '''UPDATE appointments SET status = 'ยกเลิก'
    WHERE appt_id = ? AND status = 'จองแล้ว' '''
show_sql(sql, (appt_id,))
cursor.execute(sql, (appt_id,))
conn.commit()
print("-> แก้ไป", cursor.rowcount, "แถว")

# 6.3 หลังแก้: ดูแถวเดิมด้วย appt_id
# ผลที่ควรได้: แถวยังอยู่ แต่ status = ยกเลิก
print()
print("[หลัง UPDATE]")
sql = '''SELECT appt_id, patient_id, schedule_id, status
    FROM appointments
    WHERE appt_id = ?'''
run_select(cursor, sql, (appt_id,))

# 6.4 ลองยกเลิกซ้ำด้วยคำสั่งเดิม
# ผลที่ควรได้: แก้ไป 0 แถว เพราะสถานะไม่ใช่ 'จองแล้ว' แล้ว
print()
print("[ลองยกเลิกซ้ำ]")
cursor.execute('''UPDATE appointments SET status = 'ยกเลิก'
    WHERE appt_id = ? AND status = 'จองแล้ว' ''', (appt_id,))
conn.commit()
print("-> แก้ไป", cursor.rowcount, "แถว  (ยกเลิกซ้ำไม่ได้)")
wait()


# =====================================================================
# ตัวอย่างที่ 7 : INSERT - จองช่องเดิมใหม่หลังยกเลิก
# ช่อง schedule_id 10 (นพ.ประวิทย์ วันนี้ 09:00) เพิ่งถูกยกเลิกในตัวอย่างที่ 6
# UNIQUE แบบมีเงื่อนไขไม่นับคิวที่ยกเลิก จึงจองช่องนี้ใหม่ได้
# =====================================================================
title("ตัวอย่างที่ 7/10 : จองช่องเดิมใหม่หลังยกเลิก")
schedule_id = 10

# 7.1 ให้ พงศกร (patient_id 14) จองช่องที่ 10
# ผลที่ควรได้: จองสำเร็จ ได้คิวใหม่ appt_id 31  status เป็นค่าเริ่มต้น 'จองแล้ว'
print("[จองช่องที่เพิ่งถูกยกเลิก]")
sql = '''INSERT INTO appointments (patient_id, schedule_id, symptom)
    VALUES (?, ?, ?)'''
params = (14, schedule_id, 'ปวดหลัง')
show_sql(sql, params)
cursor.execute(sql, params)
conn.commit()
print("-> จองสำเร็จ ได้คิวใหม่ appt_id =", cursor.lastrowid)

# 7.2 ดูทุกคิวของช่องที่ 10
# ผลที่ควรได้: 2 แถว คือคิวเดิมที่ยกเลิก (เก็บเป็นประวัติ) + คิวใหม่ที่จองแล้ว
print()
print("[ทุกคิวของช่องที่ 10]")
sql = '''SELECT appt_id, patient_id, schedule_id, status, booked_at
    FROM appointments
    WHERE schedule_id = ?
    ORDER BY appt_id'''
run_select(cursor, sql, (schedule_id,))

# 7.3 ลองจองช่องที่ 11 ซึ่งมีคิวของปวีณาอยู่แล้ว
# ผลที่ควรได้: ฐานข้อมูลปฏิเสธ  UNIQUE constraint failed: appointments.schedule_id
print()
print("[ลองจองช่องที่มีคนจองแล้ว]")
params = (15, 11, 'ปวดหัว')
sql = '''INSERT INTO appointments (patient_id, schedule_id, symptom)
    VALUES (?, ?, ?)'''
show_sql(sql, params)
try:
    cursor.execute(sql, params)
    conn.commit()
    print("-> จองได้ (ไม่ควรเกิดขึ้น)")
except sqlite3.IntegrityError as error:
    print("-> จองไม่ได้:", error)
wait()


# =====================================================================
# ตัวอย่างที่ 8 : UPDATE - แก้เบอร์โทรของวิภาวรรณ (patient_id 4)
# =====================================================================
title("ตัวอย่างที่ 8/10 : UPDATE แก้เบอร์โทรผู้ป่วย")
patient_id = 4
new_phone = '0879998888'

# 8.1 ก่อนแก้: SELECT ด้วยเงื่อนไขเดียวกับ UPDATE
# ผลที่ควรได้: 1 แถว เบอร์เดิม 0872223344
print("[ก่อน UPDATE]")
sql = '''SELECT patient_id, patient_name, phone
    FROM patients
    WHERE patient_id = ?'''
run_select(cursor, sql, (patient_id,))

# 8.2 UPDATE
# ผลที่ควรได้: แก้ไป 1 แถว
print()
print("[รัน UPDATE]")
sql_update = '''UPDATE patients SET phone = ?
    WHERE patient_id = ?'''
show_sql(sql_update, (new_phone, patient_id))
cursor.execute(sql_update, (new_phone, patient_id))
conn.commit()
print("-> แก้ไป", cursor.rowcount, "แถว")

# 8.3 หลังแก้
# ผลที่ควรได้: เบอร์ใหม่ 0879998888 และคิวของเธอไม่ต้องแก้ตาม เพราะคิวเก็บแค่ patient_id
print()
print("[หลัง UPDATE]")
run_select(cursor, sql, (patient_id,))

# 8.4 ลองแก้เป็นเบอร์ที่ซ้ำกับสมหญิง
# ผลที่ควรได้: ฐานข้อมูลปฏิเสธ  UNIQUE constraint failed: patients.phone
print()
print("[ลองแก้เป็นเบอร์ที่มีคนใช้แล้ว]")
show_sql(sql_update, ('0812345678', patient_id))
try:
    cursor.execute(sql_update, ('0812345678', patient_id))
    conn.commit()
    print("-> แก้ได้ (ไม่ควรเกิดขึ้น)")
except sqlite3.IntegrityError as error:
    print("-> แก้ไม่ได้:", error)
wait()


# =====================================================================
# ตัวอย่างที่ 9 : DELETE - ลบช่องเวลาที่ไม่มีใครจองของ พญ.รัตนา (doctor_id 10) วันมะรืน
# สมมติแพทย์ลางาน  ลบได้เฉพาะช่องที่ไม่เคยมีคิวเลย (ไม่มีแถวใน appointments)
# =====================================================================
title("ตัวอย่างที่ 9/10 : DELETE ลบช่องเวลาที่ไม่มีใครจอง")
doctor_id = 10

# 9.1 ก่อนลบ: SELECT ด้วยเงื่อนไขเดียวกับ DELETE
# ผลที่ควรได้: 12 แถว (ทุกช่องของวันมะรืน 09:00 ถึง 15:30 เพราะไม่มีใครจอง)
print("[ก่อน DELETE]")
sql = '''SELECT schedule_id, doctor_id, work_date, slot_time
    FROM schedules
    WHERE doctor_id = ?
      AND work_date = date('now', 'localtime', '+2 day')
      AND schedule_id NOT IN (SELECT schedule_id FROM appointments)'''
run_select(cursor, sql, (doctor_id,))

# 9.2 DELETE
# ผลที่ควรได้: ลบไป 12 แถว
print()
print("[รัน DELETE]")
sql = '''DELETE FROM schedules
    WHERE doctor_id = ?
      AND work_date = date('now', 'localtime', '+2 day')
      AND schedule_id NOT IN (SELECT schedule_id FROM appointments)'''
show_sql(sql, (doctor_id,))
cursor.execute(sql, (doctor_id,))
conn.commit()
print("-> ลบไป", cursor.rowcount, "แถว")

# 9.3 หลังลบ: ดูช่องของ พญ.รัตนา วันมะรืนอีกครั้ง (วันอื่นยังอยู่ครบ ไม่ได้แสดงเพราะมีหลายร้อยแถว)
# ผลที่ควรได้: 0 แถว
print()
print("[หลัง DELETE]")
sql = '''SELECT schedule_id, doctor_id, work_date, slot_time
    FROM schedules
    WHERE doctor_id = ?
      AND work_date = date('now', 'localtime', '+2 day')'''
run_select(cursor, sql, (doctor_id,))
wait()


# =====================================================================
# ตัวอย่างที่ 10 : DELETE - ลองลบผู้ป่วยที่มีคิวแล้ว (สมหญิง patient_id 1)
# appointments ยังอ้างถึง patient_id 1 อยู่ foreign key จึงไม่ยอมให้ลบ
# ถ้าไม่ได้สั่ง PRAGMA foreign_keys = ON  SQLite จะลบให้ และคิวของเธอจะชี้ไปหาผู้ป่วยที่ไม่มีอยู่จริง
# =====================================================================
title("ตัวอย่างที่ 10/10 : DELETE ลองลบผู้ป่วยที่มีคิวแล้ว")
patient_id = 1

# 10.1 ก่อนลบ: SELECT ด้วยเงื่อนไขเดียวกับ DELETE และดูว่ามีคิวกี่คิว
# ผลที่ควรได้: 1 แถว สมหญิง ใจดี มี 2 คิว
print("[ก่อน DELETE]")
sql = '''SELECT p.patient_id, p.patient_name, p.phone, COUNT(a.appt_id) AS total_appts
    FROM patients p
    LEFT JOIN appointments a ON a.patient_id = p.patient_id
    WHERE p.patient_id = ?
    GROUP BY p.patient_id'''
run_select(cursor, sql, (patient_id,))

# 10.2 DELETE
# ผลที่ควรได้: ฐานข้อมูลปฏิเสธ  FOREIGN KEY constraint failed
print()
print("[รัน DELETE]")
sql_delete = '''DELETE FROM patients
    WHERE patient_id = ?'''
show_sql(sql_delete, (patient_id,))
try:
    cursor.execute(sql_delete, (patient_id,))
    conn.commit()
    print("-> ลบได้ (ไม่ควรเกิดขึ้น)")
except sqlite3.IntegrityError as error:
    print("-> ลบไม่ได้:", error)

# 10.3 หลังลองลบ
# ผลที่ควรได้: สมหญิงยังอยู่ครบ 1 แถว และยังมี 2 คิวเหมือนเดิม
print()
print("[หลัง DELETE]")
run_select(cursor, sql, (patient_id,))


#Closing the connection
conn.close()
print()
print("จบตัวอย่างทั้งหมด  ข้อมูลใน clinic.db ถูกแก้ไปแล้ว")
print("ก่อน Demo โปรแกรม ให้รัน python create_db.py เพื่อรีเซ็ตข้อมูล")
