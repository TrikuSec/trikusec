<!-- 30e5b7f2-caab-4394-90ff-378d9a44b94f db755a8d-9f76-49fe-af0b-c314caa8db36 -->
# Add Rule View Sidebar to Device Detail

## Overview

Add a "View" action with an eye icon to rule rows in the Device detail page's Compliance Policy Rulesets section. When clicked, it opens a read-only sidebar displaying rule details and evaluation debug information (query field name, operator, expected value, actual value from report, and pass/fail status). The sidebar will close any previously open sidebars.

## Implementation Steps

### 1. Backend: Create Rule Evaluation View

**File**: `src/frontend/views.py`

Add a new view function `rule_evaluate_for_device` that:

- Accepts `device_id` and `rule_id` as URL parameters
- Fetches the device and its last report
- Fetches the rule details
- Uses `parse_query()` from `src/api/utils/policy_query.py` to extract field, operator, and expected value
- Gets the actual value from the parsed report using `report.get(field)`
- Evaluates the rule using `rule.evaluate(report)`
- Returns JSON response with:
  - Rule details (id, name, description, rule_query, enabled)
  - Query components (field, operator, expected_value)
  - Actual value from report (or indication if key not found)
  - Evaluation result (pass/fail)

**File**: `src/frontend/urls.py`

Add URL pattern:

```python
path('device/<int:device_id>/rule/<int:rule_id>/evaluate/', views.rule_evaluate_for_device, name='rule_evaluate_for_device')
```

### 2. Frontend: Create View Sidebar Template

**File**: `src/frontend/templates/device/rule_view_sidebar.html` (new file)

Create a sidebar template following the collapsible sidebar pattern similar to `src/frontend/templates/policy/rule_edit_sidebar.html` but read-only:

- Fixed right panel with close button
- Display rule basic info (name, description, enabled status)
- Display "Query Evaluation" section with:
  - Rule query (monospace font)
  - Field name being checked
  - Operator
  - Expected value
  - Actual value from report (or "Key not found" message)
  - Evaluation result (Pass/Fail with appropriate color)
- Close button at the bottom
- Use CSS classes: `.rule-view-panel-button` for close buttons

### 3. Frontend: Update Device Compliance Template

**File**: `src/frontend/templates/device/device_compliance.html`

In the rule row actions section (around line 99-107), add eye icon button before the edit button:

```html
<button onclick="toggleRuleViewPanel({{ device.id }}, {{ rule.id }})" class="text-gray-600 hover:text-gray-800" title="View Rule Evaluation">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
</button>
```

### 4. Frontend: Include Sidebar in Device Detail

**File**: `src/frontend/templates/device_detail.html`

Include the new sidebar template after the existing sidebars (search for where `rule_edit_sidebar.html` is included and add after it):

```django
{% include 'device/rule_view_sidebar.html' %}
```

### 5. Frontend: Create JavaScript for View Sidebar

**File**: `src/frontend/static/js/rule_view.js` (new file)

Create JavaScript functions:

- `toggleRuleViewPanel(deviceId, ruleId)`: Opens/closes the view panel and closes other sidebars
- `loadRuleEvaluation(deviceId, ruleId)`: Fetches rule evaluation data via AJAX from the new endpoint
- `displayRuleEvaluation(data)`: Populates the sidebar with the evaluation data
- `closeRuleViewPanel()`: Closes the view panel
- Event listeners for close buttons with class `.rule-view-panel-button`

Key behavior: Before opening, close other sidebars (`#rule-edit-panel`, `#ruleset-selection-panel`, `#ruleset-edit-panel`)

### 6. Frontend: Load JavaScript in Device Detail

**File**: `src/frontend/templates/device_detail.html`

In the `{% block scripts %}` section, add:

```html
<script src="{% static 'js/rule_view.js' %}"></script>
```

## Testing Approach

- Navigate to a device detail page with assigned rulesets and rules
- Click the eye icon on a rule row
- Verify the sidebar opens with correct rule details and evaluation info
- Verify actual values from report are displayed correctly
- Verify "Key not found" message appears when field doesn't exist in report
- Verify clicking eye icon while edit sidebar is open closes the edit sidebar
- Verify close button and cancel button work correctly

## Files to Modify

1. `src/frontend/views.py` - Add rule evaluation view
2. `src/frontend/urls.py` - Add URL pattern
3. `src/frontend/templates/device/device_compliance.html` - Add eye icon button
4. `src/frontend/templates/device_detail.html` - Include sidebar and load JS

## Files to Create

1. `src/frontend/templates/device/rule_view_sidebar.html` - View sidebar template
2. `src/frontend/static/js/rule_view.js` - JavaScript for view sidebar functionality

### To-dos

- [ ] Create rule_evaluate_for_device view in frontend/views.py that fetches rule and device data, evaluates the rule, and returns JSON with debug information
- [ ] Add URL pattern for device/<device_id>/rule/<rule_id>/evaluate/ in frontend/urls.py
- [ ] Create rule_view_sidebar.html template with read-only rule details and evaluation debug information display
- [ ] Add eye icon button to rule rows in device_compliance.html that triggers toggleRuleViewPanel()
- [ ] Include rule_view_sidebar.html in device_detail.html template
- [ ] Create rule_view.js with functions to open/close sidebar, fetch evaluation data via AJAX, and display results
- [ ] Load rule_view.js in device_detail.html scripts block