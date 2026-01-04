# ADR-0001: openEHR Template Management

## Status
Accepted

## Context

Open CIS uses EHRBase as its openEHR Clinical Data Repository. EHRBase requires Operational Templates (OPT) to be registered before compositions can be created against them. Without the template, composition creation fails with a 400 error.

Templates define the structure of clinical data by constraining openEHR archetypes. For example, a "Vital Signs" template combines the `blood_pressure.v2` and `pulse.v2` observation archetypes within an `encounter.v1` composition archetype.

### Problem

1. Templates must be uploaded to EHRBase before the application can store clinical data
2. Developers may forget to upload templates when setting up a new environment
3. Different environments (dev, staging, prod) need consistent template configurations

## Decision

We will implement automatic template registration on API startup:

1. **Template Storage**: OPT files are stored in `api/templates/` directory, named `{template_id}.opt`

2. **Startup Registration**: On API startup, the application:
   - Checks which templates are already registered in EHRBase
   - Uploads any missing required templates
   - Logs success/failure for each template

3. **Required Templates**: The list of required templates is maintained in `src/ehrbase/templates.py`:
   ```python
   REQUIRED_TEMPLATES = [
       "open-cis.vital-signs.v1",
   ]
   ```

4. **Graceful Degradation**: If EHRBase is unavailable or template upload fails:
   - The API continues to start
   - A warning is logged
   - Features requiring that template will fail gracefully

## Template Creation

Proper OPT files should be created using openEHR tooling:

1. **Ocean Template Designer** (free): https://tools.openehr.org/designer/
2. **Better Archetype Designer**: https://tools.better.care/
3. **ADL Designer**: https://tools.openehr.org/designer/

The workflow:
1. Import required archetypes from CKM (Clinical Knowledge Manager)
2. Create a template constraining those archetypes
3. Export as OPT 1.4 format
4. Place the `.opt` file in `api/templates/`

### Template Structure

Our vital signs template (`open-cis.vital-signs.v1`) includes:
- **Composition**: `openEHR-EHR-COMPOSITION.encounter.v1` - Container for clinical encounter
- **Blood Pressure**: `openEHR-EHR-OBSERVATION.blood_pressure.v2` - Systolic/diastolic readings
- **Pulse**: `openEHR-EHR-OBSERVATION.pulse.v2` - Heart rate measurement

## Consequences

### Positive
- New environments automatically get required templates
- Developers don't need to manually upload templates
- Template configuration is version-controlled
- Consistent behavior across environments

### Negative
- OPT files are large and complex XML
- Creating new templates requires external tooling
- Template upload adds startup time (minimal)

### Neutral
- Templates are EHRBase-specific (other CDRs may need different formats)
- Template IDs must match between OPT files and application code

## File Locations

```
api/
├── templates/
│   └── open-cis.vital-signs.v1.opt    # OPT template file
├── scripts/
│   └── upload_templates.py             # Manual upload script
└── src/
    └── ehrbase/
        └── templates.py                 # Template management code
```

## Related

- PRD-0004: Vital Signs Chart
- EHRBase documentation: https://ehrbase.readthedocs.io/
- openEHR CKM: https://ckm.openehr.org/
