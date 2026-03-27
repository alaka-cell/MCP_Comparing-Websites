import sqlite3

# Connect to your database
conn = sqlite3.connect('auth.db')  # or 'auth/users.db' depending on your setup
cursor = conn.cursor()

# Get all users
cursor.execute('SELECT id, username, role FROM users')
users = cursor.fetchall()

print("All Users:")
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

conn.close()