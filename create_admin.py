import sqlite3
import bcrypt

# Connect to database
conn = sqlite3.connect('auth.db')
cursor = conn.cursor()

# Admin credentials
admin_username = "admin"
admin_password = "admin123"

# Hash password (same as your app)
password_bytes = admin_password.encode('utf-8')[:72]
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

# Insert admin account
try:
    cursor.execute(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        (admin_username, hashed, 'admin')
    )
    conn.commit()
    print(f"✅ Admin account created!")
    print(f"   Username: {admin_username}")
    print(f"   Password: {admin_password}")
except sqlite3.IntegrityError:
    print("❌ Admin already exists")
finally:
    conn.close()