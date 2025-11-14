<!-- cc124b7e-61b5-474d-ac0d-b38b05ecf23f 7b65023a-9374-4b26-8f1a-face55ab0a09 -->
# Collapsible License Sidebar Implementation

Convert the license key edit/new license window into a collapsible sidebar panel, similar to the rulesect selection edition menu.

## Pattern Reference

Following the existing pattern from:

- Template: `src/frontend/templates/policy/rule_edit_sidebar.html`
- JavaScript: `src/frontend/static/js/rules.js` (`toggleRuleEditPanel`, `loadRuleDetails`)

## Files to Create

### 1. License Edit Sidebar Template

**File:** `src/frontend/templates/license/license_edit_sidebar.html` (new)

Create a fixed right-side panel with:

- Header with "Edit License" / "Create License" title and close button
- Form fields: name, max_devices, expires_at, is_active toggle (styled like rule enabled toggle)
- Apply and Cancel buttons at bottom
- Hidden by default with `hidden` class
- Fixed positioning: `fixed right-0 top-0 h-full w-1/4`

### 2. License JavaScript Functions

**File:** `src/frontend/static/js/licenses.js` (new)

Create functions:

- `toggleLicenseEditPanel(licenseId)`: Toggle sidebar visibility, set form action, load data
- `loadLicenseDetails(licenseId)`: Populate form fields (empty for new, fetch data for edit)
- Event listeners for all buttons with class `license-edit-panel-button`

Pass license data from Django context to JavaScript (similar to `rules` variable in rulesets.js).

## Files to Modify

### 3. Update License List Template

**File:** `src/frontend/templates/license/license_list.html`

Changes:

- Change "+ New License" link (line 11) to button with `onclick="toggleLicenseEditPanel(null)"`
- Change edit icon link (line 73) to button with `onclick="toggleLicenseEditPanel({{ license.id }})"`
- Change "Create one" link (line 96) to button with `onclick="toggleLicenseEditPanel(null)"`
- Include sidebar template: `{% include 'license/license_edit_sidebar.html' %}`
- Load JavaScript: `<script src="{% static 'js/licenses.js' %}"></script>`
- Pass licenses data to JavaScript in script block

### 4. Update License Detail Template

**File:** `src/frontend/templates/license/license_detail.html`

Changes:

- Change "Edit" link (line 12) to button with `onclick="toggleLicenseEditPanel({{ license.id }})"`
- Include sidebar template: `{% include 'license/license_edit_sidebar.html' %}`
- Load JavaScript: `<script src="{% static 'js/licenses.js' %}"></script>`
- Pass license data to JavaScript in script block

### 5. Update Django Views

**File:** `src/frontend/views.py`

Modify `license_create` (line 463) and `license_edit` (line 489):

- Check if request is AJAX/has specific header for sidebar submissions
- Return JSON response with success/error for AJAX requests
- Redirect to referer or license_detail on success
- Keep backward compatibility for any direct URL access

### 6. Update URL Configuration (if needed)

**File:** `src/frontend/urls.py`

Verify URLs for license_create and license_edit accept POST submissions and handle the form correctly.

## Files to Remove

### 7. Remove Full-Page License Form

**File:** `src/frontend/templates/license/license_form.html`

Delete this file as it's replaced by the sidebar.

## Implementation Details

### Form Field Styling

Match the rule edit sidebar styling:

- Toggle switch for `is_active` field (like rule enabled/disabled)
- Standard text inputs with Tailwind classes
- DateTime picker for `expires_at`
- Number input for `max_devices`

### JavaScript Data Passing

In templates with the sidebar, add script block:

```javascript
const licenses = {{ licenses_json|safe }};  // For list page
const license = {{ license_json|safe }};    // For detail page
```

Serialize license data in Django views using `json.dumps()`.

### CSRF Token Handling

Ensure CSRF token is included in the sidebar form and JavaScript handles it for AJAX submissions.

### Success/Error Handling

- On success: Close sidebar, refresh page or update UI
- On error: Display error messages in sidebar without closing it
- Use Django messages framework for user feedback

### To-dos

- [ ] Create license_edit_sidebar.html with collapsible panel structure
- [ ] Create licenses.js with toggle and load functions
- [ ] Update license_list.html to use sidebar instead of links
- [ ] Update license_detail.html to use sidebar instead of links
- [ ] Modify license_create and license_edit views for AJAX handling
- [ ] Delete license_form.html template
- [ ] Test create/edit from both list and detail pages