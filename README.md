# Campus Placement Management System

A complete web application for managing campus recruitment. Students can apply for jobs, companies can post jobs and shortlist candidates, and admins can manage the entire placement process.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Backend:** Python Flask
- **Database:** MySQL
- **Template Engine:** Jinja2

## Prerequisites

- Python 3.8 or higher
- MySQL Server 5.7+ or 8.0+
- pip (Python package manager)

## Setup Instructions

### Step 1: Clone or extract the project

Ensure all project files are in a folder named `placement-system`.

### Step 2: Create and activate a virtual environment (recommended)

**Windows (PowerShell):**
```powershell
cd placement-system
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
cd placement-system
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
cd placement-system
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create the MySQL database

1. Start MySQL (XAMPP, WAMP, or MySQL service).
2. Open MySQL command line or phpMyAdmin.
3. Run the SQL script to create the database and tables:

**Option A – MySQL command line:**
```bash
mysql -u root -p < database.sql
```

**Option B – From MySQL shell:**
```sql
source /path/to/placement-system/database.sql
```

Or copy the contents of `database.sql` and execute them in phpMyAdmin.

### Step 5: Configure the database connection

Edit `config.py` and set your MySQL credentials:

```python
MYSQL_HOST = 'localhost'   # or your MySQL host
MYSQL_USER = 'root'       # your MySQL username
MYSQL_PASSWORD = 'your_password'  # your MySQL password
MYSQL_DB = 'placement_system'
```

You can also set these as environment variables: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`.

### Step 6: Create upload folder (optional)

The app creates `static/uploads/resumes/` automatically. If you get permission errors, create it manually:

```bash
mkdir -p static/uploads/resumes
```

### Step 7: Run the application

```bash
python app.py
```

You should see output similar to:

```
 * Running on http://0.0.0.0:5000
```

### Step 8: Open in browser

Go to: **http://localhost:5000**

---

## Default Login Credentials

| Role    | Email                   | Password  |
|---------|-------------------------|-----------|
| Admin   | admin@placement.com     | admin123  |

Students and companies must register. After company registration, an admin must **approve** the company before they can log in.

---

## User Roles and Features

### Student
- Register and login
- Create/edit profile (name, department, CGPA, phone)
- Upload resume (PDF)
- Browse and search jobs
- Apply for jobs
- Track application status (applied / shortlisted / selected / rejected)
- Dashboard with recent applications

### Company
- Register (status: pending until admin approval)
- Login (only after approval)
- Dashboard (job count, application count)
- Post job openings (title, description, salary, eligibility, location)
- View all posted jobs and toggle active/inactive
- View applicants per job
- Shortlist, select, or reject applicants

### Admin
- Login with default credentials
- Dashboard with counts (students, companies, jobs, applications, placed)
- Manage students (view list)
- Manage companies (approve / reject pending registrations)
- Manage jobs (view all jobs)
- View all applications
- Placement statistics (by company, by department)

---

## Project Structure

```
placement-system/
├── app.py              # Main Flask application
├── config.py           # Configuration (DB, uploads, secret key)
├── database.sql       # MySQL schema and tables
├── requirements.txt   # Python dependencies
├── README.md          # This file
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── jobs.html
│   │   └── applications.html
│   ├── company/
│   │   ├── dashboard.html
│   │   ├── post_job.html
│   │   └── applicants.html
│   └── admin/
│       ├── dashboard.html
│       ├── manage_students.html
│       ├── manage_companies.html
│       └── manage_jobs.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── uploads/
        └── resumes/    # Uploaded PDFs (created automatically)
```

---

## Security Notes

- Passwords are hashed with **bcrypt**.
- File uploads are restricted to **PDF** and **5 MB** max.
- Change `SECRET_KEY` in `config.py` (or set `SECRET_KEY` env variable) in production.
- Change the default admin password after first login in production.

---

## Troubleshooting

1. **"Can't connect to MySQL"**  
   Check that MySQL is running and that `config.py` has the correct host, user, password, and database name.

2. **"No module named 'MySQLdb'"**  
   On Windows, if `mysqlclient` fails to install, try:
   ```bash
   pip install pymysql
   ```
   Then in `app.py` add at the top (after other imports):
   ```python
   import pymysql
   pymysql.install_as_MySQLdb()
   ```

3. **Company cannot login**  
   Admin must approve the company from **Admin → Companies** first.

4. **Resume upload fails**  
   Ensure `static/uploads/resumes` exists and the app has write permission.

---

## License

This project is for educational use (e.g. college final year project).
