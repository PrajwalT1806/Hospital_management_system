from flask import Flask, send_from_directory, render_template, request, redirect, url_for, session
import hashlib
import sqlite3
import os
import json
from datetime import datetime
from flask_restful import Resource, Api
import pymongo
from flask_mail import Mail, Message
from bson.objectid import ObjectId



# client = MongoClient(config['mongo_uri'])
# db = client['your_database']  # Replace 'your_database' with your actual database name
# collection = db['reviews']  # Collection to store reviews
# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["Feedback"]
review_collection = mongo_db["Reviews"]
emergency_collection=mongo_db["emergency"]

# Importing resources from packages
from package.patient import Patients, Patient
from package.doctor import Doctors, Doctor
from package.appointment import Appointments, Appointment
from package.common import Common
from package.medication import Medication, Medications
from package.department import Departments, Department
from package.nurse import Nurse, Nurses
from package.room import Room, Rooms
from package.procedure import Procedure, Procedures 
from package.prescribes import Prescribes, Prescribe
from package.undergoes import Undergoess, Undergoes

# Load config from JSON file
with open('config.json') as data_file:
    config = json.load(data_file)

app = Flask(__name__, static_url_path='')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

api = Api(app)

# Add resources to API
api.add_resource(Patients, '/patient')
api.add_resource(Patient, '/patient/<int:id>')
api.add_resource(Doctors, '/doctor')
api.add_resource(Doctor, '/doctor/<int:id>')
api.add_resource(Appointments, '/appointment')
api.add_resource(Appointment, '/appointment/<int:id>')
api.add_resource(Common, '/common')
api.add_resource(Medications, '/medication')
api.add_resource(Medication, '/medication/<int:code>')
api.add_resource(Departments, '/department')
api.add_resource(Department, '/department/<int:department_id>')
api.add_resource(Nurses, '/nurse')
api.add_resource(Nurse, '/nurse/<int:id>')
api.add_resource(Rooms, '/room')
api.add_resource(Room, '/room/<int:room_no>')
api.add_resource(Procedures, '/procedure')
api.add_resource(Procedure, '/procedure/<int:code>')
api.add_resource(Prescribes, '/prescribes')
api.add_resource(Undergoess, '/undergoes')





# Sender's name and email address
# Function to encrypt password
def encrypt_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to create user table
def create_user_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, gender TEXT, password TEXT, role TEXT)''')
    conn.commit()
    conn.close()

create_user_table()

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        password = encrypt_password(password)
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, password, role))
        user = c.fetchone()
        conn.close()

        if user:
            session['email'] = email
            if user[5] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[5] == 'user':
                return redirect(url_for('pat'))
        else:
            message = 'Invalid email, password, or role'

    return render_template('login.html', message=message)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        gender = request.form['gender']
        password = request.form['password']
        role = request.form['role']

        password = encrypt_password(password)

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, gender, password, role) VALUES (?, ?, ?, ?, ?)", (name, email, gender, password, role))
            conn.commit()
            conn.close()
            message = 'Registered successfully. Please log in.'
            return redirect(url_for('login', message=message))
        except sqlite3.IntegrityError as e:
            message = 'Email already exists'
            print("Error:", e)

    return render_template('register.html', message=message)

# Index route
@app.route('/')
def index():
    return render_template('login.html')

# Admin dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'email' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Patient dashboard route
@app.route('/pat.html')
def pat():
    if 'email' in session:
        today_date = datetime.now().strftime("%Y-%m-%d")
        return render_template('pat.html', today_date=today_date)
    else:
        return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('index'))

# About page route
@app.route('/about.html')
def about():
    if 'email' in session:
        return render_template('about.html')
    else:
        return redirect(url_for('pat'))

# Department page route
@app.route('/dep.html')
def dep():
    if 'email' in session:
        return render_template('dep.html')
    else:
        return redirect(url_for('pat'))
    
@app.route('/doc.html')
def doc():
    if 'email' in session:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM doctor")
        doctors = c.fetchall()
        conn.close()
        return render_template('doc.html', doctors=doctors)
    else:
        return redirect(url_for('pat'))
    

@app.route('/patdetails.html', methods=['GET', 'POST'])
def patdetails():
    message = None
    
    if 'email' in session:  # Check if email is in session
        email = session['email']  # Retrieve email from session
        
        if request.method == 'POST':  # Check if request method is POST
            first_name = request.form['pat_first_name']
            last_name = request.form['pat_last_name']
            insurance_no = request.form['pat_insurance_no']
            phone_no = request.form['pat_ph_no']
            registration_date = request.form['pat_date']
            address = request.form['pat_address']
            
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            
            try:
                # Check if the phone number is already registered for the particular date
                c.execute("SELECT * FROM patient WHERE pat_date = ? AND pat_ph_no = ?", (registration_date, phone_no))
                if c.fetchone() is not None:
                    message = 'Patient already registered for this date and phone number.'
                else:
                    c.execute("INSERT INTO patient (pat_first_name, pat_last_name, pat_insurance_no, pat_ph_no, pat_date, pat_address) VALUES (?, ?, ?, ?, ?, ?)", (first_name, last_name, insurance_no, phone_no, registration_date, address))
                    conn.commit()
                    message = 'Patient registered successfully.'
                   
                    return redirect(url_for('pat', message=message))
            except sqlite3.IntegrityError as e:
                message = 'Error registering patient.'
                print("Error:", e)
            finally:
                conn.close()

    return render_template('patdetails.html', message=message)



@app.route('/review.html', methods=['GET','POST'])
def review():
    if 'email' in session:
        if request.method == 'POST':
            appointment_date = request.form['appointmentDate']
            doctor_name = request.form['doctorName']
            rating = int(request.form['rating'])
            suggestions = request.form['suggestions']

            # Insert data into MongoDB
            feedback_data = {
                'appointment_date': appointment_date,
                'doctor_name': doctor_name,
                'rating': rating,
                'suggestions': suggestions
            }
            review_collection.insert_one(feedback_data)

            # Redirect to thank you page or wherever you want
            return redirect(url_for('pat'))
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM doctor")
        doctors = c.fetchall()
        conn.close()

    # Handle unauthorized access or other cases
    return render_template('review.html',doctors=doctors)


@app.route('/hist.html', methods=['GET', 'POST'])
def hist():
    if 'email' in session:  # Assuming the user is logged in
        if request.method == 'POST':
            phone_number = request.form['phone']
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM patient WHERE pat_ph_no=?", (phone_number,))
            history = c.fetchall()
            conn.close()
            return render_template('hist.html', history=history)
        else:
            return render_template('hist.html')  # Show the form to enter phone number
    else:
        return redirect(url_for('pat')) 
@app.route('/show.html')
def show():
    # Check if admin is logged in
    if 'email' not in session :
        return redirect(url_for('login'))  # Redirect to login if not logged in or not an admin
    
    # Fetch reviews from MongoDB
    reviews = review_collection.find()
    return render_template('show.html', reviews=reviews)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'tejaskumarv.cs21@rvce.edu.in'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'welcome123*'  # Your Gmail password

mail = Mail(app)

@app.route('/eme.html', methods=['GET', 'POST'])
def eme():
    message = None
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        location = request.form.get('location')
        symptoms = request.form.get('symptoms')

        # Check if all fields are filled
        if not (phone and name and location and symptoms):
            message = 'Please fill all details.'
            return render_template('eme.html', message=message)

        # Define the default value for the 'value' field
        value = False

        # Store data in MongoDB with 'value' set to False
        emergency_collection.insert_one({
            'phone': phone,
            'name': name,
            'location': location,
            'symptoms': symptoms,
            'value': value  # Adding the 'value' field with the default value
        })

        # Return success message
        message = 'Emergency appointment submitted successfully.'

        # Fetch emergency appointments with value 'False' from MongoDB
        emergency_appointments = emergency_collection.find({'value': False})

        # Fetch all users with role 'admin' from database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE role='admin'")
        admin_emails = [row[0] for row in c.fetchall()]
        conn.close()

        # Send email to each admin and update value to True
        for appointment in emergency_appointments:
            for email in admin_emails:
                # Create message for each admin
                msg = Message("Emergency Appointment", sender=("Tejas Kumar V", "tejaskumarv.cs21@rvce.edu.in"), recipients=[email])
                msg.body = f"Hello Admin,\n\nAn emergency appointment has been submitted with the following details:\n\nName: {appointment['name']}\nPhone: {appointment['phone']}\nLocation: {appointment['location']}\nSymptoms: {appointment['symptoms']}\n\nPlease take appropriate action.\n\nRegards,\nYour Hospital Team"
                
                # Send email
                mail.send(msg)
                
            # Update value to True after sending email
            emergency_collection.update_one({'_id': appointment['_id']}, {'$set': {'value': True}})

    return render_template('eme.html', message=message)
# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
