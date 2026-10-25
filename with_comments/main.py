# main.py : หน้าต่างหลักของระบบจองคิวคลินิก Pinku Hospital
# วิธีรัน: python main.py  (ต้องติดตั้ง tkcalendar และรัน python create_db.py ก่อนอย่างน้อย 1 ครั้ง)

import tkinter as tk  # ไลบรารีสร้างหน้าจอที่มากับ Python
from tkinter import ttk  # widget แบบใหม่ (Notebook ที่ใช้แบ่งแท็บ)
import database  # ไฟล์ database.py (เชื่อมต่อฐานข้อมูล)
import theme  # ไฟล์ theme.py (ชื่อโปรแกรม สี และฟอนต์)
import dialogs  # ไฟล์ dialogs.py (หน้าต่างแจ้งเตือนแบบเข้าธีม)
import header_bar  # ไฟล์ header_bar.py (แถบหัวโปรแกรม สรุปคิววันนี้)
import patient_tab  # ไฟล์ patient_tab.py (แท็บ "ผู้ป่วย")
import booking_tab  # ไฟล์ booking_tab.py (แท็บ "จองคิว")
import search_tab  # ไฟล์ search_tab.py (แท็บ "ค้นหาและจัดการคิว")


def on_tab_changed(event):  # ทำงานทุกครั้งที่ผู้ใช้สลับแท็บ
    header_bar.refresh()  # อัปเดตตัวเลขสรุปวันนี้ทุกครั้งที่สลับแท็บ
    notebook = event.widget  # ตัว Notebook ที่ถูกสลับแท็บ
    index = notebook.index('current')  # ลำดับแท็บที่เปิดอยู่ (0, 1, 2)
    if index == 0:  # แท็บ "ผู้ป่วย"
        patient_tab.refresh()  # โหลดรายชื่อผู้ป่วยใหม่
    elif index == 1:  # แท็บ "จองคิว"
        booking_tab.refresh()  # โหลดวันและช่องเวลาว่างใหม่ (อาจมีคิวถูกยกเลิกจากแท็บอื่น)
    else:  # แท็บ "ค้นหาและจัดการคิว"
        search_tab.refresh()  # ค้นหาซ้ำด้วยเงื่อนไขเดิม ให้เห็นคิวที่เพิ่งจอง


def main():  # จุดเริ่มต้นของโปรแกรม
    root = tk.Tk()  # สร้างหน้าต่างหลัก
    root.title(theme.APP_NAME + ' - ระบบจองคิวคลินิก')  # ชื่อบนแถบหน้าต่าง
    root.geometry('1100x720')  # ขนาดเริ่มต้นของหน้าต่าง
    root.minsize(950, 660)  # ห้ามย่อเล็กกว่านี้ ไม่งั้นช่องต่างๆ จะทับกัน
    theme.setup_style(root)  # ตั้งสีและฟอนต์ Tahoma ก่อนสร้าง widget ทุกตัว (รวมถึงหน้าต่างแจ้งเตือน)
    dialogs.set_main_window(root)  # บอก dialogs.py ว่าหน้าต่างหลักคืออันนี้ (ใช้หาตำแหน่งกึ่งกลาง)

    if not database.database_ready():  # ลำดับที่ 1: ตรวจว่ามี clinic.db และสร้างตารางแล้ว
        root.withdraw()  # ซ่อนหน้าต่างหลักไว้ก่อน
        dialogs.show_error('ไม่พบฐานข้อมูล', 'ไม่พบไฟล์ clinic.db หรือยังไม่ได้สร้างตาราง\nกรุณารัน python create_db.py ก่อน แล้วเปิดโปรแกรมใหม่')  # แจ้งวิธีแก้เป็นภาษาไทย
        root.destroy()  # ปิดโปรแกรม
        return  # จบการทำงาน

    if patient_tab.DateEntry is None:  # ยังไม่ได้ติดตั้ง tkcalendar (ปฏิทินเลือกวันเกิด)
        root.withdraw()  # ซ่อนหน้าต่างหลักไว้ก่อน
        print('ไม่พบ tkcalendar ให้รันคำสั่ง: python -m pip install tkcalendar')  # บอกใน Terminal ด้วย
        dialogs.show_error('ยังไม่ได้ติดตั้ง tkcalendar', 'โปรแกรมต้องใช้ tkcalendar สำหรับปฏิทินเลือกวันเกิด\nกรุณาเปิด Terminal แล้วรันคำสั่ง\n\npython -m pip install tkcalendar\n\nติดตั้งเสร็จแล้วเปิดโปรแกรมใหม่')  # บอกคำสั่งที่ต้องรันเป็นภาษาไทย แทนการขึ้น error
        root.destroy()  # ปิดโปรแกรม
        return  # จบการทำงาน

    header_bar.create_bar(root).pack(fill='x')  # แถบหัวโปรแกรม (ชื่อ + สรุปคิววันนี้) ชิดด้านบน กว้างเต็มหน้าต่าง

    notebook = ttk.Notebook(root)  # ตัวแบ่งหน้าจอเป็นแท็บ
    notebook.pack(fill='both', expand=True, padx=10, pady=(4, 10))  # ขยายเต็มพื้นที่ที่เหลือใต้แถบหัว

    notebook.add(patient_tab.create_tab(notebook), text='ผู้ป่วย')  # แท็บที่ 1 สร้างจาก patient_tab.py
    notebook.add(booking_tab.create_tab(notebook), text='จองคิว')  # แท็บที่ 2 สร้างจาก booking_tab.py
    notebook.add(search_tab.create_tab(notebook), text='ค้นหาและจัดการคิว')  # แท็บที่ 3 สร้างจาก search_tab.py

    notebook.bind('<<NotebookTabChanged>>', on_tab_changed)  # สลับแท็บเมื่อไร ให้โหลดข้อมูลใหม่

    root.mainloop()  # เริ่มรอรับการกดของผู้ใช้ จนกว่าจะปิดหน้าต่าง


if __name__ == '__main__':  # ถ้ารันไฟล์นี้โดยตรง (python main.py)
    main()  # เรียกฟังก์ชัน main
