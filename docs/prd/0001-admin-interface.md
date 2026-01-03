# PRD-0001: Open CIS Admin Interface

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Build a modern, user-friendly admin interface within the existing Open CIS Vue application to manage openEHR/EHRBase operations. This internal tool will enable developers and clinical informaticists to interact with EHRBase without relying on external tools, Swagger UI, or curl commands.

**Inspiration:** [openEHRTool-v2](https://github.com/crs4/openEHRTool-v2) - CRS4's FastAPI/Vue3 tool with Redis caching for EHRBase artifact IDs and activity logging. Provides EHR methods, template management, composition operations, and AQL queries. Our version will integrate into the existing Open CIS app with enhanced UI using shadcn-vue instead of building a standalone tool.

---

## Problem Statement

**Current Pain Points:**
- No visual interface for managing openEHR templates, EHRs, and compositions
- Developers must use curl commands, Swagger UI, or external tools like Better Studio
- Testing and debugging compositions requires manual JSON crafting
- No easy way to execute AQL queries and visualize results
- Onboarding new developers to openEHR concepts is difficult without a GUI

**User Personas:**
1. **Developer** - Needs to test template uploads, create test EHRs, debug compositions
2. **Clinical Informaticist** - Wants to validate templates, run queries, inspect data structures
3. **QA/Tester** - Requires seed data creation, data verification, query testing

---

## Goals & Success Metrics

### Goals
- Reduce time to interact with EHRBase from 5+ minutes (finding docs, crafting curl) to <30 seconds (GUI click)
- Enable non-technical users to explore openEHR concepts visually
- Provide a learning tool for understanding openEHR templates, compositions, and AQL
- Eliminate dependency on external tools for basic EHRBase operations

### Success Metrics
- 100% of basic CRUD operations available via GUI (templates, EHRs, compositions)
- AQL query interface with syntax highlighting and result visualization
- Template upload/download with validation feedback
- <5 second response time for listing operations
- Mobile-responsive design (view-only acceptable on mobile)

---

## Feature Requirements

### Phase 1: Core Admin Features (MVP)

#### 1. Template Management
**Priority:** P0 (Must Have)

**User Stories:**
- As a developer, I want to upload OPT files (XML) to EHRBase so I can test new templates
- As a user, I want to see a list of all uploaded templates with their metadata
- As a user, I want to download template definitions for reference
- As a user, I want to delete test templates to clean up my environment

**Functional Requirements:**
- **Template List View**
  - Table/card display with columns: Template ID, Version, Created Date, Description
  - Search/filter by template ID or description
  - Sort by date, name
  - Pagination (20 items per page default)

- **Template Upload**
  - Drag-and-drop zone for OPT/XML files
  - File validation (check XML structure before upload)
  - Real-time upload progress indicator
  - Success/error feedback with detailed messages
  - Batch upload support (multiple files)

- **Template Details**
  - View raw XML in syntax-highlighted editor (read-only)
  - Display metadata: template ID, version, author, archetype details
  - Download button (saves OPT file locally)
  - Delete button with confirmation modal

**Technical Notes:**
- Use existing `ehrbase_client.upload_template()` from `api/src/ehrbase/templates.py`
- Store template metadata in app database (Prisma) for faster listing
- Use Monaco Editor or CodeMirror for XML display

---

#### 2. EHR Management
**Priority:** P0 (Must Have)

**User Stories:**
- As a developer, I want to create EHRs for test patients
- As a user, I want to see all EHRs and their metadata
- As a user, I want to link EHRs to patient records in the app database

**Functional Requirements:**
- **EHR List View**
  - Table with columns: EHR ID, Patient ID (if linked), Created Date, Status
  - Link to patient detail page if associated with app patient
  - Search by EHR ID or patient name
  - Badge indicators for linked vs unlinked EHRs

- **EHR Creation**
  - Option 1: Create standalone EHR (generates UUID)
  - Option 2: Create EHR for existing patient (dropdown selector)
  - Option 3: Create EHR + Patient simultaneously
  - Display EHR ID immediately after creation

- **EHR Details**
  - View EHR metadata (time_created, system_id, ehr_status)
  - List all compositions within this EHR (grouped by template)
  - Quick actions: Create Composition, View in EHRBase

**Technical Notes:**
- Use `ehrbase_client.create_ehr()` from `api/src/ehrbase/client.py`
- Sync EHR IDs with Prisma `Patient` model (foreign key relationship)
- Consider adding `ehr_status` field to Prisma schema for caching

---

#### 3. Composition Management
**Priority:** P0 (Must Have)

**User Stories:**
- As a developer, I want to create compositions from templates to test data structures
- As a user, I want to view existing compositions in human-readable format
- As a user, I want to edit and update compositions for testing
- As a QA tester, I want to generate example compositions with dummy data

**Functional Requirements:**
- **Composition List View**
  - Grouped by EHR ID and Template Type
  - Table columns: Composition UID, Template, EHR ID, Composer, Date
  - Filters: Template type, Date range, EHR ID
  - Quick preview (show first 100 chars of content)

- **Composition Creation Wizard**
  - Step 1: Select EHR (dropdown with search)
  - Step 2: Select Template (visual cards with template name/description)
  - Step 3: Choose input method:
    - **Form Builder:** Auto-generated form from template archetype (stretch goal)
    - **JSON Editor:** Monaco editor with schema validation
    - **Example Generator:** Auto-fill with dummy data based on template
  - Step 4: Preview & Submit

- **Composition Details**
  - Display composition in formatted JSON (syntax highlighted)
  - Show metadata: composer, time_committed, template_id
  - Edit mode: Toggle to JSON editor, validate on save
  - Delete with confirmation
  - Version history (if EHRBase supports)

**Technical Notes:**
- Use `ehrbase_client.create_composition()` from `api/src/ehrbase/compositions.py`
- JSON schema validation against template before submission
- Consider using `@rjsf/core` (React JSON Schema Form) or Vue equivalent for form generation
- Monaco Editor with JSON schema support for validation

---

#### 4. AQL Query Interface
**Priority:** P1 (Should Have)

**User Stories:**
- As a developer, I want to run AQL queries to explore data
- As a user, I want to see query results in a readable table format
- As a user, I want to save frequently used queries for reuse

**Functional Requirements:**
- **Query Editor**
  - Monaco Editor with AQL syntax highlighting
  - Query templates/snippets (e.g., "Get all EHRs", "Find vital signs")
  - Auto-complete for common AQL keywords (SELECT, FROM, WHERE)
  - Execute button with keyboard shortcut (Cmd+Enter)

- **Results Display**
  - Table view for SELECT results (auto-detect columns from resultSet)
  - JSON tree view toggle for raw response
  - Export results (CSV, JSON)
  - Result count and query execution time
  - Error display with line numbers (if query fails)

- **Query Library**
  - Save queries with name and description
  - Store in app database (user-specific or global)
  - Quick load from saved queries
  - Share query URL (encode query in URL params)

**Technical Notes:**
- Use `ehrbase_client.execute_aql_query()` from `api/src/ehrbase/queries.py`
- Monaco Editor with custom AQL language definition
- Consider using AG Grid or TanStack Table for result display
- Store saved queries in Prisma (new `SavedQuery` model)

---

### Phase 2: Advanced Features (Post-MVP)

#### 5. Composition Form Builder
**Priority:** P2 (Nice to Have)

Auto-generate forms from openEHR archetypes:
- Parse OPT/XML to extract data points
- Generate Vue forms with validation
- Support common archetypes (Vital Signs, Medications, Lab Results)
- Custom form templates per template ID

**Technical Challenges:**
- Archetype parsing is complex (consider using ADL Parser library)
- Mapping archetypes to UI components requires openEHR expertise
- May require significant R&D phase

---

#### 6. Data Visualization & Analytics
**Priority:** P2 (Nice to Have)

- Dashboard showing EHRBase statistics (total EHRs, compositions by type, storage size)
- Composition timeline view (visualize patient data over time)
- Query result charts (bar, line, pie based on AQL results)
- Template usage analytics (most used templates, data completeness)

**Technical Notes:**
- Use Chart.js or Apache ECharts for visualizations
- Pre-built AQL queries for common analytics
- Cache results in Redis for performance

---

#### 7. Template Archetype Designer (Future)
**Priority:** P3 (Future Consideration)

- Visual archetype editor (drag-and-drop components)
- Template validation and testing
- Export to OPT/XML format

**Note:** This is extremely complex and may be out of scope. Consider integrating with existing tools (Archetype Designer) via iframe or links instead.

---

## Learnings from openEHRTool-v2

### What to Adopt
1. **Redis Caching Strategy**
   - Cache artifact IDs (template IDs, composition UIDs) for faster lookups
   - Activity logging for audit trail and debugging
   - Consider adding Redis to our docker-compose stack

2. **Session Management**
   - User authentication for multi-user environments
   - Track which user performed which admin action

3. **Method-Specific Panels**
   - Dedicated UI sections for EHR, Template, Composition, Query operations
   - Matches our planned sidebar navigation structure

### What to Improve
1. **Better UI/UX**
   - openEHRTool-v2 is functional but lacks polish
   - We'll use shadcn-vue for modern, accessible components
   - Add responsive design for tablet/mobile viewing

2. **Integration vs Standalone**
   - openEHRTool-v2 is a separate application
   - We'll integrate admin into existing Open CIS app (single deployment)
   - Share authentication, database, and API infrastructure

3. **Enhanced Features**
   - Add export functionality (CSV, JSON) for query results
   - Saved query library with sharing capabilities
   - Real-time validation feedback during composition creation

### Technical Compatibility
- **EHRBase Version:** openEHRTool-v2 tested with EHRBase 2.15.0 (we're using similar version)
- **Python Version:** Both use Python 3.11+
- **FastAPI:** Both use async FastAPI patterns
- **Vue 3:** Same frontend framework

---

## User Interface Design

### Design Principles
1. **Consistency:** Use existing shadcn-vue components and design system
2. **Clarity:** Clear labels, helpful tooltips, inline documentation
3. **Feedback:** Loading states, success/error messages, validation feedback
4. **Efficiency:** Keyboard shortcuts, quick actions, batch operations
5. **Accessibility:** WCAG 2.1 AA compliance, screen reader support

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Top Navigation (existing)                           │
│ [Patients] [Encounters] [Admin] [Profile]           │
└─────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────────────────┐
│ Admin Sidebar│  Main Content Area                   │
│              │                                       │
│ Templates    │  ┌─────────────────────────────────┐ │
│ EHRs         │  │  Page Header                    │ │
│ Compositions │  │  [Actions] [Search] [Filter]    │ │
│ AQL Queries  │  └─────────────────────────────────┘ │
│ Settings     │                                       │
│              │  ┌─────────────────────────────────┐ │
│              │  │                                 │ │
│              │  │  Data Table / Editor            │ │
│              │  │                                 │ │
│              │  │                                 │ │
│              │  └─────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────┘
```

### Component Library
Leverage existing shadcn-vue components:
- **Tables:** Data Table with sorting, filtering, pagination
- **Forms:** Input, Select, Textarea, File Upload (Dropzone)
- **Buttons:** Primary, Secondary, Destructive, Ghost
- **Modals:** Dialog for confirmations, Sheet for side panels
- **Feedback:** Toast for notifications, Alert for inline messages
- **Code:** Monaco Editor integration (add as new component)
- **Navigation:** Tabs for sub-sections, Breadcrumbs for context

### Visual Design Enhancements (vs openEHRTool-v2)
- Modern color palette with proper contrast ratios
- Subtle animations and transitions (not distracting)
- Responsive grid layouts (mobile, tablet, desktop)
- Dark mode support (leverage existing theme)
- Icon set (Lucide icons, consistent with current app)

---

## Technical Architecture

### Frontend (Vue 3 + TypeScript)

**New Pages:**
```
web/src/pages/admin/
├── index.vue                 # Admin dashboard/overview
├── templates/
│   ├── index.vue            # Template list
│   ├── upload.vue           # Template upload page
│   └── [id].vue             # Template detail
├── ehrs/
│   ├── index.vue            # EHR list
│   ├── create.vue           # EHR creation
│   └── [id].vue             # EHR detail (with compositions)
├── compositions/
│   ├── index.vue            # Composition list
│   ├── create.vue           # Composition creation wizard
│   └── [id].vue             # Composition detail/edit
└── queries/
    ├── index.vue            # Query editor + saved queries
    └── results/[id].vue     # Query results viewer
```

**New Stores (Pinia):**
```typescript
// web/src/stores/admin/
adminTemplateStore.ts    // Template CRUD + state
adminEhrStore.ts         // EHR CRUD + state
adminCompositionStore.ts // Composition CRUD + state
adminQueryStore.ts       // AQL query execution + history
```

**New Composables:**
```typescript
// web/src/composables/admin/
useTemplateUpload.ts     // Upload logic, validation, progress
useAqlEditor.ts          // Monaco editor setup, syntax highlighting
useCompositionBuilder.ts // Composition creation helpers
```

**New Types:**
```typescript
// web/src/types/admin.ts
interface Template {
  template_id: string
  version: string
  description?: string
  created_at: string
  content: string // OPT XML
}

interface EhrSummary {
  ehr_id: string
  patient_id?: number
  created_at: string
  composition_count: number
}

interface Composition {
  uid: string
  ehr_id: string
  template_id: string
  composer: string
  time_committed: string
  content: object // FLAT or STRUCTURED format
}

interface AqlQuery {
  id?: number
  name: string
  description?: string
  query: string
  created_at?: string
  updated_at?: string
}
```

---

### Backend (FastAPI + Python)

**New API Endpoints:**

```python
# api/src/admin/ (new module)
router.py
service.py
schemas.py
repository.py  # For saving queries, template metadata

# api/src/admin/router.py
GET    /api/admin/templates              # List templates
POST   /api/admin/templates              # Upload template
GET    /api/admin/templates/{id}         # Get template details
DELETE /api/admin/templates/{id}         # Delete template

GET    /api/admin/ehrs                   # List EHRs (with filters)
POST   /api/admin/ehrs                   # Create EHR
GET    /api/admin/ehrs/{ehr_id}          # Get EHR details

GET    /api/admin/compositions           # List compositions
POST   /api/admin/compositions           # Create composition
GET    /api/admin/compositions/{uid}     # Get composition
PUT    /api/admin/compositions/{uid}     # Update composition
DELETE /api/admin/compositions/{uid}     # Delete composition

POST   /api/admin/queries/execute        # Execute AQL query
GET    /api/admin/queries/saved          # List saved queries
POST   /api/admin/queries/saved          # Save query
DELETE /api/admin/queries/saved/{id}     # Delete saved query
```

**Service Layer:**
```python
# api/src/admin/service.py
class AdminService:
    async def list_templates(self) -> list[TemplateMetadata]:
        # Call EHRBase REST API, cache in Prisma

    async def upload_template(self, file: UploadFile) -> Template:
        # Validate XML, upload to EHRBase, store metadata

    async def list_ehrs(self, filters: EhrFilters) -> list[EhrSummary]:
        # Query EHRBase + join with Prisma patients

    async def create_composition(
        self, ehr_id: str, template_id: str, content: dict
    ) -> Composition:
        # Validate against template schema, post to EHRBase

    async def execute_aql(self, query: str) -> AqlResult:
        # Execute via ehrbase_client, format results
```

**Prisma Schema Updates:**
```prisma
// api/prisma/schema.prisma

model TemplateMetadata {
  id          Int      @id @default(autoincrement())
  templateId  String   @unique @map("template_id")
  version     String
  description String?
  uploadedAt  DateTime @default(now()) @map("uploaded_at")

  @@map("template_metadata")
}

model SavedQuery {
  id          Int      @id @default(autoincrement())
  name        String
  description String?
  query       String
  createdBy   Int?     @map("created_by")
  createdAt   DateTime @default(now()) @map("created_at")
  updatedAt   DateTime @updatedAt @map("updated_at")

  user        User?    @relation(fields: [createdBy], references: [id])

  @@map("saved_queries")
}

// Optional: Add ehr_id to Patient model for linking
model Patient {
  // ... existing fields
  ehrId       String?  @unique @map("ehr_id")
}
```

---

## Implementation Plan

### Phase 1: MVP (Weeks 1-3)

**Week 1: Setup & Templates**
- [ ] Create admin module structure (frontend + backend)
- [ ] Add admin navigation to main app
- [ ] Implement template list view
- [ ] Implement template upload (drag-and-drop)
- [ ] Add Prisma model for template metadata
- [ ] Template detail view with XML display

**Week 2: EHRs & Compositions**
- [ ] EHR list view with patient linking
- [ ] EHR creation flow
- [ ] Composition list view
- [ ] Composition detail/view
- [ ] Composition creation (JSON editor mode)

**Week 3: AQL & Polish**
- [ ] AQL query editor with Monaco
- [ ] Query execution and results display
- [ ] Saved queries feature
- [ ] Error handling and loading states
- [ ] User testing and bug fixes

### Phase 2: Enhancements (Weeks 4-5)

**Week 4:**
- [ ] Composition form builder (basic version)
- [ ] Example data generator
- [ ] Export functionality (CSV, JSON)
- [ ] Query templates/snippets

**Week 5:**
- [ ] Data visualization dashboard
- [ ] Analytics and reporting
- [ ] Performance optimization
- [ ] Documentation

---

## Security & Permissions

### Access Control
- **Role-based access:**
  - `ADMIN`: Full access to all admin features
  - `CLINICIAN`: Read-only access to queries and views
  - `DEVELOPER`: Full access except deletion in production

- **Environment-based restrictions:**
  - Production: Disable template deletion, composition editing
  - Staging/Dev: All features enabled

### Data Protection
- Sanitize uploaded OPT files (XML validation, size limits)
- Rate limiting on AQL query execution (prevent abuse)
- Audit logging for all admin actions (who, what, when)
- No PHI exposure in logs or error messages

### Implementation
```python
# api/src/auth/permissions.py
class Permission(Enum):
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"

# Decorator for protected routes
@router.delete("/templates/{id}")
@require_permission(Permission.ADMIN_DELETE)
async def delete_template(id: str, user: CurrentUser):
    ...
```

---

## Testing Strategy

### Unit Tests
- Template upload validation logic
- AQL query parsing and sanitization
- Composition schema validation
- Service layer business logic

### Integration Tests
- EHRBase API interactions (mock with pytest-httpx)
- Prisma database operations
- End-to-end template upload flow
- Query execution with sample data

### E2E Tests (Playwright)
- Navigate to admin section
- Upload template file
- Create EHR and composition
- Execute AQL query and verify results

### Manual Testing Checklist
- [ ] Upload various OPT files (valid, invalid, large files)
- [ ] Create compositions with different templates
- [ ] Test AQL syntax errors and valid queries
- [ ] Verify mobile responsiveness
- [ ] Test with screen reader (accessibility)

---

## Documentation

### User Documentation
- **Admin Guide:** How to use each feature (templates, EHRs, compositions, queries)
- **AQL Tutorial:** Introduction to AQL with examples
- **Troubleshooting:** Common errors and solutions

### Developer Documentation
- **API Reference:** OpenAPI spec for admin endpoints
- **Architecture Diagram:** Component relationships and data flow
- **Contribution Guide:** How to add new admin features

### Location
```
docs/
├── admin-guide.md           # User-facing documentation
├── aql-tutorial.md          # AQL learning resource
├── admin-api-reference.md   # API documentation
└── admin-architecture.md    # Technical architecture
```

---

## Dependencies & Tools

### New NPM Packages
```json
{
  "monaco-editor": "^0.45.0",           // Code editor
  "@monaco-editor/vue": "^1.1.0",       // Vue wrapper
  "@tanstack/vue-table": "^8.11.0",     // Advanced tables
  "vue-dropzone": "^6.0.2",             // File upload
  "json-schema-faker": "^0.5.3"         // Example data generation
}
```

### New Python Packages
```toml
# pyproject.toml
[project.dependencies]
redis = "^5.0.0"         # Caching for artifact IDs and activity logs
xmlschema = "^2.5.0"     # Validate OPT files

[project.optional-dependencies]
dev = [
  "pytest-httpx",        # Mock EHRBase HTTP calls
  "faker",               # Generate test data
  "fakeredis",           # Redis mocking for tests
]
```

### Infrastructure Updates
```yaml
# docker-compose.yml - Add Redis service
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-data:
```

### Redis Cache Strategy (Inspired by openEHRTool-v2)
```python
# api/src/admin/cache.py
from redis import asyncio as aioredis

class AdminCache:
    """Cache for EHRBase artifacts and activity logs"""

    async def cache_template_id(self, template_id: str, ttl: int = 3600):
        """Cache template ID for quick validation"""

    async def log_activity(self, user_id: int, action: str, details: dict):
        """Store activity log for audit trail"""

    async def get_cached_composition_uids(self, ehr_id: str) -> list[str]:
        """Get cached composition UIDs for an EHR"""
```

---

## Open Questions & Risks

### Open Questions
1. **Form generation complexity:** Should we build archetype-to-form mapping or rely on JSON editor for MVP?
   - **Recommendation:** Start with JSON editor, add form builder in Phase 2 for 2-3 common templates

2. **Template versioning:** How do we handle multiple versions of the same template?
   - **Recommendation:** Display all versions, allow selection in composition creation

3. **Multi-tenancy:** If we add multi-organization support, how does admin scope?
   - **Recommendation:** Admin is organization-scoped, superadmin for cross-org

### Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| EHRBase API changes break integration | High | Medium | Version lock EHRBase, add integration tests |
| Complex archetype parsing is too hard | Medium | High | Skip form builder in MVP, use JSON editor |
| Performance issues with large result sets | Medium | Medium | Pagination, query timeouts, result limits |
| Users upload malicious XML files | High | Low | Strict XML validation, file size limits, sandboxing |

---

## Success Criteria

**MVP is successful if:**
- ✅ Can upload, list, view, delete templates via GUI
- ✅ Can create EHRs and link to patients
- ✅ Can create compositions using JSON editor
- ✅ Can execute AQL queries and export results
- ✅ All operations complete in <5 seconds
- ✅ Zero critical bugs in first week of use
- ✅ 2+ developers provide positive feedback

**Long-term success:**
- 80% of EHRBase interactions happen via GUI (not curl/Swagger)
- New developers onboard to openEHR in <1 day (vs current ~3 days)
- Template creation and testing cycle reduced by 50%

---

## Future Considerations

### v2.0 Ideas
- **Multi-tenant support:** Organization-scoped admin panels
- **Collaboration features:** Share queries, comment on compositions
- **Real-time updates:** WebSocket for live composition updates
- **Import/Export:** Bulk operations for templates and compositions
- **Template Marketplace:** Share common templates across organizations
- **AI-assisted query writing:** Natural language to AQL conversion
- **Data migration tools:** Import from HL7, FHIR, legacy systems

### Integration Opportunities
- **FHIR Gateway:** Convert FHIR resources to openEHR compositions
- **HL7 Parser:** Import HL7 v2 messages as compositions
- **Analytics Platform:** Export to data warehouse for BI tools
- **Notification System:** Alerts when compositions match criteria

---

## References

- [openEHRTool-v2 GitHub](https://github.com/crs4/openEHRTool-v2) - Inspiration project
- [EHRBase REST API Docs](https://docs.ehrbase.org/) - API reference
- [openEHR Specifications](https://specifications.openehr.org/) - Domain concepts
- [AQL Syntax Guide](https://specifications.openehr.org/releases/QUERY/latest/AQL.html) - Query language
- [Better Platform](https://platform.better.care/) - Commercial reference implementation

---

## Appendix A: Sample AQL Queries

```sql
-- Get all EHRs
SELECT e/ehr_id/value FROM EHR e

-- Find all compositions for a patient
SELECT
  c/uid/value,
  c/archetype_details/template_id/value,
  c/context/start_time/value
FROM EHR e
CONTAINS COMPOSITION c
WHERE e/ehr_id/value = '{{ehr_id}}'

-- Get vital signs for a patient
SELECT
  c/uid/value as composition_id,
  obs/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
  obs/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS OBSERVATION obs[openEHR-EHR-OBSERVATION.blood_pressure.v2]
WHERE e/ehr_id/value = '{{ehr_id}}'
ORDER BY c/context/start_time/value DESC

-- Count compositions by template
SELECT
  c/archetype_details/template_id/value as template,
  COUNT(*) as count
FROM EHR e
CONTAINS COMPOSITION c
GROUP BY template
ORDER BY count DESC
```

---

## Appendix B: UI Mockup Descriptions

### Template List View
- **Header:** "Templates" with upload button (primary action)
- **Search bar:** Full-text search across template ID and description
- **Table:**
  - Columns: Template ID (bold, clickable), Version (badge), Description (truncated), Uploaded (relative time)
  - Row actions: View, Download, Delete (icon buttons)
  - Hover: Highlight row, show quick preview tooltip
- **Empty state:** Illustration with "No templates yet" and "Upload your first template" CTA

### AQL Query Editor
- **Split view:**
  - Left (40%): Saved queries sidebar with search and categories
  - Right (60%): Editor (top 50%), Results (bottom 50%)
- **Editor toolbar:**
  - Run button (Cmd+Enter hint), Format query, Clear, Save
- **Results tabs:**
  - Table view (default), JSON view, Export (dropdown)
- **Footer:** Query execution time, row count, EHRBase status indicator

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Open CIS Team | Initial PRD draft |

