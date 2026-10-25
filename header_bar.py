import tkinter as tk
import database
import theme

ui = {}


def add_number(bar, key, text, color):
    box = tk.Frame(bar, background=theme.WHITE, padx=14, pady=2)
    box.pack(side='right', padx=(8, 0))
    ui[key] = tk.StringVar(value='0')
    tk.Label(box, textvariable=ui[key], font=('Tahoma', 16, 'bold'), foreground=color, background=theme.WHITE).pack()
    tk.Label(box, text=text, font=('Tahoma', 10), foreground=theme.TEXT, background=theme.WHITE).pack()


def create_bar(parent):
    bar = tk.Frame(parent, background=theme.PRIMARY, padx=16, pady=8)
    name_box = tk.Frame(bar, background=theme.PRIMARY)
    name_box.pack(side='left')
    tk.Label(name_box, text=theme.APP_NAME, font=('Tahoma', 18, 'bold'), foreground=theme.WHITE, background=theme.PRIMARY).pack(anchor='w')
    tk.Label(name_box, text='ระบบจองคิวคลินิก', font=('Tahoma', 10), foreground=theme.WHITE, background=theme.PRIMARY).pack(anchor='w')

    add_number(bar, 'cancelled', 'ยกเลิก', theme.ACCENT)
    add_number(bar, 'waiting', 'รอตรวจ', theme.PRIMARY_DARK)
    add_number(bar, 'done', 'ตรวจแล้ว', theme.DONE)
    add_number(bar, 'total', 'คิวทั้งหมด', theme.TEXT)
    ui['date_text'] = tk.StringVar()
    tk.Label(bar, textvariable=ui['date_text'], font=theme.FONT_BOLD, foreground=theme.WHITE, background=theme.PRIMARY, justify='right').pack(side='right', padx=(0, 6))
    refresh()
    return bar


def refresh():
    row = database.get_today_summary()
    ui['date_text'].set('สรุปคิววันนี้\n' + row[0])
    ui['total'].set(str(row[1]))
    ui['done'].set(str(row[2]))
    ui['waiting'].set(str(row[3]))
    ui['cancelled'].set(str(row[4]))
