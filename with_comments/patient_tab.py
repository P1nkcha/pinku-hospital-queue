# patient_tab.py : แท็บ "ผู้ป่วย" (ลำดับที่ 2 ลงทะเบียนผู้ป่วยใหม่ หรือแก้ไขข้อมูลผู้ป่วย)
# คลิกเลือกผู้ป่วยในตาราง จะเห็นประวัติการรักษาของคนนั้นด้านล่าง

import tkinter as tk  # ไลบรารีสร้างหน้าจอ
from tkinter import ttk  # widget แบบ ttk
import sqlite3  # ใช้จับ error ที่มาจากฐานข้อมูล
from datetime import date, datetime  # ใช้ตรวจวันเกิด
import database  # ฟังก์ชันเชื่อมต่อฐานข้อมูลจาก database.py
import dialogs  # หน้าต่างแจ้งเตือนแบบเข้าธีม
import theme  # สีและฟอนต์ของโปรแกรม
try:  # ลองโหลดปฏิทินเลือกวันที่ (ต้องติดตั้งเพิ่มด้วย python -m pip install tkcalendar)
    from tkcalendar import DateEntry  # ช่องกรอกวันที่ที่มีปฏิทินเลื่อนลง
except ImportError:  # ยังไม่ได้ติดตั้ง
    DateEntry = None  # main.py จะเห็นค่า None แล้วแจ้งวิธีติดตั้งเป็นภาษาไทย แทนการขึ้น error

ui = {}  # เก็บ widget และตัวแปรของแท็บนี้ ไว้ใช้ข้ามฟังก์ชัน


def create_tab(parent):  # สร้างหน้าตาแท็บ แล้วส่ง frame กลับไปให้ main.py
    frame = ttk.Frame(parent, padding=10)  # กรอบหลักของแท็บ

    top = ttk.Frame(frame)  # ครึ่งบน: ฟอร์มทางซ้าย และรายชื่อผู้ป่วยทางขวา
    top.pack(fill='both', expand=True)  # ขยายเต็มพื้นที่ที่เหลือจากประวัติการรักษา

    form = ttk.LabelFrame(top, text='ข้อมูลผู้ป่วย', padding=12)  # กรอบฟอร์มทางซ้าย
    form.pack(side='left', fill='y', padx=(0, 10))  # วางชิดซ้าย สูงเต็มครึ่งบน

    ui['name_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องชื่อ
    ui['phone_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องเบอร์โทร
    ui['birth_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องวันเกิด
    ui['mode_var'] = tk.StringVar(value='โหมด: ลงทะเบียนผู้ป่วยใหม่')  # ข้อความบอกว่ากำลังเพิ่มใหม่หรือแก้ไข
    ui['selected_id'] = None  # รหัสผู้ป่วยที่เลือกมาแก้ไข (None = ยังไม่ได้เลือก)
    ui['birth_from_user'] = False  # ช่องวันเกิดมีวันที่ที่ผู้ใช้เลือกหรือพิมพ์เอง (หรือโหลดจากฐานข้อมูล) แล้วหรือยัง

    ttk.Label(form, textvariable=ui['mode_var'], foreground=theme.PRIMARY_DARK).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 6))  # แสดงโหมดปัจจุบันเป็นสีหลักแบบเข้ม
    ttk.Label(form, text='ชื่อ-นามสกุล').grid(row=1, column=0, sticky='w', pady=4)  # ป้ายช่องชื่อ
    ttk.Entry(form, textvariable=ui['name_var'], width=28).grid(row=1, column=1, pady=4)  # ช่องกรอกชื่อ
    ttk.Label(form, text='เบอร์โทร').grid(row=2, column=0, sticky='w', pady=4)  # ป้ายช่องเบอร์โทร
    ttk.Entry(form, textvariable=ui['phone_var'], width=28).grid(row=2, column=1, pady=4)  # ช่องกรอกเบอร์โทร
    ttk.Label(form, text='วันเกิด').grid(row=3, column=0, sticky='w', pady=4)  # ป้ายช่องวันเกิด
    birth_entry = DateEntry(form, textvariable=ui['birth_var'], width=26, font=theme.FONT,  # ช่องวันเกิดแบบมีปฏิทินเลื่อนลง
                            date_pattern='yyyy-mm-dd', locale='th_TH', maxdate=date.today(),  # รูปแบบ YYYY-MM-DD ปี ค.ศ. ชื่อเดือนภาษาไทย ห้ามเลือกวันในอนาคต
                            firstweekday='sunday', showweeknumbers=False,  # สัปดาห์เริ่มวันอาทิตย์ ไม่แสดงเลขสัปดาห์
                            background=theme.PRIMARY, foreground=theme.TEXT, bordercolor=theme.SECONDARY,  # หัวปฏิทิน (เดือน ปี และลูกศรเลื่อนเดือน) พื้นชมพู ตัวสีเข้ม
                            headersbackground=theme.SECONDARY, headersforeground=theme.TEXT,  # แถวชื่อวัน พื้นสีรอง
                            normalbackground=theme.WHITE, normalforeground=theme.TEXT,  # วันธรรมดา พื้นขาว
                            weekendbackground=theme.WHITE, weekendforeground=theme.TEXT,  # วันเสาร์อาทิตย์ พื้นขาวเหมือนวันธรรมดา
                            othermonthbackground=theme.WHITE, othermonthwebackground=theme.WHITE,  # วันของเดือนก่อนหรือเดือนถัดไป พื้นขาว
                            othermonthforeground=theme.HINT, othermonthweforeground=theme.HINT,  # วันของเดือนอื่น ตัวสีเทา
                            selectbackground=theme.PRIMARY, selectforeground=theme.TEXT)  # วันที่เลือก พื้นชมพู ตัวสีเข้ม
    birth_entry.configure(validate='none')  # ปิดการแก้ค่าอัตโนมัติของ DateEntry: พิมพ์ผิดแล้วจะไม่ถูกเปลี่ยนเป็นวันนี้เงียบๆ ให้ check_form เตือนแทน
    birth_entry.delete(0, 'end')  # เริ่มต้นช่องว่าง (DateEntry ใส่วันนี้ให้เองตอนสร้าง)
    birth_entry.grid(row=3, column=1, pady=4)  # วางช่องวันเกิด
    birth_entry.bind('<<DateEntrySelected>>', on_birth_picked)  # เลือกวันจากปฏิทินแล้ว
    birth_entry.bind('<KeyRelease>', on_birth_typed)  # พิมพ์วันเกิดเอง
    birth_entry.bind('<ButtonPress-1>', on_birth_click, add='+')  # คลิกช่องวันเกิด (ทำงานต่อจากคำสั่งเปิดปฏิทินของ DateEntry)
    frame.bind_all('<ButtonPress-1>', on_any_click, add='+')  # คลิกที่อื่นในโปรแกรม = ปิดปฏิทินที่เปิดค้างไว้
    ui['birth_entry'] = birth_entry  # เก็บไว้ใช้ในฟังก์ชันอื่น
    ttk.Label(form, text='เลือกจากปฏิทิน หรือพิมพ์ เช่น 1990-05-01', foreground=theme.HINT).grid(row=4, column=1, sticky='w')  # วิธีกรอกวันเกิด (YYYY-MM-DD ปี ค.ศ.)

    ttk.Button(form, text='ลงทะเบียนผู้ป่วยใหม่', command=add_patient).grid(row=5, column=0, columnspan=2, sticky='we', pady=(12, 3))  # ปุ่มเพิ่มผู้ป่วยใหม่
    ttk.Button(form, text='บันทึกการแก้ไข', command=update_patient).grid(row=6, column=0, columnspan=2, sticky='we', pady=3)  # ปุ่มบันทึกการแก้ไข
    ttk.Button(form, text='ล้างฟอร์ม', style='Light.TButton', command=clear_form).grid(row=7, column=0, columnspan=2, sticky='we', pady=3)  # ปุ่มล้างช่องกรอก (ปุ่มรอง)

    right = ttk.Frame(top)  # กรอบด้านขวา ใส่ช่องค้นหาและตาราง
    right.pack(side='left', fill='both', expand=True)  # ขยายเต็มพื้นที่ที่เหลือ

    search_bar = ttk.Frame(right)  # แถบค้นหาด้านบน
    search_bar.pack(fill='x')  # กว้างเต็มกรอบ
    ttk.Label(search_bar, text='ค้นหาชื่อหรือเบอร์โทร').pack(side='left')  # ป้ายช่องค้นหา
    ui['keyword_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องค้นหา
    keyword_entry = ttk.Entry(search_bar, textvariable=ui['keyword_var'], width=25)  # ช่องกรอกคำค้น
    keyword_entry.pack(side='left', padx=6)  # วางต่อจากป้าย
    keyword_entry.bind('<Return>', on_keyword_enter)  # กด Enter ในช่องค้นหา = ค้นหา
    ttk.Button(search_bar, text='ค้นหา', command=refresh).pack(side='left')  # ปุ่มค้นหา
    ttk.Button(search_bar, text='แสดงทั้งหมด', style='Light.TButton', command=show_all).pack(side='left', padx=6)  # ปุ่มแสดงผู้ป่วยทุกคน (ปุ่มรอง)

    ttk.Label(right, text='คลิกที่รายชื่อเพื่อนำข้อมูลขึ้นฟอร์มสำหรับแก้ไข และดูประวัติการรักษา', foreground=theme.HINT).pack(anchor='w', pady=(6, 4))  # คำแนะนำการใช้งาน

    table = ttk.Frame(right)  # กรอบใส่ตารางกับแถบเลื่อน
    table.pack(fill='both', expand=True)  # ขยายเต็มพื้นที่
    columns = ('id', 'name', 'phone', 'birth')  # ชื่อคอลัมน์ภายในโปรแกรม
    tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse', height=7)  # ตารางแสดงรายชื่อ เลือกได้ทีละแถว สูง 7 แถว
    tree.heading('id', text='รหัส')  # หัวคอลัมน์รหัส
    tree.heading('name', text='ชื่อ-นามสกุล')  # หัวคอลัมน์ชื่อ
    tree.heading('phone', text='เบอร์โทร')  # หัวคอลัมน์เบอร์โทร
    tree.heading('birth', text='วันเกิด')  # หัวคอลัมน์วันเกิด
    tree.column('id', width=60, anchor='center')  # ความกว้างคอลัมน์รหัส
    tree.column('name', width=220)  # ความกว้างคอลัมน์ชื่อ
    tree.column('phone', width=130, anchor='center')  # ความกว้างคอลัมน์เบอร์โทร
    tree.column('birth', width=120, anchor='center')  # ความกว้างคอลัมน์วันเกิด
    scroll = ttk.Scrollbar(table, orient='vertical', command=tree.yview)  # แถบเลื่อนแนวตั้ง
    tree.configure(yscrollcommand=scroll.set)  # ผูกตารางกับแถบเลื่อน
    tree.pack(side='left', fill='both', expand=True)  # วางตาราง
    scroll.pack(side='left', fill='y')  # วางแถบเลื่อนข้างตาราง
    tree.bind('<<TreeviewSelect>>', on_select)  # คลิกเลือกแถว = นำข้อมูลขึ้นฟอร์ม
    ui['tree'] = tree  # เก็บตารางไว้ใช้ในฟังก์ชันอื่น

    history = ttk.LabelFrame(frame, text='ประวัติการรักษา', padding=8)  # ครึ่งล่าง: ประวัติการรักษาของผู้ป่วยที่เลือก
    history.pack(fill='x', pady=(8, 0))  # กว้างเต็มแท็บ ใต้ฟอร์มและรายชื่อ
    ui['history_text'] = tk.StringVar()  # ข้อความบอกว่ากำลังดูประวัติของใคร หรือยังไม่มีประวัติ
    ttk.Label(history, textvariable=ui['history_text'], foreground=theme.PRIMARY_DARK).pack(anchor='w', pady=(0, 4))  # แสดงข้อความ
    history_table = ttk.Frame(history)  # กรอบใส่ตารางประวัติกับแถบเลื่อน
    history_table.pack(fill='x')  # กว้างเต็มกรอบ
    history_columns = ('date', 'doctor', 'dept', 'diagnosis', 'treatment')  # ชื่อคอลัมน์ภายในโปรแกรม
    history_tree = ttk.Treeview(history_table, columns=history_columns, show='headings', selectmode='none', height=4)  # ตารางประวัติ ดูอย่างเดียว ไม่ต้องเลือกแถว สูง 4 แถว (เกินนี้เลื่อนดูได้)
    history_tree.heading('date', text='วันที่')  # วันที่มาตรวจ (วันนัดของคิว)
    history_tree.heading('doctor', text='แพทย์')  # แพทย์ที่ตรวจ
    history_tree.heading('dept', text='แผนก')  # แผนกของแพทย์
    history_tree.heading('diagnosis', text='ผลวินิจฉัย')  # ผลวินิจฉัย
    history_tree.heading('treatment', text='การรักษา')  # การรักษา
    history_tree.column('date', width=95, anchor='center')  # ความกว้างคอลัมน์วันที่
    history_tree.column('doctor', width=170)  # ความกว้างคอลัมน์แพทย์
    history_tree.column('dept', width=120)  # ความกว้างคอลัมน์แผนก
    history_tree.column('diagnosis', width=210)  # ความกว้างคอลัมน์ผลวินิจฉัย
    history_tree.column('treatment', width=400)  # คอลัมน์การรักษากว้างสุด เพราะข้อความยาว
    history_scroll = ttk.Scrollbar(history_table, orient='vertical', command=history_tree.yview)  # แถบเลื่อนแนวตั้ง
    history_tree.configure(yscrollcommand=history_scroll.set)  # ผูกตารางกับแถบเลื่อน
    history_tree.pack(side='left', fill='x', expand=True)  # วางตาราง
    history_scroll.pack(side='left', fill='y')  # วางแถบเลื่อนข้างตาราง
    ui['history_tree'] = history_tree  # เก็บตารางไว้ใช้ในฟังก์ชันอื่น

    refresh()  # โหลดรายชื่อผู้ป่วยครั้งแรก
    return frame  # ส่ง frame กลับไปให้ main.py ใส่ลงแท็บ


def refresh():  # โหลดรายชื่อผู้ป่วยตามคำค้น (ช่องค้นหาว่าง = แสดงทุกคน)
    keyword = ui['keyword_var'].get().strip()  # คำค้นที่ผู้ใช้พิมพ์ ตัดช่องว่างหัวท้าย
    pattern = '%' + keyword + '%'  # % คือ "อะไรก็ได้" จึงค้นเจอแม้พิมพ์แค่บางส่วน (ต่อกับค่า ไม่ได้ต่อเข้าคำสั่ง SQL)
    sql = '''SELECT patient_id, patient_name, phone, birth_date  -- ข้อมูลที่จะแสดงในตาราง
        FROM patients                                           -- จากตารางผู้ป่วย
        WHERE patient_name LIKE ? OR phone LIKE ?               -- ชื่อหรือเบอร์มีคำค้นอยู่
        ORDER BY patient_id'''  # เรียงตามรหัสผู้ป่วย
    rows = database.fetch_all(sql, (pattern, pattern))  # ส่งคำค้นแทน ? ทั้ง 2 ตัว
    tree = ui['tree']  # ตารางรายชื่อ
    for item in tree.get_children():  # ทุกแถวเดิมในตาราง
        tree.delete(item)  # ลบออกก่อนใส่ข้อมูลใหม่
    for row in rows:  # ทุกแถวที่ได้จากฐานข้อมูล
        tree.insert('', 'end', iid=str(row[0]), values=row)  # ใส่ลงตาราง ใช้รหัสผู้ป่วยเป็น iid ของแถว
    load_history(ui['selected_id'])  # โหลดประวัติของผู้ป่วยที่เลือกค้างไว้ใหม่ (อาจเพิ่งบันทึกตรวจแล้วจากแท็บอื่น)


def load_history(patient_id):  # แสดงประวัติการรักษาของผู้ป่วย (None = ยังไม่ได้เลือกผู้ป่วย)
    history_tree = ui['history_tree']  # ตารางประวัติการรักษา
    for item in history_tree.get_children():  # ทุกแถวเดิมในตาราง
        history_tree.delete(item)  # ลบออกก่อนใส่ข้อมูลใหม่
    if patient_id is None:  # ยังไม่ได้เลือกผู้ป่วย
        ui['history_text'].set('คลิกเลือกผู้ป่วยในตารางด้านบน เพื่อดูประวัติการรักษา')  # บอกวิธีดูประวัติ
        return  # ไม่ต้องโหลดอะไร
    patient = database.fetch_one('SELECT patient_name FROM patients WHERE patient_id = ?', (patient_id,))  # ชื่อผู้ป่วย
    if patient is None:  # ไม่พบผู้ป่วย (ถูกลบไปจากที่อื่น)
        ui['history_text'].set('ไม่พบผู้ป่วยรายนี้ในระบบแล้ว')  # แจ้งในข้อความ
        return  # หยุด
    sql = '''SELECT s.work_date, d.doctor_name, dp.dept_name,              -- วันที่ตรวจ แพทย์ แผนก
            t.diagnosis, IFNULL(t.treatment, '-')                          -- ผลวินิจฉัย และการรักษา (ไม่ได้กรอก แสดงเป็น -)
        FROM treatments t                                                  -- เริ่มจากตารางผลการรักษา
        JOIN appointments a ON t.appt_id     = a.appt_id                   -- ต่อเพื่อรู้ว่าเป็นคิวของผู้ป่วยคนไหน
        JOIN schedules s    ON a.schedule_id = s.schedule_id               -- ต่อเพื่อดูวันที่ตรวจ
        JOIN doctors d      ON s.doctor_id   = d.doctor_id                 -- ต่อเพื่อดูชื่อแพทย์
        JOIN departments dp ON d.dept_id     = dp.dept_id                  -- ต่อเพื่อดูชื่อแผนก
        WHERE a.patient_id = ?                                             -- เฉพาะผู้ป่วยที่เลือก (patient_id อยู่ใน appointments ไม่ได้เก็บซ้ำใน treatments)
        ORDER BY s.work_date DESC, s.slot_time DESC'''  # เรียงจากครั้งล่าสุดไปเก่าสุด
    rows = database.fetch_all(sql, (patient_id,))  # ประวัติทุกครั้งของผู้ป่วยคนนี้
    for row in rows:  # ทุกครั้งที่มาตรวจ
        history_tree.insert('', 'end', values=row)  # ใส่ลงตาราง
    if len(rows) == 0:  # ยังไม่เคยมีผลการรักษา
        ui['history_text'].set(patient[0] + ' ยังไม่มีประวัติการรักษา')  # บอกว่ายังไม่มีประวัติ
    else:  # มีประวัติ
        ui['history_text'].set(patient[0] + ' มีประวัติการรักษา ' + str(len(rows)) + ' ครั้ง (เรียงจากล่าสุด)')  # บอกชื่อและจำนวนครั้ง


def on_keyword_enter(event):  # กด Enter ในช่องค้นหา
    refresh()  # ค้นหาทันที


def show_all():  # ปุ่ม "แสดงทั้งหมด"
    ui['keyword_var'].set('')  # ล้างคำค้น
    refresh()  # โหลดผู้ป่วยทุกคน


def on_select(event):  # คลิกเลือกผู้ป่วยในตาราง แล้วนำข้อมูลขึ้นฟอร์มเพื่อแก้ไข
    selected = ui['tree'].selection()  # แถวที่ถูกเลือก
    if len(selected) == 0:  # ถ้าไม่มีแถวที่เลือก (เช่น เพิ่งล้างฟอร์ม)
        return  # ไม่ต้องทำอะไร
    patient_id = int(selected[0])  # iid ของแถว = รหัสผู้ป่วย
    sql = '''SELECT patient_name, phone, birth_date  -- ข้อมูลที่จะนำขึ้นฟอร์ม
        FROM patients                                                     -- จากตารางผู้ป่วย
        WHERE patient_id = ?'''  # ดึงจากฐานข้อมูลโดยตรง เพราะค่าที่อ่านจาก Treeview จะแปลงเบอร์เป็นตัวเลขจนเลข 0 ข้างหน้าหาย
    row = database.fetch_one(sql, (patient_id,))  # ได้ข้อมูลผู้ป่วย 1 แถว
    if row is None:  # ถ้าไม่พบ (ถูกลบไปจากที่อื่น)
        return  # ไม่ต้องทำอะไร
    ui['selected_id'] = patient_id  # จำว่ากำลังแก้ไขผู้ป่วยคนไหน
    ui['name_var'].set(row[0])  # ใส่ชื่อในฟอร์ม
    ui['phone_var'].set(row[1])  # ใส่เบอร์โทรในฟอร์ม
    ui['birth_var'].set(row[2])  # ใส่วันเกิดเดิมในฟอร์ม (แสดงในช่อง DateEntry)
    ui['birth_from_user'] = True  # วันเกิดมาจากฐานข้อมูล เปิดปฏิทินแล้วจะแสดงวันนี้ให้
    ui['mode_var'].set('โหมด: แก้ไขข้อมูลผู้ป่วยรหัส ' + str(patient_id))  # เปลี่ยนข้อความบอกโหมด
    load_history(patient_id)  # แสดงประวัติการรักษาของผู้ป่วยคนนี้


def clear_form():  # ปุ่ม "ล้างฟอร์ม" กลับไปโหมดลงทะเบียนใหม่
    ui['name_var'].set('')  # ล้างชื่อ
    ui['phone_var'].set('')  # ล้างเบอร์โทร
    ui['birth_var'].set('')  # ล้างวันเกิด (ช่องว่าง ไม่ใส่วันนี้ให้)
    ui['birth_from_user'] = False  # ยังไม่มีวันเกิดที่ผู้ใช้เลือก
    ui['selected_id'] = None  # ยกเลิกการเลือกผู้ป่วย
    ui['mode_var'].set('โหมด: ลงทะเบียนผู้ป่วยใหม่')  # กลับเป็นโหมดเพิ่มใหม่
    ui['tree'].selection_remove(ui['tree'].selection())  # ยกเลิกแถวที่ไฮไลต์ในตาราง
    load_history(None)  # ล้างตารางประวัติการรักษา


def on_birth_picked(event):  # เลือกวันเกิดจากปฏิทินแล้ว
    ui['birth_from_user'] = True  # จำว่าผู้ใช้เลือกวันเกิดเอง


def on_birth_typed(event):  # พิมพ์ในช่องวันเกิด
    birth = ui['birth_var'].get().strip()  # ข้อความที่พิมพ์อยู่ตอนนี้
    ui['birth_from_user'] = is_valid_date(birth) and birth <= date.today().isoformat()  # นับว่ามีวันเกิดแล้ว เมื่อพิมพ์ครบเป็นวันที่จริงที่ไม่ใช่วันในอนาคต


def on_birth_click(event):  # คลิกช่องวันเกิด (DateEntry เปิดปฏิทินไปก่อนแล้ว ถ้าคลิกที่ลูกศร)
    clicked_arrow = 'downarrow' in ui['birth_entry'].identify(event.x, event.y)  # ตรวจว่าคลิกที่ลูกศรเปิดปฏิทินหรือไม่
    if clicked_arrow and not ui['birth_from_user']:  # เปิดปฏิทินตอนที่ช่องยังไม่มีวันเกิดที่ถูกต้อง
        ui['birth_var'].set('')  # DateEntry เติมวันที่ให้เองตอนเปิดปฏิทิน ล้างออก กันบันทึกเป็นวันนี้โดยไม่ตั้งใจ (ถ้าไม่เลือกวัน ช่องจะยังว่าง)


def on_any_click(event):  # คลิกที่ใดก็ได้ในโปรแกรม (DateEntry ไม่ปิดปฏิทินเองเมื่อคลิกช่องอื่นหรือปุ่มอื่น)
    popup = ui['birth_entry'].winfo_children()[0]  # หน้าต่างปฏิทินเลื่อนลงที่ DateEntry สร้างไว้ (ซ่อนอยู่ถ้ายังไม่เปิด)
    clicked_inside = str(event.widget).startswith(str(ui['birth_entry']))  # คลิกที่ช่องวันเกิดหรือในปฏิทินเอง (ชื่อ widget ขึ้นต้นด้วยชื่อช่องวันเกิด)
    if popup.winfo_ismapped() and not clicked_inside:  # ปฏิทินเปิดอยู่ แต่คลิกที่อื่น
        popup.withdraw()  # ปิดปฏิทิน (ถ้ายังไม่ได้เลือกวัน ช่องวันเกิดยังเหมือนเดิม)
        ui['birth_entry'].state(['!pressed'])  # ให้ลูกศรกลับเป็นแบบปกติ


def read_form():  # อ่านค่าจากฟอร์ม และจัดรูปแบบให้เรียบร้อย
    name = ui['name_var'].get().strip()  # ชื่อ ตัดช่องว่างหัวท้าย
    phone = ui['phone_var'].get().replace('-', '').replace(' ', '')  # เบอร์โทร ตัดขีดและช่องว่างออก (081-234-5678 -> 0812345678)
    birth = ui['birth_var'].get().strip()  # วันเกิด ตัดช่องว่างหัวท้าย
    return name, phone, birth  # ส่งค่าทั้ง 3 กลับ


def is_phone(phone):  # ตรวจว่าเบอร์เป็นตัวเลข 0-9 จำนวน 10 ตัว และขึ้นต้นด้วย 0
    if len(phone) != 10:  # ต้องยาว 10 ตัวพอดี
        return False  # ไม่ผ่าน
    if phone[0] != '0':  # ตัวแรกต้องเป็น 0
        return False  # ไม่ผ่าน
    for ch in phone:  # ตรวจทีละตัวอักษร
        if ch not in '0123456789':  # ใช้วิธีนี้แทน isdigit() เพราะ isdigit() ยอมรับเลขไทย ๐-๙ ด้วย
            return False  # มีตัวที่ไม่ใช่เลขอารบิก
    return True  # ผ่านทุกข้อ


def is_valid_date(text):  # ตรวจว่าเป็นวันที่จริงในรูปแบบ YYYY-MM-DD
    if len(text) != 10:  # ต้องยาว 10 ตัวพอดี เช่น 1990-05-01
        return False  # ไม่ผ่าน
    try:  # ลองแปลงข้อความเป็นวันที่
        datetime.strptime(text, '%Y-%m-%d')  # ถ้าไม่ใช่วันที่จริง เช่น 2026-02-30 จะเกิด ValueError
    except ValueError:  # แปลงไม่ได้
        return False  # ไม่ผ่าน
    return True  # เป็นวันที่ที่ถูกต้อง


def check_form(name, phone, birth):  # ตรวจข้อมูลในฟอร์ม คืนข้อความเตือน หรือ '' ถ้าถูกต้องทั้งหมด
    if name == '' or phone == '' or birth == '':  # มีช่องว่าง
        return 'กรุณากรอกชื่อ-นามสกุล เบอร์โทร และวันเกิดให้ครบ'  # เตือนให้กรอกให้ครบ
    if not is_phone(phone):  # เบอร์ผิดรูปแบบ
        return 'เบอร์โทรต้องเป็นตัวเลข 10 หลัก และขึ้นต้นด้วย 0 เช่น 0812345678'  # บอกรูปแบบที่ถูก
    if not is_valid_date(birth):  # วันเกิดผิดรูปแบบหรือไม่มีวันนี้จริง
        return 'วันเกิดไม่ถูกต้อง กรุณากรอกแบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น 1990-05-01'  # บอกรูปแบบที่ถูก
    if birth > date.today().isoformat():  # วันเกิดเลยวันนี้ไปแล้ว (เทียบข้อความ YYYY-MM-DD ได้เลย)
        return 'วันเกิดต้องไม่เป็นวันในอนาคต\nถ้ากรอกเป็นปี พ.ศ. ให้ลบ 543 เป็นปี ค.ศ. ก่อน'  # มักเกิดจากกรอกปี พ.ศ.
    if birth < '1900-01-01':  # ปีเก่าเกินจริง
        return 'ปีเกิดต้องไม่ต่ำกว่า ค.ศ. 1900'  # กันพิมพ์ปีผิด
    return ''  # ไม่มีข้อผิดพลาด


def add_patient():  # ปุ่ม "ลงทะเบียนผู้ป่วยใหม่"
    name, phone, birth = read_form()  # อ่านค่าจากฟอร์ม
    message = check_form(name, phone, birth)  # ตรวจข้อมูล
    if message != '':  # ถ้ามีข้อผิดพลาด
        dialogs.show_warning('ข้อมูลไม่ถูกต้อง', message)  # แจ้งเตือนภาษาไทย
        return  # หยุด ไม่บันทึก
    owner = database.fetch_one('SELECT patient_name FROM patients WHERE phone = ?', (phone,))  # ตรวจว่าเบอร์นี้มีคนใช้แล้วหรือยัง
    if owner is not None:  # เบอร์ซ้ำ
        dialogs.show_warning('เบอร์โทรซ้ำ', 'เบอร์ ' + phone + ' เป็นของผู้ป่วย "' + owner[0] + '" อยู่แล้ว\nถ้าเป็นคนเดียวกัน ให้คลิกเลือกจากรายชื่อเพื่อแก้ไขแทน')  # บอกว่าซ้ำกับใคร
        return  # หยุด ไม่บันทึก
    sql = '''INSERT INTO patients (patient_name, phone, birth_date)  -- เพิ่มผู้ป่วยใหม่ 1 แถว
        VALUES (?, ?, ?)'''  # ค่าทั้ง 3 ส่งแทน ? ไม่ต่อเข้าคำสั่ง
    try:  # ลองบันทึก
        new_id = database.insert(sql, (name, phone, birth))  # บันทึก และได้รหัสผู้ป่วยใหม่กลับมา
    except sqlite3.Error as error:  # ฐานข้อมูลไม่ยอมบันทึก
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))  # แสดงเหตุผลเป็นภาษาไทย
        return  # หยุด
    dialogs.show_info('ลงทะเบียนสำเร็จ', 'ลงทะเบียน "' + name + '" เรียบร้อย\nรหัสผู้ป่วย: ' + str(new_id))  # แจ้งผลสำเร็จ
    clear_form()  # ล้างฟอร์มพร้อมรับคนต่อไป
    ui['keyword_var'].set('')  # ล้างคำค้น ให้เห็นผู้ป่วยทุกคน
    refresh()  # โหลดตารางใหม่
    ui['tree'].see(str(new_id))  # เลื่อนตารางไปที่ผู้ป่วยคนใหม่


def update_patient():  # ปุ่ม "บันทึกการแก้ไข"
    patient_id = ui['selected_id']  # รหัสผู้ป่วยที่เลือกไว้
    if patient_id is None:  # ยังไม่ได้เลือกใคร
        dialogs.show_warning('ยังไม่ได้เลือกผู้ป่วย', 'กรุณาคลิกเลือกผู้ป่วยจากรายชื่อทางขวาก่อน')  # บอกวิธีเลือก
        return  # หยุด
    name, phone, birth = read_form()  # อ่านค่าจากฟอร์ม
    message = check_form(name, phone, birth)  # ตรวจข้อมูลแบบเดียวกับตอนลงทะเบียน
    if message != '':  # ถ้ามีข้อผิดพลาด
        dialogs.show_warning('ข้อมูลไม่ถูกต้อง', message)  # แจ้งเตือนภาษาไทย
        return  # หยุด
    owner = database.fetch_one('SELECT patient_name FROM patients WHERE phone = ? AND patient_id <> ?', (phone, patient_id))  # หาคนอื่นที่ใช้เบอร์นี้ (ไม่นับตัวเอง)
    if owner is not None:  # เบอร์ซ้ำกับคนอื่น
        dialogs.show_warning('เบอร์โทรซ้ำ', 'เบอร์ ' + phone + ' เป็นของผู้ป่วย "' + owner[0] + '" อยู่แล้ว')  # บอกว่าซ้ำกับใคร
        return  # หยุด
    sql = '''UPDATE patients                              -- แก้ข้อมูลผู้ป่วย
        SET patient_name = ?, phone = ?, birth_date = ?   -- ค่าใหม่ทั้ง 3 ช่อง
        WHERE patient_id = ?'''  # เฉพาะผู้ป่วยที่เลือก
    try:  # ลองบันทึก
        count = database.execute(sql, (name, phone, birth, patient_id))  # รันคำสั่ง ได้จำนวนแถวที่ถูกแก้
    except sqlite3.Error as error:  # ฐานข้อมูลไม่ยอมบันทึก
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))  # แสดงเหตุผลเป็นภาษาไทย
        return  # หยุด
    if count == 0:  # ไม่มีแถวไหนถูกแก้
        dialogs.show_warning('ไม่พบผู้ป่วย', 'ไม่พบผู้ป่วยรายนี้ในระบบแล้ว กรุณาโหลดรายชื่อใหม่')  # อาจถูกลบจากที่อื่น
        return  # หยุด
    dialogs.show_info('บันทึกสำเร็จ', 'แก้ไขข้อมูลของ "' + name + '" เรียบร้อย\n(คิวเดิมของผู้ป่วยไม่ต้องแก้ตาม เพราะคิวเก็บแค่รหัสผู้ป่วย)')  # แจ้งผลสำเร็จ
    clear_form()  # ล้างฟอร์ม
    refresh()  # โหลดตารางใหม่ให้เห็นข้อมูลที่แก้
    if ui['tree'].exists(str(patient_id)):  # ถ้าผู้ป่วยคนนี้ยังอยู่ในผลค้นหาปัจจุบัน
        ui['tree'].see(str(patient_id))  # เลื่อนตารางไปที่ผู้ป่วยที่เพิ่งแก้
