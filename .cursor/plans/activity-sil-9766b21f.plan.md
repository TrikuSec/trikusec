<!-- 9766b21f-687b-4a38-a11b-d239b1ca1b6f 8db3fa0f-6e55-4051-aa27-d41efb0cbb04 -->
# Activity Silencing Feature Implementation

## Overview

Add a "Configure Silent Events" button that opens a sidebar panel for managing activity silencing rules. These rules will retroactively filter the activity view based on key name, event type, and host pattern.

## Database Schema Changes

### 1. Extend ActivityIgnorePattern Model

Update `src/api/models.py` - `ActivityIgnorePattern` class (lines 79-93):

**Add new fields:**

- `event_type`: CharField with choices ('all', 'added', 'changed', 'removed')
- `host_pattern`: CharField (default '*' for all hosts, supports patterns like 'web-*')
- Rename `pattern` to `key_pattern` for clarity

**Update:**

- `unique_together` constraint to include event_type and host_pattern
- Add appropriate indexes for filtering performance
- Update `__str__` method to show all criteria

### 2. Create Migration

Create migration file at `src/api/migrations/0014_extend_activity_ignore_pattern.py`:

- Add `event_type` field (default='all')
- Add `host_pattern` field (default='*')
- Rename `pattern` to `key_pattern` (using `AlterField` + data migration)
- Update indexes and constraints

## Backend Implementation

### 3. Update Activity View Filtering Logic

Modify `src/frontend/views.py` - `activity()` function (lines 1000-1161):

**Current behavior:** Activities are generated from DiffReport objects without filtering.

**New behavior:**

- After generating activities list (line 1058), apply filtering
- Fetch active `ActivityIgnorePattern` rules for the organization
- For each activity, check if it matches any rule:
  - Match key_pattern (exact match or wildcard)
  - Match event_type ('all' or specific type)
  - Match host_pattern against device hostname (use fnmatch for wildcard patterns)
- Remove matching activities before grouping

### 4. Create Silence Rule Management Views

Create new views in `src/frontend/views.py`:

**`silence_rule_list(request)`** (read-only, embedded in sidebar)

- Return JSON list of all silence rules for the current organization
- Include: id, key_pattern, event_type, host_pattern, is_active

**`silence_rule_create(request)`**

- POST endpoint for creating new silence rules
- Validate key_pattern, event_type, host_pattern
- Handle AJAX (return JSON) and fallback (redirect)

**`silence_rule_edit(request, rule_id)`**

- POST endpoint for updating existing rules
- Support AJAX and fallback

**`silence_rule_delete(request, rule_id)`**

- POST endpoint for deleting rules
- Support AJAX and fallback

### 5. Create Django Form

Create `src/frontend/forms.py` - `ActivityIgnorePatternForm`:

- Fields: key_pattern, event_type, host_pattern, is_active
- Validation for patterns (no empty strings)
- Help text explaining wildcard patterns

## Frontend Implementation

### 6. Create Sidebar Template

Create `src/frontend/templates/activity/silence_rules_sidebar.html`:

**Structure:**

- Fixed right-side panel (w-1/3 or w-96)
- Header: "Configure Silent Events" + close button
- Body: List of existing rules (table or cards)
- Each rule shows: key pattern, event type badge, host pattern
- Edit/Delete buttons for each rule
- "Add New Rule" form at bottom
- Form fields: key_pattern (text), event_type (select), host_pattern (text)
- Submit/Cancel buttons

### 7. Create JavaScript Module

Create `src/frontend/static/js/silence_rules.js`:

**Functions:**

- `toggleSilenceRulesPanel()`: Show/hide sidebar
- `loadSilenceRules()`: Fetch rules via AJAX, populate list
- `submitSilenceRuleForm()`: Create new rule via AJAX
- `editSilenceRule(ruleId)`: Open edit form in sidebar
- `updateSilenceRule()`: Update rule via AJAX
- `deleteSilenceRule(ruleId)`: Delete with confirmation
- `showFormErrors(errors)`: Display validation errors
- Event delegation for buttons (Firefox compatibility)

### 8. Update Activity Template

Modify `src/frontend/templates/activity.html`:

**Add button** (near line 191, next to title):

- "Configure Silent Events" button with icon
- Onclick handler to toggle sidebar

**Include sidebar template** (before {% endblock %}, around line 301):

- {% include 'activity/silence_rules_sidebar.html' %}

**Load JavaScript** (in {% block scripts %}, after line 342):

- Load silence_rules.js
- Pass organization data to JavaScript

### 9. Add URL Patterns

Update `src/trikusec/urls.py` to add routes:

- `path('activity/silence/', views.silence_rule_list, name='silence_rule_list')`
- `path('activity/silence/create/', views.silence_rule_create, name='silence_rule_create')`
- `path('activity/silence/<int:rule_id>/edit/', views.silence_rule_edit, name='silence_rule_edit')`
- `path('activity/silence/<int:rule_id>/delete/', views.silence_rule_delete, name='silence_rule_delete')`

## Testing

### 10. Write Tests

Add tests to `src/api/tests.py`:

- Test ActivityIgnorePattern model with new fields
- Test pattern matching logic (key, event type, host pattern)
- Test wildcard patterns (fnmatch behavior)

Add tests to `src/frontend/tests_e2e.py`:

- Test opening/closing silence rules sidebar
- Test creating a new silence rule
- Test editing existing rule
- Test deleting rule
- Test that silenced activities are hidden from view

## Implementation Notes

### Pattern Matching Logic

Use Python's `fnmatch` module for wildcard matching:

```python
import fnmatch

# Match key pattern
if rule.key_pattern != '*' and not fnmatch.fnmatch(activity['key'], rule.key_pattern):
    continue

# Match host pattern
if rule.host_pattern != '*' and not fnmatch.fnmatch(device.hostname, rule.host_pattern):
    continue

# Match event type
if rule.event_type != 'all' and activity['type'] != rule.event_type:
    continue
```

### Sidebar Design

Follow existing sidebar pattern from:

- Rules: `src/frontend/templates/policy/rule_edit_sidebar.html`
- Licenses: `src/frontend/templates/license/license_edit_sidebar.html`

Key elements:

- Fixed positioning with z-50
- Header with title and close button
- Form with proper CSRF token
- Error message container
- Action buttons fixed at bottom
- Event delegation for Firefox compatibility

### Organization Context

Currently single-tenant, but code is prepared for multi-tenancy:

- All silence rules belong to an organization
- Get default organization in views: `Organization.objects.first()`
- Filter rules by organization when applying

## Files to Create

1. `src/api/migrations/0014_extend_activity_ignore_pattern.py`
2. `src/frontend/templates/activity/silence_rules_sidebar.html`
3. `src/frontend/static/js/silence_rules.js`

## Files to Modify

1. `src/api/models.py` - ActivityIgnorePattern model
2. `src/frontend/views.py` - activity() view + new CRUD views
3. `src/frontend/forms.py` - Add ActivityIgnorePatternForm
4. `src/frontend/templates/activity.html` - Add button + include sidebar
5. `src/trikusec/urls.py` - Add URL patterns
6. `src/api/tests.py` - Add unit tests
7. `src/frontend/tests_e2e.py` - Add E2E tests

### To-dos

- [ ] Extend ActivityIgnorePattern model and create migration
- [ ] Update activity view to filter based on silence rules
- [ ] Create ActivityIgnorePatternForm for validation
- [ ] Create CRUD views for silence rule management
- [ ] Create silence_rules_sidebar.html template
- [ ] Create silence_rules.js for sidebar interactions
- [ ] Add button and include sidebar in activity.html
- [ ] Add URL patterns for silence rule endpoints
- [ ] Write unit tests for pattern matching logic
- [ ] Write E2E tests for sidebar UI interactions