import sqlite3

# Database functions
def get_db_connection():
    conn = sqlite3.connect('invoices.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            project_id INTEGER,
            project TEXT,
            contractor_name TEXT,
            vendor_name TEXT,
            invoice_amount REAL,
            balance REAL
        )
    ''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    sample_data = [
        (1, 'Project X', 'Contractor A', 'Vendor A', 20000, 15000),
        (1, 'Project X', 'Contractor B', 'Vendor B', 18000, 5000),
        (2, 'Project Y', 'Contractor C', 'Vendor C', 22000, 22000),
        (1, 'Project X', 'Contractor D', 'Vendor D', 25000, 10000),
        (3, 'Project Z', 'Contractor E', 'Vendor E', 30000, 30000),
        (1, 'Project X', 'Contractor F', 'Vendor F', 16000, 12000),
        (2, 'Project Y', 'Contractor G', 'Vendor G', 29000, 5000),
        (3, 'Project Z', 'Contractor H', 'Vendor H', 35000, 20000),
        (1, 'Project X', 'Contractor I', 'Vendor I', 21000, 6000),
        (2, 'Project Y', 'Contractor J', 'Vendor J', 24000, 24000)  
    ]
    cursor.executemany('INSERT INTO invoices (project_id, project, contractor_name, vendor_name, invoice_amount, balance) VALUES (?, ?, ?, ?, ?, ?)', sample_data)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()  # Initialize the database
    insert_sample_data()  # Insert sample data
    print("Sample data inserted.")