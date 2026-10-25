# database.py : ส่วนเชื่อมต่อฐานข้อมูล clinic.db ที่ทุกแท็บเรียกใช้
# ทุกคำสั่ง SQL ส่งค่าผ่าน ? (parameterized query) ไม่เอาข้อความมาต่อกันเป็นคำสั่ง

import sqlite3  # โมดูล SQLite ที่มากับ Python ไม่ต้องติดตั้งเพิ่ม
import os  # ใช้หาตำแหน่งไฟล์บนเครื่อง

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # โฟลเดอร์ที่ไฟล์นี้อยู่
DB_PATH = os.path.join(BASE_DIR, 'clinic.db')  # clinic.db อยู่โฟลเดอร์เดียวกับโปรแกรมเสมอ


def get_connection():  # เปิดการเชื่อมต่อใหม่ทุกครั้งที่จะใช้ฐานข้อมูล
    conn = sqlite3.connect(DB_PATH)  # เชื่อมต่อไฟล์ clinic.db
    conn.execute("PRAGMA foreign_keys = ON")  # เปิดตรวจ foreign key ทุกครั้งที่เชื่อมต่อ (SQLite ปิดไว้เป็นค่าเริ่มต้น)
    return conn  # ส่งการเชื่อมต่อกลับไปให้ฟังก์ชันที่เรียก


def database_ready():  # ตรวจว่ามีไฟล์ clinic.db และสร้างตารางแล้วหรือยัง
    if not os.path.exists(DB_PATH):  # ถ้ายังไม่มีไฟล์ (ต้องตรวจก่อน connect เพราะ connect จะสร้างไฟล์เปล่าให้เอง)
        return False  # แปลว่ายังไม่ได้รัน create_db.py
    rows = fetch_all("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", ('appointments',))  # หาตาราง appointments ในฐานข้อมูล
    return len(rows) == 1  # เจอตาราง = พร้อมใช้งาน


def fetch_all(sql, params=()):  # ใช้กับ SELECT ที่ได้ผลหลายแถว
    conn = get_connection()  # เปิดการเชื่อมต่อ (เปิด foreign key ให้แล้ว)
    cursor = conn.cursor()  # สร้าง cursor สำหรับรันคำสั่ง
    cursor.execute(sql, params)  # รัน SQL โดยส่งค่าที่แทน ? แยกไปต่างหาก
    rows = cursor.fetchall()  # ดึงผลทุกแถวออกมาเป็น list ของ tuple
    conn.close()  # ปิดการเชื่อมต่อ
    return rows  # ส่งผลกลับ


def fetch_one(sql, params=()):  # ใช้กับ SELECT ที่ต้องการแค่แถวเดียว
    rows = fetch_all(sql, params)  # รันด้วย fetch_all
    if len(rows) == 0:  # ถ้าไม่มีผลเลย
        return None  # ส่ง None กลับไป
    return rows[0]  # ส่งแถวแรกกลับไป


def execute(sql, params=()):  # ใช้กับ UPDATE และ DELETE  คืนค่าจำนวนแถวที่ถูกแก้
    conn = get_connection()  # เปิดการเชื่อมต่อ
    cursor = conn.cursor()  # สร้าง cursor
    try:  # ลองรันคำสั่ง
        cursor.execute(sql, params)  # รัน SQL พร้อมค่าที่แทน ?
        conn.commit()  # บันทึกการเปลี่ยนแปลงลงไฟล์
        count = cursor.rowcount  # จำนวนแถวที่ถูกแก้
    finally:  # ไม่ว่าจะสำเร็จหรือเกิด error
        conn.close()  # ปิดการเชื่อมต่อเสมอ ไม่ให้ไฟล์ค้างล็อก (ถ้าเกิด error จะส่ง error ต่อให้ฟังก์ชันที่เรียกจัดการ)
    return count  # ส่งจำนวนแถวกลับ


def insert(sql, params=()):  # ใช้กับ INSERT  คืนค่ารหัสของแถวที่เพิ่งเพิ่ม
    conn = get_connection()  # เปิดการเชื่อมต่อ
    cursor = conn.cursor()  # สร้าง cursor
    try:  # ลองรันคำสั่ง
        cursor.execute(sql, params)  # รัน INSERT พร้อมค่าที่แทน ?
        conn.commit()  # บันทึกลงไฟล์
        new_id = cursor.lastrowid  # รหัส (AUTOINCREMENT) ของแถวที่เพิ่งเพิ่ม
    finally:  # ไม่ว่าจะสำเร็จหรือเกิด error
        conn.close()  # ปิดการเชื่อมต่อเสมอ
    return new_id  # ส่งรหัสใหม่กลับ


def execute_transaction(commands):  # รันหลายคำสั่งเป็นชุดเดียว (transaction) สำเร็จทั้งหมด หรือไม่เปลี่ยนอะไรเลย
    conn = get_connection()  # เปิดการเชื่อมต่อ (ทุกคำสั่งในชุดใช้การเชื่อมต่อเดียวกัน)
    cursor = conn.cursor()  # สร้าง cursor
    try:  # ลองรันทีละคำสั่ง
        for sql, params in commands:  # commands คือ list ของ (คำสั่ง SQL, ค่าที่แทน ?)
            cursor.execute(sql, params)  # รันคำสั่ง (ยังไม่บันทึกลงไฟล์จนกว่าจะ commit)
            if cursor.rowcount == 0:  # คำสั่งนี้ไม่ได้เปลี่ยนแถวไหนเลย เช่น สถานะคิวถูกเปลี่ยนไปก่อนแล้ว
                conn.rollback()  # ย้อนคำสั่งก่อนหน้าในชุดนี้ทั้งหมด
                return False  # บอกว่าไม่ได้บันทึก
        conn.commit()  # ทุกคำสั่งผ่าน บันทึกลงไฟล์พร้อมกันทีเดียว
        return True  # บอกว่าบันทึกสำเร็จ
    except sqlite3.Error:  # มีคำสั่งใดคำสั่งหนึ่งพลาด
        conn.rollback()  # ย้อนกลับทั้งชุด ข้อมูลจะเหมือนก่อนเริ่ม
        raise  # ส่ง error ต่อให้ฟังก์ชันที่เรียกแปลงเป็นข้อความภาษาไทย
    finally:  # ไม่ว่าจะสำเร็จหรือเกิด error
        conn.close()  # ปิดการเชื่อมต่อเสมอ


def get_today_summary():  # สรุปคิวของวันนี้ด้วย SQL คำสั่งเดียว ใช้แสดงที่แถบหัวโปรแกรม
    sql = '''SELECT date('now', 'localtime'),                                    -- วันนี้ แบบ YYYY-MM-DD
            COUNT(*),                                                             -- คิวทั้งหมดของวันนี้
            IFNULL(SUM(CASE WHEN a.status = 'ตรวจแล้ว' THEN 1 ELSE 0 END), 0),    -- นับเฉพาะตรวจแล้ว
            IFNULL(SUM(CASE WHEN a.status = 'จองแล้ว' THEN 1 ELSE 0 END), 0),     -- นับเฉพาะรอตรวจ (จองแล้ว)
            IFNULL(SUM(CASE WHEN a.status = 'ยกเลิก' THEN 1 ELSE 0 END), 0)       -- นับเฉพาะยกเลิก
        FROM appointments a                                                       -- จากตารางการจองคิว
        JOIN schedules s ON a.schedule_id = s.schedule_id                         -- ต่อเพื่อดูวันที่ของคิว
        WHERE s.work_date = date('now', 'localtime')'''  # เฉพาะคิวของวันนี้ (วันนี้ไม่มีคิว SUM จะได้ NULL จึงใช้ IFNULL ให้เป็น 0)
    return fetch_one(sql)  # ได้ 1 แถว: (วันนี้, ทั้งหมด, ตรวจแล้ว, รอตรวจ, ยกเลิก)


def error_to_thai(error):  # แปลง error ของ SQLite เป็นข้อความภาษาไทยที่คนทั่วไปเข้าใจ
    text = str(error)  # ข้อความ error ภาษาอังกฤษจาก SQLite
    print("[ข้อมูลสำหรับผู้พัฒนา] SQLite error:", text)  # พิมพ์ไว้ใน Terminal เท่านั้น ไม่แสดงบนหน้าจอโปรแกรม
    if 'UNIQUE constraint failed: patients.phone' in text:  # เบอร์โทรซ้ำกับผู้ป่วยคนอื่น
        return 'เบอร์โทรนี้มีผู้ป่วยลงทะเบียนไว้แล้ว กรุณาตรวจสอบเบอร์อีกครั้ง'  # ข้อความที่จะแสดงให้ผู้ใช้เห็น
    if 'UNIQUE constraint failed: appointments.schedule_id' in text:  # ช่องเวลามีคิวที่ยังไม่ยกเลิกอยู่แล้ว
        return 'ช่องเวลานี้มีผู้ป่วยจองไปแล้ว กรุณาเลือกช่องเวลาอื่น'  # แจ้งให้เลือกช่องใหม่
    if 'UNIQUE constraint failed: treatments.appt_id' in text:  # คิวนี้มีผลการรักษาบันทึกไว้แล้ว
        return 'คิวนี้มีการบันทึกผลการรักษาไว้แล้ว ไม่สามารถบันทึกซ้ำได้'  # 1 คิวมีผลการรักษาได้ 1 ครั้ง
    if 'UNIQUE constraint failed' in text:  # ข้อมูลซ้ำแบบอื่น
        return 'ข้อมูลนี้มีอยู่ในระบบแล้ว ไม่สามารถบันทึกซ้ำได้'  # ข้อความทั่วไปเรื่องข้อมูลซ้ำ
    if 'FOREIGN KEY constraint failed' in text:  # ข้อมูลที่เชื่อมโยงกันไม่ครบ
        return 'ทำรายการไม่ได้ เพราะข้อมูลนี้ยังเชื่อมโยงกับข้อมูลอื่นอยู่ หรือข้อมูลที่อ้างถึงถูกลบไปแล้ว กรุณาโหลดข้อมูลใหม่แล้วลองอีกครั้ง'  # อธิบาย foreign key แบบภาษาคน
    if 'CHECK constraint failed' in text and 'phone' in text:  # เบอร์โทรผิดรูปแบบ
        return 'เบอร์โทรต้องเป็นตัวเลข 10 หลัก และขึ้นต้นด้วย 0'  # บอกรูปแบบที่ถูก
    if 'CHECK constraint failed' in text and 'birth_date' in text:  # วันเกิดผิดรูปแบบ
        return 'วันเกิดไม่ถูกต้อง กรุณากรอกแบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น 1990-05-01'  # บอกรูปแบบที่ถูก
    if 'CHECK constraint failed' in text:  # ข้อมูลผิดรูปแบบอื่นๆ
        return 'ข้อมูลบางช่องไม่อยู่ในรูปแบบที่ระบบรับได้ กรุณาตรวจสอบอีกครั้ง'  # ข้อความทั่วไป
    if 'NOT NULL constraint failed' in text:  # มีช่องที่จำเป็นว่างอยู่
        return 'กรุณากรอกข้อมูลให้ครบทุกช่องที่จำเป็น'  # ให้กรอกให้ครบ
    if 'locked' in text:  # ไฟล์ถูกโปรแกรมอื่นล็อกไว้
        return 'ฐานข้อมูลกำลังถูกใช้งานโดยโปรแกรมอื่น เช่น DB Browser ที่ยังไม่ได้กด Write Changes กรุณาบันทึกหรือปิดโปรแกรมนั้นก่อน แล้วลองใหม่'  # บอกวิธีแก้
    if 'no such table' in text:  # ยังไม่ได้สร้างตาราง
        return 'ไม่พบตารางในฐานข้อมูล กรุณารัน python create_db.py ก่อน'  # บอกวิธีแก้
    return 'เกิดข้อผิดพลาดกับฐานข้อมูล บันทึกไม่สำเร็จ กรุณาลองใหม่อีกครั้ง'  # error อื่นที่ไม่ได้คาดไว้
