from tkinter import ttk

APP_NAME = 'Pinku Clinic'

PRIMARY = "#FD82C0"
PRIMARY_DARK = "#444044"
SECONDARY = "#FDEBF9"
ACCENT = '#F56477'
ACCENT_DARK = '#D94860'
WHITE = '#FFFFFF'
TEXT = '#1E3A47'
HINT = '#3E5C69'
WARNING_TEXT = '#A61E33'
DONE = '#1A7F37'
CANCELLED = "#918F8F"
FONT = ('Tahoma', 11)
FONT_BOLD = ('Tahoma', 11, 'bold')


def setup_style(root):
    root.option_add('*Font', FONT)
    root.option_add('*TCombobox*Listbox.font', FONT)
    root.option_add('*TCombobox*Listbox.selectBackground', SECONDARY)
    root.option_add('*TCombobox*Listbox.selectForeground', TEXT)
    root.configure(background=SECONDARY)
    style = ttk.Style(root)
    style.theme_use('clam')

    style.configure('.', font=FONT, background=SECONDARY, foreground=TEXT, focuscolor=PRIMARY)
    style.configure('TLabelframe', background=SECONDARY, bordercolor=PRIMARY)
    style.configure('TLabelframe.Label', background=SECONDARY, foreground=PRIMARY_DARK, font=FONT_BOLD)

    style.configure('TEntry', fieldbackground=WHITE, bordercolor=PRIMARY, lightcolor=WHITE, padding=3)
    style.map('TEntry', bordercolor=[('focus', PRIMARY_DARK)], lightcolor=[('focus', SECONDARY)])
    style.configure('TCombobox', fieldbackground=WHITE, background=WHITE, bordercolor=PRIMARY, arrowcolor=PRIMARY_DARK, padding=3)
    style.map('TCombobox', fieldbackground=[('readonly', WHITE)], background=[('active', SECONDARY), ('readonly', WHITE)],
              selectbackground=[('readonly', WHITE)], selectforeground=[('readonly', TEXT)], bordercolor=[('focus', PRIMARY_DARK)])

    style.configure('TButton', background=PRIMARY, foreground=TEXT, font=FONT_BOLD, bordercolor=PRIMARY_DARK,
                    lightcolor=PRIMARY, darkcolor=PRIMARY, focuscolor=WHITE, padding=(10, 3))
    style.map('TButton', background=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)],
              foreground=[('pressed', WHITE), ('active', WHITE)],
              lightcolor=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)], darkcolor=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)])
    style.configure('Light.TButton', background=WHITE, foreground=PRIMARY_DARK, bordercolor=PRIMARY, lightcolor=WHITE, darkcolor=WHITE)
    style.map('Light.TButton', background=[('pressed', SECONDARY), ('active', SECONDARY)],
              foreground=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)],
              lightcolor=[('pressed', SECONDARY), ('active', SECONDARY)], darkcolor=[('pressed', SECONDARY), ('active', SECONDARY)])
    style.configure('Danger.TButton', background=ACCENT, foreground=TEXT, bordercolor=ACCENT_DARK, lightcolor=ACCENT, darkcolor=ACCENT)
    style.map('Danger.TButton', background=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)],
              foreground=[('pressed', WHITE), ('active', WHITE)],
              lightcolor=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)], darkcolor=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)])

    style.configure('TNotebook', background=SECONDARY, bordercolor=PRIMARY, tabmargins=(0, 6, 0, 0))
    style.configure('TNotebook.Tab', background=PRIMARY, foreground=TEXT, font=FONT_BOLD, padding=(16, 6), bordercolor=PRIMARY_DARK, lightcolor=PRIMARY)
    style.map('TNotebook.Tab', background=[('selected', SECONDARY), ('active', PRIMARY_DARK)],
              foreground=[('selected', PRIMARY_DARK), ('active', WHITE)], lightcolor=[('selected', SECONDARY)],
              padding=[('selected', (16, 6))])

    style.configure('Treeview', background=WHITE, fieldbackground=WHITE, foreground=TEXT, rowheight=30, bordercolor=PRIMARY)
    style.map('Treeview', background=[('selected', SECONDARY)], foreground=[('selected', TEXT)])
    style.configure('Treeview.Heading', background=PRIMARY, foreground=TEXT, font=FONT_BOLD, bordercolor=PRIMARY_DARK, lightcolor=PRIMARY, darkcolor=PRIMARY, relief='flat')
    style.map('Treeview.Heading', background=[('active', PRIMARY_DARK)], foreground=[('active', WHITE)])

    style.configure('TScrollbar', background=SECONDARY, troughcolor=WHITE, bordercolor=PRIMARY, arrowcolor=PRIMARY_DARK, lightcolor=SECONDARY, darkcolor=SECONDARY)
    style.map('TScrollbar', background=[('active', PRIMARY)], arrowcolor=[('active', TEXT)])
