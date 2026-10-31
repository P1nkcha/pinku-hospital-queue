import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date, datetime
import database
import header_bar
import dialogs
import theme

ui = {}
form = {}


def create_tab(parent):
    frame = ttk.Frame(parent, padding=10)

    box = ttk.LabelFrame(frame, text='ค้นหาคิว (กรอกช่องไหนก็ได้ ถ้ากรอกหลายช่อง ต้องตรงทุกช่อง)', padding=10)
    box.pack(fill='x')
    ui['name_var'] = tk.StringVar()
    ui['phone_var'] = tk.StringVar()
    ui['date_var'] = tk.StringVar(value=date.today().isoformat())
    ttk.Label(box, text='ชื่อผู้ป่วย').grid(row=0, column=0, sticky='w')
    name_entry = ttk.Entry(box, textvariable=ui['name_var'], width=13)
    name_entry.grid(row=0, column=1, padx=(5, 10))
    ttk.Label(box, text='เบอร์โทร').grid(row=0, column=2, sticky='w')
    phone_entry = ttk.Entry(box, textvariable=ui['phone_var'], width=11)
    phone_entry.grid(row=0, column=3, padx=(5, 10))
    ttk.Label(box, text='วันที่ (YYYY-MM-DD)').grid(row=0, column=4, sticky='w')
    date_entry = ttk.Entry(box, textvariable=ui['date_var'], width=11)
    date_entry.grid(row=0, column=5, padx=5)
    ttk.Button(box, text='วันนี้', style='Light.TButton', command=set_today).grid(row=0, column=6, padx=(0, 10))
    ttk.Button(box, text='ค้นหา', command=search).grid(row=0, column=7)
    ttk.Button(box, text='ล้างเงื่อนไข', style='Light.TButton', command=clear_search).grid(row=0, column=8, padx=5)
    name_entry.bind('<Return>', on_enter)
    phone_entry.bind('<Return>', on_enter)
    date_entry.bind('<Return>', on_enter)

    ui['result_text'] = tk.StringVar()
    ttk.Label(frame, textvariable=ui['result_text'], foreground=theme.PRIMARY_DARK).pack(anchor='w', pady=(8, 4))

    table = ttk.Frame(frame)
    table.pack(fill='both', expand=True)
    columns = ('appt_id', 'work_date', 'slot_time', 'patient', 'phone', 'doctor', 'dept', 'symptom', 'status')
    headings = ('คิว', 'วันที่', 'เวลา', 'ผู้ป่วย', 'เบอร์โทร', 'แพทย์', 'แผนก', 'อาการ', 'สถานะ')
    widths = (45, 95, 55, 150, 100, 160, 110, 125, 75)
    tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse', style='Queue.Treeview')
    for i in range(len(columns)):
        tree.heading(columns[i], text=headings[i])
        tree.column(columns[i], width=widths[i], minwidth=40, stretch=True)
    for name in ('appt_id', 'work_date', 'slot_time', 'phone', 'status'):
        tree.column(name, anchor='center')
    tree.tag_configure('booked', background=theme.BOOKED_BG, foreground=theme.TEXT)
    tree.tag_configure('done', background=theme.DONE_BG, foreground=theme.TEXT)
    tree.tag_configure('cancelled', background=theme.CANCELLED_BG, foreground=theme.TEXT)
    scroll_y = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
    scroll_x = ttk.Scrollbar(table, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    tree.grid(row=0, column=0, sticky='nsew')
    scroll_y.grid(row=0, column=1, sticky='ns')
    scroll_x.grid(row=1, column=0, sticky='ew')
    table.rowconfigure(0, weight=1)
    table.columnconfigure(0, weight=1)
    ui['tree'] = tree

    actions = ttk.Frame(frame)
    actions.pack(fill='x', pady=(10, 0))
    ttk.Label(actions, text='จัดการคิวที่เลือก:').pack(side='left')
    ttk.Button(actions, text='ยกเลิกคิว', style='Danger.TButton', command=cancel_appointment).pack(side='left', padx=8, ipady=3)
    ttk.Button(actions, text='บันทึกว่าตรวจแล้ว', command=mark_done).pack(side='left', ipady=3)
    ttk.Label(actions, text='สีส้ม = จองแล้ว · สีเขียว = ตรวจแล้ว · สีเทา = ยกเลิก', foreground=theme.HINT).pack(side='right')

    load_results()
    return frame


def is_valid_date(text):
    if len(text) != 10:
        return False
    try:
        datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return False
    return True


def read_conditions():
    name = ui['name_var'].get().strip()
    phone = ui['phone_var'].get().replace('-', '').replace(' ', '')
    work_date = ui['date_var'].get().strip()
    return name, phone, work_date


def load_results():
    name, phone, work_date = read_conditions()
    sql = '''SELECT a.appt_id, s.work_date, s.slot_time, p.patient_name, p.phone,
            d.doctor_name, dp.dept_name, IFNULL(a.symptom, '-'), a.status
        FROM appointments a
        JOIN patients p     ON a.patient_id  = p.patient_id
        JOIN schedules s    ON a.schedule_id = s.schedule_id
        JOIN doctors d      ON s.doctor_id   = d.doctor_id
        JOIN departments dp ON d.dept_id     = dp.dept_id
        WHERE (? = '' OR p.patient_name LIKE ?)
          AND (? = '' OR p.phone = ?)
          AND (? = '' OR s.work_date = ?)
        ORDER BY s.work_date, s.slot_time, d.doctor_name'''
    params = (name, '%' + name + '%', phone, phone, work_date, work_date)
    rows = database.fetch_all(sql, params)
    tree = ui['tree']
    for item in tree.get_children():
        tree.delete(item)
    for row in rows:
        tag = 'booked'
        if row[8] == 'ยกเลิก':
            tag = 'cancelled'
        elif row[8] == 'ตรวจแล้ว':
            tag = 'done'
        tree.insert('', 'end', iid=str(row[0]), values=row, tags=(tag,))
    summary = 'พบ ' + str(len(rows)) + ' คิว'
    if name == '' and phone == '' and work_date == '':
        summary = summary + ' (แสดงทุกคิว)'
    ui['result_text'].set(summary)


def search():
    name, phone, work_date = read_conditions()
    if work_date != '' and not is_valid_date(work_date):
        dialogs.show_warning('วันที่ไม่ถูกต้อง', 'กรุณากรอกวันที่แบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น ' + date.today().isoformat() + '\nหรือกดปุ่ม "วันนี้"')
        return
    load_results()


def on_enter(event):
    search()


def set_today():
    ui['date_var'].set(date.today().isoformat())
    search()


def clear_search():
    ui['name_var'].set('')
    ui['phone_var'].set('')
    ui['date_var'].set('')
    load_results()


def refresh():
    name, phone, work_date = read_conditions()
    if work_date != '' and not is_valid_date(work_date):
        return
    load_results()


def get_selected_appointment():
    selected = ui['tree'].selection()
    if len(selected) == 0:
        dialogs.show_warning('ยังไม่ได้เลือกคิว', 'กรุณาคลิกเลือกคิวในตารางก่อน')
        return None
    appt_id = int(selected[0])
    sql = '''SELECT a.appt_id, a.status, s.work_date, s.slot_time, p.patient_name, d.doctor_name
        FROM appointments a
        JOIN patients p  ON a.patient_id  = p.patient_id
        JOIN schedules s ON a.schedule_id = s.schedule_id
        JOIN doctors d   ON s.doctor_id   = d.doctor_id
        WHERE a.appt_id = ?'''
    row = database.fetch_one(sql, (appt_id,))
    if row is None:
        dialogs.show_warning('ไม่พบคิว', 'ไม่พบคิวนี้ในระบบแล้ว กรุณาค้นหาใหม่')
        load_results()
        return None
    return row


def describe(row):
    return 'คิวที่: ' + str(row[0]) + '\nผู้ป่วย: ' + row[4] + '\nแพทย์: ' + row[5] + '\nวันที่: ' + row[2] + '  เวลา: ' + row[3]


def select_row(appt_id):
    if ui['tree'].exists(str(appt_id)):
        ui['tree'].selection_set(str(appt_id))
        ui['tree'].see(str(appt_id))


def cancel_appointment():
    row = get_selected_appointment()
    if row is None:
        return
    if row[1] != 'จองแล้ว':
        dialogs.show_warning('ยกเลิกไม่ได้', 'คิวที่ ' + str(row[0]) + ' มีสถานะ "' + row[1] + '" แล้ว\nยกเลิกได้เฉพาะคิวที่สถานะ "จองแล้ว"')
        return
    if not dialogs.ask_yes_no('ยืนยันการยกเลิกคิว', 'ต้องการยกเลิกคิวนี้ใช่ไหม?\n\n' + describe(row) + '\n\nหลังยกเลิก ช่องเวลานี้จะว่างให้ผู้ป่วยคนอื่นจองได้', icon='warning'):
        return
    sql = '''UPDATE appointments SET status = 'ยกเลิก'
        WHERE appt_id = ? AND status = 'จองแล้ว' '''
    try:
        count = database.execute(sql, (row[0],))
    except sqlite3.Error as error:
        dialogs.show_error('ยกเลิกไม่สำเร็จ', database.error_to_thai(error))
        return
    if count == 0:
        dialogs.show_warning('ยกเลิกไม่ได้', 'สถานะของคิวนี้ถูกเปลี่ยนไปแล้ว กรุณาค้นหาใหม่')
    else:
        dialogs.show_info('ยกเลิกคิวสำเร็จ', 'ยกเลิกคิวที่ ' + str(row[0]) + ' เรียบร้อย')
    load_results()
    select_row(row[0])
    header_bar.refresh()


def mark_done():
    row = get_selected_appointment()
    if row is None:
        return
    if row[1] != 'จองแล้ว':
        dialogs.show_warning('บันทึกไม่ได้', 'คิวที่ ' + str(row[0]) + ' มีสถานะ "' + row[1] + '" แล้ว\nบันทึกว่าตรวจแล้วได้เฉพาะคิวที่สถานะ "จองแล้ว"')
        return
    if row[2] > date.today().isoformat():
        dialogs.show_warning('ยังไม่ถึงวันนัด', 'คิวนี้นัดวันที่ ' + row[2] + '\nบันทึกว่าตรวจแล้วได้เฉพาะคิวของวันนี้หรือวันที่ผ่านมา')
        return
    if not dialogs.ask_yes_no('ยืนยันการบันทึก', 'บันทึกว่าคิวนี้ตรวจแล้วใช่ไหม?\n\n' + describe(row)):
        return
    result = ask_treatment(row)
    if result is None:
        return
    diagnosis = result[0]
    treatment = result[1]
    commands = [
        ('''UPDATE appointments SET status = 'ตรวจแล้ว'
            WHERE appt_id = ? AND status = 'จองแล้ว' ''', (row[0],)),
        ('''INSERT INTO treatments (appt_id, diagnosis, treatment)
            VALUES (?, ?, ?)''', (row[0], diagnosis, treatment)),
    ]
    try:
        saved = database.execute_transaction(commands)
    except sqlite3.Error as error:
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))
        return
    if not saved:
        dialogs.show_warning('บันทึกไม่ได้', 'สถานะของคิวนี้ถูกเปลี่ยนไปแล้ว กรุณาค้นหาใหม่')
    else:
        dialogs.show_info('บันทึกสำเร็จ', 'บันทึกว่าคิวที่ ' + str(row[0]) + ' ตรวจแล้ว เรียบร้อย\nผลวินิจฉัย: ' + diagnosis)
    load_results()
    select_row(row[0])
    header_bar.refresh()


def ask_treatment(row):
    window = dialogs.create_window('บันทึกผลการรักษา')
    form['window'] = window
    form['result'] = None
    form['diagnosis_var'] = tk.StringVar()
    form['treatment_var'] = tk.StringVar()

    tk.Frame(window, background=theme.PRIMARY, height=6).pack(fill='x')
    box = ttk.Frame(window, padding=16)
    box.pack(fill='both', expand=True)
    ttk.Label(box, text=describe(row)).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
    ttk.Label(box, text='ผลวินิจฉัย (บังคับกรอก)').grid(row=1, column=0, sticky='w', pady=5)
    form['diagnosis_entry'] = ttk.Entry(box, textvariable=form['diagnosis_var'], width=45)
    form['diagnosis_entry'].grid(row=1, column=1, padx=(10, 0), pady=5)
    ttk.Label(box, text='การรักษา (ไม่บังคับ)').grid(row=2, column=0, sticky='w', pady=5)
    ttk.Entry(box, textvariable=form['treatment_var'], width=45).grid(row=2, column=1, padx=(10, 0), pady=5)
    buttons = ttk.Frame(box)
    buttons.grid(row=3, column=0, columnspan=2, sticky='e', pady=(14, 0))
    ttk.Button(buttons, text='ยกเลิก', style='Light.TButton', command=on_form_cancel).pack(side='right')
    ttk.Button(buttons, text='บันทึก', command=on_form_save).pack(side='right', padx=(0, 8))

    window.bind('<Return>', on_form_enter)
    window.bind('<Escape>', on_form_escape)
    window.protocol('WM_DELETE_WINDOW', on_form_cancel)
    dialogs.show_modal(window, form['diagnosis_entry'])
    return form['result']


def on_form_save():
    diagnosis = form['diagnosis_var'].get().strip()
    if diagnosis == '':
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณากรอกผลวินิจฉัยก่อนบันทึก')
        form['diagnosis_entry'].focus_set()
        return
    treatment = form['treatment_var'].get().strip()
    if treatment == '':
        treatment = None
    form['result'] = (diagnosis, treatment)
    form['window'].destroy()


def on_form_cancel():
    form['result'] = None
    form['window'].destroy()


def on_form_enter(event):
    on_form_save()


def on_form_escape(event):
    on_form_cancel()
