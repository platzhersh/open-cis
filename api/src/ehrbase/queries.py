"""Common AQL queries for clinical data retrieval."""

# Get all vital signs for a patient
VITAL_SIGNS_QUERY = """
SELECT
    c/uid/value as composition_id,
    o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
    o/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic,
    o/data[at0001]/events[at0006]/time/value as time
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v2]
WHERE e/ehr_id/value = $ehr_id
ORDER BY o/data[at0001]/events[at0006]/time/value DESC
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
