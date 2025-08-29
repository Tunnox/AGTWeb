# ================================== Imports ==================================
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2
from werkzeug.utils import secure_filename
import os
import base64
import requests
import datetime
import smtplib
import re
from dotenv import load_dotenv
from email.message import EmailMessage
import random
from werkzeug.security import generate_password_hash
import random, smtplib
from email.mime.text import MIMEText
from werkzeug.security import check_password_hash

# ============================= Flask Setup ===================================
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key
load_dotenv()

# ============================= Configurations ================================
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
GITHUB_REPO = os.environ.get('GITHUB_REPO')

# PostgreSQL connection
connection = psycopg2.connect(
    dbname='AGT',
    user='postgres',
    password='pgsqtk116chuk95',
    host='chukspace.ctiuisa62ks5.eu-north-1.rds.amazonaws.com',
    port='5432'
)

# =============================================================================
# ============================== ROUTES =======================================
# =============================================================================

# --------------------------- General Pages -----------------------------------
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/main')
def home_index():
    return render_template('main.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/units')
def units():
    return render_template('units.html')

@app.route('/my_profile')
def my_profile_page():
    return render_template('my_profile.html')

@app.route('/profile_view')
def profile_view():
    return render_template('profile_view.html')

@app.route('/login_admin')
def login_admin():
    return render_template('login.html')


# --------------------------- AGT LOGIN ---------------------------------------
@app.route('/agt_login', methods=['POST'])
def agt_login():
    data = request.get_json()
    login_username = data['loginUsername']
    login_password = data['loginPassword']

    cur = connection.cursor()
    try:
        cur.execute(
            '''
            SELECT id, user_id, worker_id, role, user_name, email, password_hash, created_at, updated_at
            FROM public.agt_admin
            WHERE (user_name = %s OR email = %s)
            ''',
            (login_username, login_username)
        )
        admin = cur.fetchone()

        if admin and check_password_hash(admin[6], login_password):  # password_hash is the 7th column
            return jsonify({"message": "Login successful!", "success": True}), 200
        else:
            return jsonify({"message": "Invalid credentials, please try again."}), 401
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    finally:
        cur.close()



# --------------------------- Attendance Check (General) ----------------------
@app.route('/teens_check_attendance', methods=['POST'])
def teens_check_attendance():
    data = request.get_json()
    name = data.get('name')
    today = datetime.datetime.now().date()

    try:
        cur = connection.cursor()
        cur.execute("""
            SELECT "Date"
            FROM public."AGT_Attendacne"
            WHERE "Name" = %s AND DATE("Date") = %s
            LIMIT 1;
        """, (name, today))
        result = cur.fetchone()
        cur.close()
        if result:
            return jsonify({"present": True, "date": str(result[0])})
        else:
            return jsonify({"present": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# =============================================================================
# ============================== ROTA ROUTES ==================================
# =============================================================================

@app.route('/rota/search_user', methods=['POST'])
def rota_search_user():
    keyword = request.form.get("keyword", "").strip()
    if not keyword:
        return jsonify([])

    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT id, first_name, last_name, department 
            FROM public.agt_user_data_records
            WHERE first_name ILIKE %s OR last_name ILIKE %s
            LIMIT 10
        """, (f"%{keyword}%", f"%{keyword}%"))
        results = cur.fetchall()
        return jsonify([
            {"id": r[0], "first_name": r[1], "last_name": r[2], "department": r[3]}
            for r in results
        ])
    finally:
        cur.close()


@app.route("/rota/get_worker/<int:user_id>")
def rota_get_worker(user_id):
    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT worker_id, role, department
            FROM public.agt_workers_voluntiers_records
            WHERE user_id = %s
        """, (user_id,))
        worker = cur.fetchone()
        if worker:
            return jsonify({
                "worker_id": worker[0],
                "role": worker[1],
                "department": worker[2]
            })
        return jsonify({"error": "Worker not found"}), 404
    finally:
        cur.close()


@app.route("/rota/add", methods=["POST"])
def rota_add():
    data = request.get_json()
    worker_id = data.get("worker_id")
    service_date = data.get("service_date")
    service_slot = data.get("service_slot")
    assignment = data.get("assignment", "")

    # Extract month name (e.g., "January") from service_date
    month_str = datetime.datetime.strptime(service_date, "%Y-%m-%d").strftime("%B")

    cur = connection.cursor()
    try:
        cur.execute("""
            INSERT INTO public.agt_rota
            (rota_id, worker_id, month, service_date, service_slot, availability, assignment, 
             submission_date, submission_status, approval_status, approved_by, remarks, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'available', %s,
                    now(), 'pending', 'pending', 0, '', now(), now())
            RETURNING id
        """, (0, worker_id, month_str, service_date, service_slot, assignment))
        new_id = cur.fetchone()[0]
        connection.commit()
        return jsonify({"message": "Rota entry added", "id": new_id})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@app.route("/rota/calendar", methods=["GET"])
def rota_calendar():
    department = request.args.get("department")

    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT r.service_date, r.service_slot, r.assignment,
                   u.first_name, u.last_name,
                   w.role, w.department
            FROM public.agt_rota r
            JOIN public.agt_workers_voluntiers_records w ON r.worker_id = w.worker_id
            JOIN public.agt_user_data_records u ON w.user_id = u.id
            WHERE (%s IS NULL OR w.department = %s)
            ORDER BY r.service_date
        """, (department, department))
        records = cur.fetchall()
        return jsonify([
            {
                "service_date": str(r[0]),
                "service_slot": r[1],
                "assignment": r[2],
                "first_name": r[3],
                "last_name": r[4],
                "role": r[5],
                "department": r[6]
            }
            for r in records
        ])
    finally:
        cur.close()



# =============================================================================
# ======================== ADULT CHURCH ROUTES ================================
# =============================================================================

@app.route('/adult_church')
def adult_index():
    return render_template('agtadult.html')

@app.route('/adult_church/search', methods=['POST'])
def adult_search():
    keyword = request.form['keyword']
    cursor = connection.cursor()

    connection.rollback()
    
    sql_query = """
        SELECT id, first_name, last_name, age, gender, birthday, contact_number,
               age_group, department, relationship_status, email, address, consent
        FROM "public"."agt_user_data_records"
        WHERE "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "age"::TEXT ILIKE %s 
           OR "gender" ILIKE %s
           OR "birthday" ILIKE %s
           OR "contact_number"::TEXT ILIKE %s
           OR "age_group" ILIKE %s
           OR "department" ILIKE %s
           OR "relationship_status" ILIKE %s
           OR "email" ILIKE %s
           OR "address" ILIKE %s
           OR consent::TEXT ILIKE %s
        LIMIT 10
    """
    cursor.execute(sql_query, [f'%{keyword}%'] * 12)
    results = cursor.fetchall()
    cursor.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        records = [
            {
                "id": r[0],
                "first_name": r[1],
                "last_name": r[2],
                "age": r[3],
                "gender": r[4],
                "birthday": r[5],
                "contact_number": r[6],
                "age_group": r[7],
                "department": r[8],
                "relationship_status": r[9],
                "email": r[10],
                "address": r[11],
                "consent": r[12]
            }
            for r in results
        ]
        return jsonify(records)

    return render_template('agtadult.html', results=results)

@app.route('/adult_church/update', methods=['POST'])
def adult_update():
    data = request.form
    cursor = connection.cursor()

    sql_update = """
        UPDATE "public"."agt_user_data_records"
        SET first_name = %s, last_name = %s, age = %s, gender = %s, birthday = %s,
            contact_number = %s, age_group = %s, department = %s,
            relationship_status = %s, email = %s, address = %s, consent = %s,
            updated_at = NOW()
        WHERE id = %s
    """

    cursor.execute(sql_update, (
        data['first_name'], data['last_name'], data['age'], data['gender'], data['birthday'],
        data['contact_number'], data['age_group'], data['department'], data['relationship_status'],
        data['email'], data['address'], data['consent'], data['id']
    ))

    connection.commit()
    cursor.close()
    flash('Record updated successfully!')
    return redirect(url_for('adult_index'))

@app.route('/adult_church/insert', methods=['GET','POST'])
def adult_insert():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        birthday = request.form['birthday']
        contact_number = request.form['contact_number']
        age_group = request.form['age_group']
        department = request.form['department']
        relationship_status = request.form['relationship_status']
        email = request.form['email']
        address = request.form['address']
        consent = request.form['consent']

        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO "public"."agt_user_data_records"
                (first_name, last_name, age, gender, birthday, contact_number,
                 age_group, department, relationship_status, email, address, consent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (first_name, last_name, age, gender, birthday, contact_number,
               age_group, department, relationship_status, email, address, consent))
        connection.commit()
        cursor.close()

    flash('Record inserted successfully!')
    return redirect(url_for('adult_index'))

# ----------------------- Worker Check for Attendance -------------------------
@app.route('/check_worker/<int:user_id>', methods=['GET'])
def check_worker(user_id):
    try:
        cur = connection.cursor()
        cur.execute("""
            SELECT worker_id, department
            FROM public."agt_workers_voluntires_records"
            WHERE user_id = %s
            LIMIT 1;
        """, (user_id,))
        worker = cur.fetchone()
        cur.close()

        if worker:
            return jsonify({"is_worker": True, "worker_id": worker[0], "department": worker[1]})
        else:
            return jsonify({"is_worker": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ----------------------- Attendance Recording -------------------------------
@app.route('/record_adult_attendance', methods=['POST'])
def record_adult_attendance():
    data = request.get_json()
    user_id = data.get('user_id')
    worker_id = data.get('worker_id')  # optional
    status = data.get('status', 'present')
    service = data.get('service', 'first service')

    try:
        cur = connection.cursor()
        cur.execute("""
            INSERT INTO public."agt_attendance_manager"
                (user_id, worker_id, attendance_date, attendance_time, status, service)
            VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME, %s, %s);
        """, (user_id, worker_id, status, service))

        connection.commit()
        cur.close()
        return jsonify({"message": "Attendance recorded successfully!"}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/get_adult_attendance_dates', methods=['GET'])
def get_adult_attendance_dates():
    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT DATE("Date") FROM public."AGT_Attendacne"
            ORDER BY DATE("Date") DESC
        """)
        dates = [str(row[0]) for row in cur.fetchall()]
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/download_adult_attendance_csv', methods=['GET'])
def download_adult_attendance_csv():
    import csv
    from io import StringIO

    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify({"error": "Date parameter is required"}), 400

    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT "Name", "Date", "Contact"
            FROM public."AGT_Attendacne"
            WHERE DATE("Date") = %s
        """, (selected_date,))
        records = cur.fetchall()
        cur.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Date", "Contact"])
        writer.writerows(records)
        csv_data = output.getvalue().encode('utf-8')

        return (
            csv_data,
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename="AGT_Attendance_{selected_date}.csv"'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ======================== TEENS CHURCH ROUTES ================================
# =============================================================================

@app.route('/teens_church')
def teens_index():
    return render_template('agtteens.html')

@app.route('/teens_church/search', methods=['POST'])
def teens_search():
    keyword = request.form.get('keyword', '')

    cursor = connection.cursor()
    sql_query = """
        SELECT * FROM "public"."AGT_TEENS_DATA_RECORDS" 
        WHERE "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "age"::TEXT ILIKE %s 
           OR "gender" ILIKE %s
           OR "birthday" ILIKE %s
           OR "contact_number"::TEXT ILIKE %s
           OR "age_group" ILIKE %s
           OR "department" ILIKE %s
           OR "relationship_status" ILIKE %s
           OR "email" ILIKE %s
           OR "address" ILIKE %s
           OR "consent" ILIKE %s
        LIMIT 10
    """
    cursor.execute(sql_query, [f'%{keyword}%'] * 12)
    results = cursor.fetchall()
    cursor.close()

    # Return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        records = []
        for r in results:
            record = {
                "first_name": r[0],
                "last_name": r[1],
                "age": r[2],
                "gender": r[3],
                "birthday": r[4],
                "contact_number": r[5],
                "age_group": r[6],
                "department": r[7],
                "relationship_status": r[8],
                "email": r[9],
                "address": r[10],
                "consent": r[11]
            }
            records.append(record)
        return jsonify(records)

    # Else, default to HTML rendering (e.g., for fallback use)
    return render_template('agtteens.html', results=results)

@app.route('/teens_church/update', methods=['POST'])
def teens_update():
    data = request.form
    cursor = connection.cursor()
    
    # SQL query to update the record
    sql_update = """
        UPDATE "public"."AGT_TEENS_DATA_RECORDS"
        SET "first_name" = %s, "last_name" = %s, "age" = %s, "gender" = %s, "birthday" = %s,
            "contact_number" = %s, "age_group" = %s, "department" = %s, "relationship_status" = %s, "email" = %s, "address" = %s, "consent" = %s
        WHERE "first_name" = %s
    """
    
    # Execute the update query
    cursor.execute(sql_update, (
        data['first_name'], data['last_name'], data['age'], data['gender'], data['birthday'],
        data['contact_number'], data['age_group'], data['department'], data['relationship_status'], data['email'], data['address'], data['consent'],
        data['first_name']
    ))
    
    connection.commit()  # Commit the changes
    cursor.close()
    flash('Record updated successfully!')
    return redirect(url_for('teens_index'))

@app.route('/teens_church/insert', methods=['GET','POST'])
def teens_insert():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        birthday = request.form['birthday']
        contact_number = request.form['contact_number']
        age_group = request.form['age_group']
        department = request.form['department']
        relationship_status = request.form['relationship_status']
        email = request.form['email']
        address = request.form['address']
        consent = request.form['consent']


        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."AGT_TEENS_DATA_RECORDS" ("first_name", "last_name", "age", "gender", "birthday", "contact_number", "age_group", "department", "relationship_status", "email", "address", "consent")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (first_name, last_name, age, gender, birthday, contact_number, age_group, department, relationship_status, email, address, consent))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Record inserted successfully!')
    return redirect(url_for('teens_index'))

@app.route('/teens_record_attendance', methods=['POST'])
def teens_record_attendance():
    data = request.get_json()
    name = data.get('name')
    contact = data.get('contact')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cur = connection.cursor()
        cur.execute("""
            INSERT INTO public."AGT_Attendacne" ("Name", "Date", "Contact")
            VALUES (%s, %s, %s);
        """, (name, now, contact))
        connection.commit()
        cur.close()
        return jsonify({"message": "Teen attendance recorded successfully!"}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/teens_get_dates', methods=['GET'])
def teens_get_attendance_dates():
    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT DATE("Date") FROM public."AGT_Attendacne"
            WHERE "Name" IN (
                SELECT CONCAT("first_name", ' ', "last_name")
                FROM public."AGT_TEENS_DATA_RECORDS"
            )
            ORDER BY DATE("Date") DESC;
        """)
        dates = [str(row[0]) for row in cur.fetchall()]
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/teens_download_attendance_csv', methods=['GET'])
def download_teens_attendance_csv():
    import csv
    from io import StringIO

    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify({"error": "Date parameter is required"}), 400

    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT "Name", "Date", "Contact"
            FROM public."AGT_Attendacne"
            WHERE DATE("Date") = %s
              AND "Name" IN (
                  SELECT CONCAT("first_name", ' ', "last_name")
                  FROM public."AGT_TEENS_DATA_RECORDS"
              );
        """, (selected_date,))
        records = cur.fetchall()
        cur.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Date", "Contact"])
        writer.writerows(records)
        csv_data = output.getvalue().encode('utf-8')

        return (
            csv_data,
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename="AGT_Teens_Attendance_{selected_date}.csv"'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/teens_roll_call_names', methods=['GET'])
def teens_roll_call_names():
    try:
        cur = connection.cursor()
        cur.execute("""
            SELECT CONCAT("first_name", ' ', "last_name") AS full_name, contact_number
            FROM public."AGT_TEENS_DATA_RECORDS"
            ORDER BY "first_name", "last_name";
        """)
        data = [{"name": row[0], "contact": row[1]} for row in cur.fetchall()]
        cur.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ======================= CHILDREN CHURCH ROUTES ==============================
# =============================================================================

@app.route('/childrens_church')
def children_index():
    return render_template('agtchild.html')

@app.route('/childrens_church/search', methods=['POST'])
def children_search():
    keyword = request.form['keyword']
    cursor = connection.cursor()

    sql_query = """
        SELECT * FROM "public"."AGT_CHILDREN_DATA_RECORDS" 
        WHERE "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "age"::TEXT ILIKE %s 
           OR "gender" ILIKE %s
           OR "contact_number"::TEXT ILIKE %s
           OR "age_group" ILIKE %s
           OR "consent" ILIKE %s
           OR "birthday" ILIKE %s
        LIMIT 10
    """
    cursor.execute(sql_query, [f'%{keyword}%'] * 8)
    results = cursor.fetchall()
    cursor.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        records = [
            {
                "first_name": r[0],
                "last_name": r[1],
                "age": r[2],
                "gender": r[3],
                "contact_number": r[4],
                "age_group": r[5],
                "consent": r[6],
                "birthday": r[7]
            }
            for r in results
        ]
        return jsonify(records)

    return render_template('agtchild.html', results=results)

@app.route('/childrens_church/update', methods=['POST'])
def children_update():
    data = request.form
    cursor = connection.cursor()
    
    # SQL query to update the record
    sql_update = """
        UPDATE "public"."AGT_CHILDREN_DATA_RECORDS"
        SET "first_name" = %s, "last_name" = %s, "age" = %s, "gender" = %s, 
            "contact_number" = %s, "age_group" = %s, "consent" = %s, "birthday" = %s
        WHERE "first_name" = %s
    """
    
    # Execute the update query
    cursor.execute(sql_update, (
        data['first_name'], data['last_name'], data['age'], data['gender'],
        data['contact_number'], data['age_group'], data['consent'], data['birthday'],
        data['first_name']
    ))
    
    connection.commit()  # Commit the changes
    cursor.close()
    flash('Record updated successfully!')
    return redirect(url_for('children_index'))

@app.route('/childrens_church/insert', methods=['GET','POST'])
def children_insert():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        contact_number = request.form['contact_number']
        age_group = request.form['age_group']
        consent = request.form['consent']
        birthday = request.form['birthday']

        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."AGT_CHILDREN_DATA_RECORDS" ("first_name", "last_name", "age", "gender", "contact_number", "age_group", "consent", "birthday")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (first_name, last_name, age, gender, contact_number, age_group, consent, birthday))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Record inserted successfully!')
    return redirect(url_for('children_index'))

@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    data = request.get_json()
    name = data.get('name')
    contact = data.get('contact')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cur = connection.cursor()
        cur.execute("""
            INSERT INTO public."AGT_Attendacne" ("Name", "Date", "Contact")
            VALUES (%s, %s, %s);
        """, (name, now, contact))
        connection.commit()
        cur.close()
        return jsonify({"message": "Attendance recorded successfully!"})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/get_attendance_dates')
def get_attendance_dates():
    cur = connection.cursor()
    cur.execute("""
        SELECT DISTINCT DATE("Date") FROM public."AGT_Attendacne"
        ORDER BY DATE("Date") DESC
    """)
    dates = [str(r[0]) for r in cur.fetchall()]
    cur.close()
    return jsonify(dates)

@app.route('/download_attendance_csv')
def download_attendance_csv():
    import csv
    from io import StringIO
    date = request.args.get('date')
    cur = connection.cursor()
    cur.execute("""
        SELECT "Name", "Date", "Contact" FROM public."AGT_Attendacne"
        WHERE DATE("Date") = %s
    """, (date,))
    records = cur.fetchall()
    cur.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Name", "Date", "Contact"])
    cw.writerows(records)
    output = si.getvalue().encode('utf-8')

    return (
        output,
        200,
        {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="AGT_Attendance_{date}.csv"'
        }
    )

@app.route('/get_children_by_age_group')
def get_children_by_age_group():
    group = request.args.get('group')
    if not group:
        return jsonify([])

    age_range = {
        '0-5': (0, 5),
        '6-8': (6, 8),
        '9-12': (9, 12)
    }.get(group)

    if not age_range:
        return jsonify([])

    cursor = connection.cursor()
    cursor.execute("""
        SELECT CONCAT(first_name, ' ', last_name) AS name, contact_number
        FROM public."AGT_CHILDREN_DATA_RECORDS"
        WHERE age BETWEEN %s AND %s
        ORDER BY first_name, last_name
    """, age_range)
    results = [{"name": r[0], "contact": r[1]} for r in cursor.fetchall()]
    cursor.close()
    return jsonify(results)


# =============================================================================
# ========================== PROFILE FEATURES =================================
# =============================================================================

# ---------- Helpers ----------
def upload_to_github(file_storage):
    file_storage.stream.seek(0)
    filename = secure_filename(file_storage.filename)
    now = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{now}_{filename}"

    content = base64.b64encode(file_storage.read()).decode('utf-8')
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{unique_filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {"message": f"Upload {unique_filename}", "content": content}
    response = requests.put(api_url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        return response.json()['content']['download_url'], response.json()['content']['path']
    else:
        raise Exception(f"GitHub upload failed: {response.status_code}, {response.json()}")


def send_email(to, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@gmail.com', 'your_app_password')
        smtp.send_message(msg)


# --------------------------- Search User Records -----------------------------
@app.route('/search_user_records', methods=['GET'])
def search_user_records():
    keyword = request.args.get('keyword', '')
    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT id, first_name, last_name, contact_number, email
            FROM public."agt_user_data_records"
            WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s
            LIMIT 10
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        results = cur.fetchall()
        return jsonify([
            {"id": r[0], "first_name": r[1], "last_name": r[2], "contact_number": r[3], "email": r[4]}
            for r in results
        ])
    finally:
        cur.close()




# --------------------------- Register Profile --------------------------------
# --------------------------- Register Profile --------------------------------
@app.route('/register_profile', methods=['POST'])
def register_profile():
    try:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        # Generate unique profile_id
        profile_id = random.randint(1000000000, 9999999999)
        
        # Securely hash password
        #password_hash = generate_password_hash(password)

        cur = connection.cursor()

        # Insert with the raw password (⚠️ not hashed)
        cur.execute("""
            INSERT INTO public.agt_user_profile 
                (profile_id, user_id, user_name, email, password_hash, worker_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, DEFAULT, now(), now())
            RETURNING id
        """, (profile_id, user_id, username, email, password))

        new_id = cur.fetchone()[0]
        connection.commit()   # commit transaction
        cur.close()

        return jsonify({
            'message': 'Profile created successfully',
            'id': new_id,
            'profile_id': profile_id
        }), 201

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500


# --------------------------- Login Profile -----------------------------------
@app.route('/login_profile', methods=['POST'])
def login_profile():
    data = request.get_json()
    identity = data.get('identity')
    password = data.get('password')

    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT id, user_id, user_name, email
            FROM public."agt_user_profile"
            WHERE (user_name = %s OR email = %s) AND password_hash = %s
        """, (identity, identity, password))
        profile = cur.fetchone()
        if not profile:
            return jsonify({'error': 'Invalid login credentials'}), 401

        _, user_id, username, email = profile

        # Get user details
        cur.execute("""SELECT * FROM public."agt_user_data_records" WHERE id = %s""", (user_id,))
        user_row = cur.fetchone()
        details = dict(zip([d[0] for d in cur.description], user_row))

        # Worker check
        cur.execute("""SELECT * FROM public."agt_workers_voluntiers_records" WHERE user_id = %s""", (user_id,))
        worker_row = cur.fetchone()
        worker_details = None
        approval_status = None

        if worker_row:
            worker_details = dict(zip([d[0] for d in cur.description], worker_row))

            # Check approval table
            cur.execute("""SELECT approval_status FROM public."worker_approval" WHERE worker_id = %s""", (worker_details['worker_id'],))
            approval = cur.fetchone()
            if approval:
                approval_status = approval[0]
            else:
                approval_status = None

        return jsonify({
            'message': 'Login successful',
            'user': {
                'email': email,
                'username': username,
                'details': details,
                'worker': worker_details,
                'worker_approval_status': approval_status
            }
        }), 200


    finally:
        cur.close()


# --------------------------- Update User Details -----------------------------
@app.route('/update_user_details', methods=['POST'])
def update_user_details():
    data = request.get_json()
    email = data.get('email')
    updates = data.get('updates')
    if not email or not updates:
        return jsonify({'error': 'Missing parameters'}), 400

    cur = connection.cursor()
    try:
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [email]
        cur.execute(f"""
            UPDATE public."agt_user_data_records"
            SET {set_clause}, updated_at = NOW()
            WHERE email = %s
        """, values)
        connection.commit()
        return jsonify({'message': 'User record updated successfully'}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()


# --------------------------- Worker Registration -----------------------------

@app.route('/register_worker', methods=['POST'])
def register_worker():
    data = request.get_json()
    user_id = data.get('user_id')
    # --- collect all other fields as before ---
    date_of_birth = data.get('date_of_birth')
    emergency_contact_name = data.get('emergency_contact_name')
    emergency_contact_number = data.get('emergency_contact_number')
    emergency_contact_relationship = data.get('emergency_contact_relationship')
    role = data.get('role')
    position_type = data.get('position_type')
    department = data.get('department')
    start_date = data.get('start_date')
    dbs_check_date = data.get('dbs_check_date')
    dbs_certificate_number = data.get('dbs_certificate_number')
    safeguarding_training_date = data.get('safeguarding_training_date')
    medical_conditions = data.get('medical_conditions')
    consent = data.get('consent', False)

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    cur = connection.cursor()
    try:
        # Generate unique worker_id
        while True:
            worker_id = random.randint(1000, 9999)
            cur.execute('SELECT 1 FROM public."agt_workers_voluntiers_records" WHERE worker_id = %s', (worker_id,))
            if not cur.fetchone():
                break

        # Insert into workers table
        cur.execute("""
            INSERT INTO public."agt_workers_voluntiers_records"
            (worker_id, user_id, date_of_birth, emergency_contact_name, emergency_contact_number,
             emergency_contact_relationship, role, position_type, department, start_date,
             dbs_check_date, dbs_certificate_number, safeguarding_training_date,
             medical_conditions, consent, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            worker_id, user_id, date_of_birth, emergency_contact_name, emergency_contact_number,
            emergency_contact_relationship, role, position_type, department, start_date,
            dbs_check_date, dbs_certificate_number, safeguarding_training_date,
            medical_conditions, consent
        ))

        # Insert into approval table
        random_text = f"Approval request {random.randint(100000,999999)}"
        cur.execute("""
            INSERT INTO public."worker_approval"
            (worker_id, date_submitted, approval_status, details, date_approved)
            VALUES (%s, NOW(), %s, %s, %s)
        """, (worker_id, "pending_approval", random_text, "awaiting"))

        connection.commit()

        # Send notification email
        try:
            body = f"""
            Dear Admin,

            A member has registered to be a worker using the church web app. Please see details

            Role: {role}
            Position Type: {position_type}
            Department: {department}
            Date of Birth: {date_of_birth}
            Emergency Contact: {emergency_contact_name} ({emergency_contact_relationship}) - {emergency_contact_number}
            Start Date: {start_date}
            DBS Check Date: {dbs_check_date}
            DBS Certificate: {dbs_certificate_number}
            Safeguarding Training Date: {safeguarding_training_date}
            Medical Conditions: {medical_conditions}
            Consent: {consent}

            This is now submitted for approval. To approve this request sign into chukspace.

            Thanks
            AGT Data Management App
            """

            msg = MIMEText(body)
            msg["Subject"] = "New Worker Registration - Pending Approval"
            msg["From"] = "realgeoemy@gmail.com"
            msg["To"] = "chukwuemekaumunna@gmail.com"

            with smtplib.SMTP("smtp.gmail.com", 465) as server:
                server.login("yourchurchapp@gmail.com", "Oluwaseun1.")
                server.send_message(msg)
        except Exception as mail_error:
            print("Email sending failed:", mail_error)

        return jsonify({
            'message': f'You have registered for the position of {role} in the {department} department as a {position_type}. '
                       'Your form has been sent for approval. Once approved, your worker details will be displayed here, and you can modify where needed.'
        }), 201

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()




# =============================================================================
# =============================== MAIN ========================================
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)
