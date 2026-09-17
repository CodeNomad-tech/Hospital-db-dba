-- ============================================================
-- Role-Based Access Control (least privilege)
-- ============================================================
-- Design:
--   hospital_admin      - full DDL/DML, used only by the DBA
--   hospital_doctor     - read/write on clinical tables, read-only
--                         on billing, no access to raw patient
--                         insurance/billing modification
--   hospital_reception  - manage patients & appointments, read-only
--                         on clinical/billing detail
--   hospital_analyst    - read-only on everything, for reporting/BI
-- ============================================================

SET search_path TO hospital;

-- --- Roles (NOLOGIN group roles; create LOGIN users that inherit them) ---
CREATE ROLE hospital_admin       NOLOGIN;
CREATE ROLE hospital_doctor      NOLOGIN;
CREATE ROLE hospital_reception   NOLOGIN;
CREATE ROLE hospital_analyst     NOLOGIN;

-- --- Admin: full control ---
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hospital TO hospital_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hospital TO hospital_admin;
GRANT USAGE, CREATE ON SCHEMA hospital TO hospital_admin;

-- --- Doctor: clinical read/write, billing read-only, no schema changes ---
GRANT USAGE ON SCHEMA hospital TO hospital_doctor;
GRANT SELECT, INSERT, UPDATE ON medical_records, prescriptions, admissions TO hospital_doctor;
GRANT SELECT ON patients, appointments, medications, doctors, departments, rooms TO hospital_doctor;
GRANT SELECT ON billing, insurance_policies TO hospital_doctor;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA hospital TO hospital_doctor;

-- --- Reception: manage patients/appointments/billing, no clinical notes ---
GRANT USAGE ON SCHEMA hospital TO hospital_reception;
GRANT SELECT, INSERT, UPDATE ON patients, appointments, billing, insurance_policies TO hospital_reception;
GRANT SELECT ON doctors, departments, rooms, admissions TO hospital_reception;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA hospital TO hospital_reception;
-- Explicitly deny access to clinical notes at the row content level:
REVOKE ALL ON medical_records, prescriptions FROM hospital_reception;

-- --- Analyst: read-only, everything, for BI/reporting tools ---
GRANT USAGE ON SCHEMA hospital TO hospital_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA hospital TO hospital_analyst;

-- --- Example login users (rotate/change passwords before real use!) ---
-- CREATE USER dr_smith WITH PASSWORD 'change_me' IN ROLE hospital_doctor;
-- CREATE USER reception_jane WITH PASSWORD 'change_me' IN ROLE hospital_reception;
-- CREATE USER bi_dashboard WITH PASSWORD 'change_me' IN ROLE hospital_analyst;

-- --- Row-level security example: doctors only see their own patients'
--     medical records unless explicitly given broader access. Disabled
--     by default here so the demo data is visible; flip ENABLE to
--     ROW LEVEL SECURITY to turn it on. ---
-- ALTER TABLE medical_records ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY doctor_own_records ON medical_records
--     FOR SELECT TO hospital_doctor
--     USING (doctor_id = current_setting('app.current_doctor_id')::INT);
