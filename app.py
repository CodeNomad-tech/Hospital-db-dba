import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hospital-dev-secret-2026-sovereign")


# -----------------------------------------------------------------------------
# Database Connection & Query Execution
# -----------------------------------------------------------------------------
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "hospital_db"),
        user=os.getenv("DB_USER", "hospital_admin_login"),
        password=os.getenv("DB_PASSWORD", "change_me_in_env"),
        cursor_factory=RealDictCursor,
        connect_timeout=3,
    )
    with conn.cursor() as cur:
        cur.execute("SET search_path TO hospital")
    return conn


def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        conn.close()


def execute_sql(query: str, params: tuple = ()) -> None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Demonstration / Fallback Datasets (Used when PostgreSQL is offline)
# -----------------------------------------------------------------------------
FALLBACK_DEPARTMENTS = [
    {"department_id": 1, "name": "Cardiology", "location": "Building A, Floor 2"},
    {"department_id": 2, "name": "Emergency", "location": "Building A, Floor 1"},
    {"department_id": 3, "name": "Pediatrics", "location": "Building B, Floor 1"},
    {"department_id": 4, "name": "Orthopedics", "location": "Building B, Floor 3"},
    {"department_id": 5, "name": "Radiology", "location": "Building A, Floor 1"},
]

FALLBACK_ROOMS = [
    {"room_id": 1, "room_number": "A101", "room_type": "EMERGENCY", "department_id": 2, "department_name": "Emergency", "status": "AVAILABLE"},
    {"room_id": 2, "room_number": "A102", "room_type": "EMERGENCY", "department_id": 2, "department_name": "Emergency", "status": "AVAILABLE"},
    {"room_id": 3, "room_number": "A201", "room_type": "ICU", "department_id": 1, "department_name": "Cardiology", "status": "OCCUPIED", "patient_name": "Peter Lungu"},
    {"room_id": 4, "room_number": "B101", "room_type": "GENERAL", "department_id": 3, "department_name": "Pediatrics", "status": "AVAILABLE"},
    {"room_id": 5, "room_number": "B301", "room_type": "PRIVATE", "department_id": 4, "department_name": "Orthopedics", "status": "OCCUPIED", "patient_name": "David Sakala"},
    {"room_id": 6, "room_number": "B302", "room_type": "OPERATING", "department_id": 4, "department_name": "Orthopedics", "status": "MAINTENANCE"},
]

FALLBACK_DOCTORS = [
    {"doctor_id": 1, "first_name": "Amina", "last_name": "Mwansa", "specialty": "Cardiologist", "department_id": 1, "department_name": "Cardiology", "department_location": "Building A, Floor 2", "phone": "0977100001", "email": "a.mwansa@hospital.org", "hire_date": "2019-03-01"},
    {"doctor_id": 2, "first_name": "James", "last_name": "Banda", "specialty": "Emergency Medicine", "department_id": 2, "department_name": "Emergency", "department_location": "Building A, Floor 1", "phone": "0977100002", "email": "j.banda@hospital.org", "hire_date": "2020-06-15"},
    {"doctor_id": 3, "first_name": "Grace", "last_name": "Phiri", "specialty": "Pediatrician", "department_id": 3, "department_name": "Pediatrics", "department_location": "Building B, Floor 1", "phone": "0977100003", "email": "g.phiri@hospital.org", "hire_date": "2018-01-10"},
    {"doctor_id": 4, "first_name": "Michael", "last_name": "Tembo", "specialty": "Orthopedic Surgeon", "department_id": 4, "department_name": "Orthopedics", "department_location": "Building B, Floor 3", "phone": "0977100004", "email": "m.tembo@hospital.org", "hire_date": "2021-09-01"},
    {"doctor_id": 5, "first_name": "Ruth", "last_name": "Chanda", "specialty": "Radiologist", "department_id": 5, "department_name": "Radiology", "department_location": "Building A, Floor 1", "phone": "0977100005", "email": "r.chanda@hospital.org", "hire_date": "2017-11-20"},
]

FALLBACK_PATIENTS = [
    {"patient_id": 1, "first_name": "John", "last_name": "Mumba", "date_of_birth": "1985-04-12", "gender": "MALE", "phone": "0966111111", "email": "john.mumba@example.com", "address": "12 Cairo Rd, Lusaka", "blood_type": "O+", "insurance_provider": "NHIMA"},
    {"patient_id": 2, "first_name": "Mary", "last_name": "Zulu", "date_of_birth": "1992-08-23", "gender": "FEMALE", "phone": "0966222222", "email": "mary.zulu@example.com", "address": "45 Church Rd, Lusaka", "blood_type": "A+", "insurance_provider": "Madison Insurance"},
    {"patient_id": 3, "first_name": "Peter", "last_name": "Lungu", "date_of_birth": "1978-01-05", "gender": "MALE", "phone": "0966333333", "email": "peter.lungu@example.com", "address": "9 Great East Rd, Lusaka", "blood_type": "B-", "insurance_provider": "NHIMA"},
    {"patient_id": 4, "first_name": "Chipo", "last_name": "Mulenga", "date_of_birth": "2010-11-30", "gender": "FEMALE", "phone": "0966444444", "email": "chipo.parent@example.com", "address": "3 Kabulonga, Lusaka", "blood_type": "AB+", "insurance_provider": None},
    {"patient_id": 5, "first_name": "David", "last_name": "Sakala", "date_of_birth": "1965-06-17", "gender": "MALE", "phone": "0966555555", "email": "david.sakala@example.com", "address": "21 Woodlands, Lusaka", "blood_type": "O-", "insurance_provider": None},
]

FALLBACK_APPOINTMENTS = [
    {"appointment_id": 1, "patient_id": 1, "patient_name": "John Mumba", "doctor_name": "Amina Mwansa", "appointment_date": "2026-09-19 10:00", "status": "SCHEDULED", "reason": "Routine cardiac checkup"},
    {"appointment_id": 2, "patient_id": 2, "patient_name": "Mary Zulu", "doctor_name": "Grace Phiri", "appointment_date": "2026-09-18 14:30", "status": "SCHEDULED", "reason": "Child vaccination"},
    {"appointment_id": 3, "patient_id": 3, "patient_name": "Peter Lungu", "doctor_name": "James Banda", "appointment_date": "2026-09-14 09:15", "status": "COMPLETED", "reason": "Chest pain evaluation"},
    {"appointment_id": 4, "patient_id": 4, "patient_name": "Chipo Mulenga", "doctor_name": "Grace Phiri", "appointment_date": "2026-09-07 11:00", "status": "COMPLETED", "reason": "Fever and cough"},
    {"appointment_id": 5, "patient_id": 5, "patient_name": "David Sakala", "doctor_name": "Michael Tembo", "appointment_date": "2026-09-22 16:00", "status": "SCHEDULED", "reason": "Knee pain follow-up"},
]

FALLBACK_ADMISSIONS = [
    {"admission_id": 1, "patient_id": 3, "patient_name": "Peter Lungu", "room_id": 1, "room_number": "A101", "room_type": "EMERGENCY", "department_name": "Emergency", "doctor_name": "James Banda", "admission_date": "2026-09-14 08:30", "discharge_date": "2026-09-16 12:00", "diagnosis": "Acute chest pain, ruled out MI"},
    {"admission_id": 2, "patient_id": 5, "patient_name": "David Sakala", "room_id": 5, "room_number": "B301", "room_type": "PRIVATE", "department_name": "Orthopedics", "doctor_name": "Michael Tembo", "admission_date": "2026-09-16 14:00", "discharge_date": None, "diagnosis": "Post-op knee observation"},
]

FALLBACK_MEDICATIONS = [
    {"medication_id": 1, "name": "Ibuprofen 400mg", "manufacturer": "GenPharm", "stock_quantity": 500, "unit_price": 0.15},
    {"medication_id": 2, "name": "Amoxicillin 250mg", "manufacturer": "MedCorp", "stock_quantity": 300, "unit_price": 0.25},
    {"medication_id": 3, "name": "Paracetamol 500mg", "manufacturer": "GenPharm", "stock_quantity": 1000, "unit_price": 0.10},
    {"medication_id": 4, "name": "Artemether/Lumefantrine 80/480mg", "manufacturer": "National Medical", "stock_quantity": 450, "unit_price": 1.20},
    {"medication_id": 5, "name": "Metformin 500mg", "manufacturer": "MedCorp", "stock_quantity": 800, "unit_price": 0.30},
]

FALLBACK_PRESCRIPTIONS = [
    {"prescription_id": 1, "patient_id": 3, "patient_name": "Peter Lungu", "medication_name": "Ibuprofen 400mg", "dosage": "400mg twice daily", "duration_days": 7, "doctor_name": "James Banda", "diagnosis": "Costochondritis"},
    {"prescription_id": 2, "patient_id": 4, "patient_name": "Chipo Mulenga", "medication_name": "Paracetamol 500mg", "dosage": "500mg every 6 hours", "duration_days": 5, "doctor_name": "Grace Phiri", "diagnosis": "Viral upper respiratory infection"},
]

FALLBACK_BILLING = [
    {"bill_id": 1, "patient_id": 3, "patient_name": "Peter Lungu", "admission_id": 1, "appointment_id": 3, "amount": 1850.00, "status": "PAID", "bill_date": "2026-09-16 11:30", "insurance_provider": "NHIMA"},
    {"bill_id": 2, "patient_id": 4, "patient_name": "Chipo Mulenga", "admission_id": None, "appointment_id": 4, "amount": 320.00, "status": "PAID", "bill_date": "2026-09-08 15:45", "insurance_provider": None},
    {"bill_id": 3, "patient_id": 5, "patient_name": "David Sakala", "admission_id": 2, "appointment_id": None, "amount": 4200.00, "status": "UNPAID", "bill_date": "2026-09-17 09:00", "insurance_provider": None},
]


def get_overview_data() -> Dict[str, Any]:
    try:
        return {
            "patients": fetch_one("SELECT COUNT(*) AS total FROM patients")["total"],
            "doctors": fetch_one("SELECT COUNT(*) AS total FROM doctors")["total"],
            "appointments": fetch_one("SELECT COUNT(*) AS total FROM appointments")["total"],
            "admissions": fetch_one("SELECT COUNT(*) AS total FROM admissions WHERE discharge_date IS NULL")["total"],
            "unpaid_bills": fetch_one("SELECT COUNT(*) AS total FROM billing WHERE status != 'PAID'")["total"],
            "total_billing": float(fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM billing")["total"]),
        }
    except Exception:
        return {
            "patients": len(FALLBACK_PATIENTS),
            "doctors": len(FALLBACK_DOCTORS),
            "appointments": len(FALLBACK_APPOINTMENTS),
            "admissions": 1,
            "unpaid_bills": 1,
            "total_billing": sum(b["amount"] for b in FALLBACK_BILLING),
        }


# -----------------------------------------------------------------------------
# Route 1: National Landing Page (Government & Donor Portal)
# -----------------------------------------------------------------------------
@app.route("/")
def landing():
    overview = get_overview_data()
    try:
        rooms = fetch_all(
            """
            SELECT r.room_id, r.room_number, r.room_type, r.status, d.name AS department_name
            FROM rooms r
            JOIN departments d ON d.department_id = r.department_id
            ORDER BY r.room_number
            """
        )
    except Exception:
        rooms = FALLBACK_ROOMS

    return render_template("landing.html", overview=overview, rooms=rooms)


# -----------------------------------------------------------------------------
# Route 2: Strategic Grant & Policy Dossier
# -----------------------------------------------------------------------------
@app.route("/about")
def about_view():
    return render_template("about.html")


# -----------------------------------------------------------------------------
# Route 3: Clinical Operations & Triage Dashboard
# -----------------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def index():
    search_term = request.args.get("q", "").strip()
    database_error = None

    try:
        if search_term:
            like_term = f"%{search_term.lower()}%"
            patients = fetch_all(
                """
                SELECT patient_id, first_name, last_name, email, phone, blood_type
                FROM patients
                WHERE LOWER(first_name) LIKE %s OR LOWER(last_name) LIKE %s OR phone LIKE %s
                ORDER BY last_name, first_name
                LIMIT 20
                """,
                (like_term, like_term, like_term),
            )
        else:
            patients = fetch_all(
                """
                SELECT patient_id, first_name, last_name, email, phone, blood_type
                FROM patients
                ORDER BY patient_id DESC
                LIMIT 20
                """
            )

        appointments = fetch_all(
            """
            SELECT a.appointment_id, a.appointment_date, a.status, a.reason,
                   p.patient_id, p.first_name || ' ' || p.last_name AS patient_name,
                   d.first_name || ' ' || d.last_name AS doctor_name
            FROM appointments a
            JOIN patients p ON p.patient_id = a.patient_id
            JOIN doctors d ON d.doctor_id = a.doctor_id
            ORDER BY a.appointment_date DESC
            LIMIT 10
            """
        )

        billing = fetch_all(
            """
            SELECT b.bill_id, b.amount, b.status, b.bill_date,
                   p.first_name || ' ' || p.last_name AS patient_name
            FROM billing b
            JOIN patients p ON p.patient_id = b.patient_id
            ORDER BY b.bill_date DESC
            LIMIT 10
            """
        )

        doctors = fetch_all(
            "SELECT doctor_id, first_name, last_name, specialty FROM doctors ORDER BY last_name, first_name"
        )
        patients_for_select = fetch_all(
            "SELECT patient_id, first_name, last_name FROM patients ORDER BY last_name, first_name"
        )
        overview = get_overview_data()

    except Exception as exc:
        database_error = str(exc)
        if search_term:
            st = search_term.lower()
            patients = [p for p in FALLBACK_PATIENTS if st in p["first_name"].lower() or st in p["last_name"].lower() or st in (p.get("phone") or "")]
        else:
            patients = FALLBACK_PATIENTS
        appointments = FALLBACK_APPOINTMENTS
        billing = FALLBACK_BILLING
        doctors = FALLBACK_DOCTORS
        patients_for_select = FALLBACK_PATIENTS
        overview = get_overview_data()

    return render_template(
        "index.html",
        patients=patients,
        appointments=appointments,
        billing=billing,
        doctors=doctors,
        patients_for_select=patients_for_select,
        overview=overview,
        search_term=search_term,
        database_error=database_error,
    )


# -----------------------------------------------------------------------------
# Route 4: Citizen Health Registry (EHR) List & Creation
# -----------------------------------------------------------------------------
@app.route("/patients")
def patients_list():
    search_term = request.args.get("q", "").strip()
    blood_type_filter = request.args.get("blood_type", "").strip()

    try:
        query = """
            SELECT p.patient_id, p.first_name, p.last_name, p.date_of_birth, p.gender,
                   p.phone, p.email, p.address, p.blood_type, p.created_at,
                   ip.provider AS insurance_provider
            FROM patients p
            LEFT JOIN insurance_policies ip ON ip.patient_id = p.patient_id
            WHERE 1=1
        """
        params = []
        if search_term:
            query += " AND (LOWER(p.first_name) LIKE %s OR LOWER(p.last_name) LIKE %s OR p.phone LIKE %s OR LOWER(p.email) LIKE %s)"
            st = f"%{search_term.lower()}%"
            params.extend([st, st, st, st])
        if blood_type_filter:
            query += " AND p.blood_type = %s"
            params.append(blood_type_filter)

        query += " ORDER BY p.patient_id DESC"
        patients = fetch_all(query, tuple(params))
    except Exception:
        patients = FALLBACK_PATIENTS
        if search_term:
            st = search_term.lower()
            patients = [p for p in patients if st in p["first_name"].lower() or st in p["last_name"].lower() or st in (p.get("phone") or "") or st in (p.get("email") or "")]
        if blood_type_filter:
            patients = [p for p in patients if p.get("blood_type") == blood_type_filter]

    return render_template(
        "patients.html",
        patients=patients,
        search_term=search_term,
        blood_type_filter=blood_type_filter,
    )


@app.route("/patients/new", methods=["POST"])
def create_patient():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    date_of_birth = request.form.get("date_of_birth")
    gender = request.form.get("gender")
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    blood_type = request.form.get("blood_type")

    if not all([first_name, last_name, date_of_birth, gender]):
        flash("First name, last name, date of birth, and gender are required.", "error")
        return redirect(url_for("patients_list"))

    try:
        execute_sql(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, blood_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (first_name, last_name, date_of_birth, gender, phone or None, email or None, address or None, blood_type or None),
        )
        flash(f"Citizen record for {first_name} {last_name} registered successfully.", "success")
    except Exception as exc:
        flash(f"Database unavailable or error saving patient: {exc}", "error")

    return redirect(url_for("patients_list"))


# -----------------------------------------------------------------------------
# Route 5: Citizen EHR Deep Profile (Diagnoses, Prescriptions, Admissions, NHIMA)
# -----------------------------------------------------------------------------
@app.route("/patients/<int:patient_id>")
def patient_detail(patient_id: int):
    try:
        patient = fetch_one(
            """
            SELECT patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, blood_type
            FROM patients
            WHERE patient_id = %s
            """,
            (patient_id,),
        )
        insurance = fetch_one(
            """
            SELECT policy_id, provider, policy_number, coverage_details, valid_until
            FROM insurance_policies
            WHERE patient_id = %s
            LIMIT 1
            """,
            (patient_id,),
        )
        appointments = fetch_all(
            """
            SELECT a.appointment_id, a.appointment_date, a.status, a.reason,
                   d.first_name || ' ' || d.last_name AS doctor_name
            FROM appointments a
            JOIN doctors d ON d.doctor_id = a.doctor_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC
            """,
            (patient_id,),
        )
        records = fetch_all(
            """
            SELECT m.record_id, m.visit_date, m.diagnosis, m.treatment, m.notes,
                   d.first_name || ' ' || d.last_name AS doctor_name
            FROM medical_records m
            JOIN doctors d ON d.doctor_id = m.doctor_id
            WHERE m.patient_id = %s
            ORDER BY m.visit_date DESC
            """,
            (patient_id,),
        )
        prescriptions = fetch_all(
            """
            SELECT pr.prescription_id, med.name AS medication_name, pr.dosage, pr.duration_days
            FROM prescriptions pr
            JOIN medical_records m ON m.record_id = pr.record_id
            JOIN medications med ON med.medication_id = pr.medication_id
            WHERE m.patient_id = %s
            """,
            (patient_id,),
        )
        admissions = fetch_all(
            """
            SELECT adm.admission_id, adm.admission_date, adm.discharge_date, adm.diagnosis,
                   r.room_number, r.room_type,
                   d.first_name || ' ' || d.last_name AS doctor_name
            FROM admissions adm
            JOIN rooms r ON r.room_id = adm.room_id
            JOIN doctors d ON d.doctor_id = adm.attending_doctor_id
            WHERE adm.patient_id = %s
            ORDER BY adm.admission_date DESC
            """,
            (patient_id,),
        )
        billing = fetch_all(
            """
            SELECT bill_id, amount, status, bill_date
            FROM billing
            WHERE patient_id = %s
            ORDER BY bill_date DESC
            """,
            (patient_id,),
        )
    except Exception:
        patient = next((p for p in FALLBACK_PATIENTS if p["patient_id"] == patient_id), FALLBACK_PATIENTS[0])
        insurance = {"provider": "NHIMA", "policy_number": "NH-0001-22", "coverage_details": "Standard national coverage", "valid_until": "2027-01-01"}
        appointments = [a for a in FALLBACK_APPOINTMENTS if a["patient_id"] == patient_id]
        records = [
            {"record_id": 1, "visit_date": "2026-09-14 09:30", "diagnosis": "Cardiovascular assessment & mild hypertension", "treatment": "Dietary modification, low sodium, exercise", "notes": "Follow up in 4 weeks", "doctor_name": "Amina Mwansa"}
        ]
        prescriptions = [p for p in FALLBACK_PRESCRIPTIONS if p["patient_id"] == patient_id]
        admissions = [a for a in FALLBACK_ADMISSIONS if a["patient_id"] == patient_id]
        billing = [b for b in FALLBACK_BILLING if b["patient_id"] == patient_id]

    return render_template(
        "patient_detail.html",
        patient=patient,
        insurance=insurance,
        appointments=appointments,
        records=records,
        prescriptions=prescriptions,
        admissions=admissions,
        billing=billing,
    )


# -----------------------------------------------------------------------------
# Route 6: Hospital Bed Management & Inpatient Ward Grid
# -----------------------------------------------------------------------------
@app.route("/admissions")
def admissions_view():
    try:
        rooms = fetch_all(
            """
            SELECT r.room_id, r.room_number, r.room_type, r.status,
                   d.name AS department_name,
                   (
                       SELECT p.first_name || ' ' || p.last_name
                       FROM admissions adm
                       JOIN patients p ON p.patient_id = adm.patient_id
                       WHERE adm.room_id = r.room_id AND adm.discharge_date IS NULL
                       ORDER BY adm.admission_date DESC
                       LIMIT 1
                   ) AS patient_name
            FROM rooms r
            JOIN departments d ON d.department_id = r.department_id
            ORDER BY r.room_number
            """
        )
        active_admissions = fetch_all(
            """
            SELECT adm.admission_id, adm.patient_id, adm.admission_date, adm.diagnosis,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   r.room_number, r.room_type, d.name AS department_name,
                   doc.first_name || ' ' || doc.last_name AS doctor_name
            FROM admissions adm
            JOIN patients p ON p.patient_id = adm.patient_id
            JOIN rooms r ON r.room_id = adm.room_id
            JOIN departments d ON d.department_id = r.department_id
            JOIN doctors doc ON doc.doctor_id = adm.attending_doctor_id
            WHERE adm.discharge_date IS NULL
            ORDER BY adm.admission_date DESC
            """
        )
        available_rooms = fetch_all(
            """
            SELECT r.room_id, r.room_number, r.room_type, d.name AS department_name
            FROM rooms r
            JOIN departments d ON d.department_id = r.department_id
            WHERE r.status = 'AVAILABLE'
            ORDER BY r.room_number
            """
        )
        doctors = fetch_all("SELECT doctor_id, first_name, last_name, specialty FROM doctors ORDER BY last_name")
        patients_for_select = fetch_all("SELECT patient_id, first_name, last_name FROM patients ORDER BY last_name")
    except Exception:
        rooms = FALLBACK_ROOMS
        active_admissions = [a for a in FALLBACK_ADMISSIONS if a.get("discharge_date") is None]
        available_rooms = [r for r in FALLBACK_ROOMS if r["status"] == "AVAILABLE"]
        doctors = FALLBACK_DOCTORS
        patients_for_select = FALLBACK_PATIENTS

    return render_template(
        "admissions.html",
        rooms=rooms,
        active_admissions=active_admissions,
        available_rooms=available_rooms,
        doctors=doctors,
        patients_for_select=patients_for_select,
    )


@app.route("/admissions/new", methods=["POST"])
def create_admission():
    patient_id = request.form.get("patient_id")
    room_id = request.form.get("room_id")
    attending_doctor_id = request.form.get("attending_doctor_id")
    diagnosis = request.form.get("diagnosis", "").strip()

    if not all([patient_id, room_id, attending_doctor_id, diagnosis]):
        flash("Patient, room, attending doctor, and diagnosis are required.", "error")
        return redirect(url_for("admissions_view"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admissions (patient_id, room_id, attending_doctor_id, admission_date, diagnosis)
                VALUES (%s, %s, %s, now(), %s)
                """,
                (int(patient_id), int(room_id), int(attending_doctor_id), diagnosis),
            )
            cur.execute(
                "UPDATE rooms SET status = 'OCCUPIED' WHERE room_id = %s",
                (int(room_id),),
            )
        conn.commit()
        conn.close()
        flash("Citizen admitted to hospital ward successfully.", "success")
    except Exception as exc:
        flash(f"Unable to complete admission: {exc}", "error")

    return redirect(url_for("admissions_view"))


@app.route("/admissions/<int:admission_id>/discharge", methods=["POST"])
def discharge_patient(admission_id: int):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT room_id FROM admissions WHERE admission_id = %s", (admission_id,))
            row = cur.fetchone()
            if row:
                room_id = row["room_id"]
                cur.execute(
                    "UPDATE admissions SET discharge_date = now() WHERE admission_id = %s",
                    (admission_id,),
                )
                cur.execute(
                    "UPDATE rooms SET status = 'AVAILABLE' WHERE room_id = %s",
                    (room_id,),
                )
        conn.commit()
        conn.close()
        flash("Inpatient discharged and bed marked AVAILABLE.", "success")
    except Exception as exc:
        flash(f"Unable to process discharge: {exc}", "error")

    return redirect(url_for("admissions_view"))


# -----------------------------------------------------------------------------
# Route 7: Essential Medicines & Pharmacy Module
# -----------------------------------------------------------------------------
@app.route("/pharmacy")
def pharmacy_view():
    try:
        medications = fetch_all("SELECT medication_id, name, manufacturer, stock_quantity, unit_price FROM medications ORDER BY name")
        recent_prescriptions = fetch_all(
            """
            SELECT pr.prescription_id, pr.dosage, pr.duration_days,
                   m.name AS medication_name,
                   p.patient_id, p.first_name || ' ' || p.last_name AS patient_name,
                   doc.first_name || ' ' || doc.last_name AS doctor_name,
                   rec.diagnosis
            FROM prescriptions pr
            JOIN medications m ON m.medication_id = pr.medication_id
            JOIN medical_records rec ON rec.record_id = pr.record_id
            JOIN patients p ON p.patient_id = rec.patient_id
            JOIN doctors doc ON doc.doctor_id = rec.doctor_id
            ORDER BY pr.prescription_id DESC
            """
        )
    except Exception:
        medications = FALLBACK_MEDICATIONS
        recent_prescriptions = FALLBACK_PRESCRIPTIONS

    return render_template("pharmacy.html", medications=medications, recent_prescriptions=recent_prescriptions)


# -----------------------------------------------------------------------------
# Route 8: Specialist Doctors & Staff Registry
# -----------------------------------------------------------------------------
@app.route("/doctors")
def doctors_list():
    try:
        doctors = fetch_all(
            """
            SELECT d.doctor_id, d.first_name, d.last_name, d.specialty, d.phone, d.email, d.hire_date,
                   dept.name AS department_name, dept.location AS department_location
            FROM doctors d
            JOIN departments dept ON dept.department_id = d.department_id
            ORDER BY dept.name, d.last_name
            """
        )
        departments = fetch_all("SELECT department_id, name, location FROM departments ORDER BY name")
    except Exception:
        doctors = FALLBACK_DOCTORS
        departments = FALLBACK_DEPARTMENTS

    return render_template("doctors.html", doctors=doctors, departments=departments)


# -----------------------------------------------------------------------------
# Route 9: NHIMA Health Insurance & Hospital Billing Ledger
# -----------------------------------------------------------------------------
@app.route("/billing")
def billing_view():
    status_filter = request.args.get("status", "").strip().upper()

    try:
        all_bills = fetch_all(
            """
            SELECT b.bill_id, b.patient_id, b.admission_id, b.appointment_id, b.amount, b.status, b.bill_date,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   ip.provider AS insurance_provider
            FROM billing b
            JOIN patients p ON p.patient_id = b.patient_id
            LEFT JOIN insurance_policies ip ON ip.patient_id = p.patient_id
            ORDER BY b.bill_date DESC
            """
        )
    except Exception:
        all_bills = FALLBACK_BILLING

    if status_filter:
        bills = [b for b in all_bills if b["status"] == status_filter]
    else:
        bills = all_bills

    total_amount = sum(float(b["amount"]) for b in all_bills)
    paid_bills = [b for b in all_bills if b["status"] == "PAID"]
    paid_amount = sum(float(b["amount"]) for b in paid_bills)
    unpaid_bills = [b for b in all_bills if b["status"] == "UNPAID"]
    unpaid_amount = sum(float(b["amount"]) for b in unpaid_bills)
    waived_bills = [b for b in all_bills if b["status"] == "WAIVED"]
    waived_amount = sum(float(b["amount"]) for b in waived_bills)

    return render_template(
        "billing.html",
        bills=bills,
        all_bills=all_bills,
        status_filter=status_filter,
        total_amount=total_amount,
        paid_amount=paid_amount,
        paid_count=len(paid_bills),
        unpaid_amount=unpaid_amount,
        unpaid_count=len(unpaid_bills),
        waived_amount=waived_amount,
    )


@app.route("/billing/update", methods=["POST"])
def update_billing():
    bill_id = request.form.get("bill_id")
    status = request.form.get("status")
    redirect_patient_id = request.form.get("redirect_patient_id")

    if not all([bill_id, status]):
        flash("Billing update requires a valid bill identifier and status.", "error")
        return redirect(url_for("billing_view"))

    try:
        execute_sql(
            "UPDATE billing SET status = %s WHERE bill_id = %s",
            (status, int(bill_id)),
        )
        flash(f"Claim #BILL-{bill_id} status updated to {status}.", "success")
    except Exception as exc:
        flash(f"Unable to update billing claim: {exc}", "error")

    if redirect_patient_id:
        return redirect(url_for("patient_detail", patient_id=int(redirect_patient_id)))
    return redirect(request.referrer or url_for("billing_view"))


# -----------------------------------------------------------------------------
# Route 10: Public Health Intelligence & Epidemiological Analytics
# -----------------------------------------------------------------------------
@app.route("/analytics")
def analytics_view():
    try:
        # Department caseload
        dept_rows = fetch_all(
            """
            SELECT d.name, COUNT(adm.admission_id) AS total
            FROM departments d
            LEFT JOIN rooms r ON r.department_id = d.department_id
            LEFT JOIN admissions adm ON adm.room_id = r.room_id
            GROUP BY d.name
            ORDER BY d.name
            """
        )
        # Room classification
        room_rows = fetch_all(
            """
            SELECT room_type, COUNT(*) AS total
            FROM rooms
            GROUP BY room_type
            ORDER BY room_type
            """
        )
        # Blood type distribution
        blood_rows = fetch_all(
            """
            SELECT COALESCE(blood_type, 'Unknown') AS blood_type, COUNT(*) AS total
            FROM patients
            GROUP BY blood_type
            ORDER BY blood_type
            """
        )
        # Billing breakdown
        bill_rows = fetch_all(
            """
            SELECT status, COALESCE(SUM(amount), 0) AS total
            FROM billing
            GROUP BY status
            ORDER BY status
            """
        )
        total_appts = fetch_one("SELECT COUNT(*) AS total FROM appointments")["total"]
        completed_appts = fetch_one("SELECT COUNT(*) AS total FROM appointments WHERE status = 'COMPLETED'")["total"]
        total_rooms = fetch_one("SELECT COUNT(*) AS total FROM rooms")["total"]
        occupied_rooms = fetch_one("SELECT COUNT(*) AS total FROM rooms WHERE status = 'OCCUPIED'")["total"]
        insured_patients = fetch_one("SELECT COUNT(DISTINCT patient_id) AS total FROM insurance_policies")["total"]
        total_patients = fetch_one("SELECT COUNT(*) AS total FROM patients")["total"]
    except Exception:
        dept_rows = [{"name": "Emergency", "total": 1}, {"name": "Orthopedics", "total": 1}, {"name": "Cardiology", "total": 0}, {"name": "Pediatrics", "total": 0}, {"name": "Radiology", "total": 0}]
        room_rows = [{"room_type": "EMERGENCY", "total": 2}, {"room_type": "ICU", "total": 1}, {"room_type": "GENERAL", "total": 1}, {"room_type": "PRIVATE", "total": 1}, {"room_type": "OPERATING", "total": 1}]
        blood_rows = [{"blood_type": "O+", "total": 1}, {"blood_type": "A+", "total": 1}, {"blood_type": "B-", "total": 1}, {"blood_type": "AB+", "total": 1}, {"blood_type": "O-", "total": 1}]
        bill_rows = [{"status": "PAID", "total": 2170.00}, {"status": "UNPAID", "total": 4200.00}]
        total_appts = 5
        completed_appts = 2
        total_rooms = 6
        occupied_rooms = 2
        insured_patients = 3
        total_patients = 5

    completion_rate = int((completed_appts / total_appts * 100) if total_appts else 0)
    bed_occupancy_rate = int((occupied_rooms / total_rooms * 100) if total_rooms else 0)
    insured_ratio = int((insured_patients / total_patients * 100) if total_patients else 0)

    total_billed = sum(float(r["total"]) for r in bill_rows)
    paid_val = next((float(r["total"]) for r in bill_rows if r["status"] == "PAID"), 0.0)
    recovery_rate = int((paid_val / total_billed * 100) if total_billed else 0)

    return render_template(
        "analytics.html",
        total_appointments=total_appts,
        completion_rate=completion_rate,
        bed_occupancy_rate=bed_occupancy_rate,
        insured_ratio=insured_ratio,
        recovery_rate=recovery_rate,
        dept_labels=[r["name"] for r in dept_rows],
        dept_values=[r["total"] for r in dept_rows],
        room_labels=[r["room_type"] for r in room_rows],
        room_values=[r["total"] for r in room_rows],
        blood_labels=[r["blood_type"] for r in blood_rows],
        blood_values=[r["total"] for r in blood_rows],
        bill_labels=[r["status"] for r in bill_rows],
        bill_values=[float(r["total"]) for r in bill_rows],
    )


# -----------------------------------------------------------------------------
# Route 11: Database Administration Governance & Replication Health
# -----------------------------------------------------------------------------
@app.route("/system-health")
def system_health_view():
    return render_template("system_health.html")


# -----------------------------------------------------------------------------
# Route 12: Appointment Creation Endpoint
# -----------------------------------------------------------------------------
@app.route("/appointments/new", methods=["POST"])
def create_appointment():
    patient_id = request.form.get("patient_id")
    doctor_id = request.form.get("doctor_id")
    appointment_date = request.form.get("appointment_date")
    reason = request.form.get("reason", "").strip()

    if not all([patient_id, doctor_id, appointment_date]):
        flash("Please provide patient, doctor, and consultation date.", "error")
        return redirect(url_for("index"))

    try:
        execute_sql(
            """
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, reason)
            VALUES (%s, %s, %s, 'SCHEDULED', %s)
            """,
            (int(patient_id), int(doctor_id), appointment_date, reason or "General consultation"),
        )
        flash("Consultation appointment scheduled successfully.", "success")
    except Exception as exc:
        flash(f"Unable to save appointment: {exc}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
