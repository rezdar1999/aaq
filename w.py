import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

# إعداد قاعدة البيانات
def initialize_db():
    conn = sqlite3.connect("cashier_system.db")
    cursor = conn.cursor()

    # جدول المستخدمين
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')

    # جدول المنتجات
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE,
                        name TEXT,
                        quantity INTEGER,
                        wholesale_price REAL,
                        retail_price REAL)''')

    # جدول المعاملات
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        quantity INTEGER,
                        total_price REAL,
                        date TEXT,
                        FOREIGN KEY (product_id) REFERENCES products (id))''')

    # جدول المصروفات والإيرادات
    cursor.execute('''CREATE TABLE IF NOT EXISTS financials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT,
                        amount REAL,
                        description TEXT,
                        date TEXT)''')

    # إضافة مستخدم افتراضي
    cursor.execute('''INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)''', ("admin", "1234"))

    conn.commit()
    conn.close()

# شاشة تسجيل الدخول
def login_screen():
    def login():
        username = username_entry.get()
        password = password_entry.get()

        conn = sqlite3.connect("cashier_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            root.destroy()
            main_screen()
        else:
            messagebox.showerror("فشل تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")

    root = tk.Tk()
    root.title("تسجيل الدخول")
    root.geometry("400x250")
    root.configure(bg="#f4f4f4")

    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 12, "bold"), background="#007BFF", foreground="white")
    style.map("TButton", background=[("active", "#0056b3")])

    frame = ttk.Frame(root, padding="20")
    frame.pack(expand=True)

    ttk.Label(frame, text="اسم المستخدم:").grid(row=0, column=0, pady=5)
    username_entry = ttk.Entry(frame)
    username_entry.grid(row=0, column=1, pady=5)

    ttk.Label(frame, text="كلمة المرور:").grid(row=1, column=0, pady=5)
    password_entry = ttk.Entry(frame, show="*")
    password_entry.grid(row=1, column=1, pady=5)

    login_button = ttk.Button(frame, text="دخول", command=login)
    login_button.grid(row=2, column=0, columnspan=2, pady=10)

    root.mainloop()

# الشاشة الرئيسية
def main_screen():
    total_expenses = 0
    total_revenue = 0

    def open_add_product():
        def add_product():
            code = code_entry.get()
            name = name_entry.get()
            quantity = int(quantity_entry.get())
            wholesale_price = float(wholesale_entry.get())
            retail_price = float(retail_entry.get())

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO products (code, name, quantity, wholesale_price, retail_price) 
                                  VALUES (?, ?, ?, ?, ?)''', (code, name, quantity, wholesale_price, retail_price))
                conn.commit()
                messagebox.showinfo("نجاح", "تمت إضافة المنتج بنجاح.")
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "كود المنتج موجود بالفعل.")
            conn.close()

        product_window = tk.Toplevel()
        product_window.title("إضافة منتج")
        product_window.geometry("500x400")
        product_window.configure(bg="#f4f4f4")

        frame = ttk.Frame(product_window, padding="10")
        frame.pack(expand=True)

        ttk.Label(frame, text="كود المنتج").grid(row=0, column=0, pady=5)
        code_entry = ttk.Entry(frame)
        code_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="اسم المنتج").grid(row=1, column=0, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="الكمية").grid(row=2, column=0, pady=5)
        quantity_entry = ttk.Entry(frame)
        quantity_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="سعر الجملة").grid(row=3, column=0, pady=5)
        wholesale_entry = ttk.Entry(frame)
        wholesale_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="سعر البيع").grid(row=4, column=0, pady=5)
        retail_entry = ttk.Entry(frame)
        retail_entry.grid(row=4, column=1, pady=5)

        ttk.Button(frame, text="إضافة", command=add_product).grid(row=5, column=0, columnspan=2, pady=10)

    def open_cashier():
        def add_to_invoice():
            code = code_entry.get()

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, quantity, retail_price FROM products WHERE code = ?", (code,))
            product = cursor.fetchone()

            if product:
                product_id, name, available_quantity, retail_price = product
                name_var.set(name)
                price_var.set(retail_price)

                quantity = int(quantity_entry.get())
                if quantity <= available_quantity:
                    total = quantity * retail_price
                    invoice_tree.insert("", "end", values=(code, name, quantity, retail_price, total))
                else:
                    messagebox.showerror("خطأ", "الكمية المطلوبة غير متوفرة.")
            else:
                messagebox.showerror("خطأ", "المنتج غير موجود.")

            conn.close()

        def save_invoice():
            nonlocal total_revenue
            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()

            for row in invoice_tree.get_children():
                code, name, quantity, price, total = invoice_tree.item(row, "values")
                total_revenue += float(total)

                cursor.execute("SELECT id FROM products WHERE code = ?", (code,))
                product_id = cursor.fetchone()[0]
                cursor.execute('''INSERT INTO transactions (product_id, quantity, total_price, date) 
                                  VALUES (?, ?, ?, ?)''', (product_id, int(quantity), float(total), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (int(quantity), product_id))

            cursor.execute('''INSERT INTO financials (type, amount, description, date) 
                              VALUES (?, ?, ?, ?)''', ("إيراد", total_revenue, "فاتورة مبيعات", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            conn.close()

            for row in invoice_tree.get_children():
                invoice_tree.delete(row)

            messagebox.showinfo("نجاح", "تم حفظ الفاتورة بنجاح.")

        cashier_window = tk.Toplevel()
        cashier_window.title("الكاشير")
        cashier_window.geometry("700x500")
        cashier_window.configure(bg="#f4f4f4")

        tk.Label(cashier_window, text="كود المنتج").grid(row=0, column=0)
        code_entry = tk.Entry(cashier_window)
        code_entry.grid(row=0, column=1)

        tk.Label(cashier_window, text="اسم المنتج").grid(row=1, column=0)
        name_var = tk.StringVar()
        tk.Entry(cashier_window, textvariable=name_var, state="readonly").grid(row=1, column=1)

        tk.Label(cashier_window, text="سعر البيع").grid(row=2, column=0)
        price_var = tk.StringVar()
        tk.Entry(cashier_window, textvariable=price_var, state="readonly").grid(row=2, column=1)

        tk.Label(cashier_window, text="الكمية").grid(row=3, column=0)
        quantity_entry = tk.Entry(cashier_window)
        quantity_entry.grid(row=3, column=1)

        tk.Button(cashier_window, text="إضافة للفاتورة", command=add_to_invoice).grid(row=4, column=0, columnspan=2)

        invoice_tree = ttk.Treeview(cashier_window, columns=("code", "name", "quantity", "price", "total"), show="headings")
        invoice_tree.grid(row=5, column=0, columnspan=2)
        invoice_tree.heading("code", text="كود المنتج")
        invoice_tree.heading("name", text="اسم المنتج")
        invoice_tree.heading("quantity", text="الكمية")
        invoice_tree.heading("price", text="السعر")
        invoice_tree.heading("total", text="الإجمالي")

        tk.Button(cashier_window, text="حفظ الفاتورة", command=save_invoice).grid(row=6, column=0, columnspan=2)

    def open_financials():
        def add_financial():
            financial_type = type_var.get()
            amount = float(amount_entry.get())
            description = description_entry.get()

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO financials (type, amount, description, date) 
                              VALUES (?, ?, ?, ?)''', (financial_type, amount, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

            messagebox.showinfo("نجاح", "تم إضافة المعاملة المالية بنجاح.")
            load_financials()

        def load_financials():
            for row in financial_tree.get_children():
                financial_tree.delete(row)

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT type, amount, description, date FROM financials")
            financials = cursor.fetchall()
            for financial in financials:
                financial_tree.insert("", "end", values=financial)
            conn.close()

        financials_window = tk.Toplevel()
        financials_window.title("المصروفات والإيرادات")
        financials_window.geometry("600x500")
        financials_window.configure(bg="#f4f4f4")

        tk.Label(financials_window, text="النوع").grid(row=0, column=0)
        type_var = ttk.Combobox(financials_window, values=["إيراد", "مصروف"])
        type_var.grid(row=0, column=1)
        type_var.set("إيراد")

        tk.Label(financials_window, text="المبلغ").grid(row=1, column=0)
        amount_entry = tk.Entry(financials_window)
        amount_entry.grid(row=1, column=1)

        tk.Label(financials_window, text="الوصف").grid(row=2, column=0)
        description_entry = tk.Entry(financials_window)
        description_entry.grid(row=2, column=1)

        tk.Button(financials_window, text="إضافة", command=add_financial).grid(row=3, column=0, columnspan=2)

        financial_tree = ttk.Treeview(financials_window, columns=("type", "amount", "description", "date"), show="headings")
        financial_tree.grid(row=4, column=0, columnspan=2)
        financial_tree.heading("type", text="النوع")
        financial_tree.heading("amount", text="المبلغ")
        financial_tree.heading("description", text="الوصف")
        financial_tree.heading("date", text="التاريخ")

        load_financials()

    def open_profit_loss():
        def filter_data():
            period = period_var.get()
            current_date = datetime.now()
            start_date = None

            if period == "يومي":
                start_date = current_date - timedelta(days=1)
            elif period == "أسبوعي":
                start_date = current_date - timedelta(weeks=1)
            elif period == "شهري":
                start_date = current_date - timedelta(days=30)
            elif period == "نصف سنة":
                start_date = current_date - timedelta(days=182)
            elif period == "سنة":
                start_date = current_date - timedelta(days=365)

            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()

            cursor.execute('''SELECT SUM(amount) FROM financials WHERE type = "إيراد" AND date >= ?''', (start_date_str,))
            revenue = cursor.fetchone()[0] or 0

            cursor.execute('''SELECT SUM(amount) FROM financials WHERE type = "مصروف" AND date >= ?''', (start_date_str,))
            expenses = cursor.fetchone()[0] or 0

            cursor.execute('''SELECT SUM(total_price) FROM transactions WHERE date >= ?''', (start_date_str,))
            total_sales = cursor.fetchone()[0] or 0

            profit = total_sales - expenses
            cursor.close()

            profit_loss_window = tk.Toplevel()
            profit_loss_window.title("الأرباح والخسائر")
            profit_loss_window.geometry("400x300")
            profit_loss_window.configure(bg="#f4f4f4")

            tk.Label(profit_loss_window, text=f"إجمالي الإيرادات: {revenue}").grid(row=0, column=0)
            tk.Label(profit_loss_window, text=f"إجمالي المصروفات: {expenses}").grid(row=1, column=0)
            tk.Label(profit_loss_window, text=f"إجمالي المبيعات: {total_sales}").grid(row=2, column=0)
            tk.Label(profit_loss_window, text=f"الربح أو الخسارة: {profit}").grid(row=3, column=0)

        profit_loss_window = tk.Toplevel()
        profit_loss_window.title("الأرباح والخسائر")
        profit_loss_window.geometry("400x300")
        profit_loss_window.configure(bg="#f4f4f4")

        tk.Label(profit_loss_window, text="اختر الفترة الزمنية:").grid(row=0, column=0)
        period_var = ttk.Combobox(profit_loss_window, values=["يومي", "أسبوعي", "شهري", "نصف سنة", "سنة"])
        period_var.grid(row=0, column=1)
        period_var.set("يومي")

        tk.Button(profit_loss_window, text="تصفية", command=filter_data).grid(row=1, columnspan=2)

    def logout():
        main_window.destroy()
        login_screen()

    main_window = tk.Tk()
    main_window.title("نظام الكاشير")
    main_window.geometry("500x400")
    main_window.configure(bg="#f4f4f4")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"), background="#28a745", foreground="white")
    style.map("TButton", background=[("active", "#218838")])

    frame = ttk.Frame(main_window, padding="10")
    frame.pack(expand=True)

    ttk.Button(frame, text="إضافة منتج", command=open_add_product).grid(row=0, column=0, pady=10, padx=10)
    ttk.Button(frame, text="الكاشير", command=open_cashier).grid(row=0, column=1, pady=10, padx=10)
    ttk.Button(frame, text="المصروفات والإيرادات", command=open_financials).grid(row=1, column=0, pady=10, padx=10)
    ttk.Button(frame, text="الأرباح والخسائر", command=open_profit_loss).grid(row=1, column=1, pady=10, padx=10)
    ttk.Button(frame, text="تسجيل الخروج", command=logout).grid(row=2, column=0, columnspan=2, pady=10)

    main_window.mainloop()

initialize_db()
login_screen()