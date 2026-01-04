"""Common AQL queries for clinical data retrieval."""

# Get all vital signs (blood pressure + pulse) for a patient
VITAL_SIGNS_QUERY = """
SELECT
    c/uid/value as composition_id,
    c/context/start_time/value as recorded_at,
    bp/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
    bp/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic,
    pulse/data[at0002]/events[at0003]/data[at0001]/items[at0004]/value/magnitude as pulse_rate
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS (
    OBSERVATION bp[openEHR-EHR-OBSERVATION.blood_pressure.v1] OR
    OBSERVATION pulse[openEHR-EHR-OBSERVATION.pulse.v1]
)
WHERE e/ehr_id/value = $ehr_id
ORDER BY c/context/start_time/value DESC
"""

# Get vital signs for a patient within a date range
VITAL_SIGNS_DATE_RANGE_QUERY = """
SELECT
    c/uid/value as composition_id,
    c/context/start_time/value as recorded_at,
    bp/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
    bp/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic,
    pulse/data[at0002]/events[at0003]/data[at0001]/items[at0004]/value/magnitude as pulse_rate
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS (
    OBSERVATION bp[openEHR-EHR-OBSERVATION.blood_pressure.v1] OR
    OBSERVATION pulse[openEHR-EHR-OBSERVATION.pulse.v1]
)
WHERE e/ehr_id/value = $ehr_id
AND c/context/start_time/value >= $from_date
AND c/context/start_time/value <= $to_date
ORDER BY c/context/start_time/value DESC
"""

# Get all encounters for a patient
ENCOUNTERS_QUERY = """
SELECT
    c/uid/value as composition_id,
    c/context/start_time/value as start_time,
    c/name/value as type
FROM EHR e
CONTAINS COMPOSITION c[openEHR-EHR-COMPOSITION.encounter.v1]
WHERE e/ehr_id/value = $ehr_id
ORDER BY c/context/start_time/value DESC
"""

# Get medication orders for a patient
MEDICATIONS_QUERY = """
SELECT
    c/uid/value as composition_id,
    i/activities[at0001]/description[at0002]/items[at0070]/value/value as medication_name,
    i/activities[at0001]/description[at0002]/items[at0009]/value/value as dose
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS INSTRUCTION i[openEHR-EHR-INSTRUCTION.medication_order.v3]
WHERE e/ehr_id/value = $ehr_id
"""

# Count vital signs for a patient
VITAL_SIGNS_COUNT_QUERY = """
SELECT COUNT(c/uid/value) as count
FROM EHR e
CONTAINS COMPOSITION c
WHERE e/ehr_id/value = $ehr_id
AND c/archetype_details/template_id/value = 'open-cis.vital-signs.v1'
"""
