import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from ttkthemes import ThemedTk 

#Database 
conn = sqlite3.connect("library.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER,
    fine_per_day REAL NOT NULL,
    status TEXT DEFAULT 'Available',
    quantity INTEGER DEFAULT 1
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS readers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    reader_id INTEGER,
    borrow_date TEXT,
    due_date TEXT,
    return_date TEXT,
    fine_amount REAL,
    FOREIGN KEY(book_id) REFERENCES books(id),
    FOREIGN KEY(reader_id) REFERENCES readers(id)
)
""")

try:
    cur.execute("SELECT reader_id FROM transactions LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE transactions ADD COLUMN reader_id INTEGER")

try:
    cur.execute("SELECT quantity FROM books LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE books ADD COLUMN quantity INTEGER DEFAULT 1")
    messagebox.showwarning("Database Update", "The 'quantity' column was added to the books table. Please restart the application if you encounter issues.")

conn.commit()

#All Functions for GUI actions
def delete_book():
    selected = catalog_tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a book to delete.")
        return
    
    book_id = catalog_tree.item(selected[0])['values'][0]
    
    if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete book ID {book_id}? This will also delete its transaction history."):
        cur.execute("DELETE FROM books WHERE id=?", (book_id,))
        cur.execute("DELETE FROM transactions WHERE book_id=?", (book_id,))
        conn.commit()
        messagebox.showinfo("Success", "Book deleted successfully.")
        load_books()
        load_recent_activity()

def add_reader(parent_window, callback=None):
    def save_reader():
        name = reader_name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a reader's name.")
            return
        
        try:
            cur.execute("INSERT INTO readers (name) VALUES (?)", (name,))
            conn.commit()
            messagebox.showinfo("Success", f"Reader '{name}' added successfully.")
            add_reader_win.destroy()
            if callback:
                callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Reader with name '{name}' already exists.")

    add_reader_win = tk.Toplevel(parent_window)
    add_reader_win.title("Add Reader")
    add_reader_win.geometry("300x120")
    add_reader_win.grab_set() 
    add_reader_win.transient(parent_window)
    tk.Label(add_reader_win, text="Reader Name:", font=('Helvetica', 10, 'bold')).pack(pady=(10, 2))
    reader_name_entry = ttk.Entry(add_reader_win, width=30)
    reader_name_entry.pack(pady=5)
    ttk.Button(add_reader_win, text="Save", command=save_reader).pack(pady=5)

def manage_readers():
    reader_win = tk.Toplevel(root)
    reader_win.title("Manage Readers")
    reader_win.geometry("600x400")
    reader_win.grab_set() 
    reader_win.transient(root)

    frame = ttk.Frame(reader_win, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    reader_tree = ttk.Treeview(frame, columns=("ID", "Name", "Borrowed Books", "Total Fine"), show="headings")
    for col in ("ID", "Name", "Borrowed Books", "Total Fine"):
        reader_tree.heading(col, text=col)
    reader_tree.column("ID", width=40)
    reader_tree.column("Name", width=150)
    reader_tree.column("Borrowed Books", width=120)
    reader_tree.column("Total Fine", width=80)
    reader_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=reader_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    reader_tree.configure(yscrollcommand=scrollbar.set)

    def load_readers():
        for row in reader_tree.get_children():
            reader_tree.delete(row)
        cur.execute("SELECT id, name FROM readers")
        for reader_id, name in cur.fetchall():
            cur.execute("SELECT COUNT(*) FROM transactions WHERE reader_id=? AND return_date IS NULL", (reader_id,))
            borrowed_count = cur.fetchone()[0]
            cur.execute("SELECT SUM(fine_amount) FROM transactions WHERE reader_id=?", (reader_id,))
            total_fine = cur.fetchone()[0] or 0.0
            reader_tree.insert("", tk.END, values=(reader_id, name, borrowed_count, f"₹{total_fine:.2f}"))

    def delete_reader():
        selected = reader_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a reader to delete.")
            return
        reader_id = reader_tree.item(selected[0])['values'][0]
        cur.execute("SELECT COUNT(*) FROM transactions WHERE reader_id=? AND return_date IS NULL", (reader_id,))
        borrowed_count = cur.fetchone()[0]
        if borrowed_count > 0:
            messagebox.showerror("Error", "Cannot delete a reader with active borrowed books.")
            return
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete this reader? This will also delete their transaction history."):
            cur.execute("DELETE FROM readers WHERE id=?", (reader_id,))
            cur.execute("DELETE FROM transactions WHERE reader_id=?", (reader_id,))
            conn.commit()
            messagebox.showinfo("Success", "Reader and their history deleted successfully.")
            load_readers()
            load_books()
            load_recent_activity()

    btn_frame = ttk.Frame(reader_win, padding=10)
    btn_frame.pack()
    ttk.Button(btn_frame, text="Add Reader", command=lambda: add_reader(reader_win, load_readers)).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Delete Selected Reader", command=delete_reader).grid(row=0, column=1, padx=5)
    load_readers()


def add_book():
    def save_book():
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        year = year_entry.get().strip()
        fine_rate = fine_entry.get().strip()
        quantity = quantity_entry.get().strip()
        
        if not all([title, author, fine_rate, quantity]):
            messagebox.showerror("Error", "Please fill all required fields.")
            return
        
        try:
            year_val = int(year) if year else None
            fine_val = float(fine_rate)
            quantity_val = int(quantity)
        except ValueError:
            messagebox.showerror("Error", "Year, fine rate, and quantity must be numbers.")
            return
            
        cur.execute("INSERT INTO books (title, author, year, fine_per_day, quantity) VALUES (?, ?, ?, ?, ?)", 
                    (title, author, year_val, fine_val, quantity_val))
        conn.commit()
        messagebox.showinfo("Success", "Book added successfully.")
        add_win.destroy()
        load_books()

    add_win = tk.Toplevel(root)
    add_win.title("Add Book")
    add_win.geometry("350x250")
    add_win.grab_set()
    add_win.transient(root)
    
    frame = ttk.Frame(add_win, padding=10)
    frame.pack(fill="both", expand=True)

    labels = ["Title:", "Author:", "Year:", "Fine per day:", "Quantity:"]
    entries = []
    
    for i, label_text in enumerate(labels):
        ttk.Label(frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entry = ttk.Entry(frame, width=30)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
        entries.append(entry)
    
    title_entry, author_entry, year_entry, fine_entry, quantity_entry = entries
    ttk.Button(frame, text="Save", command=save_book).grid(row=5, column=0, columnspan=2, pady=10)


def borrow_book():
    selected = catalog_tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a book to borrow.")
        return
        
    book_id = catalog_tree.item(selected[0])['values'][0]
    
    cur.execute("SELECT quantity FROM books WHERE id=?", (book_id,))
    total_quantity = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM transactions WHERE book_id=? AND return_date IS NULL", (book_id,))
    borrowed_copies = cur.fetchone()[0]

    if total_quantity - borrowed_copies < 1:
        messagebox.showerror("Error", "All copies of this book are currently borrowed.")
        return

    def save_borrow():
        borrower_name = borrower_entry.get().strip()
        days = days_entry.get().strip()
        
        if not borrower_name or not days:
            messagebox.showerror("Error", "Please fill all fields.")
            return
            
        try:
            days_int = int(days)
        except ValueError:
            messagebox.showerror("Error", "Days must be an integer.")
            return
            
        cur.execute("SELECT id FROM readers WHERE name=?", (borrower_name,))
        reader = cur.fetchone()
        if reader:
            reader_id = reader[0]
        else:
            cur.execute("INSERT INTO readers (name) VALUES (?)", (borrower_name,))
            reader_id = cur.lastrowid
            
        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=days_int)
        
        cur.execute("INSERT INTO transactions (book_id, reader_id, borrow_date, due_date) VALUES (?, ?, ?, ?)", 
                    (book_id, reader_id, borrow_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d")))
        
        conn.commit()
        messagebox.showinfo("Success", f"Book borrowed by {borrower_name}.")
        borrow_win.destroy()
        load_books()
        load_recent_activity()

    borrow_win = tk.Toplevel(root)
    borrow_win.title("Borrow Book")
    borrow_win.geometry("350x180")
    borrow_win.grab_set()
    borrow_win.transient(root)

    frame = ttk.Frame(borrow_win, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Borrower Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    borrower_entry = ttk.Entry(frame, width=30)
    borrower_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    ttk.Label(frame, text="Days to borrow:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    days_entry = ttk.Entry(frame, width=30)
    days_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    ttk.Button(frame, text="Save", command=save_borrow).grid(row=2, column=0, columnspan=2, pady=10)


def return_book():
    selected = catalog_tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a book to return.")
        return
        
    book_id = catalog_tree.item(selected[0])['values'][0]
    
    cur.execute("""
    SELECT t.id, t.due_date, b.fine_per_day, r.name
    FROM transactions t 
    JOIN books b ON t.book_id = b.id 
    JOIN readers r ON t.reader_id = r.id
    WHERE t.book_id=? AND t.return_date IS NULL
    """, (book_id,))
    row = cur.fetchone()
    
    if not row:
        messagebox.showerror("Error", "Book is not currently borrowed.")
        return
        
    transaction_id, due_date_str, fine_rate, borrower_name = row
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
    today = datetime.now()
    days_overdue = (today - due_date).days
    fine_amount = max(0, days_overdue) * fine_rate

    def confirm_return():
        cur.execute("UPDATE transactions SET return_date=?, fine_amount=? WHERE id=?", 
                    (today.strftime("%Y-%m-%d"), fine_amount, transaction_id))
        conn.commit()
        messagebox.showinfo("Success", f"Book returned by {borrower_name}.\nDays overdue: {max(0, days_overdue)}\nFine: ₹{fine_amount:.2f}")
        ret_win.destroy()
        load_books()
        load_recent_activity()

    ret_win = tk.Toplevel(root)
    ret_win.title("Return Book")
    ret_win.geometry("300x150")
    ret_win.grab_set()
    ret_win.transient(root)

    ttk.Label(ret_win, text=f"Borrower: {borrower_name}", font=('Helvetica', 10, 'bold')).pack(pady=(10, 2))
    ttk.Label(ret_win, text=f"Days Overdue: {max(0, days_overdue)}").pack(pady=2)
    ttk.Label(ret_win, text=f"Fine Amount: ₹{fine_amount:.2f}").pack(pady=2)
    ttk.Button(ret_win, text="Confirm Return", command=confirm_return).pack(pady=10)


def load_books(query=""):
    """Loads all books into the Treeview, optionally filtered by a search query."""
    for row in catalog_tree.get_children():
        catalog_tree.delete(row)

    # Prepare the search query for SQL
    sql_query = """
    SELECT 
        b.id, b.title, b.author, b.year, b.fine_per_day, b.quantity,
        COUNT(CASE WHEN t.return_date IS NULL THEN 1 ELSE NULL END) AS borrowed_copies
    FROM books b 
    LEFT JOIN transactions t ON b.id = t.book_id
    WHERE b.title LIKE ? OR b.author LIKE ?
    GROUP BY b.id
    """
    search_term = f"%{query}%"
    cur.execute(sql_query, (search_term, search_term))

    for book in cur.fetchall():
        book_id, title, author, year, fine_rate, total_quantity, borrowed_copies = book
        available_copies = total_quantity - borrowed_copies
        display_status = f"{borrowed_copies} borrowed / {available_copies} left"
        
        tag = ""
        is_overdue = False
        if borrowed_copies > 0:
            cur.execute("SELECT due_date FROM transactions WHERE book_id=? AND return_date IS NULL", (book_id,))
            for due_row in cur.fetchall():
                due_date = datetime.strptime(due_row[0], "%Y-%m-%d")
                if datetime.now() > due_date:
                    is_overdue = True
                    break
        
        if is_overdue:
            tag = "overdue"
        elif available_copies == 0:
            tag = "unavailable"

        catalog_tree.insert("", tk.END, values=(book_id, title, author, year, fine_rate, display_status, total_quantity), tags=(tag,))

def load_recent_activity():
    for row in recent_activity_tree.get_children():
        recent_activity_tree.delete(row)
        
    cur.execute("""
    SELECT 
        t.borrow_date,
        b.title,
        r.name,
        t.return_date IS NULL
    FROM transactions t
    JOIN books b ON t.book_id = b.id
    JOIN readers r ON t.reader_id = r.id
    ORDER BY t.borrow_date DESC
    LIMIT 10
    """)
    
    for row in cur.fetchall():
        borrow_date_str, book_title, reader_name, is_borrowed = row
        status = "Borrowed" if is_borrowed else "Returned"
        recent_activity_tree.insert("", tk.END, values=(borrow_date_str, book_title, reader_name, status))

#Search Function
def search_books():
    """Gets the text from the search entry and calls load_books with the query."""
    query = search_entry.get()
    load_books(query)
# Main GUI Setup
root = ThemedTk(theme="ubuntu") 
root.title("Library Management System")
root.geometry("1000x600")


# Main container with a notebook for tabs
main_notebook = ttk.Notebook(root)
main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Catalog Tab
catalog_frame = ttk.Frame(main_notebook, padding=10)
main_notebook.add(catalog_frame, text="Catalog")

# Search bar
search_frame = ttk.Frame(catalog_frame)
search_frame.pack(fill=tk.X, pady=(0, 10))
search_label = ttk.Label(search_frame, text="Search:", font=('Helvetica', 10, 'bold'))
search_label.pack(side=tk.LEFT, padx=(0, 5))
search_entry = ttk.Entry(search_frame, width=50)
search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
ttk.Button(search_frame, text="Search", command=search_books).pack(side=tk.LEFT, padx=(5, 0)) # <-- Command added here

# Treeview for the book catalog
catalog_columns = ("ID", "Title", "Author", "Year", "Fine/day", "Status", "Quantity")
catalog_tree = ttk.Treeview(catalog_frame, columns=catalog_columns, show="headings")
catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

for col in catalog_columns:
    catalog_tree.heading(col, text=col)
    catalog_tree.column(col, anchor=tk.W, width=100)
catalog_tree.column("ID", width=40)
catalog_tree.column("Fine/day", width=70)
catalog_tree.column("Status", width=150)
catalog_tree.column("Quantity", width=60)

catalog_scrollbar = ttk.Scrollbar(catalog_frame, orient="vertical", command=catalog_tree.yview)
catalog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
catalog_tree.configure(yscrollcommand=catalog_scrollbar.set)

# Tags for highlighting rows
catalog_tree.tag_configure("overdue", foreground="red")
catalog_tree.tag_configure("unavailable", foreground="gray")

# Buttons for actions on the catalog
catalog_btn_frame = ttk.Frame(root, padding=10)
catalog_btn_frame.pack(fill=tk.X)
ttk.Button(catalog_btn_frame, text="Add Book", command=add_book).grid(row=0, column=0, padx=5)
ttk.Button(catalog_btn_frame, text="Delete Book", command=delete_book).grid(row=0, column=1, padx=5)
ttk.Button(catalog_btn_frame, text="Borrow Book", command=borrow_book).grid(row=0, column=2, padx=5)
ttk.Button(catalog_btn_frame, text="Return Book", command=return_book).grid(row=0, column=3, padx=5)

# Dashboard Tab
dashboard_frame = ttk.Frame(main_notebook, padding=10)
main_notebook.add(dashboard_frame, text="Dashboard")

ttk.Label(dashboard_frame, text="Recent Activity", font=('Helvetica', 12, 'bold')).pack(pady=(0, 10))

recent_activity_columns = ("Date", "Book Title", "Reader Name", "Status")
recent_activity_tree = ttk.Treeview(dashboard_frame, columns=recent_activity_columns, show="headings")
recent_activity_tree.pack(fill=tk.BOTH, expand=True)
for col in recent_activity_columns:
    recent_activity_tree.heading(col, text=col)
    recent_activity_tree.column(col, anchor=tk.W)

#Management Tab
management_frame = ttk.Frame(main_notebook, padding=10)
main_notebook.add(management_frame, text="Management")

ttk.Button(management_frame, text="Manage Readers", command=manage_readers).pack(pady=10)

# Load initial data
load_books()
load_recent_activity()

root.mainloop()

# Close the database connection when the application is closed
conn.close()