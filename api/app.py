from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2
from werkzeug.utils import secure_filename
import os
import base64
import requests
import datetime
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key
load_dotenv()

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
# Configure your PostgreSQL database connection here
connection = psycopg2.connect(dbname='AGT', user='postgres', password='pgsqtk116chuk95', host='chukspace.ctiuisa62ks5.eu-north-1.rds.amazonaws.com', port='5432')

#_____________________________AGT LOGIN______________________________________________________________________________________________
# Adult Data Management Routes
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/my_profile')
def my_profile_page():
    return render_template('my_profile.html')

@app.route('/profile_view')
def my_profile_page():
    return render_template('profile_view.html')

@app.route('/login_admin')
def login_admin():
    return render_template('login.html')
    
@app.route('/agt_login', methods=['POST'])
def agt_login():
    data = request.get_json()
    login_username = data['loginUsername']
    login_password = data['loginPassword']

    cur = connection.cursor()
    try:
        cur.execute(
            'SELECT * FROM "public"."AGT_USER_LOGIN" WHERE ("USERNAME" = %s OR "EMAIL" = %s) AND "PASSWORD" = %s;', 
            (login_username, login_username, login_password)
        )
        user = cur.fetchone()
        
        if user:
            return jsonify({"message": "Login successful!", "success": True}), 200
        else:
            return jsonify({"message": "Invalid credentials, please create an account."}), 401
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    finally:
        cur.close()
        
#_____________________________AGT HOME PAGE_____________________________________________________________________________________________
@app.route('/main')
def home_index():
    return render_template('main.html')
#____________________________AGT ADULT CHURCH______________________________________________________________________________________________

@app.route('/adult_church')
def adult_index():
    return render_template('agtadult.html')

@app.route('/adult_church/search', methods=['POST'])
def adult_search():
    keyword = request.form['keyword']
    cursor = connection.cursor()

    sql_query = """
        SELECT * FROM "public"."AGT_ADULT_DATA_RECORDS" 
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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        records = [
            {
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
            for r in results
        ]
        return jsonify(records)

    return render_template('agtadult.html', results=results)


@app.route('/adult_church/update', methods=['POST'])
def adult_update():
    data = request.form
    cursor = connection.cursor()
    
    # SQL query to update the record
    sql_update = """
        UPDATE "public"."AGT_ADULT_DATA_RECORDS"
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
            INSERT INTO "public"."AGT_ADULT_DATA_RECORDS" ("first_name", "last_name", "age", "gender", "birthday", "contact_number", "age_group", "department", "relationship_status", "email", "address", "consent")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (first_name, last_name, age, gender, birthday, contact_number, age_group, department, relationship_status, email, address, consent))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Record inserted successfully!')
    return redirect(url_for('adult_index'))

@app.route('/record_adult_attendance', methods=['POST'])
def record_adult_attendance():
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



#_____________________________AGT TEENS CHURCH___________________________________________________________________________________________________

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



#_______________________AGT CHILDREN CHURCH__________________________________________________________________________________________________________
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
#__________________________________________________________________________________________________________________________________
#__________________________________________________________________________________________________________________________________
# Profile feature routes for user registration, login, and record view/edit
# Profile feature routes for user registration, login, and record view/edit

#Functions 
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


@app.route('/search_user_records', methods=['GET'])
def search_user_records():
    keyword = request.args.get('keyword', '')
    cur = connection.cursor()
    try:
        query = """
            SELECT first_name, last_name, contact_number FROM (
                SELECT "first_name", "last_name", "contact_number" FROM "public"."AGT_TEENS_DATA_RECORDS"
                WHERE "first_name" ILIKE %s OR "last_name" ILIKE %s OR "email" ILIKE %s
                UNION
                SELECT "first_name", "last_name", "contact_number" FROM "public"."AGT_ADULT_DATA_RECORDS"
                WHERE "first_name" ILIKE %s OR "last_name" ILIKE %s OR "email" ILIKE %s
                UNION
                SELECT "first_name", "last_name", "contact_number" FROM "public"."AGT_CHILDREN_DATA_RECORDS"
                WHERE "first_name" ILIKE %s OR "last_name" ILIKE %s
            ) AS combined
            LIMIT 10;
        """
        params = tuple([f"%{keyword}%"] * 8)
        cur.execute(query, params)
        results = cur.fetchall()
        return jsonify([{"first_name": r[0], "last_name": r[1], "contact_number": r[2]} for r in results])
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/register_profile', methods=['POST'])
def register_profile():
    try:
        data = request.form
        profile_pic = request.files['profile_picture']
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        email = data.get('email') or f"{username}@agt.org"
        fullname = data.get('fullname')
        contact_number = data.get('contact_number')

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        cur = connection.cursor()

        # ✅ Check for existing profile by full name, username, or email
        cur.execute("""
            SELECT "Full_Name", "Username", "Email" FROM public."AGT_User_Profile"
            WHERE "Full_Name" = %s OR "Username" = %s OR "Email" = %s
            LIMIT 1
        """, (fullname, username, email))
        existing = cur.fetchone()

        if existing:
            existing_name, existing_user, existing_email = existing
            if existing_name == fullname:
                return jsonify({'error': 'A profile already exists for this user.'}), 409
            elif existing_user == username:
                return jsonify({'error': 'Username is already taken.'}), 409
            elif existing_email == email:
                return jsonify({'error': 'Email is already registered.'}), 409

        # ✅ Upload picture and insert new profile
        profile_pic.stream.seek(0)
        url, _ = upload_to_github(profile_pic)

        cur.execute("""
            INSERT INTO public."AGT_User_Profile" 
            ("Email", "Username", "Password", "Full_Name", "Contact_Number", "Profile_Picture")
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, username, password, fullname, contact_number, url))

        connection.commit()
        cur.close()
        return jsonify({'message': 'Profile created successfully!'}), 201

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/login_profile', methods=['POST'])
def login_profile():
    data = request.get_json()
    identity = data.get('identity')
    password = data.get('password')
    cur = connection.cursor()
    cur.execute("""
        SELECT "Email", "Username", "Full_Name", "Contact_Number", "Profile_Picture"
        FROM public."AGT_User_Profile"
        WHERE ("Username" = %s OR "Email" = %s) AND "Password" = %s;
    """, (identity, identity, password))
    user = cur.fetchone()
    cur.close()
    if not user:
        return jsonify({'error': 'Invalid login credentials'}), 401
    return jsonify({
        'message': 'Login successful',
        'user': {
            'email': user[0],
            'username': user[1],
            'fullname': user[2],
            'contact_number': user[3],
            'profile_picture': user[4]
        }
    }), 200
    
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    identity = data.get('identity')
    new_password = data.get('new_password')

    if not identity or not new_password:
        return jsonify({'error': 'Missing identity or new password'}), 400

    # ✅ Server-side password strength validation
    if (len(new_password) < 8 or
        not re.search(r'[A-Z]', new_password) or
        not re.search(r'[a-z]', new_password) or
        not re.search(r'[0-9]', new_password) or
        not re.search(r'[^a-zA-Z0-9]', new_password)):
        return jsonify({'error': 'Password is too weak. Must include uppercase, lowercase, number, and symbol.'}), 400

    cur = connection.cursor()
    try:
        # Check if user exists and update password
        cur.execute("""
            UPDATE public."AGT_User_Profile"
            SET "Password" = %s
            WHERE "Username" = %s OR "Email" = %s
            RETURNING "Email", "Full_Name";
        """, (new_password, identity, identity))

        result = cur.fetchone()
        if not result:
            return jsonify({'error': 'User not found'}), 404

        email, full_name = result
        connection.commit()

        # ✅ Send confirmation email
        send_email(
            to=email,
            subject="Your AGT Profile Password Was Reset",
            body=f"Hello {full_name},\n\nYour password has been reset successfully.\n\nIf you didn't request this, please contact admin immediately."
        )

        return jsonify({'message': 'Password reset successful! A confirmation email has been sent.'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

#______--------_______________--------
def send_email(to, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'your_email@gmail.com'  # ✅ Replace with your email
    msg['To'] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@gmail.com', 'your_app_password')  # ✅ Use App Password
        smtp.send_message(msg)

@app.route('/get_user_details', methods=['POST'])
def get_user_details():
    data = request.get_json()
    email = data.get('email')
    cur = connection.cursor()
    user_data = None
    try:
        cur.execute('SELECT * FROM "public"."AGT_TEENS_DATA_RECORDS" WHERE "email" = %s LIMIT 1', (email,))
        result = cur.fetchone()
        if result:
            user_data = {'category': 'teens', 'data': dict(zip([desc[0] for desc in cur.description], result))}
        else:
            cur.execute('SELECT * FROM "public"."AGT_ADULT_DATA_RECORDS" WHERE "email" = %s LIMIT 1', (email,))
            result = cur.fetchone()
            if result:
                user_data = {'category': 'adult', 'data': dict(zip([desc[0] for desc in cur.description], result))}
            else:
                cur.execute('SELECT * FROM "public"."AGT_CHILDREN_DATA_RECORDS" WHERE "email" = %s LIMIT 1', (email,))
                result = cur.fetchone()
                if result:
                    user_data = {'category': 'children', 'data': dict(zip([desc[0] for desc in cur.description], result))}
        if user_data:
            return jsonify(user_data), 200
        else:
            return jsonify({'error': 'User data not found in any group'}), 404
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/update_user_details', methods=['POST'])
def update_user_details():
    data = request.get_json()
    email = data.get('email')
    updates = data.get('updates')
    table = data.get('category')
    if not email or not updates or not table:
        return jsonify({'error': 'Missing parameters'}), 400
    cur = connection.cursor()
    try:
        valid_tables = {
            'teens': 'AGT_TEENS_DATA_RECORDS',
            'adult': 'AGT_ADULT_DATA_RECORDS',
            'children': 'AGT_CHILDREN_DATA_RECORDS'
        }
        table_name = valid_tables.get(table)
        if not table_name:
            return jsonify({'error': 'Invalid category'}), 400
        set_clause = ', '.join(f'"{k}" = %s' for k in updates)
        values = list(updates.values()) + [email]
        cur.execute(f"""
            UPDATE public."{table_name}"
            SET {set_clause}
            WHERE "email" = %s
        """, values)
        connection.commit()
        return jsonify({'message': 'User record updated successfully'}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

if __name__ == '__main__':
    app.run(debug=True)
