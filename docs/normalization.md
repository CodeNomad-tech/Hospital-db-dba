# Normalization Notes

The schema is normalized to **Third Normal Form (3NF)**. This section
documents the reasoning, since "why is it normalized this way" is a common
interview question.

## 1NF — atomic values, no repeating groups
Every column holds a single atomic value. The obvious violation to avoid
here was storing a patient's list of past diagnoses or medications as a
comma-separated string in the `patients` row. Instead, `medical_records`
and `prescriptions` are separate tables with one row per event.

## 2NF — no partial dependency on a composite key
Only one table has a natural composite-key candidate: `prescriptions`
(record + medication). Its non-key attributes (`dosage`, `duration_days`)
depend on the *combination* of record and medication, not on either alone,
so 2NF holds. Everywhere else, single-column surrogate primary keys
(`SERIAL`) sidestep partial-dependency issues entirely.

## 3NF — no transitive dependency on non-key attributes
The clearest transitive dependency to watch for was **department data
being duplicated on the doctors/rooms tables**. Early draft schemas are
tempted to store `department_name` and `department_location` directly on
`doctors`. That's a transitive dependency (`doctor -> department_id ->
department_name`) and it means renaming a department requires updating
every doctor row. Instead, `departments` is its own table and everything
else references `department_id`.

Same reasoning applied to:
- **Insurance details** — pulled into `insurance_policies` rather than
  columns on `patients`, since a patient can hold more than one policy
  and provider details shouldn't be duplicated per patient.
- **Medication details** — `medications` is separate from `prescriptions`
  so that `unit_price` and `stock_quantity` live in exactly one place.

## Deliberate denormalization: none (yet)
For an OLTP hospital system at this scale, full 3NF is the right call —
data integrity (never double-charging or losing sync on a patient's
insurance provider) matters more than the marginal join cost. If this
system needed to serve a reporting/analytics workload at scale, the
`docs/query-tuning.md` notes cover where a materialized view or a
read-replica-backed star schema would make sense instead of denormalizing
the OLTP tables directly.
