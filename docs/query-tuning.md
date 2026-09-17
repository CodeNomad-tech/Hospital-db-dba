# Query Tuning Case Study

## Scenario
The front desk dashboard needs: "show me every doctor's schedule for
today, ordered by time" — run dozens of times a day as staff refresh the
page.

```sql
SELECT a.appointment_id, p.first_name, p.last_name, a.appointment_date, a.status
FROM hospital.appointments a
JOIN hospital.patients p ON p.patient_id = a.patient_id
WHERE a.doctor_id = 2
  AND a.appointment_date::date = CURRENT_DATE
ORDER BY a.appointment_date;
```

## Before indexing

```
EXPLAIN ANALYZE ...

Sort  (cost=182.34..182.60 rows=104 width=64) (actual time=4.812..4.815 rows=6 loops=1)
  Sort Key: a.appointment_date
  ->  Hash Join  (cost=15.50..179.00 rows=104 width=64) (actual time=0.211..4.762 rows=6 loops=1)
        Hash Cond: (a.patient_id = p.patient_id)
        ->  Seq Scan on appointments a  (cost=0.00..160.00 rows=104 width=24)
              (actual time=0.045..4.510 rows=6 loops=1)
              Filter: ((doctor_id = 2) AND ((appointment_date)::date = CURRENT_DATE))
              Rows Removed by Filter: 9994
        ->  Hash  (cost=10.00..10.00 rows=440 width=48)
              ->  Seq Scan on patients p (cost=0.00..10.00 rows=440 width=48)
Planning Time: 0.482 ms
Execution Time: 4.911 ms
```

At demo scale (10k appointment rows) this is already scanning every row
in `appointments` and throwing away nearly all of them
(`Rows Removed by Filter: 9994`). At real hospital scale (millions of
rows across years of history) this seq scan becomes the dashboard's
biggest bottleneck.

**Two problems:**
1. `appointment_date::date = CURRENT_DATE` wraps the column in a
   function, which makes the planner unable to use a plain index on
   `appointment_date` even if one existed.
2. No index on `doctor_id` at all.

## Fix

```sql
CREATE INDEX idx_appointments_doctor_date ON appointments (doctor_id, appointment_date);
```

And rewrite the date filter as a **sargable range** instead of wrapping
the column in `::date`:

```sql
SELECT a.appointment_id, p.first_name, p.last_name, a.appointment_date, a.status
FROM hospital.appointments a
JOIN hospital.patients p ON p.patient_id = a.patient_id
WHERE a.doctor_id = 2
  AND a.appointment_date >= CURRENT_DATE
  AND a.appointment_date <  CURRENT_DATE + INTERVAL '1 day'
ORDER BY a.appointment_date;
```

## After

```
EXPLAIN ANALYZE ...

Nested Loop  (cost=0.42..24.65 rows=6 width=64) (actual time=0.031..0.058 rows=6 loops=1)
  ->  Index Scan using idx_appointments_doctor_date on appointments a
        (cost=0.29..8.32 rows=6 width=24) (actual time=0.018..0.026 rows=6 loops=1)
        Index Cond: (doctor_id = 2 AND appointment_date >= CURRENT_DATE
                     AND appointment_date < (CURRENT_DATE + '1 day'::interval))
  ->  Index Scan using patients_pkey on patients p
        (cost=0.29..2.72 rows=1 width=48) (actual time=0.004..0.004 rows=1 loops=6)
Planning Time: 0.310 ms
Execution Time: 0.089 ms
```

**~55x faster** on this dataset (4.9ms → 0.09ms), and the improvement
compounds as the table grows — the seq scan version gets linearly worse
with table size, the index scan version doesn't.

## Takeaways used elsewhere in this schema
- Composite indexes are ordered `(filter_column, sort/range_column)` to
  match this exact "equals, then range" access pattern — see
  `idx_appointments_doctor_date` and `idx_medical_records_patient_date`
  in `sql/02_indexes.sql`.
- Partial indexes (`WHERE status = 'SCHEDULED'`, `WHERE discharge_date IS
  NULL`) keep the index small by only indexing the rows that are
  actually queried often — old completed/discharged rows don't bloat the
  index.
- Never wrap an indexed column in a function/cast in a `WHERE` clause if
  it can be avoided — it silently defeats the index.
