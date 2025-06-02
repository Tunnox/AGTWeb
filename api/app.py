from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key

# Configure your PostgreSQL database connection here
connection = psycopg2.connect(dbname='AGT', user='postgres', password='pgsqtk116chuk95', host='chukspace.ctiuisa62ks5.eu-north-1.rds.amazonaws.com', port='5432')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    cursor = connection.cursor()
    
    # SQL query to search for data in DATA_RECORDS table
    sql_query = f"""
        SELECT * FROM "public"."data_records" 
        WHERE "title" ILIKE %s OR
           "first_name" ILIKE %s 
           OR "last_name" ILIKE %s 
           OR "age"::TEXT ILIKE %s 
           OR "gender" ILIKE %s
           OR "date_of_birth"::TEXT ILIKE %s
           OR "address" ILIKE %s
           OR "email" ILIKE %s
           OR "mobile_number"::TEXT ILIKE %s 
           OR "status" ILIKE %s  
           OR "department" ILIKE %s
           OR "relationship_status" ILIKE %s
           OR "employement_status" ILIKE %s
           OR "consent" ILIKE %s
    """
    
    # Execute the query with wildcard search
    cursor.execute(sql_query, [f'%{keyword}%'] * 14)
    
    results = cursor.fetchall()
    
    # Close cursor after fetching results
    cursor.close()
    
    return render_template('index.html', results=results)


@app.route('/insert', methods=['GET','POST'])
def insert():
    if request.method == 'POST':
        title = request.form['title']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        date_of_birth = request.form['date_of_birth']
        address = request.form['address']
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        status = request.form['status']
        department = request.form['department']
        relationship_status = request.form['relationship_status']
        employment_status = request.form['employment_status']
        consent = request.form['consent']

        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO "public"."data_records" ("title", "first_name", "last_name", "age", "gender", "date_of_birth", "address", "email", "mobile_number", "status", "department", "relationship_status", "employement_status", "consent")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (title, first_name, last_name, age, gender,date_of_birth, address, email, mobile_number, status,department, relationship_status, employment_status, consent))
        connection.commit()  # Don't forget to commit the transaction!
        cursor.close()
    
    flash('Record inserted successfully!')
    return redirect(url_for('index'))

@app.route('/insert_attendance', methods=['GET', 'POST'])
def insert_attendance():
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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
    
    
