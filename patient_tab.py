import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date, datetime
import database
import dialogs
import theme
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

ui = {}


def create_tab(parent):
    frame = ttk.Frame(parent, padding=10)

    top = ttk.Frame(frame)
    top.pack(fill='both', expand=True)

    form = ttk.LabelFrame(top, text='ข้อมูลผู้ป่วย', padding=12)
    form.pack(side='left', fill='y', padx=(0, 10))

    ui['name_var'] = tk.StringVar()
    ui['phone_var'] = tk.StringVar()
    ui['birth_var'] = tk.StringVar()
    ui['mode_var'] = tk.StringVar(value='โหมด: ลงทะเบียนผู้ป่วยใหม่')
    ui['selected_id'] = None
    ui['birth_from_user'] = False

    ttk.Label(form, textvariable=ui['mode_var'], foreground=theme.PRIMARY_DARK).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 6))
    ttk.Label(form, text='ชื่อ-นามสกุล').grid(row=1, column=0, sticky='w', pady=4)
    ttk.Entry(form, textvariable=ui['name_var'], width=28).grid(row=1, column=1, pady=4)
    ttk.Label(form, text='เบอร์โทร').grid(row=2, column=0, sticky='w', pady=4)
    ttk.Entry(form, textvariable=ui['phone_var'], width=28).grid(row=2, column=1, pady=4)
    ttk.Label(form, text='วันเกิด').grid(row=3, column=0, sticky='w', pady=4)
    birth_entry = DateEntry(form, textvariable=ui['birth_var'], width=26, font=theme.FONT,
                            date_pattern='yyyy-mm-dd', locale='th_TH', maxdate=date.today(),
                            firstweekday='sunday', showweeknumbers=False,
                            background=theme.PRIMARY, foreground=theme.TEXT, bordercolor=theme.SECONDARY,
                            headersbackground=theme.SECONDARY, headersforeground=theme.TEXT,
                            normalbackground=theme.WHITE, normalforeground=theme.TEXT,
                            weekendbackground=theme.WHITE, weekendforeground=theme.TEXT,
                            othermonthbackground=theme.WHITE, othermonthwebackground=theme.WHITE,
                            othermonthforeground=theme.HINT, othermonthweforeground=theme.HINT,
                            selectbackground=theme.PRIMARY, selectforeground=theme.TEXT)
    birth_entry.configure(validate='none')
    birth_entry.delete(0, 'end')
    birth_entry.grid(row=3, column=1, pady=4)
    birth_entry.bind('<<DateEntrySelected>>', on_birth_picked)
    birth_entry.bind('<KeyRelease>', on_birth_typed)
    birth_entry.bind('<ButtonPress-1>', on_birth_click, add='+')
    frame.bind_all('<ButtonPress-1>', on_any_click, add='+')
    ui['birth_entry'] = birth_entry
    ttk.Label(form, text='เลือกจากปฏิทิน หรือพิมพ์ เช่น 1990-05-01', foreground=theme.HINT).grid(row=4, column=1, sticky='w')

    ttk.Button(form, text='ลงทะเบียนผู้ป่วยใหม่', command=add_patient).grid(row=5, column=0, columnspan=2, sticky='we', pady=(12, 3))
    ttk.Button(form, text='บันทึกการแก้ไข', command=update_patient).grid(row=6, column=0, columnspan=2, sticky='we', pady=3)
    ttk.Button(form, text='ล้างฟอร์ม', style='Light.TButton', command=clear_form).grid(row=7, column=0, columnspan=2, sticky='we', pady=3)

    right = ttk.Frame(top)
    right.pack(side='left', fill='both', expand=True)

    search_bar = ttk.Frame(right)
    search_bar.pack(fill='x')
    ttk.Label(search_bar, text='ค้นหาชื่อหรือเบอร์โทร').pack(side='left')
    ui['keyword_var'] = tk.StringVar()
    keyword_entry = ttk.Entry(search_bar, textvariable=ui['keyword_var'], width=25)
    keyword_entry.pack(side='left', padx=6)
    keyword_entry.bind('<Return>', on_keyword_enter)
    ttk.Button(search_bar, text='ค้นหา', command=refresh).pack(side='left')
    ttk.Button(search_bar, text='แสดงทั้งหมด', style='Light.TButton', command=show_all).pack(side='left', padx=6)

    ttk.Label(right, text='คลิกที่รายชื่อเพื่อนำข้อมูลขึ้นฟอร์มสำหรับแก้ไข และดูประวัติการรักษา', foreground=theme.HINT).pack(anchor='w', pady=(6, 4))

    table = ttk.Frame(right)
    table.pack(fill='both', expand=True)
    columns = ('id', 'name', 'phone', 'birth')
    tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse', height=7)
    tree.heading('id', text='รหัส')
    tree.heading('name', text='ชื่อ-นามสกุล')
    tree.heading('phone', text='เบอร์โทร')
    tree.heading('birth', text='วันเกิด')
    tree.column('id', width=60, anchor='center')
    tree.column('name', width=220)
    tree.column('phone', width=130, anchor='center')
    tree.column('birth', width=120, anchor='center')
    scroll = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side='left', fill='both', expand=True)
    scroll.pack(side='left', fill='y')
    tree.bind('<<TreeviewSelect>>', on_select)
    ui['tree'] = tree

    history = ttk.LabelFrame(frame, text='ประวัติการรักษา', padding=8)
    history.pack(fill='x', pady=(8, 0))
    ui['history_text'] = tk.StringVar()
    ttk.Label(history, textvariable=ui['history_text'], foreground=theme.PRIMARY_DARK).pack(anchor='w', pady=(0, 4))
    history_table = ttk.Frame(history)
    history_table.pack(fill='x')
    history_columns = ('date', 'doctor', 'dept', 'diagnosis', 'treatment')
    history_tree = ttk.Treeview(history_table, columns=history_columns, show='headings', selectmode='none', height=4)
    history_tree.heading('date', text='วันที่')
    history_tree.heading('doctor', text='แพทย์')
    history_tree.heading('dept', text='แผนก')
    history_tree.heading('diagnosis', text='ผลวินิจฉัย')
    history_tree.heading('treatment', text='การรักษา')
    history_tree.column('date', width=95, anchor='center')
    history_tree.column('doctor', width=170)
    history_tree.column('dept', width=120)
    history_tree.column('diagnosis', width=210)
    history_tree.column('treatment', width=400)
    history_scroll = ttk.Scrollbar(history_table, orient='vertical', command=history_tree.yview)
    history_tree.configure(yscrollcommand=history_scroll.set)
    history_tree.pack(side='left', fill='x', expand=True)
    history_scroll.pack(side='left', fill='y')
    ui['history_tree'] = history_tree

    refresh()
    return frame


def refresh():
    keyword = ui['keyword_var'].get().strip()
    pattern = '%' + keyword + '%'
    sql = '''SELECT patient_id, patient_name, phone, birth_date
        FROM patients
        WHERE patient_name LIKE ? OR phone LIKE ?
        ORDER BY patient_id'''
    rows = database.fetch_all(sql, (pattern, pattern))
    tree = ui['tree']
    for item in tree.get_children():
        tree.delete(item)
    for row in rows:
        tree.insert('', 'end', iid=str(row[0]), values=row)
    load_history(ui['selected_id'])


def load_history(patient_id):
    history_tree = ui['history_tree']
    for item in history_tree.get_children():
        history_tree.delete(item)
    if patient_id is None:
        ui['history_text'].set('คลิกเลือกผู้ป่วยในตารางด้านบน เพื่อดูประวัติการรักษา')
        return
    patient = database.fetch_one('SELECT patient_name FROM patients WHERE patient_id = ?', (patient_id,))
    if patient is None:
        ui['history_text'].set('ไม่พบผู้ป่วยรายนี้ในระบบแล้ว')
        return
    sql = '''SELECT s.work_date, d.doctor_name, dp.dept_name,
            t.diagnosis, IFNULL(t.treatment, '-')
        FROM treatments t
        JOIN appointments a ON t.appt_id     = a.appt_id
        JOIN schedules s    ON a.schedule_id = s.schedule_id
        JOIN doctors d      ON s.doctor_id   = d.doctor_id
        JOIN departments dp ON d.dept_id     = dp.dept_id
        WHERE a.patient_id = ?
        ORDER BY s.work_date DESC, s.slot_time DESC'''
    rows = database.fetch_all(sql, (patient_id,))
    for row in rows:
        history_tree.insert('', 'end', values=row)
    if len(rows) == 0:
        ui['history_text'].set(patient[0] + ' ยังไม่มีประวัติการรักษา')
    else:
        ui['history_text'].set(patient[0] + ' มีประวัติการรักษา ' + str(len(rows)) + ' ครั้ง (เรียงจากล่าสุด)')


def on_keyword_enter(event):
    refresh()


def show_all():
    ui['keyword_var'].set('')
    refresh()


def on_select(event):
    selected = ui['tree'].selection()
    if len(selected) == 0:
        return
    patient_id = int(selected[0])
    sql = '''SELECT patient_name, phone, birth_date
        FROM patients
        WHERE patient_id = ?'''
    row = database.fetch_one(sql, (patient_id,))
    if row is None:
        return
    ui['selected_id'] = patient_id
    ui['name_var'].set(row[0])
    ui['phone_var'].set(row[1])
    ui['birth_var'].set(row[2])
    ui['birth_from_user'] = True
    ui['mode_var'].set('โหมด: แก้ไขข้อมูลผู้ป่วยรหัส ' + str(patient_id))
    load_history(patient_id)


def clear_form():
    ui['name_var'].set('')
    ui['phone_var'].set('')
    ui['birth_var'].set('')
    ui['birth_from_user'] = False
    ui['selected_id'] = None
    ui['mode_var'].set('โหมด: ลงทะเบียนผู้ป่วยใหม่')
    ui['tree'].selection_remove(ui['tree'].selection())
    load_history(None)


def on_birth_picked(event):
    ui['birth_from_user'] = True


def on_birth_typed(event):
    birth = ui['birth_var'].get().strip()
    ui['birth_from_user'] = is_valid_date(birth) and birth <= date.today().isoformat()


def on_birth_click(event):
    clicked_arrow = 'downarrow' in ui['birth_entry'].identify(event.x, event.y)
    if clicked_arrow and not ui['birth_from_user']:
        ui['birth_var'].set('')


def on_any_click(event):
    popup = ui['birth_entry'].winfo_children()[0]
    clicked_inside = str(event.widget).startswith(str(ui['birth_entry']))
    if popup.winfo_ismapped() and not clicked_inside:
        popup.withdraw()
        ui['birth_entry'].state(['!pressed'])


def read_form():
    name = ui['name_var'].get().strip()
    phone = ui['phone_var'].get().replace('-', '').replace(' ', '')
    birth = ui['birth_var'].get().strip()
    return name, phone, birth


def is_phone(phone):
    if len(phone) != 10:
        return False
    if phone[0] != '0':
        return False
    for ch in phone:
        if ch not in '0123456789':
            return False
    return True


def is_valid_date(text):
    if len(text) != 10:
        return False
    try:
        datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return False
    return True


def check_form(name, phone, birth):
    if name == '' or phone == '' or birth == '':
        return 'กรุณากรอกชื่อ-นามสกุล เบอร์โทร และวันเกิดให้ครบ'
    if not is_phone(phone):
        return 'เบอร์โทรต้องเป็นตัวเลข 10 หลัก และขึ้นต้นด้วย 0 เช่น 0812345678'
    if not is_valid_date(birth):
        return 'วันเกิดไม่ถูกต้อง กรุณากรอกแบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น 1990-05-01'
    if birth > date.today().isoformat():
        return 'วันเกิดต้องไม่เป็นวันในอนาคต\nถ้ากรอกเป็นปี พ.ศ. ให้ลบ 543 เป็นปี ค.ศ. ก่อน'
    if birth < '1900-01-01':
        return 'ปีเกิดต้องไม่ต่ำกว่า ค.ศ. 1900'
    return ''


def add_patient():
    name, phone, birth = read_form()
    message = check_form(name, phone, birth)
    if message != '':
        dialogs.show_warning('ข้อมูลไม่ถูกต้อง', message)
        return
    owner = database.fetch_one('SELECT patient_name FROM patients WHERE phone = ?', (phone,))
    if owner is not None:
        dialogs.show_warning('เบอร์โทรซ้ำ', 'เบอร์ ' + phone + ' เป็นของผู้ป่วย "' + owner[0] + '" อยู่แล้ว\nถ้าเป็นคนเดียวกัน ให้คลิกเลือกจากรายชื่อเพื่อแก้ไขแทน')
        return
    sql = '''INSERT INTO patients (patient_name, phone, birth_date)
        VALUES (?, ?, ?)'''
    try:
        new_id = database.insert(sql, (name, phone, birth))
    except sqlite3.Error as error:
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))
        return
    dialogs.show_info('ลงทะเบียนสำเร็จ', 'ลงทะเบียน "' + name + '" เรียบร้อย\nรหัสผู้ป่วย: ' + str(new_id))
    clear_form()
    ui['keyword_var'].set('')
    refresh()
    ui['tree'].see(str(new_id))


def update_patient():
    patient_id = ui['selected_id']
    if patient_id is None:
        dialogs.show_warning('ยังไม่ได้เลือกผู้ป่วย', 'กรุณาคลิกเลือกผู้ป่วยจากรายชื่อทางขวาก่อน')
        return
    name, phone, birth = read_form()
    message = check_form(name, phone, birth)
    if message != '':
        dialogs.show_warning('ข้อมูลไม่ถูกต้อง', message)
        return
    owner = database.fetch_one('SELECT patient_name FROM patients WHERE phone = ? AND patient_id <> ?', (phone, patient_id))
    if owner is not None:
        dialogs.show_warning('เบอร์โทรซ้ำ', 'เบอร์ ' + phone + ' เป็นของผู้ป่วย "' + owner[0] + '" อยู่แล้ว')
        return
    sql = '''UPDATE patients
        SET patient_name = ?, phone = ?, birth_date = ?
        WHERE patient_id = ?'''
    try:
        count = database.execute(sql, (name, phone, birth, patient_id))
    except sqlite3.Error as error:
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))
        return
    if count == 0:
        dialogs.show_warning('ไม่พบผู้ป่วย', 'ไม่พบผู้ป่วยรายนี้ในระบบแล้ว กรุณาโหลดรายชื่อใหม่')
        return
    dialogs.show_info('บันทึกสำเร็จ', 'แก้ไขข้อมูลของ "' + name + '" เรียบร้อย\n(คิวเดิมของผู้ป่วยไม่ต้องแก้ตาม เพราะคิวเก็บแค่รหัสผู้ป่วย)')
    clear_form()
    refresh()
    if ui['tree'].exists(str(patient_id)):
        ui['tree'].see(str(patient_id))
