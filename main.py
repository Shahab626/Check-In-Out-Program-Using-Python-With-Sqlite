import sqlite3
from datetime import datetime, timedelta
import threading , time

# Connect to the database
conn = sqlite3.connect('clock_in.db')

# Create a cursor object
c = conn.cursor()

# Create the user table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              pin TEXT NOT NULL,
              password TEXT NOT NULL,
              is_admin INTEGER NOT NULL DEFAULT 0)''')

# Create the timecard table
c.execute('''CREATE TABLE IF NOT EXISTS timecards
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              clock_in DATETIME NOT NULL,
              clock_out DATETIME DEFAULT NULL,
              hours_worked INTEGER DEFAULT NULL,
              FOREIGN KEY (user_id) REFERENCES users(id))''')

# Add default admin user
c.execute('''SELECT * FROM users WHERE pin=1343 AND password=1343''')
user = c.fetchone()
if not user:
    c.execute('''INSERT OR IGNORE INTO users (pin, password, is_admin) 
             VALUES (?, ?, ?)''', (1343, 1343, 1))
    # Commit changes to the database
    conn.commit()

# Close connection to database
conn.close()

def get_user():
    """Get user PIN and password"""
    pin = input("Please enter your 4-digit PIN number: ")
    password = input("Please enter your 4-digit password: ")
    return (pin, password)

def login():
    """Authenticate user login"""
    # Connect to the database
    while True:
        conn = sqlite3.connect('clock_in.db')
        c = conn.cursor()
        pin, password = get_user()
        c.execute('''SELECT * FROM users WHERE pin=? AND password=?''', (pin, password))
        user = c.fetchone()
        if user:
            conn.close()
            return user
        else:
            conn.close()
            print("Unauthorized User")


def get_time():
    print("Users")
    conn = sqlite3.connect('clock_in.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM timecards''', )
    user = c.fetchall()
    print(user)
    conn.close()

def clock_in(user_id):
    """Clock in user"""
    now = datetime.now()
    c.execute('''INSERT INTO timecards (user_id, clock_in)
                 VALUES (?, ?)''', (user_id, now))
    conn.commit()
    print("Clock-in successful")
    

def clock_out(user_id):
    """Clock out user"""
    c.execute('''SELECT * FROM timecards WHERE user_id=? AND clock_out IS NULL''', (user_id,))
    timecard = c.fetchone()
    if timecard:
        now = datetime.now()
        clock_in = datetime.fromisoformat(timecard[2])
        hours_worked = (now - clock_in).seconds / 3600
        c.execute('''UPDATE timecards SET clock_out=?, hours_worked=?
                     WHERE id=?''', (now, hours_worked, timecard[0]))
        print("Clock-out successful")
        conn.commit()
    else:
        print("No active clock-in found")
    

def view_timecard(user_id):
    """View timecard for the current week"""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    c.execute('''SELECT * FROM timecards WHERE user_id=? AND clock_in>=?
                 ORDER BY clock_in DESC''', (user_id, start_of_week))
    timecards = c.fetchall()
    if timecards:
        print(f"---------------------------------------------------")
        print(f"Check In            Check Out           Hour Worked")
        print(f"---------------------------------------------------")
        for timecard in timecards:
            clock_in = datetime.fromisoformat(timecard[2])
            clock_out = datetime.fromisoformat(timecard[3]) if timecard[3] else None
            hours_worked = round(timecard[4],4) if timecard[4] else None
            print(f"{clock_in.strftime('%Y-%m-%d %H:%M')}    {clock_out.strftime('%Y-%m-%d %H:%M') if clock_out else 'IN PROGRESS     '}    {hours_worked}")
    else:
        print("No timecards found for the current week")
    

def admin_menu():
    """Admin menu"""
    while True:
        conn = sqlite3.connect('clock_in.db')
        c = conn.cursor()
        print("""
        1. View timecards
        2. View timecard for specific user
        3. View all users
        4. Add user
        5. Delete user
        6. Set hours worked
        7. Exit
        """)
        choice = input("Enter your choice: ")
        if choice == "1":  
            c.execute('''SELECT * FROM timecards ORDER BY clock_in DESC''',)
            timecards = c.fetchall()
            if timecards:
                print(f"---------------------------------------------------")
                print(f"Check In            Check Out           Hour Worked")
                print(f"---------------------------------------------------")
                for timecard in timecards:
                    clock_in = datetime.fromisoformat(timecard[2])
                    clock_out = datetime.fromisoformat(timecard[3]) if timecard[3] else None
                    hours_worked = round(timecard[4],4) if timecard[4] else None
                    print(f"{clock_in.strftime('%Y-%m-%d %H:%M')}   {clock_out.strftime('%Y-%m-%d %H:%M') if clock_out else 'IN PROGRESS     '}    {hours_worked}")
            else:
                print("No timecards found for the user")
            conn.close()

        elif choice == "2":  
            user_id = input("Enter user ID: ")
            c.execute('''SELECT * FROM timecards WHERE user_id=? ORDER BY clock_in DESC''', (user_id,))
            timecards = c.fetchall()
 
            if timecards:
                print(f"---------------------------------------------------")
                print(f"Check In            Check Out           Hour Worked")
                print(f"---------------------------------------------------")
                for timecard in timecards:
                    clock_in = datetime.fromisoformat(timecard[2])
                    clock_out = datetime.fromisoformat(timecard[3]) if timecard[3] else None
                    hours_worked = round(timecard[4],4) if timecard[4] else None
                    print(f"{clock_in.strftime('%Y-%m-%d %H:%M')}   {clock_out.strftime('%Y-%m-%d %H:%M') if clock_out else 'IN PROGRESS     '}    {hours_worked}")
            else:
                print("No timecards found for the user")
            conn.close()
        
        elif choice == "3":
            c.execute('''SELECT * FROM users''', )
            users = c.fetchall()
            print(f"------------------------")
            print(f"ID       Pin      Status")
            print(f"------------------------")
            for user in users:
                if user[3] == 0:
                    status = 'User'
                else:
                    status = "Admin" 
                print(f"{user[0]}\t{user[1]}\t  {status}")

        elif choice == "4":
            pin = input("Enter user PIN: ")
            is_admin = input("Is the user an admin? (0/1): ")
            if is_admin:
                password = '0001'
            else:
                password = '1343'
            c.execute('''INSERT INTO users (pin, password, is_admin) VALUES (?, ?, ?)''', (pin, password, is_admin))
            conn.commit()
            print("User added successfully")
            conn.close()

        elif choice == "5":
            user_id = input("Enter user ID: ")
            c.execute('''DELETE FROM users WHERE id=?''', (user_id,))
            c.execute('''DELETE FROM timecards WHERE user_id=?''', (user_id,))
            conn.commit()
            if c.rowcount > 0:
                print("User deleted successfully")
            else:
                print("No user found")
            
            conn.close()

        elif choice == "6":
            user_id = input("Enter user ID: ")
            hours_worked = input("Enter hours worked: ")
            c.execute('''UPDATE timecards SET hours_worked=? WHERE user_id=? AND clock_out IS NOT NULL''', (hours_worked, user_id))
            conn.commit()
            if c.rowcount > 0:
                print("Hours worked updated successfully")
            else:
                print("No user found")
            conn.close()

        elif choice == "7":
            conn.close()
            break
        
        else:
            print("Invalid choice")
            conn.close()


def auto_clock_out():
    """Auto-clock out users at midnight for the previous day"""
    while True:
        conn = sqlite3.connect('clock_in.db')
        c = conn.cursor()
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            yesterday = now.date() - timedelta(days=1)
            c.execute('''SELECT * FROM timecards WHERE clock_out IS NULL''')
            timecards = c.fetchall()
            for timecard in timecards:
                clock_in = datetime.fromisoformat(timecard[2])
                if clock_in.date() < yesterday:
                    clock_out = yesterday.isoformat() + " 23:59:59"
                    hours_worked = 8.0
                    c.execute('''UPDATE timecards SET clock_out=?, hours_worked=?
                    WHERE id=?''', (clock_out, hours_worked, timecard[0]))
                    conn.commit()
            print("Auto-clock-out successful")
        time.sleep(60)
        conn.close()


if __name__ == "__main__":
    # Start auto-clock-out thread
    threading.Thread(target=auto_clock_out, daemon=True).start()
    while True:
        user = login()
        if user[3]:
            admin_menu()
        else:
            while True:
                conn = sqlite3.connect('clock_in.db')
                c = conn.cursor()
                get_time()
                print("""
                1. Clock in
                2. Clock out
                3. View timecard
                4. Exit
                """)
                choice = input("Enter your choice: ")
                if choice == "1":
                    clock_in(user[0])
                elif choice == "2":
                    clock_out(user[0])
                elif choice == "3":
                    view_timecard(user[0])
                elif choice == "4":
                    conn.close()
                    break
                else:
                    print("Invalid choice")
                conn.close()
            
 
