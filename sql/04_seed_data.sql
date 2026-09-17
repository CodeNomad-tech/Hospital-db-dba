SET search_path TO hospital;

INSERT INTO departments (name, location) VALUES
('Cardiology', 'Building A, Floor 2'),
('Emergency', 'Building A, Floor 1'),
('Pediatrics', 'Building B, Floor 1'),
('Orthopedics', 'Building B, Floor 3'),
('Radiology', 'Building A, Floor 1');

INSERT INTO rooms (room_number, room_type, department_id, status) VALUES
('A101', 'EMERGENCY', 2, 'AVAILABLE'),
('A102', 'EMERGENCY', 2, 'AVAILABLE'),
('A201', 'ICU', 1, 'AVAILABLE'),
('B101', 'GENERAL', 3, 'AVAILABLE'),
('B301', 'PRIVATE', 4, 'AVAILABLE'),
('B302', 'OPERATING', 4, 'AVAILABLE');

INSERT INTO doctors (first_name, last_name, specialty, department_id, phone, email, hire_date) VALUES
('Amina', 'Mwansa', 'Cardiologist', 1, '0977100001', 'a.mwansa@hospital.org', '2019-03-01'),
('James', 'Banda', 'Emergency Medicine', 2, '0977100002', 'j.banda@hospital.org', '2020-06-15'),
('Grace', 'Phiri', 'Pediatrician', 3, '0977100003', 'g.phiri@hospital.org', '2018-01-10'),
('Michael', 'Tembo', 'Orthopedic Surgeon', 4, '0977100004', 'm.tembo@hospital.org', '2021-09-01'),
('Ruth', 'Chanda', 'Radiologist', 5, '0977100005', 'r.chanda@hospital.org', '2017-11-20');

INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, blood_type) VALUES
('John', 'Mumba', '1985-04-12', 'MALE', '0966111111', 'john.mumba@example.com', '12 Cairo Rd, Lusaka', 'O+'),
('Mary', 'Zulu', '1992-08-23', 'FEMALE', '0966222222', 'mary.zulu@example.com', '45 Church Rd, Lusaka', 'A+'),
('Peter', 'Lungu', '1978-01-05', 'MALE', '0966333333', 'peter.lungu@example.com', '9 Great East Rd, Lusaka', 'B-'),
('Chipo', 'Mulenga', '2010-11-30', 'FEMALE', '0966444444', 'chipo.parent@example.com', '3 Kabulonga, Lusaka', 'AB+'),
('David', 'Sakala', '1965-06-17', 'MALE', '0966555555', 'david.sakala@example.com', '21 Woodlands, Lusaka', 'O-');

INSERT INTO insurance_policies (patient_id, provider, policy_number, coverage_details, valid_until) VALUES
(1, 'NHIMA', 'NH-0001-22', 'Standard national coverage', '2027-01-01'),
(2, 'Madison Insurance', 'MI-3321', 'Full medical + dental', '2026-12-31'),
(3, 'NHIMA', 'NH-0044-19', 'Standard national coverage', '2027-01-01');

INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, reason) VALUES
(1, 1, now() + interval '2 days', 'SCHEDULED', 'Routine cardiac checkup'),
(2, 3, now() + interval '1 day', 'SCHEDULED', 'Child vaccination'),
(3, 2, now() - interval '3 days', 'COMPLETED', 'Chest pain evaluation'),
(4, 3, now() - interval '10 days', 'COMPLETED', 'Fever and cough'),
(5, 4, now() + interval '5 days', 'SCHEDULED', 'Knee pain follow-up');

INSERT INTO admissions (patient_id, room_id, attending_doctor_id, admission_date, discharge_date, diagnosis) VALUES
(3, 1, 2, now() - interval '3 days', now() - interval '1 days', 'Acute chest pain, ruled out MI'),
(5, 5, 4, now() - interval '1 days', NULL, 'Post-op knee observation');

INSERT INTO medical_records (patient_id, doctor_id, appointment_id, visit_date, diagnosis, treatment, notes) VALUES
(3, 2, 3, now() - interval '3 days', 'Costochondritis', 'NSAIDs, rest', 'Follow up in 2 weeks if pain persists'),
(4, 3, 4, now() - interval '10 days', 'Viral upper respiratory infection', 'Supportive care, fluids', 'Advised school absence for 3 days');

INSERT INTO medications (name, manufacturer, stock_quantity, unit_price) VALUES
('Ibuprofen 400mg', 'GenPharm', 500, 0.15),
('Amoxicillin 250mg', 'MedCorp', 300, 0.25),
('Paracetamol 500mg', 'GenPharm', 1000, 0.10);

INSERT INTO prescriptions (record_id, medication_id, dosage, duration_days) VALUES
(1, 1, '400mg twice daily', 7),
(2, 3, '500mg every 6 hours', 5);

INSERT INTO billing (patient_id, admission_id, appointment_id, amount, status, bill_date) VALUES
(3, 1, 3, 1850.00, 'PAID', now() - interval '1 days'),
(4, NULL, 4, 320.00, 'PAID', now() - interval '9 days'),
(5, 2, NULL, 4200.00, 'UNPAID', now());
