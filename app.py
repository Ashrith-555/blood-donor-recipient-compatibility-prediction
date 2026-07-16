# app.py
from flask import Flask, render_template, request, redirect, session, url_for, flash
import re
import numpy as np
import joblib
import webbrowser
from werkzeug.serving import is_running_from_reloader
import mysql.connector
import pandas as pd
import json
from datetime import datetime

app=Flask(__name__)
app.secret_key = "secret123"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

@app.route('/team')
def team():
    return render_template("team.html")

@app.route('/info')
def info():
    return render_template("info.html")

@app.route('/clinical_guide')
def clinical_guide():
    return render_template("clinical_guide.html")

@app.route("/userlogin")
def userlogin():
    return render_template("userlogin.html")

# ------------------- Database Connection -------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        database="medicaldatabase",
         use_pure=True
        )
        return conn
    except mysql.connector.Error as e:
        print("❌ DB Connection Error:", e)
        return None


# ------------------- User Login Helpers -------------------
def check_tblusers_login(userid, password, role):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)  # <-- dictionary cursor
    cursor.execute(
        "SELECT * FROM tblusers WHERE userid=%s AND password=%s AND usertype=%s",
        (userid, password, role)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def check_patient_login(patientid, password):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM tblpatients WHERE patientid=%s AND password=%s",
        (patientid, password)
    )
    patient = cursor.fetchone()
    conn.close()
    return patient


# ------------------- Login Routes -------------------
@app.route("/adminlogin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        userid = request.form["userid"]
        password = request.form["password"]

        user = check_tblusers_login(userid, password, "admin")
        if user:
            session.update({"userid": user["userid"], "username": user["name"], "role": "admin"})
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_home"))
        else:
            flash("Invalid Admin credentials!", "danger")
    return render_template("adminlogin.html")

@app.route("/receptionistlogin", methods=["GET", "POST"])
def receptionist_login():
    if request.method == "POST":
        userid = request.form["userid"]
        password = request.form["password"]

        user = check_tblusers_login(userid, password, "receptionist")
        if user:
            session.update({"userid": user["userid"], "username": user["name"], "role": "receptionist"})
            flash("Receptionist login successful!", "success")
            return redirect(url_for("receptionist_home"))
        else:
            flash("Invalid Receptionist credentials!", "danger")
    return render_template("receptionistlogin.html")

@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        userid = request.form["userid"]
        password = request.form["password"]

        user = check_tblusers_login(userid, password, "doctor")
        if user:
            session.update({"userid": user["userid"], "username": user["name"], "role": "doctor"})
            flash("Doctor login successful!", "success")
            return redirect(url_for("doctor_home"))
        else:
            flash("Invalid Doctor credentials!", "danger")
    return render_template("doctorlogin.html")

@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        patientid = request.form["patientid"]
        password = request.form["password"]

        patient = check_patient_login(patientid, password)
        if patient:
            session.update({"userid": patient["patientid"], "username": patient["name"], "role": "patient"})
            flash("Patient login successful!", "success")
            return redirect(url_for("patient_home"))
        else:
            flash("Invalid Patient credentials!", "danger")
    return render_template("patientlogin.html")


# ------------------- Home/Dashboard Routes -------------------
@app.route("/adminhome")
def admin_home():
    if session.get("role") == "admin":
        return render_template("adminhome.html", username=session["username"])
    return redirect(url_for("adminlogin"))

@app.route("/receptionisthome")
def receptionist_home():
    if session.get("role") == "receptionist":
        return render_template("receptionisthome.html", username=session["username"])
    return redirect(url_for("receptionist_login"))

@app.route("/doctorhome")
def doctor_home():
    if session.get("role") == "doctor":
        return render_template("doctorhome.html", username=session["username"])
    return redirect(url_for("doctor_login"))

@app.route("/patienthome")
def patient_home():
    if session.get("role") == "patient":
        return render_template("patient_home.html", username=session["username"])
    return redirect(url_for("patient_login"))

# ------------------- USER MANAGEMENT -------------------

# Show all users
@app.route("/users")
def users_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblusers where usertype!=%s", ('admin',))
    users = cursor.fetchall()
    conn.close()
    return render_template("users_list.html", users=users)


# Add User
@app.route("/adduser", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        userid = request.form.get("userid", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        emailid = request.form.get("emailid", "").strip().lower()
        usertype = request.form.get("usertype", "")

        # Server-side validation
        errors = []
        if not re.match(r"^[a-zA-Z0-9_]+$", userid):
            errors.append("Invalid UserID format. Only letters, numbers, and underscores are allowed.")
        if not re.match(r"^[a-zA-Z\s]+$", name):
            errors.append("Invalid Name format. Only letters and spaces are allowed.")
        if not re.match(r"^[6-9]\d{9}$", mobile):
            errors.append("Invalid Mobile Number format. Must be 10 digits starting with 6-9.")
        if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", emailid):
            errors.append("Invalid Email format. Only @gmail.com is allowed.")
        if not password:
            errors.append("Password is required.")
        if not usertype:
            errors.append("User Type is required.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for("add_user"))

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return redirect(url_for("add_user"))
            
        cursor = conn.cursor(dictionary=True)
        
        # Check for duplicate UserID or Email
        cursor.execute("SELECT userid, emailid FROM tblusers WHERE userid=%s OR emailid=%s", (userid, emailid))
        existing_user = cursor.fetchone()
        
        if existing_user:
            if existing_user['userid'] == userid:
                flash("❌ UserID already exists. Please choose a different one.", "danger")
            elif existing_user['emailid'] == emailid:
                flash("❌ Email ID is already registered.", "danger")
            conn.close()
            return redirect(url_for("add_user"))

        try:
            cursor.execute("""
                INSERT INTO tblusers (userid, password, name, mobile, emailid, usertype)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (userid, password, name, mobile, emailid, usertype))
            conn.commit()
            flash("✅ User added successfully!", "success")
        except Exception as e:
            flash("❌ An error occurred while adding the user.", "danger")
            print("Error adding user:", e)
        finally:
            conn.close()

        return redirect(url_for("users_list"))

    return render_template("add_user.html")


# Edit User (load form with existing data)
@app.route("/edituser/<userid>", methods=["GET"])
def edit_user(userid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblusers WHERE userid=%s", (userid,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        flash("❌ User not found!", "danger")
        return redirect(url_for("users_list"))

    return render_template("edit_user.html", user=user)


# Update User (after editing)
@app.route("/updateuser/<userid>", methods=["POST"])
def update_user(userid):
    password = request.form["password"]
    name = request.form["name"]
    mobile = request.form["mobile"]
    emailid = request.form["emailid"]
    usertype = request.form["usertype"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tblusers
        SET password=%s, name=%s, mobile=%s, emailid=%s, usertype=%s
        WHERE userid=%s
    """, (password, name, mobile, emailid, usertype, userid))
    conn.commit()
    conn.close()

    flash("✅ User updated successfully!", "success")
    return redirect(url_for("users_list"))


# Delete User
@app.route("/deleteuser/<userid>", methods=["GET"])
def delete_user(userid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tblusers WHERE userid=%s", (userid,))
    conn.commit()
    conn.close()

    flash("🗑 User deleted successfully!", "success")
    return redirect(url_for("users_list"))

# ------------------- Admin Update Password -------------------
@app.route("/admin/updatepassword", methods=["GET", "POST"])
def admin_updatepassword():
    if "userid" not in session or session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("New passwords do not match!", "danger")
            return redirect(url_for("admin_updatepassword"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify current password
        cursor.execute("SELECT * FROM tblusers WHERE userid=%s AND password=%s AND usertype='admin'",
                       (session["userid"], current_password))
        user = cursor.fetchone()

        if not user:
            flash("Current password is incorrect!", "danger")
            conn.close()
            return redirect(url_for("admin_updatepassword"))

        # Update with new password
        cursor.execute("UPDATE tblusers SET password=%s WHERE userid=%s",
                       (new_password, session["userid"]))
        conn.commit()
        conn.close()

        flash("Password updated successfully!", "success")
        return redirect(url_for("admin_home"))

    return render_template("admin_updatepassword.html")





# ------------------- Add Patient -------------------
@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        patientid = request.form.get("patientid", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        mobile = request.form.get("mobile", "").strip()

        errors = []
        if not re.match(r"^[a-zA-Z0-9_]+$", patientid):
            errors.append("Invalid Patient ID format.")
        if not re.match(r"^[a-zA-Z\s]+$", name):
            errors.append("Invalid Name format.")
        if not re.match(r"^[6-9]\d{9}$", mobile):
            errors.append("Invalid Mobile Number format.")
        if not address:
            errors.append("Address is required.")
        if not password:
            errors.append("Password is required.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for("add_patient"))

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return redirect(url_for("add_patient"))
            
        cursor = conn.cursor(dictionary=True)
        
        # Check for duplicate Patient ID
        cursor.execute("SELECT patientid FROM tblpatients WHERE patientid=%s", (patientid,))
        if cursor.fetchone():
            flash("❌ Patient ID already exists. Please choose a different one.", "danger")
            conn.close()
            return redirect(url_for("add_patient"))

        try:
            cursor.execute("INSERT INTO tblpatients (patientid, password, name, address, mobile) VALUES (%s, %s, %s, %s, %s)",
                           (patientid, password, name, address, mobile))
            conn.commit()
            flash("✅ Patient added successfully!", "success")
        except Exception as e:
            flash("❌ An error occurred while adding the patient.", "danger")
            print("Error adding patient:", e)
        finally:
            conn.close()
        return redirect(url_for("patients_list"))
    return render_template("add_patient.html")


# ------------------- Patients List -------------------
@app.route("/patients_list")
def patients_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblpatients")
    patients = cursor.fetchall()
    conn.close()
    return render_template("patients_list.html", patients=patients)


# ------------------- Edit Patient -------------------
@app.route("/edit_patient/<patientid>")
def edit_patient(patientid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblpatients WHERE patientid=%s", (patientid,))
    patient = cursor.fetchone()
    conn.close()
    return render_template("edit_patient.html", patient=patient)


# ------------------- Update Patient -------------------
@app.route("/update_patient/<patientid>", methods=["POST"])
def update_patient(patientid):
    password = request.form["password"]
    name = request.form["name"]
    address = request.form["address"]
    mobile = request.form["mobile"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""UPDATE tblpatients SET password=%s, name=%s, address=%s, mobile=%s 
                      WHERE patientid=%s""", (password, name, address, mobile, patientid))
    conn.commit()
    conn.close()

    flash("Patient updated successfully!", "success")
    return redirect(url_for("patients_list"))


# ------------------- Delete Patient -------------------
@app.route("/delete_patient/<patientid>")
def delete_patient(patientid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tblpatients WHERE patientid=%s", (patientid,))
    conn.commit()
    conn.close()
    flash("Patient deleted successfully!", "success")
    return redirect(url_for("patients_list"))

# ------------------- Receptionist Update Password -------------------
@app.route("/receptionist_updatepassword", methods=["GET", "POST"])
def receptionist_updatepassword():
    if "userid" not in session or session.get("role") != "receptionist":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("receptionist_login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        userid = session["userid"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check current password
        cursor.execute("SELECT * FROM tblusers WHERE userid=%s AND password=%s AND usertype=%s",
                       (userid, current_password, "receptionist"))
        user = cursor.fetchone()

        if not user:
            flash("❌ Current password is incorrect!", "danger")
        elif new_password != confirm_password:
            flash("❌ New password and confirm password do not match!", "danger")
        else:
            cursor.execute("UPDATE tblusers SET password=%s WHERE userid=%s",
                           (new_password, userid))
            conn.commit()
            flash("✅ Password updated successfully!", "success")

        conn.close()

    return render_template("receptionist_updatepassword.html")

# ------------------- Doctor Update Password -------------------
@app.route("/doctor_updatepassword", methods=["GET", "POST"])
def doctor_updatepassword():
    if "userid" not in session or session.get("role") != "doctor":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("doctor_login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        userid = session["userid"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM tblusers WHERE userid=%s AND password=%s AND usertype=%s",
                       (userid, current_password, "doctor"))
        user = cursor.fetchone()

        if not user:
            flash("❌ Current password is incorrect!", "danger")
        elif new_password != confirm_password:
            flash("❌ New password and confirm password do not match!", "danger")
        else:
            cursor.execute("UPDATE tblusers SET password=%s WHERE userid=%s",
                           (new_password, userid))
            conn.commit()
            flash("✅ Password updated successfully!", "success")

        conn.close()

    return render_template("doctor_updatepassword.html")


# ------------------- Patient Update Password -------------------
@app.route("/patient_updatepassword", methods=["GET", "POST"])
def patient_updatepassword():
    if "userid" not in session or session.get("role") != "patient":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("patient_login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        userid = session["userid"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM tblusers WHERE userid=%s AND password=%s AND usertype=%s",
                       (userid, current_password, "patient"))
        user = cursor.fetchone()

        if not user:
            flash("❌ Current password is incorrect!", "danger")
        elif new_password != confirm_password:
            flash("❌ New password and confirm password do not match!", "danger")
        else:
            cursor.execute("UPDATE tblusers SET password=%s WHERE userid=%s",
                           (new_password, userid))
            conn.commit()
            flash("✅ Password updated successfully!", "success")

        conn.close()

    return render_template("patient_updatepassword.html")


# ------------------- Logout -------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/rf_results")
def rf_results():
    import json

    # Load saved results from JSON
    try:
        with open("rf_results.json", "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        # If JSON not found, show message or redirect
        from flask import flash, redirect, url_for
        flash("RF results not found. Please run the Random Forest model first.", "warning")
        return redirect(url_for("doctor_home"))

    accuracy = results.get("accuracy", 0)
    confusion = results.get("confusion_matrix", [])
    report = results.get("classification_report", {})
    feature_importances = results.get("top_features", [])

    return render_template(
        "rf_model.html",
        accuracy=accuracy,
        confusion_matrix=confusion,
        classification_report=report,
        feature_importances=feature_importances,
        time_efficiency=results["time_efficiency"] 
    )

@app.route("/nb_results")
def nb_results():
    import json

    # Load saved results
    with open("nb_results.json", "r") as f:
        results = json.load(f)

    accuracy = results.get("accuracy", 0)
    confusion = results.get("confusion_matrix", [])
    report = results.get("classification_report", {})
   
    return render_template(
        "nb_model.html",
        accuracy=accuracy,
        confusion_matrix=confusion,
        classification_report=report,
       time_efficiency=results["time_efficiency"] 
    )


@app.route("/compare_models")
def compare_models():
    with open("rf_results.json", "r") as f:
        rf_results = json.load(f)
    with open("nb_results.json", "r") as f:
        nb_results = json.load(f)

    return render_template(
        "compare.html",
        rf_accuracy=rf_results["accuracy"],
        rf_confusion=rf_results["confusion_matrix"],
        rf_report=rf_results["classification_report"],
        rf_time=rf_results["time_efficiency"],
        nb_accuracy=nb_results["accuracy"],
        nb_confusion=nb_results["confusion_matrix"],
        nb_report=nb_results["classification_report"],
        nb_time=nb_results["time_efficiency"],
    )


# ------------------- ML Model (Prediction) -------------------
# Load the trained pipeline (includes preprocessing + model)
rf_pipeline = joblib.load("rf_pipeline.pkl")   # <-- Save your pipeline in rf_model.py as rf_pipeline.pkl

@app.route("/predict", methods=["GET", "POST"])
def predict():
    prediction = None
    form_data = {}

    if request.method == "POST":
        # Collect form data into dictionary
        form_data = {key: request.form[key] for key in request.form}

        # Convert into DataFrame for model
        input_df = pd.DataFrame([form_data])

        # Ensure numeric fields are cast properly
        numeric_cols = ["Donor_Age", "Donor_Hb_Level", "Recipient_Age", "History_Transfusions"]
        for col in numeric_cols:
            input_df[col] = pd.to_numeric(input_df[col])

        # Load pipeline & predict
        model = joblib.load("rf_pipeline.pkl")
        prediction = model.predict(input_df)[0]  # 0 or 1

    return render_template("predict.html", prediction=prediction, form_data=form_data)


@app.route('/doctor/treatments')
def doctor_treatments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tbltreatment ORDER BY datetime DESC")
    treatments = cursor.fetchall()
    conn.close()
    return render_template('doctor_treatment.html', treatments=treatments)

@app.route('/add_treatment', methods=['POST'])
def add_treatment():
    patientid = request.form.get('patientid', '').strip()
    treatment = request.form.get('treatment', '').strip()

    errors = []
    if not re.match(r"^[a-zA-Z0-9_]+$", patientid):
        errors.append("Invalid Patient ID format.")
    if not treatment:
        errors.append("Treatment description is required.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for('doctor_treatments'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect(url_for('doctor_treatments'))

    cursor = conn.cursor(dictionary=True)
    
    # Check if patient exists
    cursor.execute("SELECT patientid FROM tblpatients WHERE patientid=%s", (patientid,))
    if not cursor.fetchone():
        flash("❌ Patient ID does not exist in the system.", "danger")
        conn.close()
        return redirect(url_for('doctor_treatments'))

    try:
        cursor.execute(
            "INSERT INTO tbltreatment (patientid, treatment, datetime) VALUES (%s, %s, %s)",
            (patientid, treatment, datetime.now())
        )
        conn.commit()
        flash("✅ Treatment added successfully", "success")
    except Exception as e:
        flash("❌ An error occurred while adding the treatment.", "danger")
        print("Error adding treatment:", e)
    finally:
        conn.close()
        
    return redirect(url_for('doctor_treatments'))

@app.route('/edit_treatment/<int:treatmentid>', methods=['POST'])
def edit_treatment(treatmentid):
    patientid = request.form['patientid']
    treatment = request.form['treatment']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tbltreatment SET patientid=%s, treatment=%s WHERE treatmentid=%s",
        (patientid, treatment, treatmentid)
    )
    conn.commit()
    conn.close()
    flash("Treatment updated successfully", "success")
    return redirect(url_for('doctor_treatments'))

@app.route('/delete_treatment/<int:treatmentid>', methods=['POST'])
def delete_treatment(treatmentid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tbltreatment WHERE treatmentid=%s", (treatmentid,))
    conn.commit()
    conn.close()
    flash("Treatment deleted successfully", "danger")
    return redirect(url_for('doctor_treatments'))

@app.route("/patient_treatments")
def patient_treatments():
    if session.get("role") != "patient":
        flash("Please login as patient to view treatments.", "warning")
        return redirect(url_for("patient_login"))

    patient_id = session.get("userid")

    # Connect to DB
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *from tbltreatment
        WHERE patientid = %s
        ORDER BY datetime DESC
    """

    cursor.execute(query, (patient_id,))
    treatments = cursor.fetchall()

    # Close connection
    cursor.close()
    conn.close()

    return render_template("patient_treatments.html", treatments=treatments)


# ------------------- Run Application -------------------
#EXECUTION OF THE APPLICATION
if __name__ == "__main__":
    # Only open browser once (avoid duplicate tabs when reloader runs)
    if not is_running_from_reloader():
        webbrowser.open_new_tab("http://127.0.0.1:5000/")

    app.run(port=5000, debug=True)
#END