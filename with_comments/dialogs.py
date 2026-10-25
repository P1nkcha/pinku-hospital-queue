# dialogs.py : หน้าต่างแจ้งเตือนที่เข้ากับธีม Pinku Hospital ใช้แทน messagebox ของ tkinter
# มี 4 แบบ: show_info (ข้อมูล), show_warning (เตือน), show_error (ผิดพลาด), ask_yes_no (ถามยืนยัน)
# ทุกแบบขึ้นตรงกลางหน้าต่างหลัก กด Enter = ตกลง กด Esc = ยกเลิก และต้องปิดก่อนถึงจะกดหน้าต่างหลักได้

import tkinter as tk  # ไลบรารีสร้างหน้าจอ
from tkinter import ttk  # widget แบบ ttk (ปุ่มใช้สีจาก theme.py)
import theme  # สีและฟอนต์ของโปรแกรม

state = {'main_window': None}  # หน้าต่างหลัก (main.py ตั้งค่าให้ตอนเปิดโปรแกรม)
current = {}  # หน้าต่างแจ้งเตือนที่เปิดอยู่ และคำตอบของผู้ใช้


def set_main_window(window):  # main.py เรียกครั้งเดียว บอกว่าหน้าต่างหลักคืออันไหน
    state['main_window'] = window  # จำไว้ใช้หาตำแหน่งกึ่งกลาง


def create_window(title):  # สร้างหน้าต่างใหม่ที่ซ้อนบนหน้าต่างที่ใช้งานอยู่ (ใช้กับกล่องแจ้งเตือนและฟอร์มผลการรักษา)
    main_window = state['main_window']  # หน้าต่างหลัก
    window = tk.Toplevel(main_window)  # หน้าต่างใหม่
    window.withdraw()  # ซ่อนไว้ก่อน จะได้ไม่เห็นหน้าต่างกระพริบที่มุมจอก่อนย้ายไปกึ่งกลาง
    window.title(title)  # ชื่อบนแถบหน้าต่าง
    window.resizable(False, False)  # ไม่ให้ยืดหดขนาด
    window.configure(background=theme.SECONDARY)  # พื้นสีรองเหมือนหน้าต่างหลัก
    owner = main_window.grab_current()  # หน้าต่างที่ล็อกอยู่ตอนนี้ (เช่น ฟอร์มผลการรักษา) ถ้าไม่มีจะได้ None
    if owner is None:  # ไม่มีหน้าต่างอื่นล็อกอยู่
        owner = main_window  # ซ้อนบนหน้าต่างหลัก
    if owner.winfo_viewable():  # หน้าต่างเจ้าของแสดงอยู่ (ตอนเปิดโปรแกรมไม่สำเร็จ หน้าต่างหลักถูกซ่อนไว้)
        window.transient(owner.winfo_toplevel())  # ให้อยู่บนหน้าต่างเจ้าของเสมอ
    return window  # ส่งหน้าต่างกลับไปใส่ข้อความและปุ่ม


def show_modal(window, focus_widget):  # แสดงหน้าต่างตรงกลาง ล็อกหน้าต่างอื่นไว้ แล้วรอจนกว่าจะปิด
    main_window = state['main_window']  # หน้าต่างหลัก
    previous_grab = main_window.grab_current()  # หน้าต่างที่ล็อกไว้ก่อนหน้า (จะคืนการล็อกให้หลังปิด)
    window.update_idletasks()  # คำนวณขนาดหน้าต่างก่อน เพื่อหาตำแหน่งกึ่งกลาง
    width = window.winfo_reqwidth()  # ความกว้างของหน้าต่างใหม่
    height = window.winfo_reqheight()  # ความสูงของหน้าต่างใหม่
    if main_window.winfo_viewable():  # หน้าต่างหลักแสดงอยู่
        border_x = main_window.winfo_rootx() - main_window.winfo_x()  # ความหนาขอบหน้าต่างด้านซ้าย (Windows วางตำแหน่งโดยนับรวมขอบ)
        border_y = main_window.winfo_rooty() - main_window.winfo_y()  # ความสูงแถบชื่อหน้าต่างด้านบน
        x = main_window.winfo_rootx() + (main_window.winfo_width() - width) // 2 - border_x  # กึ่งกลางหน้าต่างหลักแนวนอน (หักขอบออก)
        y = main_window.winfo_rooty() + (main_window.winfo_height() - height) // 2 - border_y  # กึ่งกลางหน้าต่างหลักแนวตั้ง (หักแถบชื่อออก)
    else:  # หน้าต่างหลักถูกซ่อน (เช่น ไม่พบฐานข้อมูล)
        x = (window.winfo_screenwidth() - width) // 2  # กึ่งกลางจอแนวนอน
        y = (window.winfo_screenheight() - height) // 2  # กึ่งกลางจอแนวตั้ง
    window.geometry('+' + str(max(x, 0)) + '+' + str(max(y, 0)))  # ย้ายหน้าต่างไปตำแหน่งนั้น (ไม่ให้หลุดขอบจอ)
    window.deiconify()  # แสดงหน้าต่าง
    window.lift()  # ยกขึ้นมาอยู่หน้าสุด
    window.grab_set()  # ล็อก: ต้องปิดหน้าต่างนี้ก่อน ถึงจะกดหน้าต่างอื่นได้
    focus_widget.focus_set()  # ให้ปุ่มหรือช่องกรอกที่กำหนดพร้อมใช้ทันที
    window.wait_window()  # รอจนกว่าหน้าต่างนี้จะถูกปิด
    if previous_grab is not None and previous_grab.winfo_exists():  # มีหน้าต่างที่เคยล็อกไว้และยังเปิดอยู่
        previous_grab.grab_set()  # คืนการล็อกให้หน้าต่างนั้น (เช่น กลับไปที่ฟอร์มผลการรักษา)


def show_message(kind, title, message, ask, danger):  # สร้างและแสดงกล่องข้อความ 1 กล่อง คืนค่า True (ตกลง) หรือ False (ยกเลิก)
    if kind == 'info':  # แบบข้อมูล
        color = theme.PRIMARY  # สีหลัก
        symbol = 'i'  # สัญลักษณ์ข้อมูล
    elif kind == 'warning':  # แบบเตือน
        color = theme.ACCENT  # สีเน้น
        symbol = '!'  # สัญลักษณ์เตือน
    elif kind == 'error':  # แบบผิดพลาด
        color = theme.ACCENT  # สีเน้น
        symbol = '×'  # สัญลักษณ์ผิดพลาด
    else:  # แบบถามยืนยัน
        color = theme.PRIMARY  # สีหลัก
        symbol = '?'  # สัญลักษณ์คำถาม
    if danger:  # ถามยืนยันเรื่องที่ต้องระวัง เช่น ยกเลิกคิว
        color = theme.ACCENT  # ใช้สีเน้นแทน

    window = create_window(title)  # หน้าต่างใหม่ (ยังซ่อนอยู่)
    current['window'] = window  # จำหน้าต่างไว้ปิดจากฟังก์ชันอื่น
    current['answer'] = False  # ค่าเริ่มต้น = ยกเลิก (ถ้ากดกากบาทหรือ Esc)

    tk.Frame(window, background=color, height=6).pack(fill='x')  # แถบสีด้านบน บอกชนิดของกล่อง
    body = tk.Frame(window, background=theme.WHITE, padx=22, pady=18)  # พื้นที่ข้อความ พื้นขาว
    body.pack(fill='both', expand=True)  # ขยายเต็มหน้าต่าง
    tk.Label(body, text=symbol, font=('Tahoma', 18, 'bold'), foreground=theme.WHITE, background=color, width=2).grid(row=0, column=0, rowspan=2, sticky='n', padx=(0, 16))  # วงสัญลักษณ์ด้านซ้าย
    tk.Label(body, text=title, font=('Tahoma', 12, 'bold'), foreground=theme.TEXT, background=theme.WHITE, anchor='w').grid(row=0, column=1, sticky='w')  # หัวข้อตัวหนา
    tk.Label(body, text=message, font=theme.FONT, foreground=theme.TEXT, background=theme.WHITE, justify='left', anchor='w', wraplength=440).grid(row=1, column=1, sticky='w', pady=(8, 0))  # ข้อความ ยาวเกิน 440 พิกเซลจะขึ้นบรรทัดใหม่เอง

    buttons = tk.Frame(window, background=theme.WHITE, padx=22, pady=14)  # แถวปุ่มด้านล่าง
    buttons.pack(fill='x')  # กว้างเต็มหน้าต่าง
    ok_style = 'TButton'  # ปุ่มตกลงปกติใช้สีหลัก
    if danger:  # ถามยืนยันเรื่องที่ต้องระวัง
        ok_style = 'Danger.TButton'  # ปุ่มตกลงใช้สีเน้น
    ok_button = ttk.Button(buttons, text='ตกลง', style=ok_style, command=on_ok)  # ปุ่มตกลง
    ok_button.pack(side='right')  # ชิดขวา
    if ask:  # แบบถามยืนยัน มีปุ่มยกเลิกด้วย
        ttk.Button(buttons, text='ยกเลิก', style='Light.TButton', command=on_cancel).pack(side='right', padx=(0, 8))  # ปุ่มยกเลิก อยู่ซ้ายของปุ่มตกลง

    window.bind('<Return>', on_enter)  # กด Enter = ตกลง
    window.bind('<KP_Enter>', on_enter)  # กด Enter ที่แป้นตัวเลข = ตกลง
    window.bind('<Escape>', on_escape)  # กด Esc = ยกเลิก
    window.protocol('WM_DELETE_WINDOW', on_cancel)  # กดกากบาทมุมหน้าต่าง = ยกเลิก
    show_modal(window, ok_button)  # แสดงตรงกลาง และรอจนกว่าจะปิด
    return current['answer']  # ส่งคำตอบกลับ


def on_ok():  # ปุ่ม "ตกลง"
    current['answer'] = True  # ผู้ใช้ตอบตกลง
    current['window'].destroy()  # ปิดหน้าต่าง


def on_cancel():  # ปุ่ม "ยกเลิก" หรือกดกากบาท
    current['answer'] = False  # ผู้ใช้ตอบยกเลิก
    current['window'].destroy()  # ปิดหน้าต่าง


def on_enter(event):  # กด Enter
    on_ok()  # เหมือนกดปุ่มตกลง


def on_escape(event):  # กด Esc
    on_cancel()  # เหมือนกดปุ่มยกเลิก


def show_info(title, message):  # แบบข้อมูล เช่น บันทึกสำเร็จ (ใช้แทน messagebox.showinfo)
    show_message('info', title, message, False, False)  # ไม่มีปุ่มยกเลิก


def show_warning(title, message):  # แบบเตือน เช่น กรอกข้อมูลไม่ครบ (ใช้แทน messagebox.showwarning)
    show_message('warning', title, message, False, False)  # ไม่มีปุ่มยกเลิก


def show_error(title, message):  # แบบผิดพลาด เช่น บันทึกลงฐานข้อมูลไม่สำเร็จ (ใช้แทน messagebox.showerror)
    show_message('error', title, message, False, False)  # ไม่มีปุ่มยกเลิก


def ask_yes_no(title, message, icon='question'):  # แบบถามยืนยัน คืนค่า True (ตกลง) หรือ False (ยกเลิก) ใช้แทน messagebox.askyesno
    return show_message('question', title, message, True, icon == 'warning')  # icon='warning' = เรื่องที่ต้องระวัง ใช้สีเน้น
