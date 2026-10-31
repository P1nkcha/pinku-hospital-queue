# app.py : หน้าเว็บแสดงคิวรายวัน (อ่านอย่างเดียว) ให้คนที่ต่อ Wi-Fi หรือ LAN เดียวกันเปิดดูได้
# วิธีรัน: python app.py แล้วเปิด http://127.0.0.1:5000 (เครื่องอื่นใช้ที่อยู่ IP ที่ขึ้นใน Terminal ลงท้ายด้วย :5000)

from datetime import date, datetime
from flask import Flask, render_template
import database
import theme

app = Flask(__name__)

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']
STATUS_CLASS = {'จองแล้ว': 'booked', 'ตรวจแล้ว': 'done', 'ยกเลิก': 'cancelled'}


def day_label(work_date):
    return work_date + ' วัน' + THAI_DAYS[datetime.strptime(work_date, '%Y-%m-%d').weekday()]


@app.route("/")
def home():
    if not database.database_ready():
        return 'ยังไม่มีฐานข้อมูล clinic.db กรุณารัน python create_db.py ก่อน'
    today = date.today().isoformat()

    summary_sql = '''SELECT s.work_date, a.status, COUNT(*)
        FROM appointments a
        JOIN schedules s ON a.schedule_id = s.schedule_id
        GROUP BY s.work_date, a.status
        ORDER BY CASE WHEN s.work_date >= ? THEN 0 ELSE 1 END,
                 CASE WHEN s.work_date >= ? THEN s.work_date END,
                 s.work_date DESC'''
    days = []
    day_index = {}
    for work_date, status, count in database.fetch_all(summary_sql, (today, today)):
        if work_date not in day_index:
            day_index[work_date] = len(days)
            days.append({'date': work_date, 'label': day_label(work_date), 'is_today': work_date == today,
                         'counts': {'ตรวจแล้ว': 0, 'จองแล้ว': 0, 'ยกเลิก': 0}, 'queues': []})
        days[day_index[work_date]]['counts'][status] = count
    for day in days:
        day['total'] = day['counts']['ตรวจแล้ว'] + day['counts']['จองแล้ว'] + day['counts']['ยกเลิก']

    queue_sql = '''SELECT a.appt_id, s.work_date, s.slot_time, p.patient_name,
            d.doctor_name, dp.dept_name, a.status
        FROM appointments a
        JOIN patients p     ON a.patient_id  = p.patient_id
        JOIN schedules s    ON a.schedule_id = s.schedule_id
        JOIN doctors d      ON s.doctor_id   = d.doctor_id
        JOIN departments dp ON d.dept_id     = dp.dept_id
        ORDER BY s.work_date, s.slot_time, d.doctor_id'''
    for row in database.fetch_all(queue_sql):
        days[day_index[row[1]]]['queues'].append({'appt_id': row[0], 'slot_time': row[2], 'patient': row[3],
                                                   'doctor': row[4], 'dept': row[5], 'status': row[6],
                                                   'css': STATUS_CLASS[row[6]]})

    colors = {'primary': theme.PRIMARY, 'primary_dark': theme.PRIMARY_DARK, 'secondary': theme.SECONDARY,
              'text': theme.TEXT, 'hint': theme.HINT, 'white': theme.WHITE,
              'booked_bg': theme.BOOKED_BG, 'booked_text': theme.BOOKED_TEXT,
              'done_bg': theme.DONE_BG, 'done_text': theme.DONE_TEXT,
              'cancelled_bg': theme.CANCELLED_BG, 'cancelled_text': theme.CANCELLED_TEXT}
    return render_template('index.html', app_name=theme.APP_NAME, days=days, colors=colors,
                           updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
