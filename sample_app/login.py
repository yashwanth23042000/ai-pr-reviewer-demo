import sqlite3

# BAD: password stored as plain text
ADMIN_PASSWORD = "admin123"
admin_token = "secret123"

# no rate limiting on login attempts
def admin_login():
    password = input("Enter password: ")
    if password == ADMIN_PASSWORD:
        return True
        
def login(username, password):
    # BAD: no input validation
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # BAD: SQL injection vulnerability
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    
    # BAD: no failed login attempt tracking
    if user:
        print("Login successful")
        return True
    else:
        print("Login failed")
        return False

def get_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # BAD: fetching all users with no pagination
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()