import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date, datetime, timedelta
import database
import header_bar
import dialogs
import theme

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']

ui = {}


def create_tab(parent):
    frame = ttk.Frame(parent, padding=15)

    ui['departments'] = []
    ui['doctors'] = []
    ui['dates'] = []
    ui['slots'] = []

    step1 = ttk.LabelFrame(frame, text='1. ค้นหาผู้ป่วยด้วยเบอร์โทร', padding=12)
    step1.pack(fill='x')
    ttk.Label(step1, text='เบอร์โทร').pack(side='left')
    ui['phone_var'] = tk.StringVar()
    phone_entry = ttk.Entry(step1, textvariable=ui['phone_var'], width=18)
    phone_entry.pack(side='left', padx=8)
    phone_entry.bind('<Return>', on_phone_enter)
    ttk.Button(step1, text='ค้นหาผู้ป่วย', command=find_patient).pack(side='left')
    ui['patient_text'] = tk.StringVar(value='ยังไม่ได้เลือกผู้ป่วย')
    ui['patient_label'] = ttk.Label(step1, textvariable=ui['patient_text'], foreground=theme.HINT)
    ui['patient_label'].pack(side='left', padx=15)

    step2 = ttk.LabelFrame(frame, text='2. เลือกแผนก แพทย์ วันที่ และช่องเวลาที่ยังว่าง', padding=12)
    step2.pack(fill='x', pady=12)
    ui['dept_box'] = ttk.Combobox(step2, state='readonly', width=30)
    ui['doctor_box'] = ttk.Combobox(step2, state='readonly', width=30)
    ui['date_box'] = ttk.Combobox(step2, state='readonly', width=30)
    ui['time_box'] = ttk.Combobox(step2, state='readonly', width=30)
    ttk.Label(step2, text='แผนก').grid(row=0, column=0, sticky='w', pady=5)
    ui['dept_box'].grid(row=0, column=1, sticky='w', padx=10, pady=5)
    ttk.Label(step2, text='แพทย์').grid(row=1, column=0, sticky='w', pady=5)
    ui['doctor_box'].grid(row=1, column=1, sticky='w', padx=10, pady=5)
    ttk.Label(step2, text='วันที่').grid(row=2, column=0, sticky='w', pady=5)
    ui['date_box'].grid(row=2, column=1, sticky='w', padx=10, pady=5)
    ttk.Label(step2, text='ช่องเวลา').grid(row=3, column=0, sticky='w', pady=5)
    ui['time_box'].grid(row=3, column=1, sticky='w', padx=10, pady=5)
    ui['hint_text'] = tk.StringVar(value='เลือกแผนกก่อน แล้วรายการถัดไปจะแสดงตามที่เลือก')
    ttk.Label(step2, textvariable=ui['hint_text'], foreground=theme.PRIMARY_DARK, wraplength=420).grid(row=0, column=2, rowspan=4, sticky='nw', padx=20)
    ui['dept_box'].bind('<<ComboboxSelected>>', on_dept_selected)
    ui['doctor_box'].bind('<<ComboboxSelected>>', on_doctor_selected)
    ui['date_box'].bind('<<ComboboxSelected>>', on_date_selected)

    step3 = ttk.LabelFrame(frame, text='3. อาการเบื้องต้น (ไม่บังคับกรอก)', padding=12)
    step3.pack(fill='x')
    ui['symptom_var'] = tk.StringVar()
    ttk.Entry(step3, textvariable=ui['symptom_var'], width=70).pack(side='left')

    buttons = ttk.Frame(frame)
    buttons.pack(fill='x', pady=15)
    ttk.Button(buttons, text='บันทึกการจอง', command=save_booking).pack(side='left', ipadx=10, ipady=4)
    ttk.Button(buttons, text='ล้างฟอร์ม', style='Light.TButton', command=clear_form).pack(side='left', padx=10, ipady=4)

    load_departments()
    return frame


def clean_phone(text):
    return text.replace('-', '').replace(' ', '')


def thai_date_label(work_date):
    day_name = THAI_DAYS[datetime.strptime(work_date, '%Y-%m-%d').weekday()]
    label = work_date + ' (วัน' + day_name
    if work_date == date.today().isoformat():
        label = label + ', วันนี้'
    return label + ')'


def slot_label(slot_time):
    start = datetime.strptime(slot_time, '%H:%M')
    end = start + timedelta(minutes=30)
    return slot_time + ' - ' + end.strftime('%H:%M')


def load_departments():
    rows = database.fetch_all('SELECT dept_id, dept_name FROM departments ORDER BY dept_id')
    ui['departments'] = rows
    ui['dept_box']['values'] = [row[1] for row in rows]


def load_doctors(dept_id):
    rows = database.fetch_all('SELECT doctor_id, doctor_name FROM doctors WHERE dept_id = ? ORDER BY doctor_id', (dept_id,))
    ui['doctors'] = rows
    ui['doctor_box']['values'] = [row[1] for row in rows]
    ui['doctor_box'].set('')
    clear_dates()


def load_dates(doctor_id):
    sql = '''SELECT DISTINCT s.work_date
        FROM schedules s
        LEFT JOIN appointments a ON a.schedule_id = s.schedule_id
                                AND a.status <> 'ยกเลิก'
        WHERE s.doctor_id = ?
          AND (s.work_date > date('now', 'localtime')
               OR (s.work_date = date('now', 'localtime')
                   AND s.slot_time > strftime('%H:%M', 'now', 'localtime')))
          AND a.appt_id IS NULL
        ORDER BY s.work_date'''
    rows = database.fetch_all(sql, (doctor_id,))
    ui['dates'] = [row[0] for row in rows]
    ui['date_box']['values'] = [thai_date_label(d) for d in ui['dates']]
    clear_dates_selection()
    if len(ui['dates']) == 0:
        ui['hint_text'].set('แพทย์ท่านนี้ไม่มีช่องเวลาว่างที่ยังจองได้ กรุณาเลือกแพทย์ท่านอื่น')
    else:
        ui['hint_text'].set('มีวันที่ว่าง ' + str(len(ui['dates'])) + ' วัน เลือกวันที่ แล้วเลือกช่องเวลา')


def load_slots(doctor_id, work_date):
    sql = '''SELECT s.schedule_id, s.slot_time
        FROM schedules s
        LEFT JOIN appointments a ON a.schedule_id = s.schedule_id
                                AND a.status <> 'ยกเลิก'
        WHERE s.doctor_id = ? AND s.work_date = ?
          AND (s.work_date > date('now', 'localtime')
               OR (s.work_date = date('now', 'localtime')
                   AND s.slot_time > strftime('%H:%M', 'now', 'localtime')))
          AND a.appt_id IS NULL
        ORDER BY s.slot_time'''
    rows = database.fetch_all(sql, (doctor_id, work_date))
    ui['slots'] = rows
    ui['time_box']['values'] = [slot_label(row[1]) for row in rows]
    ui['time_box'].set('')
    ui['hint_text'].set('วันที่ ' + work_date + ' มีช่องว่าง ' + str(len(rows)) + ' ช่อง')


def clear_dates_selection():
    ui['date_box'].set('')
    ui['slots'] = []
    ui['time_box']['values'] = []
    ui['time_box'].set('')


def clear_dates():
    ui['dates'] = []
    ui['date_box']['values'] = []
    clear_dates_selection()


def get_doctor_id():
    index = ui['doctor_box'].current()
    if index < 0:
        return None
    return ui['doctors'][index][0]


def on_dept_selected(event):
    index = ui['dept_box'].current()
    dept_id = ui['departments'][index][0]
    load_doctors(dept_id)
    ui['hint_text'].set('เลือกแพทย์ในแผนก' + ui['departments'][index][1])


def on_doctor_selected(event):
    load_dates(get_doctor_id())


def on_date_selected(event):
    work_date = ui['dates'][ui['date_box'].current()]
    load_slots(get_doctor_id(), work_date)


def on_phone_enter(event):
    find_patient()


def find_patient():
    phone = clean_phone(ui['phone_var'].get())
    if phone == '':
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณากรอกเบอร์โทรผู้ป่วย')
        return
    row = database.fetch_one('SELECT patient_id, patient_name, birth_date FROM patients WHERE phone = ?', (phone,))
    if row is None:
        ui['patient_text'].set('ไม่พบผู้ป่วยเบอร์ ' + phone)
        ui['patient_label'].configure(foreground=theme.WARNING_TEXT)
        dialogs.show_warning('ไม่พบผู้ป่วย', 'ไม่พบผู้ป่วยเบอร์ ' + phone + '\nกรุณาลงทะเบียนที่แท็บ "ผู้ป่วย" ก่อน')
        return
    ui['patient_text'].set('ผู้ป่วย: ' + row[1] + '  (รหัส ' + str(row[0]) + ', เกิด ' + row[2] + ')')
    ui['patient_label'].configure(foreground=theme.DONE)


def save_booking():
    phone = clean_phone(ui['phone_var'].get())
    patient = database.fetch_one('SELECT patient_id, patient_name FROM patients WHERE phone = ?', (phone,))
    if phone == '' or patient is None:
        dialogs.show_warning('ยังไม่ได้เลือกผู้ป่วย', 'กรุณากรอกเบอร์โทรของผู้ป่วยที่ลงทะเบียนแล้ว แล้วกด "ค้นหาผู้ป่วย"')
        return
    if ui['dept_box'].current() < 0:
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกแผนก')
        return
    if ui['doctor_box'].current() < 0:
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกแพทย์')
        return
    if ui['date_box'].current() < 0:
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกวันที่')
        return
    if ui['time_box'].current() < 0:
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณาเลือกช่องเวลา')
        return

    patient_id = patient[0]
    patient_name = patient[1]
    doctor_id = get_doctor_id()
    doctor_name = ui['doctors'][ui['doctor_box'].current()][1]
    work_date = ui['dates'][ui['date_box'].current()]
    schedule_id = ui['slots'][ui['time_box'].current()][0]
    slot_time = ui['slots'][ui['time_box'].current()][1]
    symptom = ui['symptom_var'].get().strip()
    if symptom == '':
        symptom = None

    today = date.today().isoformat()
    now_time = datetime.now().strftime('%H:%M')
    if work_date < today or (work_date == today and slot_time <= now_time):
        dialogs.show_warning('ช่องเวลานี้ผ่านไปแล้ว', 'ช่อง ' + slot_label(slot_time) + ' ของวันที่ ' + work_date + ' เลยเวลาปัจจุบัน (' + now_time + ') ไปแล้ว\nจองได้เฉพาะช่องที่ยังไม่ถึงเวลา กรุณาเลือกใหม่')
        load_dates(doctor_id)
        return

    taken = database.fetch_one("SELECT COUNT(*) FROM appointments WHERE schedule_id = ? AND status <> 'ยกเลิก'", (schedule_id,))
    if taken[0] > 0:
        dialogs.show_warning('ช่องเวลาไม่ว่าง', 'ช่องเวลานี้มีผู้ป่วยจองไปแล้ว กรุณาเลือกช่องเวลาอื่น')
        load_slots(doctor_id, work_date)
        return

    sql = '''SELECT d.doctor_name
        FROM appointments a
        JOIN schedules s ON a.schedule_id = s.schedule_id
        JOIN doctors d   ON s.doctor_id   = d.doctor_id
        WHERE a.patient_id = ? AND a.status <> 'ยกเลิก'
          AND s.work_date = ? AND s.slot_time = ?'''
    clash = database.fetch_one(sql, (patient_id, work_date, slot_time))
    if clash is not None:
        dialogs.show_warning('คิวซ้อนกัน', 'ผู้ป่วย "' + patient_name + '" มีคิวกับ ' + clash[0] + ' วันที่ ' + work_date + ' เวลา ' + slot_time + ' อยู่แล้ว\nผู้ป่วย 1 คนจองคิวซ้อนกันในวันและเวลาเดียวกันไม่ได้')
        return

    detail = 'ผู้ป่วย: ' + patient_name + '\nแพทย์: ' + doctor_name + '\nวันที่: ' + thai_date_label(work_date) + '\nเวลา: ' + slot_label(slot_time)
    if symptom is not None:
        detail = detail + '\nอาการ: ' + symptom
    if not dialogs.ask_yes_no('ยืนยันการจอง', 'ต้องการจองคิวนี้ใช่ไหม?\n\n' + detail):
        return

    sql = '''INSERT INTO appointments (patient_id, schedule_id, symptom)
        VALUES (?, ?, ?)'''
    try:
        new_id = database.insert(sql, (patient_id, schedule_id, symptom))
    except sqlite3.Error as error:
        dialogs.show_error('จองไม่สำเร็จ', database.error_to_thai(error))
        load_slots(doctor_id, work_date)
        return

    dialogs.show_info('จองคิวสำเร็จ', 'บันทึกการจองเรียบร้อย\nหมายเลขคิว: ' + str(new_id) + '\n\n' + detail)
    ui['symptom_var'].set('')
    load_dates(doctor_id)
    header_bar.refresh()


def clear_form():
    ui['phone_var'].set('')
    ui['patient_text'].set('ยังไม่ได้เลือกผู้ป่วย')
    ui['patient_label'].configure(foreground=theme.HINT)
    ui['dept_box'].set('')
    ui['doctors'] = []
    ui['doctor_box']['values'] = []
    ui['doctor_box'].set('')
    clear_dates()
    ui['symptom_var'].set('')
    ui['hint_text'].set('เลือกแผนกก่อน แล้วรายการถัดไปจะแสดงตามที่เลือก')


def refresh():
    doctor_id = get_doctor_id()
    if doctor_id is None:
        return
    old_date = ''
    if ui['date_box'].current() >= 0:
        old_date = ui['dates'][ui['date_box'].current()]
    old_time = ui['time_box'].get()
    load_dates(doctor_id)
    if old_date in ui['dates']:
        ui['date_box'].current(ui['dates'].index(old_date))
        load_slots(doctor_id, old_date)
        if old_time in ui['time_box']['values']:
            ui['time_box'].set(old_time)
