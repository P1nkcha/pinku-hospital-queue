import tkinter as tk
from tkinter import ttk
import theme

state = {'main_window': None}
current = {}


def set_main_window(window):
    state['main_window'] = window


def create_window(title):
    main_window = state['main_window']
    window = tk.Toplevel(main_window)
    window.withdraw()
    window.title(title)
    window.resizable(False, False)
    window.configure(background=theme.SECONDARY)
    owner = main_window.grab_current()
    if owner is None:
        owner = main_window
    if owner.winfo_viewable():
        window.transient(owner.winfo_toplevel())
    return window


def show_modal(window, focus_widget):
    main_window = state['main_window']
    previous_grab = main_window.grab_current()
    window.update_idletasks()
    width = window.winfo_reqwidth()
    height = window.winfo_reqheight()
    if main_window.winfo_viewable():
        border_x = main_window.winfo_rootx() - main_window.winfo_x()
        border_y = main_window.winfo_rooty() - main_window.winfo_y()
        x = main_window.winfo_rootx() + (main_window.winfo_width() - width) // 2 - border_x
        y = main_window.winfo_rooty() + (main_window.winfo_height() - height) // 2 - border_y
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
    window.geometry('+' + str(max(x, 0)) + '+' + str(max(y, 0)))
    window.deiconify()
    window.lift()
    window.grab_set()
    focus_widget.focus_set()
    window.wait_window()
    if previous_grab is not None and previous_grab.winfo_exists():
        previous_grab.grab_set()


def show_message(kind, title, message, ask, danger):
    if kind == 'info':
        color = theme.PRIMARY
        symbol = 'i'
    elif kind == 'warning':
        color = theme.ACCENT
        symbol = '!'
    elif kind == 'error':
        color = theme.ACCENT
        symbol = '×'
    else:
        color = theme.PRIMARY
        symbol = '?'
    if danger:
        color = theme.ACCENT

    window = create_window(title)
    current['window'] = window
    current['answer'] = False

    tk.Frame(window, background=color, height=6).pack(fill='x')
    body = tk.Frame(window, background=theme.WHITE, padx=22, pady=18)
    body.pack(fill='both', expand=True)
    tk.Label(body, text=symbol, font=('Tahoma', 18, 'bold'), foreground=theme.WHITE, background=color, width=2).grid(row=0, column=0, rowspan=2, sticky='n', padx=(0, 16))
    tk.Label(body, text=title, font=('Tahoma', 12, 'bold'), foreground=theme.TEXT, background=theme.WHITE, anchor='w').grid(row=0, column=1, sticky='w')
    tk.Label(body, text=message, font=theme.FONT, foreground=theme.TEXT, background=theme.WHITE, justify='left', anchor='w', wraplength=440).grid(row=1, column=1, sticky='w', pady=(8, 0))

    buttons = tk.Frame(window, background=theme.WHITE, padx=22, pady=14)
    buttons.pack(fill='x')
    ok_style = 'TButton'
    if danger:
        ok_style = 'Danger.TButton'
    ok_button = ttk.Button(buttons, text='ตกลง', style=ok_style, command=on_ok)
    ok_button.pack(side='right')
    if ask:
        ttk.Button(buttons, text='ยกเลิก', style='Light.TButton', command=on_cancel).pack(side='right', padx=(0, 8))

    window.bind('<Return>', on_enter)
    window.bind('<KP_Enter>', on_enter)
    window.bind('<Escape>', on_escape)
    window.protocol('WM_DELETE_WINDOW', on_cancel)
    show_modal(window, ok_button)
    return current['answer']


def on_ok():
    current['answer'] = True
    current['window'].destroy()


def on_cancel():
    current['answer'] = False
    current['window'].destroy()


def on_enter(event):
    on_ok()


def on_escape(event):
    on_cancel()


def show_info(title, message):
    show_message('info', title, message, False, False)


def show_warning(title, message):
    show_message('warning', title, message, False, False)


def show_error(title, message):
    show_message('error', title, message, False, False)


def ask_yes_no(title, message, icon='question'):
    return show_message('question', title, message, True, icon == 'warning')
