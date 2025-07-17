from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key

# Configure your PostgreSQL database connection here
connection = psycopg2.connect(dbname='AGT', user='postgres', password='pgsqtk116chuk95', host='chukspace.ctiuisa62ks5.eu-north-1.rds.amazonaws.com', port='5432')

#_____________________________AGT LOGIN______________________________________________________________________________________________
# Adult Data Management Routes
@app.route('/')
def index():
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
@app.route('/agt_home')
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
    
    # SQL query to search for data in DATA_RECORDS table
    sql_query = f"""
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
    """
    
    # Execute the query with wildcard search
    cursor.execute(sql_query, [f'%{keyword}%'] * 12)
    
    results = cursor.fetchall()
    
    # Close cursor after fetching results
    cursor.close()
    
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

@app.route('/adult_church/insert_attendance', methods=['GET', 'POST'])
def adult_insert_attendance():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date = request.form['date']

        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."ADULT_ATTENDANCE_MANAGER" ("first_name", "last_name", "date")
            VALUES (%s, %s, %s);
        """, (first_name, last_name, date))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Attendance record inserted successfully!')
    return redirect(url_for('adult_index'))

#_____________________________AGT TEENS CHURCH___________________________________________________________________________________________________

@app.route('/teens_church')
def teens_index():
    return render_template('agtteens.html')

@app.route('/teens_church/search', methods=['POST'])
def teens_search():
    keyword = request.form['keyword']
    cursor = connection.cursor()
    
    # SQL query to search for data in DATA_RECORDS table
    sql_query = f"""
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
    """
    
    # Execute the query with wildcard search
    cursor.execute(sql_query, [f'%{keyword}%'] * 12)
    
    results = cursor.fetchall()
    
    # Close cursor after fetching results
    cursor.close()
    
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

@app.route('/teens_church/insert_attendance', methods=['GET', 'POST'])
def teens_insert_attendance():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date = request.form['date']

        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."attendance_manager" ("first_name", "last_name", "date")
            VALUES (%s, %s, %s);
        """, (first_name, last_name, date))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Attendance record inserted successfully!')
    return redirect(url_for('teens_index'))

@app.route('/teens_church/api/search')
def teens_api_search():
    keyword = request.args.get('keyword', '')
    cursor = connection.cursor()
    sql_query = """
        SELECT * FROM "public"."AGT_TEENS_DATA_RECORDS" 
        WHERE "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "email" ILIKE %s
    """
    cursor.execute(sql_query, [f'%{keyword}%'] * 3)
    rows = cursor.fetchall()
    cursor.close()
    records = [{
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
    } for r in rows]
    return jsonify(records)


#_______________________AGT CHILDREN CHURCH__________________________________________________________________________________________________________
@app.route('/childrens_church')
def children_index():
    return render_template('agtchild.html')

@app.route('/childrens_church/search', methods=['POST'])
def children_search():
    keyword = request.form['keyword']
    cursor = connection.cursor()
    
    # SQL query to search for data in DATA_RECORDS table
    sql_query = f"""
        SELECT * FROM "public"."AGT_CHILDREN_DATA_RECORDS" 
        WHERE "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "age"::TEXT ILIKE %s 
           OR "gender" ILIKE %s
           OR "contact_number"::TEXT ILIKE %s
           OR "age_group" ILIKE %s
           OR "consent" ILIKE %s
           OR "birthday" ILIKE %s
    """
    
    # Execute the query with wildcard search
    cursor.execute(sql_query, [f'%{keyword}%'] * 8)
    
    results = cursor.fetchall()
    
    # Close cursor after fetching results
    cursor.close()
    
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

@app.route('/childrens_church/insert_attendance', methods=['GET', 'POST'])
def children_insert_attendance():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date = request.form['date']

        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."attendance_manager" ("first_name", "last_name", "date")
            VALUES (%s, %s, %s);
        """, (first_name, last_name, date))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Attendance record inserted successfully!')
    return redirect(url_for('children_index'))
#__________________________________________________________________________________________________________________________________
if __name__== '__main__':
    app.run(debug=True)
