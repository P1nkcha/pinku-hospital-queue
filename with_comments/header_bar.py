# header_bar.py : แถบหัวโปรแกรม แสดงชื่อ Pinku Clinic คู่กับสรุปคิวของวันนี้ 4 ตัวเลข
# แท็บอื่นเรียก header_bar.refresh() ทุกครั้งที่จอง ยกเลิก หรือบันทึกว่าตรวจแล้ว และ main.py เรียกตอนสลับแท็บ

import tkinter as tk  # ไลบรารีสร้างหน้าจอ (ใช้ widget แบบ tk เพราะตั้งสีพื้นได้ง่าย)
import database  # ฟังก์ชันเชื่อมต่อฐานข้อมูลจาก database.py
import theme  # สีและฟอนต์ของโปรแกรม

ui = {}  # เก็บตัวแปรของแถบนี้ ไว้ใช้ข้ามฟังก์ชัน


def add_number(bar, key, text, color):  # สร้างกล่องตัวเลข 1 กล่อง เช่น ตัวเลข 7 และคำว่า "คิวทั้งหมด" ด้านล่าง
    box = tk.Frame(bar, background=theme.WHITE, padx=14, pady=2)  # กล่องพื้นขาวบนแถบสีหลัก
    box.pack(side='right', padx=(8, 0))  # เรียงจากขวาไปซ้าย
    ui[key] = tk.StringVar(value='0')  # ตัวแปรเก็บตัวเลข (เปลี่ยนค่าแล้วป้ายเปลี่ยนตาม)
    tk.Label(box, textvariable=ui[key], font=('Tahoma', 16, 'bold'), foreground=color, background=theme.WHITE).pack()  # ตัวเลขตัวใหญ่ ใช้สีตามความหมาย
    tk.Label(box, text=text, font=('Tahoma', 10), foreground=theme.TEXT, background=theme.WHITE).pack()  # คำอธิบายใต้ตัวเลข


def create_bar(parent):  # สร้างแถบหัวโปรแกรม แล้วส่ง frame กลับไปให้ main.py
    bar = tk.Frame(parent, background=theme.PRIMARY, padx=16, pady=8)  # แถบพื้นสีหลัก กว้างเต็มหน้าต่าง
    name_box = tk.Frame(bar, background=theme.PRIMARY)  # ส่วนชื่อโปรแกรมทางซ้าย
    name_box.pack(side='left')  # ชิดซ้าย
    tk.Label(name_box, text=theme.APP_NAME, font=('Tahoma', 18, 'bold'), foreground=theme.TEXT, background=theme.PRIMARY).pack(anchor='w')  # ชื่อ Pinku Clinic ตัวหนาสีเข้มบนพื้นชมพู
    tk.Label(name_box, text='ระบบจองคิวคลินิก', font=('Tahoma', 10), foreground=theme.TEXT, background=theme.PRIMARY).pack(anchor='w')  # คำอธิบายใต้ชื่อ ตัวสีเข้ม

    add_number(bar, 'cancelled', 'ยกเลิก', theme.ACCENT)  # คิวที่ยกเลิก (ขวาสุด) ใช้สีเน้น
    add_number(bar, 'waiting', 'รอตรวจ', theme.PRIMARY_DARK)  # คิวที่สถานะจองแล้ว
    add_number(bar, 'done', 'ตรวจแล้ว', theme.DONE)  # คิวที่ตรวจแล้ว สีเขียว
    add_number(bar, 'total', 'คิวทั้งหมด', theme.TEXT)  # คิวทั้งหมดของวันนี้
    ui['date_text'] = tk.StringVar()  # ข้อความ "สรุปคิววันนี้ (วันที่)"
    tk.Label(bar, textvariable=ui['date_text'], font=theme.FONT_BOLD, foreground=theme.TEXT, background=theme.PRIMARY, justify='right').pack(side='right', padx=(0, 6))  # ป้ายบอกวันที่ อยู่ซ้ายของกล่องตัวเลข ตัวสีเข้ม
    refresh()  # โหลดตัวเลขครั้งแรก
    return bar  # ส่ง frame กลับไปให้ main.py วางไว้บนสุด


def refresh():  # โหลดตัวเลขสรุปของวันนี้ใหม่จากฐานข้อมูล
    row = database.get_today_summary()  # ได้ (วันนี้, ทั้งหมด, ตรวจแล้ว, รอตรวจ, ยกเลิก) จาก SQL คำสั่งเดียว
    ui['date_text'].set('สรุปคิววันนี้\n' + row[0])  # แสดงวันที่ของวันนี้ (2 บรรทัด)
    ui['total'].set(str(row[1]))  # คิวทั้งหมด = ตรวจแล้ว + รอตรวจ + ยกเลิก
    ui['done'].set(str(row[2]))  # ตรวจแล้ว
    ui['waiting'].set(str(row[3]))  # รอตรวจ
    ui['cancelled'].set(str(row[4]))  # ยกเลิก
