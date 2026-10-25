# theme.py : ชื่อโปรแกรม สี และฟอนต์ของ Pinku Hospital ทุกไฟล์ใช้ค่าจากที่นี่ที่เดียว
# ใช้ ttk theme "clam" เพราะ theme เริ่มต้นของ Windows ไม่ยอมให้เปลี่ยนสีปุ่ม

from tkinter import ttk  # widget แบบ ttk และตัวจัดการหน้าตา (Style)

APP_NAME = 'Pinku Hospital'  # ชื่อโปรแกรม แสดงที่แถบหัวและชื่อหน้าต่าง

PRIMARY = '#2A90B8'  # สีหลัก: แถบหัวโปรแกรม ปุ่มหลัก หัวตาราง
PRIMARY_DARK = '#1B5E79'  # สีหลักแบบเข้ม: ตอนชี้หรือกดปุ่มหลัก และตัวหนังสือสีฟ้าบนพื้นสีรอง
SECONDARY = '#BADEED'  # สีรอง: พื้นกรอบ แถวที่เลือกในตาราง
ACCENT = '#F56477'  # สีเน้น: ปุ่มยกเลิกคิว หน้าต่างเตือน ตัวเลขยกเลิก
ACCENT_DARK = '#D94860'  # สีเน้นแบบเข้ม: ตอนชี้หรือกดปุ่มยกเลิกคิว
WHITE = '#FFFFFF'  # พื้นช่องกรอกและตาราง และตัวหนังสือบนพื้นสีเข้ม
TEXT = '#1E3A47'  # ตัวหนังสือปกติ (น้ำเงินเข้มเกือบดำ อ่านชัดบนพื้นสีรอง)
HINT = '#3E5C69'  # ตัวหนังสือคำแนะนำ (เทาอมฟ้า เข้มพอให้อ่านออกบนพื้นสีรอง)
WARNING_TEXT = '#A61E33'  # ตัวหนังสือเตือนบนพื้นสีอ่อน (สีเน้นแบบเข้ม ไม่อย่างนั้นอ่านไม่ออก)
DONE = '#1A7F37'  # สีเขียว: คิวที่ตรวจแล้ว
CANCELLED = '#6E6E6E'  # สีเทา: คิวที่ยกเลิก

FONT = ('Tahoma', 11)  # ฟอนต์หลักของทั้งโปรแกรม รองรับภาษาไทย
FONT_BOLD = ('Tahoma', 11, 'bold')  # ตัวหนา ใช้กับปุ่ม หัวตาราง และหัวกรอบ


def setup_style(root):  # ตั้งสีและฟอนต์ของทุก widget (ต้องเรียกก่อนสร้าง widget)
    root.option_add('*Font', FONT)  # widget แบบ tk ใช้ Tahoma
    root.option_add('*TCombobox*Listbox.font', FONT)  # รายการที่เลื่อนลงของ Combobox ใช้ Tahoma
    root.option_add('*TCombobox*Listbox.selectBackground', SECONDARY)  # ตัวเลือกที่ไฮไลต์ในรายการเลื่อนลง ใช้สีรอง
    root.option_add('*TCombobox*Listbox.selectForeground', TEXT)  # ตัวหนังสือของตัวเลือกที่ไฮไลต์
    root.configure(background=SECONDARY)  # พื้นหน้าต่างหลัก
    style = ttk.Style(root)  # ตัวจัดการหน้าตาของ widget แบบ ttk
    style.theme_use('clam')  # theme ที่เปลี่ยนสีได้ทุกส่วน

    style.configure('.', font=FONT, background=SECONDARY, foreground=TEXT, focuscolor=PRIMARY)  # ค่าเริ่มต้นของทุก widget: พื้นสีรอง ตัวหนังสือสีเข้ม
    style.configure('TLabelframe', background=SECONDARY, bordercolor=PRIMARY)  # กรอบมีหัวข้อ: ขอบสีหลัก
    style.configure('TLabelframe.Label', background=SECONDARY, foreground=PRIMARY_DARK, font=FONT_BOLD)  # หัวข้อกรอบ ตัวหนาสีฟ้าเข้ม

    style.configure('TEntry', fieldbackground=WHITE, bordercolor=PRIMARY, lightcolor=WHITE, padding=3)  # ช่องกรอก พื้นขาว ขอบสีหลัก
    style.map('TEntry', bordercolor=[('focus', PRIMARY_DARK)], lightcolor=[('focus', SECONDARY)])  # ช่องที่กำลังพิมพ์ ขอบเข้มขึ้น
    style.configure('TCombobox', fieldbackground=WHITE, background=WHITE, bordercolor=PRIMARY, arrowcolor=PRIMARY_DARK, padding=3)  # รายการเลือก พื้นขาว ลูกศรสีหลัก
    style.map('TCombobox', fieldbackground=[('readonly', WHITE)], background=[('active', SECONDARY), ('readonly', WHITE)],  # readonly ก็ยังพื้นขาว
              selectbackground=[('readonly', WHITE)], selectforeground=[('readonly', TEXT)], bordercolor=[('focus', PRIMARY_DARK)])  # ไม่ไฮไลต์ข้อความทั้งช่องตอนเลือก

    style.configure('TButton', background=PRIMARY, foreground=WHITE, font=FONT_BOLD, bordercolor=PRIMARY_DARK,  # ปุ่มหลัก: พื้นสีหลัก ตัวขาวหนา
                    lightcolor=PRIMARY, darkcolor=PRIMARY, focuscolor=WHITE, padding=(10, 3))  # ไม่มีเงานูน เว้นขอบให้กดง่าย
    style.map('TButton', background=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)],  # ชี้หรือกด = สีเข้มขึ้น
              lightcolor=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)], darkcolor=[('pressed', PRIMARY_DARK), ('active', PRIMARY_DARK)])  # ขอบด้านในเข้มตาม
    style.configure('Light.TButton', background=WHITE, foreground=PRIMARY_DARK, bordercolor=PRIMARY, lightcolor=WHITE, darkcolor=WHITE)  # ปุ่มรอง (ล้าง แสดงทั้งหมด): พื้นขาว ตัวสีฟ้าเข้ม
    style.map('Light.TButton', background=[('pressed', SECONDARY), ('active', SECONDARY)],  # ชี้หรือกด = พื้นสีรอง
              lightcolor=[('pressed', SECONDARY), ('active', SECONDARY)], darkcolor=[('pressed', SECONDARY), ('active', SECONDARY)])  # ขอบด้านในตามพื้น
    style.configure('Danger.TButton', background=ACCENT, foreground=WHITE, bordercolor=ACCENT_DARK, lightcolor=ACCENT, darkcolor=ACCENT)  # ปุ่มยกเลิกคิว: พื้นสีเน้น ตัวขาว
    style.map('Danger.TButton', background=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)],  # ชี้หรือกด = สีเน้นเข้มขึ้น
              lightcolor=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)], darkcolor=[('pressed', ACCENT_DARK), ('active', ACCENT_DARK)])  # ขอบด้านในเข้มตาม

    style.configure('TNotebook', background=SECONDARY, bordercolor=PRIMARY, tabmargins=(0, 6, 0, 0))  # พื้นที่ของแท็บ
    style.configure('TNotebook.Tab', background=PRIMARY, foreground=WHITE, font=FONT_BOLD, padding=(16, 6), bordercolor=PRIMARY_DARK, lightcolor=PRIMARY)  # แท็บที่ไม่ได้เลือก: พื้นสีหลัก ตัวขาว
    style.map('TNotebook.Tab', background=[('selected', SECONDARY), ('active', PRIMARY_DARK)],  # แท็บที่เลือก: พื้นสีรองต่อกับหน้าแท็บ
              foreground=[('selected', PRIMARY_DARK)], lightcolor=[('selected', SECONDARY)],  # ตัวหนังสือของแท็บที่เลือกเป็นสีฟ้าเข้ม
              padding=[('selected', (16, 6))])  # แท็บที่เลือกเว้นขอบเท่าแท็บอื่น (clam ตั้งให้แคบลงเอง ตัวหนังสือจะชิดขอบ)

    style.configure('Treeview', background=WHITE, fieldbackground=WHITE, foreground=TEXT, rowheight=30, bordercolor=PRIMARY)  # ตาราง: พื้นขาว แถวสูงพอให้สระไทยไม่ถูกตัด
    style.map('Treeview', background=[('selected', SECONDARY)], foreground=[('selected', TEXT)])  # แถวที่เลือก: พื้นสีรอง
    style.configure('Treeview.Heading', background=PRIMARY, foreground=WHITE, font=FONT_BOLD, bordercolor=PRIMARY_DARK, lightcolor=PRIMARY, darkcolor=PRIMARY, relief='flat')  # หัวตาราง: พื้นสีหลัก ตัวขาวหนา
    style.map('Treeview.Heading', background=[('active', PRIMARY_DARK)])  # ชี้ที่หัวตาราง = สีเข้มขึ้น

    style.configure('TScrollbar', background=SECONDARY, troughcolor=WHITE, bordercolor=PRIMARY, arrowcolor=PRIMARY_DARK, lightcolor=SECONDARY, darkcolor=SECONDARY)  # แถบเลื่อน
    style.map('TScrollbar', background=[('active', PRIMARY)], arrowcolor=[('active', WHITE)])  # ชี้ที่แถบเลื่อน = สีหลัก
