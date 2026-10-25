import tkinter as tk
from tkinter import ttk
import database
import theme
import dialogs
import header_bar
import patient_tab
import booking_tab
import search_tab


def on_tab_changed(event):
    header_bar.refresh()
    notebook = event.widget
    index = notebook.index('current')
    if index == 0:
        patient_tab.refresh()
    elif index == 1:
        booking_tab.refresh()
    else:
        search_tab.refresh()


def main():
    root = tk.Tk()
    root.title(theme.APP_NAME + ' - ระบบจองคิวคลินิก')
    root.geometry('1100x720')
    root.minsize(950, 660)
    theme.setup_style(root)
    dialogs.set_main_window(root)

    if not database.database_ready():
        root.withdraw()
        dialogs.show_error('ไม่พบฐานข้อมูล', 'ไม่พบไฟล์ clinic.db หรือยังไม่ได้สร้างตาราง\nกรุณารัน python create_db.py ก่อน แล้วเปิดโปรแกรมใหม่')
        root.destroy()
        return

    if patient_tab.DateEntry is None:
        root.withdraw()
        print('ไม่พบ tkcalendar ให้รันคำสั่ง: python -m pip install tkcalendar')
        dialogs.show_error('ยังไม่ได้ติดตั้ง tkcalendar', 'โปรแกรมต้องใช้ tkcalendar สำหรับปฏิทินเลือกวันเกิด\nกรุณาเปิด Terminal แล้วรันคำสั่ง\n\npython -m pip install tkcalendar\n\nติดตั้งเสร็จแล้วเปิดโปรแกรมใหม่')
        root.destroy()
        return

    header_bar.create_bar(root).pack(fill='x')

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=(4, 10))

    notebook.add(patient_tab.create_tab(notebook), text='ผู้ป่วย')
    notebook.add(booking_tab.create_tab(notebook), text='จองคิว')
    notebook.add(search_tab.create_tab(notebook), text='ค้นหาและจัดการคิว')

    notebook.bind('<<NotebookTabChanged>>', on_tab_changed)

    root.mainloop()


if __name__ == '__main__':
    main()
