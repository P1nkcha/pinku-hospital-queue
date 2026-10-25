# booking_tab.py : แท็บ "จองคิว" (ลำดับที่ 3)
# ค้นผู้ป่วยด้วยเบอร์โทร -> เลือกแผนก -> แพทย์ -> วันที่ -> ช่องเวลาที่ยังว่าง -> บันทึก

import tkinter as tk  # ไลบรารีสร้างหน้าจอ
from tkinter import ttk  # widget แบบ ttk
import sqlite3  # ใช้จับ error ที่มาจากฐานข้อมูล
from datetime import date, datetime, timedelta  # ใช้หาวันนี้ ชื่อวัน และเวลาสิ้นสุดของช่อง
import database  # ฟังก์ชันเชื่อมต่อฐานข้อมูลจาก database.py
import header_bar  # แถบหัวโปรแกรม (อัปเดตตัวเลขสรุปวันนี้หลังจอง)
import dialogs  # หน้าต่างแจ้งเตือนแบบเข้าธีม
import theme  # สีและฟอนต์ของโปรแกรม

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']  # ชื่อวันภาษาไทย เรียงตาม weekday() ที่เริ่มจากวันจันทร์ = 0

ui = {}  # เก็บ widget ตัวแปร และรายการที่โหลดมา ไว้ใช้ข้ามฟังก์ชัน


def create_tab(parent):  # สร้างหน้าตาแท็บ แล้วส่ง frame กลับไปให้ main.py
    frame = ttk.Frame(parent, padding=15)  # กรอบหลักของแท็บ

    ui['departments'] = []  # รายการแผนก [(dept_id, dept_name), ...]
    ui['doctors'] = []  # รายการแพทย์ของแผนกที่เลือก [(doctor_id, doctor_name), ...]
    ui['dates'] = []  # วันที่ที่ยังมีช่องว่าง ['2026-10-22', ...]
    ui['slots'] = []  # ช่องเวลาที่ยังว่าง [(schedule_id, '09:00'), ...]

    step1 = ttk.LabelFrame(frame, text='1. ค้นหาผู้ป่วยด้วยเบอร์โทร', padding=12)  # กรอบขั้นที่ 1
    step1.pack(fill='x')  # กว้างเต็มแท็บ
    ttk.Label(step1, text='เบอร์โทร').pack(side='left')  # ป้ายช่องเบอร์โทร
    ui['phone_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องเบอร์โทร
    phone_entry = ttk.Entry(step1, textvariable=ui['phone_var'], width=18)  # ช่องกรอกเบอร์โทร
    phone_entry.pack(side='left', padx=8)  # วางต่อจากป้าย
    phone_entry.bind('<Return>', on_phone_enter)  # กด Enter = ค้นหา
    ttk.Button(step1, text='ค้นหาผู้ป่วย', command=find_patient).pack(side='left')  # ปุ่มค้นหา
    ui['patient_text'] = tk.StringVar(value='ยังไม่ได้เลือกผู้ป่วย')  # ข้อความแสดงผลการค้นหา
    ui['patient_label'] = ttk.Label(step1, textvariable=ui['patient_text'], foreground=theme.HINT)  # ป้ายแสดงชื่อผู้ป่วยที่พบ
    ui['patient_label'].pack(side='left', padx=15)  # วางต่อจากปุ่ม

    step2 = ttk.LabelFrame(frame, text='2. เลือกแผนก แพทย์ วันที่ และช่องเวลาที่ยังว่าง', padding=12)  # กรอบขั้นที่ 2
    step2.pack(fill='x', pady=12)  # เว้นระยะบนล่าง
    ui['dept_box'] = ttk.Combobox(step2, state='readonly', width=30)  # รายการแผนก (readonly = เลือกได้อย่างเดียว พิมพ์เองไม่ได้)
    ui['doctor_box'] = ttk.Combobox(step2, state='readonly', width=30)  # รายการแพทย์
    ui['date_box'] = ttk.Combobox(step2, state='readonly', width=30)  # รายการวันที่ที่มีช่องว่าง
    ui['time_box'] = ttk.Combobox(step2, state='readonly', width=30)  # รายการช่องเวลาที่ว่าง
    ttk.Label(step2, text='แผนก').grid(row=0, column=0, sticky='w', pady=5)  # ป้ายแผนก
    ui['dept_box'].grid(row=0, column=1, sticky='w', padx=10, pady=5)  # วางรายการแผนก
    ttk.Label(step2, text='แพทย์').grid(row=1, column=0, sticky='w', pady=5)  # ป้ายแพทย์
    ui['doctor_box'].grid(row=1, column=1, sticky='w', padx=10, pady=5)  # วางรายการแพทย์
    ttk.Label(step2, text='วันที่').grid(row=2, column=0, sticky='w', pady=5)  # ป้ายวันที่
    ui['date_box'].grid(row=2, column=1, sticky='w', padx=10, pady=5)  # วางรายการวันที่
    ttk.Label(step2, text='ช่องเวลา').grid(row=3, column=0, sticky='w', pady=5)  # ป้ายช่องเวลา
    ui['time_box'].grid(row=3, column=1, sticky='w', padx=10, pady=5)  # วางรายการช่องเวลา
    ui['hint_text'] = tk.StringVar(value='เลือกแผนกก่อน แล้วรายการถัดไปจะแสดงตามที่เลือก')  # ข้อความแนะนำทางขวา
    ttk.Label(step2, textvariable=ui['hint_text'], foreground=theme.PRIMARY_DARK, wraplength=420).grid(row=0, column=2, rowspan=4, sticky='nw', padx=20)  # แสดงคำแนะนำ
    ui['dept_box'].bind('<<ComboboxSelected>>', on_dept_selected)  # เลือกแผนกแล้ว -> โหลดแพทย์
    ui['doctor_box'].bind('<<ComboboxSelected>>', on_doctor_selected)  # เลือกแพทย์แล้ว -> โหลดวันที่ว่าง
    ui['date_box'].bind('<<ComboboxSelected>>', on_date_selected)  # เลือกวันที่แล้ว -> โหลดช่องเวลาว่าง

    step3 = ttk.LabelFrame(frame, text='3. อาการเบื้องต้น (ไม่บังคับกรอก)', padding=12)  # กรอบขั้นที่ 3
    step3.pack(fill='x')  # กว้างเต็มแท็บ
    ui['symptom_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องอาการ
    ttk.Entry(step3, textvariable=ui['symptom_var'], width=70).pack(side='left')  # ช่องกรอกอาการ

    buttons = ttk.Frame(frame)  # แถวปุ่มด้านล่าง
    buttons.pack(fill='x', pady=15)  # เว้นระยะด้านบน
    ttk.Button(buttons, text='บันทึกการจอง', command=save_booking).pack(side='left', ipadx=10, ipady=4)  # ปุ่มบันทึก
    ttk.Button(buttons, text='ล้างฟอร์ม', style='Light.TButton', command=clear_form).pack(side='left', padx=10, ipady=4)  # ปุ่มเริ่มใหม่ (ปุ่มรอง)

    load_departments()  # โหลดรายชื่อแผนกใส่ Combobox
    return frame  # ส่ง frame กลับไปให้ main.py ใส่ลงแท็บ


def clean_phone(text):  # จัดรูปแบบเบอร์โทรที่ผู้ใช้พิมพ์
    return text.replace('-', '').replace(' ', '')  # ตัดขีดและช่องว่างออก (081-234-5678 -> 0812345678)


def thai_date_label(work_date):  # ทำข้อความวันที่สำหรับแสดงใน Combobox เช่น 2026-10-22 (วันพฤหัสบดี, วันนี้)
    day_name = THAI_DAYS[datetime.strptime(work_date, '%Y-%m-%d').weekday()]  # หาชื่อวันจากวันที่
    label = work_date + ' (วัน' + day_name  # ต่อข้อความ "วันที่ (วัน...."
    if work_date == date.today().isoformat():  # ถ้าเป็นวันนี้
        label = label + ', วันนี้'  # บอกเพิ่มว่าเป็นวันนี้
    return label + ')'  # ปิดวงเล็บ


def slot_label(slot_time):  # ทำข้อความช่องเวลา เช่น 09:00 - 09:30
    start = datetime.strptime(slot_time, '%H:%M')  # แปลงเวลาเริ่มเป็นข้อมูลเวลา
    end = start + timedelta(minutes=30)  # ช่องละ 30 นาที
    return slot_time + ' - ' + end.strftime('%H:%M')  # ต่อเป็นข้อความช่วงเวลา


def load_departments():  # โหลดรายชื่อแผนกจากฐานข้อมูล
    rows = database.fetch_all('SELECT dept_id, dept_name FROM departments ORDER BY dept_id')  # แผนกทั้งหมด
    ui['departments'] = rows  # เก็บไว้เพื่อหา dept_id จากลำดับที่เลือก
    ui['dept_box']['values'] = [row[1] for row in rows]  # แสดงเฉพาะชื่อแผนก


def load_doctors(dept_id):  # โหลดแพทย์ของแผนกที่เลือก
    rows = database.fetch_all('SELECT doctor_id, doctor_name FROM doctors WHERE dept_id = ? ORDER BY doctor_id', (dept_id,))  # แพทย์ในแผนกนี้
    ui['doctors'] = rows  # เก็บไว้เพื่อหา doctor_id จากลำดับที่เลือก
    ui['doctor_box']['values'] = [row[1] for row in rows]  # แสดงเฉพาะชื่อแพทย์
    ui['doctor_box'].set('')  # ล้างแพทย์ที่เคยเลือก
    clear_dates()  # ล้างวันที่และช่องเวลา เพราะเปลี่ยนแผนกแล้ว


def load_dates(doctor_id):  # โหลดวันที่ที่แพทย์คนนี้ยังมีช่องว่างที่จองได้ (ตั้งแต่เวลานี้เป็นต้นไป)
    sql = '''SELECT DISTINCT s.work_date                                -- วันที่ไม่ซ้ำกัน
        FROM schedules s                                                -- จากตารางช่องเวลา
        LEFT JOIN appointments a ON a.schedule_id = s.schedule_id       -- จับคู่กับคิวของช่องนั้น (ถ้ามี)
                                AND a.status <> 'ยกเลิก'                 -- นับเฉพาะคิวที่ยังไม่ยกเลิก
        WHERE s.doctor_id = ?                                           -- เฉพาะแพทย์ที่เลือก
          AND (s.work_date > date('now', 'localtime')                   -- พรุ่งนี้เป็นต้นไป: นับทุกช่อง
               OR (s.work_date = date('now', 'localtime')               -- วันนี้: นับเฉพาะช่องที่
                   AND s.slot_time > strftime('%H:%M', 'now', 'localtime')))  -- ยังไม่ถึงเวลาปัจจุบัน
          AND a.appt_id IS NULL                                         -- ไม่มีคิวที่ยังไม่ยกเลิก = ช่องว่าง
        ORDER BY s.work_date'''  # เรียงจากวันใกล้ไปไกล (วันนี้ไม่มีช่องเหลือ = ไม่มีวันนี้ในรายการ)
    rows = database.fetch_all(sql, (doctor_id,))  # ส่ง doctor_id แทน ?
    ui['dates'] = [row[0] for row in rows]  # เก็บวันที่แบบ YYYY-MM-DD ไว้ใช้ตอนบันทึก
    ui['date_box']['values'] = [thai_date_label(d) for d in ui['dates']]  # แสดงวันที่พร้อมชื่อวันภาษาไทย
    clear_dates_selection()  # ล้างวันและเวลาที่เคยเลือก
    if len(ui['dates']) == 0:  # ไม่มีวันว่างเลย
        ui['hint_text'].set('แพทย์ท่านนี้ไม่มีช่องเวลาว่างที่ยังจองได้ กรุณาเลือกแพทย์ท่านอื่น')  # บอกให้เลือกแพทย์อื่น
    else:  # มีวันว่าง
        ui['hint_text'].set('มีวันที่ว่าง ' + str(len(ui['dates'])) + ' วัน เลือกวันที่ แล้วเลือกช่องเวลา')  # บอกจำนวนวันว่าง


def load_slots(doctor_id, work_date):  # โหลดช่องเวลาที่ยังว่างของแพทย์ในวันที่เลือก
    sql = '''SELECT s.schedule_id, s.slot_time                          -- รหัสช่องและเวลาเริ่ม
        FROM schedules s                                                  -- จากตารางช่องเวลา
        LEFT JOIN appointments a ON a.schedule_id = s.schedule_id       -- จับคู่กับคิวของช่องนั้น (ถ้ามี)
                                AND a.status <> 'ยกเลิก'                 -- คิวที่ยกเลิกแล้วไม่นับ ช่องจึงกลับมาว่าง
        WHERE s.doctor_id = ? AND s.work_date = ?                       -- แพทย์และวันที่ที่เลือก
          AND (s.work_date > date('now', 'localtime')                   -- ถ้าเป็นวันพรุ่งนี้เป็นต้นไป แสดงทุกช่อง
               OR (s.work_date = date('now', 'localtime')               -- ถ้าเป็นวันนี้ แสดงเฉพาะช่องที่
                   AND s.slot_time > strftime('%H:%M', 'now', 'localtime')))  -- ยังไม่ถึงเวลาปัจจุบัน
          AND a.appt_id IS NULL                                         -- เฉพาะช่องที่ยังว่าง
        ORDER BY s.slot_time'''  # เรียงตามเวลา
    rows = database.fetch_all(sql, (doctor_id, work_date))  # ส่งค่าแทน ? ตามลำดับ
    ui['slots'] = rows  # เก็บไว้เพื่อหา schedule_id จากลำดับที่เลือก
    ui['time_box']['values'] = [slot_label(row[1]) for row in rows]  # แสดงเป็นช่วงเวลา เช่น 09:00 - 09:30
    ui['time_box'].set('')  # ล้างเวลาที่เคยเลือก
    ui['hint_text'].set('วันที่ ' + work_date + ' มีช่องว่าง ' + str(len(rows)) + ' ช่อง')  # บอกจำนวนช่องว่าง


def clear_dates_selection():  # ล้างวันที่และช่องเวลาที่เลือกไว้
    ui['date_box'].set('')  # ล้างวันที่
    ui['slots'] = []  # ล้างรายการช่องเวลา
    ui['time_box']['values'] = []  # ล้างตัวเลือกช่องเวลา
    ui['time_box'].set('')  # ล้างช่องเวลาที่เลือก


def clear_dates():  # ล้างรายการวันที่ทั้งหมด (ใช้ตอนเปลี่ยนแผนกหรือล้างฟอร์ม)
    ui['dates'] = []  # ล้างรายการวันที่
    ui['date_box']['values'] = []  # ล้างตัวเลือกวันที่
    clear_dates_selection()  # ล้างวันและเวลาที่เลือก


def get_doctor_id():  # หา doctor_id จากแพทย์ที่เลือกใน Combobox
    index = ui['doctor_box'].current()  # ลำดับที่เลือก (-1 = ยังไม่ได้เลือก)
    if index < 0:  # ยังไม่ได้เลือก
        return None  # ส่ง None กลับ
    return ui['doctors'][index][0]  # ส่ง doctor_id ของลำดับนั้นกลับ


def on_dept_selected(event):  # เลือกแผนกแล้ว
    index = ui['dept_box'].current()  # ลำดับแผนกที่เลือก
    dept_id = ui['departments'][index][0]  # หา dept_id จากลำดับ
    load_doctors(dept_id)  # โหลดแพทย์ของแผนกนี้
    ui['hint_text'].set('เลือกแพทย์ในแผนก' + ui['departments'][index][1])  # แนะนำขั้นต่อไป


def on_doctor_selected(event):  # เลือกแพทย์แล้ว
    load_dates(get_doctor_id())  # โหลดวันที่ที่แพทย์คนนี้ยังว่าง


def on_date_selected(event):  # เลือกวันที่แล้ว
    work_date = ui['dates'][ui['date_box'].current()]  # วันที่แบบ YYYY-MM-DD ของลำดับที่เลือก
    load_slots(get_doctor_id(), work_date)  # โหลดช่องเวลาที่ยังว่าง


def on_phone_enter(event):  # กด Enter ในช่องเบอร์โทร
    find_patient()  # ค้นหาผู้ป่วยทันที


def find_patient():  # ปุ่ม "ค้นหาผู้ป่วย"
    phone = clean_phone(ui['phone_var'].get())  # เบอร์ที่พิมพ์ ตัดขีดและช่องว่างแล้ว
    if phone == '':  # ไม่ได้กรอกเบอร์
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณากรอกเบอร์โทรผู้ป่วย')  # เตือนให้กรอก
        return  # หยุด
    row = database.fetch_one('SELECT patient_id, patient_name, birth_date FROM patients WHERE phone = ?', (phone,))  # หาผู้ป่วยจากเบอร์โทร
    if row is None:  # ไม่พบ
        ui['patient_text'].set('ไม่พบผู้ป่วยเบอร์ ' + phone)  # แสดงผลว่าไม่พบ
        ui['patient_label'].configure(foreground=theme.WARNING_TEXT)  # ตัวอักษรสีแดง (สีเน้นแบบเข้ม)
        dialogs.show_warning('ไม่พบผู้ป่วย', 'ไม่พบผู้ป่วยเบอร์ ' + phone + '\nกรุณาลงทะเบียนที่แท็บ "ผู้ป่วย" ก่อน')  # บอกวิธีแก้
        return  # หยุด
    ui['patient_text'].set('ผู้ป่วย: ' + row[1] + '  (รหัส ' + str(row[0]) + ', เกิด ' + row[2] + ')')  # แสดงชื่อผู้ป่วยที่พบ
    ui['patient_label'].configure(foreground=theme.DONE)  # ตัวอักษรสีเขียว


def save_booking():  # ปุ่ม "บันทึกการจอง"
    phone = clean_phone(ui['phone_var'].get())  # อ่านเบอร์ล่าสุดในช่อง (กันกรณีแก้เบอร์หลังกดค้นหา)
    patient = database.fetch_one('SELECT patient_id, patient_name FROM patients WHERE phone = ?', (phone,))  # หาผู้ป่วยอีกครั้งตอนบันทึก
    if phone == '' or patient is None:  # ไม่ได้กรอกเบอร์ หรือไม่พบผู้ป่วย
        dialogs.show_warning('ยังไม่ได้เลือกผู้ป่วย', 'กรุณากรอกเบอร์โทรของผู้ป่วยที่ลงทะเบียนแล้ว แล้วกด "ค้นหาผู้ป่วย"')  # บอกวิธีแก้
        return  # หยุด
    if ui['dept_box'].current() < 0:  # ยังไม่เลือกแผนก
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกแผนก')  # เตือน
        return  # หยุด
    if ui['doctor_box'].current() < 0:  # ยังไม่เลือกแพทย์
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกแพทย์')  # เตือน
        return  # หยุด
    if ui['date_box'].current() < 0:  # ยังไม่เลือกวันที่
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกวันที่')  # เตือน
        return  # หยุด
    if ui['time_box'].current() < 0:  # ยังไม่เลือกช่องเวลา
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกช่องเวลา')  # เตือน
        return  # หยุด

    patient_id = patient[0]  # รหัสผู้ป่วย
    patient_name = patient[1]  # ชื่อผู้ป่วย
    doctor_id = get_doctor_id()  # รหัสแพทย์
    doctor_name = ui['doctors'][ui['doctor_box'].current()][1]  # ชื่อแพทย์
    work_date = ui['dates'][ui['date_box'].current()]  # วันที่แบบ YYYY-MM-DD
    schedule_id = ui['slots'][ui['time_box'].current()][0]  # รหัสช่องเวลาที่เลือก
    slot_time = ui['slots'][ui['time_box'].current()][1]  # เวลาเริ่มของช่อง
    symptom = ui['symptom_var'].get().strip()  # อาการที่กรอก
    if symptom == '':  # ไม่ได้กรอกอาการ (ไม่บังคับ)
        symptom = None  # เก็บเป็น NULL ในฐานข้อมูล

    today = date.today().isoformat()  # วันนี้ แบบ YYYY-MM-DD
    now_time = datetime.now().strftime('%H:%M')  # เวลาปัจจุบัน แบบ HH:MM
    if work_date < today or (work_date == today and slot_time <= now_time):  # เช็กซ้ำ: ช่องที่เลือกเลยเวลาไปแล้ว (เช่น เปิดหน้าจอค้างไว้นาน)
        dialogs.show_warning('ช่องเวลานี้ผ่านไปแล้ว', 'ช่อง ' + slot_label(slot_time) + ' ของวันที่ ' + work_date + ' เลยเวลาปัจจุบัน (' + now_time + ') ไปแล้ว\nจองได้เฉพาะช่องที่ยังไม่ถึงเวลา กรุณาเลือกใหม่')  # อธิบายเหตุผล
        load_dates(doctor_id)  # โหลดวันที่และช่องเวลาที่ยังจองได้ใหม่
        return  # หยุด

    taken = database.fetch_one("SELECT COUNT(*) FROM appointments WHERE schedule_id = ? AND status <> 'ยกเลิก'", (schedule_id,))  # นับคิวที่ยังไม่ยกเลิกในช่องนี้
    if taken[0] > 0:  # มีคนจองช่องนี้ไปแล้ว (เช่น จองจากอีกแท็บระหว่างที่หน้านี้เปิดค้างไว้)
        dialogs.show_warning('ช่องเวลาไม่ว่าง', 'ช่องเวลานี้มีผู้ป่วยจองไปแล้ว กรุณาเลือกช่องเวลาอื่น')  # เตือน
        load_slots(doctor_id, work_date)  # โหลดช่องว่างใหม่
        return  # หยุด

    sql = '''SELECT d.doctor_name                                        -- ชื่อแพทย์ของคิวที่ชนกัน
        FROM appointments a                                               -- เริ่มจากตารางการจองคิว
        JOIN schedules s ON a.schedule_id = s.schedule_id                -- ต่อเพื่อดูวันและเวลา
        JOIN doctors d   ON s.doctor_id   = d.doctor_id                  -- ต่อเพื่อดูชื่อแพทย์
        WHERE a.patient_id = ? AND a.status <> 'ยกเลิก'                  -- คิวที่ยังไม่ยกเลิกของผู้ป่วยคนนี้
          AND s.work_date = ? AND s.slot_time = ?'''  # ในวันและเวลาเดียวกับที่จะจอง
    clash = database.fetch_one(sql, (patient_id, work_date, slot_time))  # หาคิวที่ซ้อนกัน
    if clash is not None:  # ผู้ป่วยมีคิวอื่นในวันและเวลานี้แล้ว
        dialogs.show_warning('คิวซ้อนกัน', 'ผู้ป่วย "' + patient_name + '" มีคิวกับ ' + clash[0] + ' วันที่ ' + work_date + ' เวลา ' + slot_time + ' อยู่แล้ว\nผู้ป่วย 1 คนจองคิวซ้อนกันในวันและเวลาเดียวกันไม่ได้')  # อธิบายเหตุผล
        return  # หยุด

    detail = 'ผู้ป่วย: ' + patient_name + '\nแพทย์: ' + doctor_name + '\nวันที่: ' + thai_date_label(work_date) + '\nเวลา: ' + slot_label(slot_time)  # สรุปรายการจอง
    if symptom is not None:  # ถ้ากรอกอาการไว้
        detail = detail + '\nอาการ: ' + symptom  # แสดงอาการด้วย
    if not dialogs.ask_yes_no('ยืนยันการจอง', 'ต้องการจองคิวนี้ใช่ไหม?\n\n' + detail):  # ถามยืนยันก่อนบันทึก
        return  # ผู้ใช้กด No

    sql = '''INSERT INTO appointments (patient_id, schedule_id, symptom)  -- เพิ่มคิวใหม่ (status ได้ค่าเริ่มต้น 'จองแล้ว')
        VALUES (?, ?, ?)'''  # ค่าทั้งหมดส่งแทน ?
    try:  # ลองบันทึก
        new_id = database.insert(sql, (patient_id, schedule_id, symptom))  # บันทึก และได้หมายเลขคิวใหม่
    except sqlite3.Error as error:  # ฐานข้อมูลไม่ยอมบันทึก (เช่น ช่องนี้เพิ่งถูกจองไป)
        dialogs.show_error('จองไม่สำเร็จ', database.error_to_thai(error))  # แสดงเหตุผลเป็นภาษาไทย
        load_slots(doctor_id, work_date)  # โหลดช่องว่างใหม่
        return  # หยุด

    dialogs.show_info('จองคิวสำเร็จ', 'บันทึกการจองเรียบร้อย\nหมายเลขคิว: ' + str(new_id) + '\n\n' + detail)  # แจ้งผลสำเร็จ
    ui['symptom_var'].set('')  # ล้างช่องอาการ
    load_dates(doctor_id)  # โหลดวันที่ว่างใหม่ (ช่องที่เพิ่งจองจะหายไปจากรายการ)
    header_bar.refresh()  # อัปเดตตัวเลขสรุปวันนี้ (ถ้าจองคิวของวันนี้ ตัวเลขจะเพิ่ม)


def clear_form():  # ปุ่ม "ล้างฟอร์ม"
    ui['phone_var'].set('')  # ล้างเบอร์โทร
    ui['patient_text'].set('ยังไม่ได้เลือกผู้ป่วย')  # ล้างชื่อผู้ป่วย
    ui['patient_label'].configure(foreground=theme.HINT)  # กลับเป็นสีเทา
    ui['dept_box'].set('')  # ล้างแผนกที่เลือก
    ui['doctors'] = []  # ล้างรายการแพทย์
    ui['doctor_box']['values'] = []  # ล้างตัวเลือกแพทย์
    ui['doctor_box'].set('')  # ล้างแพทย์ที่เลือก
    clear_dates()  # ล้างวันที่และช่องเวลา
    ui['symptom_var'].set('')  # ล้างอาการ
    ui['hint_text'].set('เลือกแผนกก่อน แล้วรายการถัดไปจะแสดงตามที่เลือก')  # คำแนะนำเริ่มต้น


def refresh():  # เรียกจาก main.py ทุกครั้งที่เปิดแท็บนี้ (อาจมีคิวถูกยกเลิกหรือถูกจองจากแท็บอื่น)
    doctor_id = get_doctor_id()  # แพทย์ที่เลือกค้างไว้
    if doctor_id is None:  # ยังไม่ได้เลือกแพทย์
        return  # ไม่ต้องโหลดอะไร
    old_date = ''  # วันที่ที่เลือกค้างไว้
    if ui['date_box'].current() >= 0:  # ถ้าเลือกวันที่ไว้
        old_date = ui['dates'][ui['date_box'].current()]  # จำวันที่ไว้
    old_time = ui['time_box'].get()  # จำช่องเวลาที่เลือกไว้
    load_dates(doctor_id)  # โหลดวันที่ว่างใหม่
    if old_date in ui['dates']:  # วันเดิมยังมีช่องว่าง
        ui['date_box'].current(ui['dates'].index(old_date))  # เลือกวันเดิมให้อีกครั้ง
        load_slots(doctor_id, old_date)  # โหลดช่องว่างของวันนั้น
        if old_time in ui['time_box']['values']:  # ช่องเวลาเดิมยังว่าง
            ui['time_box'].set(old_time)  # เลือกช่องเดิมให้อีกครั้ง
