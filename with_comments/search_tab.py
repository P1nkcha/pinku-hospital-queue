# search_tab.py : แท็บ "ค้นหาและจัดการคิว" (ลำดับที่ 4 และ 5)
# ค้นหาคิวด้วยชื่อ (พิมพ์บางส่วนก็ได้) เบอร์โทร หรือวันที่  แล้วยกเลิกคิวหรือบันทึกว่าตรวจแล้ว

import tkinter as tk  # ไลบรารีสร้างหน้าจอ
from tkinter import ttk  # widget แบบ ttk
import sqlite3  # ใช้จับ error ที่มาจากฐานข้อมูล
from datetime import date, datetime  # ใช้หาวันนี้และตรวจรูปแบบวันที่
import database  # ฟังก์ชันเชื่อมต่อฐานข้อมูลจาก database.py
import header_bar  # แถบหัวโปรแกรม (อัปเดตตัวเลขสรุปวันนี้หลังยกเลิกหรือตรวจแล้ว)
import dialogs  # หน้าต่างแจ้งเตือนแบบเข้าธีม
import theme  # สีและฟอนต์ของโปรแกรม

ui = {}  # เก็บ widget และตัวแปรของแท็บนี้ ไว้ใช้ข้ามฟังก์ชัน
form = {}  # เก็บ widget และค่าของหน้าต่างกรอกผลการรักษา


def create_tab(parent):  # สร้างหน้าตาแท็บ แล้วส่ง frame กลับไปให้ main.py
    frame = ttk.Frame(parent, padding=10)  # กรอบหลักของแท็บ

    box = ttk.LabelFrame(frame, text='ค้นหาคิว (กรอกช่องไหนก็ได้ ถ้ากรอกหลายช่อง ต้องตรงทุกช่อง)', padding=10)  # กรอบเงื่อนไขค้นหา
    box.pack(fill='x')  # กว้างเต็มแท็บ
    ui['name_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องชื่อ
    ui['phone_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องเบอร์โทร
    ui['date_var'] = tk.StringVar(value=date.today().isoformat())  # ตัวแปรผูกกับช่องวันที่ เริ่มต้นเป็นวันนี้
    ttk.Label(box, text='ชื่อผู้ป่วย').grid(row=0, column=0, sticky='w')  # ป้ายช่องชื่อ
    name_entry = ttk.Entry(box, textvariable=ui['name_var'], width=13)  # ช่องกรอกชื่อ (บางส่วนก็ได้)
    name_entry.grid(row=0, column=1, padx=(5, 10))  # วางช่องชื่อ
    ttk.Label(box, text='เบอร์โทร').grid(row=0, column=2, sticky='w')  # ป้ายช่องเบอร์โทร
    phone_entry = ttk.Entry(box, textvariable=ui['phone_var'], width=11)  # ช่องกรอกเบอร์โทร
    phone_entry.grid(row=0, column=3, padx=(5, 10))  # วางช่องเบอร์โทร
    ttk.Label(box, text='วันที่ (YYYY-MM-DD)').grid(row=0, column=4, sticky='w')  # ป้ายช่องวันที่
    date_entry = ttk.Entry(box, textvariable=ui['date_var'], width=11)  # ช่องกรอกวันที่
    date_entry.grid(row=0, column=5, padx=5)  # วางช่องวันที่
    ttk.Button(box, text='วันนี้', style='Light.TButton', command=set_today).grid(row=0, column=6, padx=(0, 10))  # ปุ่มใส่วันที่ของวันนี้ (ปุ่มรอง)
    ttk.Button(box, text='ค้นหา', command=search).grid(row=0, column=7)  # ปุ่มค้นหา
    ttk.Button(box, text='ล้างเงื่อนไข', style='Light.TButton', command=clear_search).grid(row=0, column=8, padx=5)  # ปุ่มล้างช่องค้นหาทั้งหมด (ปุ่มรอง)
    name_entry.bind('<Return>', on_enter)  # กด Enter ในช่องชื่อ = ค้นหา
    phone_entry.bind('<Return>', on_enter)  # กด Enter ในช่องเบอร์ = ค้นหา
    date_entry.bind('<Return>', on_enter)  # กด Enter ในช่องวันที่ = ค้นหา

    ui['result_text'] = tk.StringVar()  # ข้อความสรุปผลการค้นหา
    ttk.Label(frame, textvariable=ui['result_text'], foreground=theme.PRIMARY_DARK).pack(anchor='w', pady=(8, 4))  # แสดงสรุปผล

    table = ttk.Frame(frame)  # กรอบใส่ตารางกับแถบเลื่อน
    table.pack(fill='both', expand=True)  # ขยายเต็มพื้นที่
    columns = ('appt_id', 'work_date', 'slot_time', 'patient', 'phone', 'doctor', 'dept', 'symptom', 'status')  # ชื่อคอลัมน์ภายในโปรแกรม
    headings = ('คิว', 'วันที่', 'เวลา', 'ผู้ป่วย', 'เบอร์โทร', 'แพทย์', 'แผนก', 'อาการ', 'สถานะ')  # หัวคอลัมน์ภาษาไทย
    widths = (45, 95, 55, 150, 100, 160, 110, 125, 75)  # ความกว้างเริ่มต้น รวม 915 พิกเซล พอดีหน้าต่าง 1100 โดยไม่ต้องเลื่อนแนวนอน
    tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse', style='Queue.Treeview')  # ตารางผลการค้นหา เลือกได้ทีละแถว ใช้สไตล์ตารางคิว (แถวที่เลือกเป็นสีชมพู)
    for i in range(len(columns)):  # ตั้งค่าทีละคอลัมน์
        tree.heading(columns[i], text=headings[i])  # ใส่หัวคอลัมน์
        tree.column(columns[i], width=widths[i], minwidth=40, stretch=True)  # ตั้งความกว้าง และให้ยืดตามขนาดหน้าต่าง (หน้าต่างกว้างขึ้น คอลัมน์กว้างตาม)
    for name in ('appt_id', 'work_date', 'slot_time', 'phone', 'status'):  # คอลัมน์ที่ควรจัดกึ่งกลาง
        tree.column(name, anchor='center')  # จัดกึ่งกลาง
    tree.tag_configure('booked', background=theme.BOOKED_BG, foreground=theme.TEXT)  # แถวที่จองแล้ว = พื้นส้มอ่อน ตัวหนังสือสีเข้มปกติ
    tree.tag_configure('done', background=theme.DONE_BG, foreground=theme.TEXT)  # แถวที่ตรวจแล้ว = พื้นเขียวอ่อน ตัวหนังสือสีเข้มปกติ
    tree.tag_configure('cancelled', background=theme.CANCELLED_BG, foreground=theme.TEXT)  # แถวที่ยกเลิก = พื้นเทาอ่อน ตัวหนังสือสีเข้มปกติ (แถวที่คลิกเลือกเป็นพื้นชมพู ตัวหนังสือยังอ่านชัด)
    scroll_y = ttk.Scrollbar(table, orient='vertical', command=tree.yview)  # แถบเลื่อนแนวตั้ง
    scroll_x = ttk.Scrollbar(table, orient='horizontal', command=tree.xview)  # แถบเลื่อนแนวนอน (จอเล็ก)
    tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)  # ผูกตารางกับแถบเลื่อน
    tree.grid(row=0, column=0, sticky='nsew')  # วางตาราง
    scroll_y.grid(row=0, column=1, sticky='ns')  # วางแถบเลื่อนแนวตั้งทางขวา
    scroll_x.grid(row=1, column=0, sticky='ew')  # วางแถบเลื่อนแนวนอนด้านล่าง
    table.rowconfigure(0, weight=1)  # ให้ตารางยืดตามความสูง
    table.columnconfigure(0, weight=1)  # ให้ตารางยืดตามความกว้าง
    ui['tree'] = tree  # เก็บตารางไว้ใช้ในฟังก์ชันอื่น

    actions = ttk.Frame(frame)  # แถวปุ่มจัดการคิวด้านล่าง
    actions.pack(fill='x', pady=(10, 0))  # เว้นระยะด้านบน
    ttk.Label(actions, text='จัดการคิวที่เลือก:').pack(side='left')  # ป้ายนำ
    ttk.Button(actions, text='ยกเลิกคิว', style='Danger.TButton', command=cancel_appointment).pack(side='left', padx=8, ipady=3)  # ปุ่มยกเลิกคิว ใช้สีเน้น
    ttk.Button(actions, text='บันทึกว่าตรวจแล้ว', command=mark_done).pack(side='left', ipady=3)  # ปุ่มเปลี่ยนสถานะเป็นตรวจแล้ว
    ttk.Label(actions, text='สีส้ม = จองแล้ว · สีเขียว = ตรวจแล้ว · สีเทา = ยกเลิก', foreground=theme.HINT).pack(side='right')  # คำอธิบายสีของแถวในตาราง

    load_results()  # เปิดแท็บครั้งแรก แสดงคิวของวันนี้
    return frame  # ส่ง frame กลับไปให้ main.py ใส่ลงแท็บ


def is_valid_date(text):  # ตรวจว่าเป็นวันที่จริงในรูปแบบ YYYY-MM-DD
    if len(text) != 10:  # ต้องยาว 10 ตัวพอดี เช่น 2026-10-22
        return False  # ไม่ผ่าน
    try:  # ลองแปลงข้อความเป็นวันที่
        datetime.strptime(text, '%Y-%m-%d')  # ถ้าไม่ใช่วันที่จริง จะเกิด ValueError
    except ValueError:  # แปลงไม่ได้
        return False  # ไม่ผ่าน
    return True  # เป็นวันที่ที่ถูกต้อง


def read_conditions():  # อ่านเงื่อนไขค้นหาจากช่องกรอกทั้ง 3 ช่อง
    name = ui['name_var'].get().strip()  # ชื่อ (บางส่วนก็ได้)
    phone = ui['phone_var'].get().replace('-', '').replace(' ', '')  # เบอร์โทร ตัดขีดและช่องว่าง
    work_date = ui['date_var'].get().strip()  # วันที่
    return name, phone, work_date  # ส่งค่าทั้ง 3 กลับ


def load_results():  # ค้นหาคิวจากฐานข้อมูลตามเงื่อนไขในช่องกรอก แล้วแสดงในตาราง
    name, phone, work_date = read_conditions()  # อ่านเงื่อนไข
    sql = '''SELECT a.appt_id, s.work_date, s.slot_time, p.patient_name, p.phone,  -- ข้อมูลคิว
            d.doctor_name, dp.dept_name, IFNULL(a.symptom, '-'), a.status          -- ไม่ได้กรอกอาการ แสดงเป็น -
        FROM appointments a                                               -- เริ่มจากตารางการจองคิว
        JOIN patients p     ON a.patient_id  = p.patient_id                         -- ต่อเพื่อดูชื่อและเบอร์ผู้ป่วย
        JOIN schedules s    ON a.schedule_id = s.schedule_id                        -- ต่อเพื่อดูวันและเวลา
        JOIN doctors d      ON s.doctor_id   = d.doctor_id                          -- ต่อเพื่อดูชื่อแพทย์
        JOIN departments dp ON d.dept_id     = dp.dept_id                           -- ต่อเพื่อดูชื่อแผนก
        WHERE (? = '' OR p.patient_name LIKE ?)                                     -- ช่องชื่อว่าง = ไม่กรองชื่อ
          AND (? = '' OR p.phone = ?)                                               -- ช่องเบอร์ว่าง = ไม่กรองเบอร์
          AND (? = '' OR s.work_date = ?)                                           -- ช่องวันที่ว่าง = ไม่กรองวันที่
        ORDER BY s.work_date, s.slot_time, d.doctor_name'''  # เรียงตามวันและเวลา
    params = (name, '%' + name + '%', phone, phone, work_date, work_date)  # ค่าแทน ? เรียงตามลำดับในคำสั่ง (ใช้คำสั่งเดียว ไม่ต้องต่อสตริงเพิ่มเงื่อนไข)
    rows = database.fetch_all(sql, params)  # รันคำสั่งค้นหา
    tree = ui['tree']  # ตารางผลการค้นหา
    for item in tree.get_children():  # ทุกแถวเดิมในตาราง
        tree.delete(item)  # ลบออกก่อนใส่ผลใหม่
    for row in rows:  # ทุกคิวที่ค้นเจอ
        tag = 'booked'  # คิวที่จองแล้ว ใช้สีส้ม
        if row[8] == 'ยกเลิก':  # คิวที่ยกเลิก
            tag = 'cancelled'  # ใช้สีเทา
        elif row[8] == 'ตรวจแล้ว':  # คิวที่ตรวจแล้ว
            tag = 'done'  # ใช้สีเขียว
        tree.insert('', 'end', iid=str(row[0]), values=row, tags=(tag,))  # ใส่ลงตาราง ใช้หมายเลขคิวเป็น iid ของแถว
    summary = 'พบ ' + str(len(rows)) + ' คิว'  # สรุปจำนวนที่พบ
    if name == '' and phone == '' and work_date == '':  # ไม่ได้ใส่เงื่อนไขเลย
        summary = summary + ' (แสดงทุกคิว)'  # บอกว่าแสดงทั้งหมด
    ui['result_text'].set(summary)  # แสดงข้อความสรุป


def search():  # ปุ่ม "ค้นหา"
    name, phone, work_date = read_conditions()  # อ่านเงื่อนไข
    if work_date != '' and not is_valid_date(work_date):  # กรอกวันที่แต่ผิดรูปแบบ
        dialogs.show_warning('วันที่ไม่ถูกต้อง', 'กรุณากรอกวันที่แบบ YYYY-MM-DD เป็นปี ค.ศ. เช่น ' + date.today().isoformat() + '\nหรือกดปุ่ม "วันนี้"')  # เตือนพร้อมตัวอย่าง
        return  # หยุด
    load_results()  # ค้นหาและแสดงผล


def on_enter(event):  # กด Enter ในช่องค้นหา
    search()  # ค้นหาทันที


def set_today():  # ปุ่ม "วันนี้"
    ui['date_var'].set(date.today().isoformat())  # ใส่วันที่ของวันนี้แบบ YYYY-MM-DD
    search()  # ค้นหาทันที


def clear_search():  # ปุ่ม "ล้างเงื่อนไข"
    ui['name_var'].set('')  # ล้างชื่อ
    ui['phone_var'].set('')  # ล้างเบอร์โทร
    ui['date_var'].set('')  # ล้างวันที่
    load_results()  # แสดงทุกคิว


def refresh():  # เรียกจาก main.py ทุกครั้งที่เปิดแท็บนี้
    name, phone, work_date = read_conditions()  # อ่านเงื่อนไขเดิม
    if work_date != '' and not is_valid_date(work_date):  # วันที่ค้างอยู่ผิดรูปแบบ
        return  # ไม่ค้นหา และไม่เด้งเตือนตอนสลับแท็บ
    load_results()  # ค้นหาซ้ำ ให้เห็นคิวที่เพิ่งจองหรือเพิ่งเปลี่ยนสถานะ


def get_selected_appointment():  # อ่านคิวที่เลือกในตาราง โดยดึงจากฐานข้อมูลโดยตรง
    selected = ui['tree'].selection()  # แถวที่ถูกเลือก
    if len(selected) == 0:  # ยังไม่ได้เลือก
        dialogs.show_warning('ยังไม่ได้เลือกคิว', 'กรุณาคลิกเลือกคิวในตารางก่อน')  # บอกวิธีเลือก
        return None  # ส่ง None กลับ
    appt_id = int(selected[0])  # iid ของแถว = หมายเลขคิว
    sql = '''SELECT a.appt_id, a.status, s.work_date, s.slot_time, p.patient_name, d.doctor_name  -- ข้อมูลล่าสุดของคิว
        FROM appointments a                                               -- เริ่มจากตารางการจองคิว
        JOIN patients p  ON a.patient_id  = p.patient_id                  -- ต่อเพื่อดูชื่อผู้ป่วย
        JOIN schedules s ON a.schedule_id = s.schedule_id                 -- ต่อเพื่อดูวันและเวลา
        JOIN doctors d   ON s.doctor_id   = d.doctor_id                   -- ต่อเพื่อดูชื่อแพทย์
        WHERE a.appt_id = ?'''  # เฉพาะคิวที่เลือก
    row = database.fetch_one(sql, (appt_id,))  # ได้ข้อมูลคิว 1 แถว
    if row is None:  # ไม่พบคิวนี้แล้ว
        dialogs.show_warning('ไม่พบคิว', 'ไม่พบคิวนี้ในระบบแล้ว กรุณาค้นหาใหม่')  # แจ้งเตือน
        load_results()  # โหลดตารางใหม่
        return None  # ส่ง None กลับ
    return row  # ส่งข้อมูลคิวกลับ


def describe(row):  # ทำข้อความสรุปคิว ใช้ในกล่องยืนยัน
    return 'คิวที่: ' + str(row[0]) + '\nผู้ป่วย: ' + row[4] + '\nแพทย์: ' + row[5] + '\nวันที่: ' + row[2] + '  เวลา: ' + row[3]  # ต่อข้อความหลายบรรทัด


def select_row(appt_id):  # ไฮไลต์คิวเดิมในตารางหลังโหลดใหม่
    if ui['tree'].exists(str(appt_id)):  # ถ้าคิวนี้ยังอยู่ในผลค้นหา
        ui['tree'].selection_set(str(appt_id))  # เลือกแถวนั้น
        ui['tree'].see(str(appt_id))  # เลื่อนให้เห็นแถว


def cancel_appointment():  # ปุ่ม "ยกเลิกคิว" (ลำดับที่ 5)
    row = get_selected_appointment()  # ข้อมูลคิวที่เลือก
    if row is None:  # ไม่ได้เลือก หรือไม่พบคิว
        return  # หยุด
    if row[1] != 'จองแล้ว':  # สถานะไม่ใช่ จองแล้ว (ตรวจแล้ว หรือ ยกเลิกไปแล้ว)
        dialogs.show_warning('ยกเลิกไม่ได้', 'คิวที่ ' + str(row[0]) + ' มีสถานะ "' + row[1] + '" แล้ว\nยกเลิกได้เฉพาะคิวที่สถานะ "จองแล้ว"')  # อธิบายเหตุผล
        return  # หยุด
    if not dialogs.ask_yes_no('ยืนยันการยกเลิกคิว', 'ต้องการยกเลิกคิวนี้ใช่ไหม?\n\n' + describe(row) + '\n\nหลังยกเลิก ช่องเวลานี้จะว่างให้ผู้ป่วยคนอื่นจองได้', icon='warning'):  # ถามยืนยันก่อนยกเลิก
        return  # ผู้ใช้กด No
    sql = '''UPDATE appointments SET status = 'ยกเลิก'   -- ไม่ลบแถว แค่เปลี่ยนสถานะ เพื่อเก็บประวัติ
        WHERE appt_id = ? AND status = 'จองแล้ว' '''  # เงื่อนไขสถานะกันการยกเลิกซ้ำ
    try:  # ลองบันทึก
        count = database.execute(sql, (row[0],))  # รันคำสั่ง ได้จำนวนแถวที่ถูกแก้
    except sqlite3.Error as error:  # ฐานข้อมูลไม่ยอมบันทึก
        dialogs.show_error('ยกเลิกไม่สำเร็จ', database.error_to_thai(error))  # แสดงเหตุผลเป็นภาษาไทย
        return  # หยุด
    if count == 0:  # ไม่มีแถวถูกแก้ (สถานะถูกเปลี่ยนไปก่อนแล้ว)
        dialogs.show_warning('ยกเลิกไม่ได้', 'สถานะของคิวนี้ถูกเปลี่ยนไปแล้ว กรุณาค้นหาใหม่')  # แจ้งเตือน
    else:  # ยกเลิกสำเร็จ
        dialogs.show_info('ยกเลิกคิวสำเร็จ', 'ยกเลิกคิวที่ ' + str(row[0]) + ' เรียบร้อย')  # แจ้งผลสำเร็จ
    load_results()  # โหลดตารางใหม่
    select_row(row[0])  # ไฮไลต์คิวเดิม ให้เห็นสถานะที่เปลี่ยน
    header_bar.refresh()  # อัปเดตตัวเลขสรุปวันนี้


def mark_done():  # ปุ่ม "บันทึกว่าตรวจแล้ว" (ลำดับที่ 5) พร้อมบันทึกผลการรักษา
    row = get_selected_appointment()  # ข้อมูลคิวที่เลือก
    if row is None:  # ไม่ได้เลือก หรือไม่พบคิว
        return  # หยุด
    if row[1] != 'จองแล้ว':  # สถานะไม่ใช่ จองแล้ว
        dialogs.show_warning('บันทึกไม่ได้', 'คิวที่ ' + str(row[0]) + ' มีสถานะ "' + row[1] + '" แล้ว\nบันทึกว่าตรวจแล้วได้เฉพาะคิวที่สถานะ "จองแล้ว"')  # อธิบายเหตุผล
        return  # หยุด
    if row[2] > date.today().isoformat():  # วันนัดยังมาไม่ถึง
        dialogs.show_warning('ยังไม่ถึงวันนัด', 'คิวนี้นัดวันที่ ' + row[2] + '\nบันทึกว่าตรวจแล้วได้เฉพาะคิวของวันนี้หรือวันที่ผ่านมา')  # อธิบายเหตุผล
        return  # หยุด
    if not dialogs.ask_yes_no('ยืนยันการบันทึก', 'บันทึกว่าคิวนี้ตรวจแล้วใช่ไหม?\n\n' + describe(row)):  # ถามยืนยัน กันกดผิด
        return  # ผู้ใช้กด No
    result = ask_treatment(row)  # เปิดหน้าต่างกรอกผลวินิจฉัยและการรักษา
    if result is None:  # ผู้ใช้กดยกเลิกในหน้าต่างกรอก
        return  # หยุด ไม่เปลี่ยนสถานะ
    diagnosis = result[0]  # ผลวินิจฉัย
    treatment = result[1]  # การรักษา (None = ไม่ได้กรอก)
    commands = [  # 2 คำสั่งที่ต้องสำเร็จพร้อมกัน (ทำใน transaction เดียว)
        ('''UPDATE appointments SET status = 'ตรวจแล้ว'  -- 1) เปลี่ยนสถานะเป็นตรวจแล้ว
            WHERE appt_id = ? AND status = 'จองแล้ว' ''', (row[0],)),  # เปลี่ยนได้เฉพาะคิวที่ยังจองอยู่
        ('''INSERT INTO treatments (appt_id, diagnosis, treatment)  -- 2) เพิ่มผลการรักษาของคิวนี้
            VALUES (?, ?, ?)''', (row[0], diagnosis, treatment)),  # recorded_at ได้วันเวลาปัจจุบันเอง
    ]  # จบรายการคำสั่ง
    try:  # ลองบันทึกทั้ง 2 คำสั่ง
        saved = database.execute_transaction(commands)  # True = สำเร็จทั้งคู่, False = สถานะถูกเปลี่ยนไปก่อน (ย้อนกลับแล้ว)
    except sqlite3.Error as error:  # คำสั่งใดคำสั่งหนึ่งพลาด ฐานข้อมูลย้อนกลับทั้งคู่แล้ว
        dialogs.show_error('บันทึกไม่สำเร็จ', database.error_to_thai(error))  # แสดงเหตุผลเป็นภาษาไทย
        return  # หยุด
    if not saved:  # ไม่มีแถวถูกแก้
        dialogs.show_warning('บันทึกไม่ได้', 'สถานะของคิวนี้ถูกเปลี่ยนไปแล้ว กรุณาค้นหาใหม่')  # แจ้งเตือน
    else:  # บันทึกสำเร็จ
        dialogs.show_info('บันทึกสำเร็จ', 'บันทึกว่าคิวที่ ' + str(row[0]) + ' ตรวจแล้ว เรียบร้อย\nผลวินิจฉัย: ' + diagnosis)  # แจ้งผลสำเร็จ
    load_results()  # โหลดตารางใหม่
    select_row(row[0])  # ไฮไลต์คิวเดิม ให้เห็นสถานะที่เปลี่ยน
    header_bar.refresh()  # อัปเดตตัวเลขสรุปวันนี้


def ask_treatment(row):  # เปิดหน้าต่างกรอกผลการรักษา คืนค่า (ผลวินิจฉัย, การรักษา) หรือ None ถ้ากดยกเลิก
    window = dialogs.create_window('บันทึกผลการรักษา')  # หน้าต่างใหม่ซ้อนบนหน้าต่างหลัก (ยังซ่อนอยู่)
    form['window'] = window  # เก็บหน้าต่างไว้ปิดจากฟังก์ชันอื่น
    form['result'] = None  # ค่าเริ่มต้น = ยังไม่ได้บันทึก
    form['diagnosis_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องผลวินิจฉัย
    form['treatment_var'] = tk.StringVar()  # ตัวแปรผูกกับช่องการรักษา

    tk.Frame(window, background=theme.PRIMARY, height=6).pack(fill='x')  # แถบสีหลักด้านบน เหมือนหน้าต่างแจ้งเตือน
    box = ttk.Frame(window, padding=16)  # กรอบหลักในหน้าต่าง
    box.pack(fill='both', expand=True)  # ขยายเต็มหน้าต่าง
    ttk.Label(box, text=describe(row)).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))  # แสดงรายละเอียดคิว
    ttk.Label(box, text='ผลวินิจฉัย (บังคับกรอก)').grid(row=1, column=0, sticky='w', pady=5)  # ป้ายช่องผลวินิจฉัย
    form['diagnosis_entry'] = ttk.Entry(box, textvariable=form['diagnosis_var'], width=45)  # ช่องกรอกผลวินิจฉัย
    form['diagnosis_entry'].grid(row=1, column=1, padx=(10, 0), pady=5)  # วางช่องผลวินิจฉัย
    ttk.Label(box, text='การรักษา (ไม่บังคับ)').grid(row=2, column=0, sticky='w', pady=5)  # ป้ายช่องการรักษา
    ttk.Entry(box, textvariable=form['treatment_var'], width=45).grid(row=2, column=1, padx=(10, 0), pady=5)  # ช่องกรอกการรักษา
    buttons = ttk.Frame(box)  # แถวปุ่มด้านล่าง
    buttons.grid(row=3, column=0, columnspan=2, sticky='e', pady=(14, 0))  # ชิดขวา
    ttk.Button(buttons, text='ยกเลิก', style='Light.TButton', command=on_form_cancel).pack(side='right')  # ปุ่มปิดโดยไม่บันทึก (ปุ่มรอง)
    ttk.Button(buttons, text='บันทึก', command=on_form_save).pack(side='right', padx=(0, 8))  # ปุ่มบันทึก

    window.bind('<Return>', on_form_enter)  # กด Enter = บันทึก
    window.bind('<Escape>', on_form_escape)  # กด Esc = ยกเลิก
    window.protocol('WM_DELETE_WINDOW', on_form_cancel)  # กดกากบาทมุมหน้าต่าง = ยกเลิก
    dialogs.show_modal(window, form['diagnosis_entry'])  # แสดงกลางหน้าต่างหลัก ต้องปิดก่อนถึงจะกดหน้าต่างหลักได้ เคอร์เซอร์อยู่ที่ช่องผลวินิจฉัย
    return form['result']  # ส่งค่าที่กรอกกลับ (None = กดยกเลิก)


def on_form_save():  # ปุ่ม "บันทึก" ในหน้าต่างกรอกผลการรักษา
    diagnosis = form['diagnosis_var'].get().strip()  # ผลวินิจฉัย ตัดช่องว่างหัวท้าย
    if diagnosis == '':  # ไม่ได้กรอกผลวินิจฉัย
        dialogs.show_warning('ข้อมูลไม่ครบ', 'กรุณากรอกผลวินิจฉัยก่อนบันทึก')  # เตือน และไม่ปิดหน้าต่างกรอก
        form['diagnosis_entry'].focus_set()  # กลับไปที่ช่องผลวินิจฉัย
        return  # หยุด
    treatment = form['treatment_var'].get().strip()  # การรักษา ตัดช่องว่างหัวท้าย
    if treatment == '':  # ไม่ได้กรอกการรักษา (ไม่บังคับ)
        treatment = None  # เก็บเป็น NULL ในฐานข้อมูล
    form['result'] = (diagnosis, treatment)  # จำค่าที่กรอกไว้ส่งกลับ
    form['window'].destroy()  # ปิดหน้าต่าง


def on_form_cancel():  # ปุ่ม "ยกเลิก" หรือปิดหน้าต่างกรอกผลการรักษา
    form['result'] = None  # ไม่บันทึกอะไร
    form['window'].destroy()  # ปิดหน้าต่าง


def on_form_enter(event):  # กด Enter ในหน้าต่างกรอกผลการรักษา
    on_form_save()  # เหมือนกดปุ่มบันทึก


def on_form_escape(event):  # กด Esc ในหน้าต่างกรอกผลการรักษา
    on_form_cancel()  # เหมือนกดปุ่มยกเลิก
