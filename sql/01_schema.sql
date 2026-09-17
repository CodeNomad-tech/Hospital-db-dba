-- ============================================================
-- Hospital Records Management System - Core Schema
-- Target: PostgreSQL 14+
-- Design: 3NF normalized. See docs/normalization.md for rationale.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS hospital;
SET search_path TO hospital;

-- ------------------------------------------------------------
-- Reference / lookup tables
-- ------------------------------------------------------------

CREATE TABLE departments (
    department_id   SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL UNIQUE,
    location         VARCHAR(100),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rooms (
    room_id          SERIAL PRIMARY KEY,
    room_number      VARCHAR(10) NOT NULL UNIQUE,
    room_type        VARCHAR(20) NOT NULL CHECK (room_type IN ('GENERAL','ICU','PRIVATE','OPERATING','EMERGENCY')),
    department_id    INTEGER NOT NULL REFERENCES departments(department_id),
    status           VARCHAR(15) NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE','OCCUPIED','MAINTENANCE')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- People
-- ------------------------------------------------------------

CREATE TABLE patients (
    patient_id       SERIAL PRIMARY KEY,
    first_name       VARCHAR(50) NOT NULL,
    last_name        VARCHAR(50) NOT NULL,
    date_of_birth    DATE NOT NULL,
    gender           VARCHAR(10) CHECK (gender IN ('MALE','FEMALE','OTHER')),
    phone            VARCHAR(20),
    email            VARCHAR(100),
    address           TEXT,
    blood_type       VARCHAR(5),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE doctors (
    doctor_id        SERIAL PRIMARY KEY,
    first_name       VARCHAR(50) NOT NULL,
    last_name        VARCHAR(50) NOT NULL,
    specialty        VARCHAR(80) NOT NULL,
    department_id    INTEGER NOT NULL REFERENCES departments(department_id),
    phone            VARCHAR(20),
    email            VARCHAR(100) UNIQUE,
    hire_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE insurance_policies (
    policy_id        SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    provider         VARCHAR(100) NOT NULL,
    policy_number    VARCHAR(50) NOT NULL,
    coverage_details TEXT,
    valid_until      DATE,
    UNIQUE (provider, policy_number)
);

-- ------------------------------------------------------------
-- Clinical operations
-- ------------------------------------------------------------

CREATE TABLE appointments (
    appointment_id   SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id        INTEGER NOT NULL REFERENCES doctors(doctor_id),
    appointment_date TIMESTAMPTZ NOT NULL,
    status           VARCHAR(15) NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED','COMPLETED','CANCELLED','NO_SHOW')),
    reason           VARCHAR(255),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE admissions (
    admission_id     SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    room_id          INTEGER NOT NULL REFERENCES rooms(room_id),
    attending_doctor_id INTEGER NOT NULL REFERENCES doctors(doctor_id),
    admission_date   TIMESTAMPTZ NOT NULL DEFAULT now(),
    discharge_date   TIMESTAMPTZ,
    diagnosis        VARCHAR(255),
    CHECK (discharge_date IS NULL OR discharge_date >= admission_date)
);

CREATE TABLE medical_records (
    record_id        SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id        INTEGER NOT NULL REFERENCES doctors(doctor_id),
    appointment_id   INTEGER REFERENCES appointments(appointment_id),
    visit_date       TIMESTAMPTZ NOT NULL DEFAULT now(),
    diagnosis        TEXT,
    treatment        TEXT,
    notes            TEXT
);

CREATE TABLE medications (
    medication_id    SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    manufacturer     VARCHAR(100),
    stock_quantity   INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    unit_price       NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE prescriptions (
    prescription_id  SERIAL PRIMARY KEY,
    record_id        INTEGER NOT NULL REFERENCES medical_records(record_id) ON DELETE CASCADE,
    medication_id    INTEGER NOT NULL REFERENCES medications(medication_id),
    dosage           VARCHAR(50) NOT NULL,
    duration_days    INTEGER NOT NULL CHECK (duration_days > 0),
    UNIQUE (record_id, medication_id)
);

-- ------------------------------------------------------------
-- Billing
-- ------------------------------------------------------------

CREATE TABLE billing (
    bill_id          SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    admission_id     INTEGER REFERENCES admissions(admission_id),
    appointment_id   INTEGER REFERENCES appointments(appointment_id),
    amount           NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    status           VARCHAR(15) NOT NULL DEFAULT 'UNPAID' CHECK (status IN ('UNPAID','PAID','PARTIAL','WAIVED')),
    bill_date        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (admission_id IS NOT NULL OR appointment_id IS NOT NULL)
);
