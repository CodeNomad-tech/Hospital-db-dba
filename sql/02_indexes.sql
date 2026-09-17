-- ============================================================
-- Indexing strategy
-- Rationale documented per index; see docs/query-tuning.md for
-- before/after EXPLAIN ANALYZE examples.
-- ============================================================

SET search_path TO hospital;

-- Patients are searched by name constantly at the front desk.
CREATE INDEX idx_patients_last_name ON patients (last_name);
CREATE INDEX idx_patients_dob ON patients (date_of_birth);

-- Appointments are the highest-write, highest-read table: filtered by
-- doctor's schedule and by date range far more than by PK.
CREATE INDEX idx_appointments_doctor_date ON appointments (doctor_id, appointment_date);
CREATE INDEX idx_appointments_patient ON appointments (patient_id);
CREATE INDEX idx_appointments_status ON appointments (status) WHERE status = 'SCHEDULED';

-- Admissions: "who is currently admitted" is a very frequent query,
-- so a partial index on active admissions keeps it fast as history grows.
CREATE INDEX idx_admissions_active ON admissions (room_id) WHERE discharge_date IS NULL;
CREATE INDEX idx_admissions_patient ON admissions (patient_id);

-- Medical records looked up by patient timeline.
CREATE INDEX idx_medical_records_patient_date ON medical_records (patient_id, visit_date DESC);

-- Billing dashboards filter heavily on unpaid balances.
CREATE INDEX idx_billing_status ON billing (status) WHERE status IN ('UNPAID','PARTIAL');
CREATE INDEX idx_billing_patient ON billing (patient_id);

-- Foreign keys that aren't already left-prefixed by another index above
-- (Postgres does NOT auto-index FK columns, unlike primary keys).
CREATE INDEX idx_doctors_department ON doctors (department_id);
CREATE INDEX idx_rooms_department ON rooms (department_id);
CREATE INDEX idx_prescriptions_medication ON prescriptions (medication_id);
