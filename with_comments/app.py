# app.py : หน้าเว็บแสดงคิวรายวัน (อ่านอย่างเดียว) ให้คนที่ต่อ Wi-Fi หรือ LAN เดียวกันเปิดดูได้
# วิธีรัน: python app.py แล้วเปิด http://127.0.0.1:5000 (เครื่องอื่นใช้ที่อยู่ IP ที่ขึ้นใน Terminal ลงท้ายด้วย :5000)

from datetime import date, datetime  # date = วันนี้ ใช้แยกวันนี้/วันข้างหน้า/วันที่ผ่านมา  datetime = แปลงวันที่เป็นชื่อวันและเวลาที่อัปเดต
from flask import Flask, render_template  # Flask = ตัวเว็บเซิร์ฟเวอร์  render_template = เติมข้อมูลลงไฟล์ templates/index.html
import database  # ใช้ฟังก์ชันเชื่อมต่อ clinic.db ชุดเดียวกับโปรแกรม (เปิด foreign key และปิดการเชื่อมต่อให้ทุกครั้ง)
import theme  # ใช้ชื่อโปรแกรมและค่าสีชุดเดียวกับโปรแกรม สีในหน้าเว็บจึงตรงกับในโปรแกรม

app = Flask(__name__)  # สร้างเว็บแอป Flask (ไฟล์หน้าเว็บอยู่ในโฟลเดอร์ templates ข้างไฟล์นี้)

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']  # ชื่อวันภาษาไทย เรียงตาม weekday() (0 = จันทร์)
STATUS_CLASS = {'จองแล้ว': 'booked', 'ตรวจแล้ว': 'done', 'ยกเลิก': 'cancelled'}  # สถานะคิว -> ชื่อ class ใน CSS ที่กำหนดสีพื้นและสีตัวหนังสือของแถว


def day_label(work_date):  # แปลง '2026-11-06' เป็น '2026-11-06 วันศุกร์' ใช้เป็นหัวตารางของแต่ละวัน
    return work_date + ' วัน' + THAI_DAYS[datetime.strptime(work_date, '%Y-%m-%d').weekday()]  # weekday() ได้ 0-6 ใช้เป็นตำแหน่งในรายการชื่อวัน


@app.route("/")  # หน้าแรกของเว็บ (URL เดิม http://<IP>:5000/)
def home():  # ทำงานทุกครั้งที่มีคนเปิดหรือรีเฟรชหน้าเว็บ ข้อมูลจึงล่าสุดเสมอ
    if not database.database_ready():  # ยังไม่มีไฟล์ clinic.db หรือยังไม่มีตาราง
        return 'ยังไม่มีฐานข้อมูล clinic.db กรุณารัน python create_db.py ก่อน'  # แจ้งแทนการแสดงหน้าว่างหรือ error
    today = date.today().isoformat()  # วันนี้แบบ YYYY-MM-DD ใช้แทน ? ในคำสั่ง SQL

    summary_sql = '''SELECT s.work_date, a.status, COUNT(*)                          -- วันที่ สถานะ และจำนวนคิวของวันและสถานะนั้น
        FROM appointments a                                                          -- เริ่มจากตารางคิว
        JOIN schedules s ON a.schedule_id = s.schedule_id                            -- ต่อเพื่อดูวันที่ของคิว
        GROUP BY s.work_date, a.status                                               -- รวมกลุ่มตามวันและสถานะ แล้ว COUNT(*) นับในแต่ละกลุ่ม
        ORDER BY CASE WHEN s.work_date >= ? THEN 0 ELSE 1 END,                       -- กลุ่ม 0 = วันนี้และวันข้างหน้า ขึ้นก่อน  กลุ่ม 1 = วันที่ผ่านมาแล้ว
                 CASE WHEN s.work_date >= ? THEN s.work_date END,                    -- ในกลุ่ม 0 เรียงวันใกล้ไปไกล (กลุ่ม 1 ได้ NULL เท่ากันหมด)
                 s.work_date DESC'''  # กลุ่ม 1 เรียงวันใหม่ไปเก่า (ให้ SQL นับและเรียงวัน ไม่ได้นับใน Python)
    days = []  # รายการวันตามลำดับที่จะแสดง (แต่ละวันเป็น dict)
    day_index = {}  # วันที่ -> ตำแหน่งในรายการ days ใช้หาวันเดิมเร็วๆ
    for work_date, status, count in database.fetch_all(summary_sql, (today, today)):  # ทุกแถวที่ SQL นับมาแล้ว (ส่งวันนี้แทน ? ทั้ง 2 ตัว)
        if work_date not in day_index:  # เจอวันนี้ครั้งแรก
            day_index[work_date] = len(days)  # จำตำแหน่งของวันนี้
            days.append({'date': work_date, 'label': day_label(work_date), 'is_today': work_date == today,  # วันที่ หัวตาราง และบอกว่าเป็นวันนี้ไหม (ใช้แสดงป้าย "วันนี้")
                         'counts': {'ตรวจแล้ว': 0, 'จองแล้ว': 0, 'ยกเลิก': 0}, 'queues': []})  # ตัวเลขสรุปเริ่มที่ 0 (สถานะที่ไม่มีคิว SQL จะไม่ส่งแถวมา) และรายการคิวของวันนั้น
        days[day_index[work_date]]['counts'][status] = count  # ใส่ตัวเลขที่ SQL นับมาให้สถานะนั้น (Python ไม่ได้นับเอง)
    for day in days:  # ทุกวันที่มีคิว
        day['total'] = day['counts']['ตรวจแล้ว'] + day['counts']['จองแล้ว'] + day['counts']['ยกเลิก']  # คิวทั้งหมด = ตรวจแล้ว + รอตรวจ + ยกเลิก (เหมือนแถบหัวในโปรแกรม)

    queue_sql = '''SELECT a.appt_id, s.work_date, s.slot_time, p.patient_name,       -- เลขคิว วันที่ เวลา ชื่อผู้ป่วย
            d.doctor_name, dp.dept_name, a.status                                    -- แพทย์ แผนก สถานะ
        FROM appointments a                                                          -- ทุกคิว รวมคิวที่ยกเลิก (แสดงเป็นแถวสีเทา)
        JOIN patients p     ON a.patient_id  = p.patient_id                          -- ต่อเพื่อดูชื่อผู้ป่วย
        JOIN schedules s    ON a.schedule_id = s.schedule_id                         -- ต่อเพื่อดูวันและเวลา
        JOIN doctors d      ON s.doctor_id   = d.doctor_id                           -- ต่อเพื่อดูชื่อแพทย์
        JOIN departments dp ON d.dept_id     = dp.dept_id                            -- ต่อเพื่อดูชื่อแผนก
        ORDER BY s.work_date, s.slot_time, d.doctor_id'''  # ทุกคิว (รวมคิวที่ยกเลิก) พร้อมชื่อผู้ป่วย แพทย์ แผนก เรียงตามวันและเวลา (ไม่มีค่าจากผู้ใช้ จึงไม่ต้องมี ?)
    for row in database.fetch_all(queue_sql):  # ทุกคิว
        days[day_index[row[1]]]['queues'].append({'appt_id': row[0], 'slot_time': row[2], 'patient': row[3],  # ใส่คิวลงตารางของวันนั้น (เรียงเวลาอยู่แล้วจาก ORDER BY)
                                                   'doctor': row[4], 'dept': row[5], 'status': row[6],  # แพทย์ แผนก สถานะ
                                                   'css': STATUS_CLASS[row[6]]})  # class ของแถว กำหนดสีตามสถานะ

    colors = {'primary': theme.PRIMARY, 'primary_dark': theme.PRIMARY_DARK, 'secondary': theme.SECONDARY,  # สีหลัก (ชมพู) สีเข้ม และสีรองจาก theme.py
              'text': theme.TEXT, 'hint': theme.HINT, 'white': theme.WHITE,  # สีตัวหนังสือ คำแนะนำ และสีขาว
              'booked_bg': theme.BOOKED_BG, 'booked_text': theme.BOOKED_TEXT,  # สีแถวจองแล้ว (ค่าเดียวกับในโปรแกรม)
              'done_bg': theme.DONE_BG, 'done_text': theme.DONE_TEXT,  # สีแถวตรวจแล้ว
              'cancelled_bg': theme.CANCELLED_BG, 'cancelled_text': theme.CANCELLED_TEXT}  # สีแถวยกเลิก
    return render_template('index.html', app_name=theme.APP_NAME, days=days, colors=colors,  # เติมข้อมูลลง templates/index.html แล้วส่งกลับเป็นหน้าเว็บ (Jinja แปลงอักขระพิเศษให้เอง กันการแทรกโค้ดผ่านชื่อผู้ป่วย)
                           updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # เวลาที่ดึงข้อมูล แสดงมุมขวาบน


if __name__ == "__main__":  # รันไฟล์นี้โดยตรง (python app.py)
    app.run(debug=False, host="0.0.0.0", port=5000)  # debug=False ปลอดภัยกว่า (ไม่เปิดหน้าดีบักที่สั่งรันโค้ดได้)  host 0.0.0.0 = เครื่องอื่นในวง Wi-Fi เดียวกันเข้าได้  พอร์ต 5000
