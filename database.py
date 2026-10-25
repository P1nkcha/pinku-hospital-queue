import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clinic.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def database_ready():
    if not os.path.exists(DB_PATH):
        return False
    rows = fetch_all("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", ('appointments',))
    return len(rows) == 1


def fetch_all(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    if len(rows) == 0:
        return None
    return rows[0]


def execute(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        count = cursor.rowcount
    finally:
        conn.close()
    return count


def insert(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        new_id = cursor.lastrowid
    finally:
        conn.close()
    return new_id


def execute_transaction(commands):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for sql, params in commands:
            cursor.execute(sql, params)
            if cursor.rowcount == 0:
                conn.rollback()
                return False
        conn.commit()
        return True
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_today_summary():
    sql = '''SELECT date('now', 'localtime'),
            COUNT(*),
            IFNULL(SUM(CASE WHEN a.status = 'ตรวจแล้ว' THEN 1 ELSE 0 END), 0),
            IFNULL(SUM(CASE WHEN a.status = 'จองแล้ว' THEN 1 ELSE 0 END), 0),
            IFNULL(SUM(CASE WHEN a.status = 'ยกเลิก' THEN 1 ELSE 0 END), 0)
        FROM appointments a
        JOIN schedules s ON a.schedule_id = s.schedule_id
        WHERE s.work_date = date('now', 'localtime')'''
    return fetch_one(sql)


def error_to_thai(error):
    text = str(error)
    print("[ข้อมูลสำหรับผู้พัฒนา] SQLite error:", text)
    if 'UNIQUE constraint failed: patients.phone' in text:
        return 'เบอร์โทรนี้มีผู้ป่วยลงทะเบียนไว้แล้ว กรุณาตรวจสอบเบอร์อีกครั้ง'
    if 'UNIQUE constraint failed: appointments.schedule_id' in text:
        return 'ช่องเวลานี้มีผู้ป่วยจองไปแล้ว กรุณาเลือกช่องเวลาอื่น'
    if 'UNIQUE constraint failed: treatments.appt_id' in text:
        return 'คิวนี้มีการบันทึกผลการรักษาไว้แล้ว ไม่สามารถบันทึกซ้ำได้'
    if 'UNIQUE constraint failed' in text:
        return 'ข้อมูลนี้มีอยู่ในระบบแล้ว ไม่สามารถบันทึกซ้ำได้'
    if 'FOREIGN KEY constraint failed' in text:
        return 'ทำรายการไม่ได้ เพราะข้อมูลนี้ยังเชื่อมโยงกับข้อมูลอื่นอยู่ หรือข้อมูลที่อ้างถึงถูกลบไปแล้ว กรุณาโหลดข้อมูลใหม่แล้วลองอีกครั้ง'
    if 'CHECK constraint failed' in text and 'phone' in text:
        return 'เบอร์โทรต้องเป็นตัวเลข 10 หลัก และขึ้นต้นด้วย 0'
    if 'CHECK constraint failed' in text and 'birth_date' in text:
        return 'วันเกิดไม่ถูกต้อง กรุณากรอกแบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น 1990-05-01'
    if 'CHECK constraint failed' in text:
        return 'ข้อมูลบางช่องไม่อยู่ในรูปแบบที่ระบบรับได้ กรุณาตรวจสอบอีกครั้ง'
    if 'NOT NULL constraint failed' in text:
        return 'กรุณากรอกข้อมูลให้ครบทุกช่องที่จำเป็น'
    if 'locked' in text:
        return 'ฐานข้อมูลกำลังถูกใช้งานโดยโปรแกรมอื่น เช่น DB Browser ที่ยังไม่ได้กด Write Changes กรุณาบันทึกหรือปิดโปรแกรมนั้นก่อน แล้วลองใหม่'
    if 'no such table' in text:
        return 'ไม่พบตารางในฐานข้อมูล กรุณารัน python create_db.py ก่อน'
    return 'เกิดข้อผิดพลาดกับฐานข้อมูล บันทึกไม่สำเร็จ กรุณาลองใหม่อีกครั้ง'
