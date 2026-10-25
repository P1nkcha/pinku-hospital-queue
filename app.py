
from flask import Flask
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clinic.db")


@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    sql = """
        SELECT
            a.appt_id,
            s.work_date,
            s.slot_time,
            p.patient_name,
            d.doctor_name,
            dp.dept_name,
            a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN schedules s ON a.schedule_id = s.schedule_id
        JOIN doctors d ON s.doctor_id = d.doctor_id
        JOIN departments dp ON d.dept_id = dp.dept_id
        WHERE a.status <> 'ยกเลิก'
        ORDER BY s.work_date, s.slot_time
    """

    try:
        queues = conn.execute(sql).fetchall()
    finally:
        conn.close()

    html = """
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="10">
        <title>ระบบจองคิวคลินิก</title>
    </head>
    <body>
        <h1>ระบบจองคิวคลินิก</h1>
        <p>หน้านี้รีเฟรชข้อมูลทุก 10 วินาที</p>
        <table border="1" cellpadding="8">
            <tr>
                <th>เลขคิว</th>
                <th>วันที่</th>
                <th>เวลา</th>
                <th>ผู้ป่วย</th>
                <th>แพทย์</th>
                <th>แผนก</th>
                <th>สถานะ</th>
            </tr>
    """

    for q in queues:
        html += "<tr>"
        for key in [
            "appt_id", "work_date", "slot_time",
            "patient_name", "doctor_name", "dept_name", "status"
        ]:
            html += "<td>" + str(q[key]) + "</td>"
        html += "</tr>"

    html += "</table></body></html>"
    return html


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
