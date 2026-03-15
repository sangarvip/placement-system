"""
Campus Placement Management System - Main Application
"""
import os
import uuid
from functools import wraps
try:
    import MySQLdb
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt

app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mysql = MySQL(app)


def get_db():
    """Get database cursor."""
    return mysql.connection.cursor()


def init_admin():
    """Create default admin if no admin exists."""
    cur = get_db()
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO admins (email, password, name) VALUES (%s, %s, %s)",
            ('admin@placement.com', hashed, 'System Admin')
        )
        mysql.connection.commit()
    cur.close()


# --- Auth decorators ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# --- Public routes ---
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')
        cur = get_db()
        if role == 'admin':
            cur.execute("SELECT admin_id, password, name FROM admins WHERE email = %s", (email,))
            row = cur.fetchone()
            cur.close()
            if row and bcrypt.checkpw(password.encode('utf-8'), row[1].encode('utf-8')):
                session.clear()
                session['user_id'] = row[0]
                session['role'] = 'admin'
                session['name'] = row[2]
                return redirect(url_for('admin_dashboard'))
        elif role == 'company':
            cur.execute("SELECT company_id, password, company_name, status FROM companies WHERE email = %s", (email,))
            row = cur.fetchone()
            cur.close()
            if row:
                if row[3] != 'approved':
                    flash('Your company registration is pending approval.', 'warning')
                    return render_template('login.html')
                if bcrypt.checkpw(password.encode('utf-8'), row[1].encode('utf-8')):
                    session.clear()
                    session['user_id'] = row[0]
                    session['role'] = 'company'
                    session['name'] = row[2]
                    return redirect(url_for('company_dashboard'))
        else:  # student
            cur.execute("SELECT student_id, password, name FROM students WHERE email = %s", (email,))
            row = cur.fetchone()
            cur.close()
            if row and bcrypt.checkpw(password.encode('utf-8'), row[1].encode('utf-8')):
                session.clear()
                session['user_id'] = row[0]
                session['role'] = 'student'
                session['name'] = row[2]
                return redirect(url_for('student_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa')
        if not all([name, email, password, department]):
            flash('All fields are required.', 'danger')
            return render_template('register.html', role='student')
        try:
            cgpa = float(cgpa) if cgpa else None
        except ValueError:
            cgpa = None
        cur = get_db()
        cur.execute("SELECT student_id FROM students WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            flash('Email already registered.', 'danger')
            return render_template('register.html', role='student')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO students (name, email, password, department, cgpa) VALUES (%s, %s, %s, %s, %s)",
            (name, email, hashed, department, cgpa)
        )
        mysql.connection.commit()
        cur.close()
        flash('Registration successful. You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', role='student')


@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        contact = request.form.get('contact_person', '').strip()
        if not all([company_name, email, password]):
            flash('Company name, email and password are required.', 'danger')
            return render_template('register.html', role='company')
        cur = get_db()
        cur.execute("SELECT company_id FROM companies WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            flash('Email already registered.', 'danger')
            return render_template('register.html', role='company')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO companies (company_name, email, password, contact_person, status) VALUES (%s, %s, %s, %s, 'pending')",
            (company_name, email, hashed, contact or None)
        )
        mysql.connection.commit()
        cur.close()
        flash('Registration submitted. Wait for admin approval.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', role='company')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# --- Student routes ---
@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    cur = get_db()
    cur.execute("""
        SELECT a.application_id, j.job_title, c.company_name, a.status, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        WHERE a.student_id = %s
        ORDER BY a.applied_at DESC
        LIMIT 10
    """, (session['user_id'],))
    applications = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM applications WHERE student_id = %s", (session['user_id'],))
    total_apps = cur.fetchone()[0]
    cur.execute("SELECT student_id, name, email, department, cgpa, resume FROM students WHERE student_id = %s", (session['user_id'],))
    profile = cur.fetchone()
    cur.close()
    return render_template('student/dashboard.html', applications=applications, total_apps=total_apps, profile=profile)


@app.route('/student/profile', methods=['GET', 'POST'])
@login_required(role='student')
def student_profile():
    cur = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa')
        phone = request.form.get('phone', '').strip()
        try:
            cgpa = float(cgpa) if cgpa else None
        except ValueError:
            cgpa = None
        # Resume upload
        resume_path = None
        if 'resume' in request.files:
            f = request.files['resume']
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                filename = f"{session['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                resume_path = f"uploads/resumes/{filename}"
        if resume_path:
            cur.execute("UPDATE students SET name=%s, department=%s, cgpa=%s, phone=%s, resume=%s WHERE student_id=%s",
                        (name, department, cgpa, phone, resume_path, session['user_id']))
        else:
            cur.execute("UPDATE students SET name=%s, department=%s, cgpa=%s, phone=%s WHERE student_id=%s",
                        (name, department, cgpa, phone, session['user_id']))
        mysql.connection.commit()
        session['name'] = name
        flash('Profile updated.', 'success')
        cur.close()
        return redirect(url_for('student_dashboard'))
    cur.execute("SELECT student_id, name, email, department, cgpa, resume, phone FROM students WHERE student_id = %s", (session['user_id'],))
    profile = cur.fetchone()
    cur.close()
    return render_template('student/dashboard.html', profile=profile, edit_profile=True)


@app.route('/student/jobs')
@login_required(role='student')
def student_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = 8
    search = request.args.get('search', '').strip()
    cur = get_db()
    if search:
        cur.execute("""
            SELECT j.job_id, j.job_title, j.job_description, j.salary, j.eligibility, c.company_name, j.created_at
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            WHERE j.is_active = 1 AND c.status = 'approved'
            AND (j.job_title LIKE %s OR j.job_description LIKE %s OR c.company_name LIKE %s)
            ORDER BY j.created_at DESC
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cur.execute("""
            SELECT j.job_id, j.job_title, j.job_description, j.salary, j.eligibility, c.company_name, j.created_at
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            WHERE j.is_active = 1 AND c.status = 'approved'
            ORDER BY j.created_at DESC
        """)
    all_jobs = cur.fetchall()
    total = len(all_jobs)
    start = (page - 1) * per_page
    jobs = all_jobs[start:start + per_page]
    # Get applied job ids for current student
    cur.execute("SELECT job_id FROM applications WHERE student_id = %s", (session['user_id'],))
    applied_ids = {r[0] for r in cur.fetchall()}
    cur.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('student/jobs.html', jobs=jobs, page=page, total_pages=total_pages, search=search, applied_ids=applied_ids)


@app.route('/student/apply/<int:job_id>', methods=['POST'])
@login_required(role='student')
def student_apply(job_id):
    cur = get_db()
    cur.execute("SELECT job_id FROM jobs WHERE job_id = %s AND is_active = 1", (job_id,))
    if not cur.fetchone():
        cur.close()
        flash('Job not found.', 'danger')
        return redirect(url_for('student_jobs'))
    cur.execute("SELECT application_id FROM applications WHERE student_id = %s AND job_id = %s", (session['user_id'], job_id))
    if cur.fetchone():
        cur.close()
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('student_jobs'))
    cur.execute("INSERT INTO applications (student_id, job_id, status) VALUES (%s, %s, 'applied')", (session['user_id'], job_id))
    mysql.connection.commit()
    cur.close()
    flash('Application submitted successfully.', 'success')
    return redirect(url_for('student_jobs'))


@app.route('/student/applications')
@login_required(role='student')
def student_applications():
    cur = get_db()
    cur.execute("""
        SELECT a.application_id, j.job_title, c.company_name, a.status, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        WHERE a.student_id = %s
        ORDER BY a.applied_at DESC
    """, (session['user_id'],))
    applications = cur.fetchall()
    cur.close()
    return render_template('student/applications.html', applications=applications)


# --- Company routes ---
@app.route('/company/dashboard')
@login_required(role='company')
def company_dashboard():
    cur = get_db()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE company_id = %s", (session['user_id'],))
    total_jobs = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        WHERE j.company_id = %s
    """, (session['user_id'],))
    total_applications = cur.fetchone()[0]
    cur.execute("""
        SELECT j.job_id, j.job_title, j.created_at,
               (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) as app_count
        FROM jobs j
        WHERE j.company_id = %s AND j.is_active = 1
        ORDER BY j.created_at DESC
        LIMIT 5
    """, (session['user_id'],))
    jobs = cur.fetchall()
    cur.close()
    return render_template('company/dashboard.html', total_jobs=total_jobs, total_applications=total_applications, jobs=jobs)


@app.route('/company/post-job', methods=['GET', 'POST'])
@login_required(role='company')
def company_post_job():
    if request.method == 'POST':
        title = request.form.get('job_title', '').strip()
        description = request.form.get('job_description', '').strip()
        salary = request.form.get('salary', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        location = request.form.get('location', '').strip()
        if not title:
            flash('Job title is required.', 'danger')
            return render_template('company/post_job.html')
        cur = get_db()
        cur.execute(
            "INSERT INTO jobs (company_id, job_title, job_description, salary, eligibility, location) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], title, description, salary or None, eligibility or None, location or None)
        )
        mysql.connection.commit()
        cur.close()
        flash('Job posted successfully.', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('company/post_job.html')


@app.route('/company/jobs')
@login_required(role='company')
def company_jobs():
    cur = get_db()
    cur.execute("""
        SELECT j.job_id, j.job_title, j.salary, j.is_active, j.created_at,
               (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) as app_count
        FROM jobs j
        WHERE j.company_id = %s
        ORDER BY j.created_at DESC
    """, (session['user_id'],))
    jobs = cur.fetchall()
    cur.close()
    return render_template('company/dashboard.html', jobs_list=jobs, show_all_jobs=True)


@app.route('/company/job/<int:job_id>/toggle', methods=['POST'])
@login_required(role='company')
def company_toggle_job(job_id):
    cur = get_db()
    cur.execute("SELECT job_id FROM jobs WHERE company_id = %s AND job_id = %s", (session['user_id'], job_id))
    if not cur.fetchone():
        cur.close()
        flash('Job not found.', 'danger')
        return redirect(url_for('company_dashboard'))
    cur.execute("UPDATE jobs SET is_active = NOT is_active WHERE job_id = %s", (job_id,))
    mysql.connection.commit()
    cur.close()
    flash('Job status updated.', 'success')
    return redirect(request.referrer or url_for('company_dashboard'))


@app.route('/company/applicants/<int:job_id>')
@login_required(role='company')
def company_applicants(job_id):
    cur = get_db()
    cur.execute("SELECT job_id, job_title FROM jobs WHERE company_id = %s AND job_id = %s", (session['user_id'], job_id))
    job = cur.fetchone()
    if not job:
        cur.close()
        flash('Job not found.', 'danger')
        return redirect(url_for('company_dashboard'))
    cur.execute("""
        SELECT a.application_id, s.student_id, s.name, s.email, s.department, s.cgpa, s.resume, a.status, a.applied_at
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.job_id = %s
        ORDER BY a.applied_at DESC
    """, (job_id,))
    applicants = cur.fetchall()
    cur.close()
    return render_template('company/applicants.html', job=job, applicants=applicants)


@app.route('/company/applicant/<int:application_id>/status', methods=['POST'])
@login_required(role='company')
def company_update_applicant_status(application_id):
    new_status = request.form.get('status')
    if new_status not in ('shortlisted', 'rejected', 'selected'):
        flash('Invalid status.', 'danger')
        return redirect(request.referrer or url_for('company_dashboard'))
    cur = get_db()
    cur.execute("""
        SELECT a.application_id FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        WHERE a.application_id = %s AND j.company_id = %s
    """, (application_id, session['user_id']))
    if not cur.fetchone():
        cur.close()
        flash('Application not found.', 'danger')
        return redirect(url_for('company_dashboard'))
    cur.execute("UPDATE applications SET status = %s WHERE application_id = %s", (new_status, application_id))
    mysql.connection.commit()
    cur.close()
    flash('Applicant status updated.', 'success')
    return redirect(request.referrer or url_for('company_dashboard'))


# --- Admin routes ---
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    cur = get_db()
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM companies WHERE status = 'approved'")
    total_companies = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM companies WHERE status = 'pending'")
    pending_companies = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    total_jobs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'selected'")
    total_placed = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications")
    total_applications = cur.fetchone()[0]
    cur.close()
    stats = {
        'students': total_students,
        'companies': total_companies,
        'pending_companies': pending_companies,
        'jobs': total_jobs,
        'placed': total_placed,
        'applications': total_applications
    }
    return render_template('admin/dashboard.html', stats=stats)


@app.route('/admin/students')
@login_required(role='admin')
def admin_manage_students():
    cur = get_db()
    cur.execute("SELECT student_id, name, email, department, cgpa, created_at FROM students ORDER BY created_at DESC")
    students = cur.fetchall()
    cur.close()
    return render_template('admin/manage_students.html', students=students)


@app.route('/admin/companies')
@login_required(role='admin')
def admin_manage_companies():
    cur = get_db()
    cur.execute("SELECT company_id, company_name, email, status, contact_person, created_at FROM companies ORDER BY created_at DESC")
    companies = cur.fetchall()
    cur.close()
    return render_template('admin/manage_companies.html', companies=companies)


@app.route('/admin/company/<int:company_id>/approve', methods=['POST'])
@login_required(role='admin')
def admin_approve_company(company_id):
    cur = get_db()
    cur.execute("UPDATE companies SET status = 'approved' WHERE company_id = %s", (company_id,))
    mysql.connection.commit()
    cur.close()
    flash('Company approved.', 'success')
    return redirect(url_for('admin_manage_companies'))


@app.route('/admin/company/<int:company_id>/reject', methods=['POST'])
@login_required(role='admin')
def admin_reject_company(company_id):
    cur = get_db()
    cur.execute("UPDATE companies SET status = 'rejected' WHERE company_id = %s", (company_id,))
    mysql.connection.commit()
    cur.close()
    flash('Company rejected.', 'info')
    return redirect(url_for('admin_manage_companies'))


# Add rejected to companies status enum - alter table if needed
@app.route('/admin/jobs')
@login_required(role='admin')
def admin_manage_jobs():
    cur = get_db()
    cur.execute("""
        SELECT j.job_id, j.job_title, j.salary, j.is_active, c.company_name, j.created_at
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY j.created_at DESC
    """)
    jobs = cur.fetchall()
    cur.close()
    return render_template('admin/manage_jobs.html', jobs=jobs)


@app.route('/admin/applications')
@login_required(role='admin')
def admin_applications():
    cur = get_db()
    cur.execute("""
        SELECT a.application_id, s.name as student_name, s.email, j.job_title, c.company_name, a.status, a.applied_at
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.applied_at DESC
    """)
    applications = cur.fetchall()
    cur.close()
    return render_template('admin/dashboard.html', applications=applications, show_applications=True)


@app.route('/admin/statistics')
@login_required(role='admin')
def admin_statistics():
    cur = get_db()
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'selected'")
    placed = cur.fetchone()[0]
    cur.execute("""
        SELECT c.company_name, COUNT(*) as hired
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        WHERE a.status = 'selected'
        GROUP BY c.company_id
    """)
    by_company = cur.fetchall()
    cur.execute("""
        SELECT s.department, COUNT(*) as placed
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.status = 'selected'
        GROUP BY s.department
    """)
    by_department = cur.fetchall()
    cur.close()
    return render_template('admin/dashboard.html', stats_page=True, total_students=total_students,
                           placed=placed, by_company=by_company, by_department=by_department)


@app.before_request
def ensure_admin():
    """Create default admin on first request when DB is available."""
    if not getattr(ensure_admin, '_ran', False):
        try:
            init_admin()
            ensure_admin._ran = True
        except Exception:
            pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
