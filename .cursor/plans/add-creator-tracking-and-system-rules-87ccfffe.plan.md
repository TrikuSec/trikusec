<!-- 87ccfffe-8795-490d-8734-28c5502e42ad c4b72649-99a0-487a-8a69-7cdd2e45c9a7 -->
# Add Creator Tracking and System Rules to Rules and Rulesets

## Overview

Add creator tracking to PolicyRule and PolicyRuleset models, update creation views to save the creator user, generate system rules, and display creator information in the UI.

## Implementation Steps

### 1. Database Schema Changes

- **File**: `src/api/models.py`
- Add `created_by` ForeignKey to `PolicyRule` model (nullable, references User)
- Add `created_by` ForeignKey to `PolicyRuleset` model (nullable, references User)
- Add `is_system` boolean field to both models (default=False) to mark system-generated rules/rulesets

### 2. Database Migration

- Create migration to add new fields
- Migration should handle existing records (set `created_by` to first user if available, or null)
- Set `is_system=False` for all existing records

### 3. Update Views to Save Creator

- **File**: `src/frontend/views.py`
- Update `rule_create()`: Set `rule.created_by = request.user` before saving
- Update `ruleset_create()`: Set `ruleset.created_by = request.user` before saving
- Update `rule_update()`: Preserve existing `created_by` (don't overwrite)
- Update `ruleset_update()`: Preserve existing `created_by` (don't overwrite)

### 4. System Rules Generation

- **File**: `src/api/management/commands/create_system_rules.py` (new)
- Create management command to generate system rules
- Get or create a "system" user (username="system", special user for system-generated content)
- Create predefined system rules (e.g., basic security checks, hardening index thresholds)
- Mark rules with `is_system=True` and `created_by=system_user`
- Optionally create a default system ruleset containing system rules

### 5. Update Admin Interface

- **File**: `src/api/admin.py`
- Add `created_by` and `is_system` to `PolicyRuleAdmin.list_display`
- Add `created_by` and `is_system` to `PolicyRulesetAdmin.list_display`
- Add filters for `created_by` and `is_system`
- Add `created_by` to fieldsets

### 6. Update Templates to Display Creator (Read-Only)

- **Files**: 
- `src/frontend/templates/policy/policy_list.html`
- `src/frontend/templates/policy/rule_detail.html`
- `src/frontend/templates/policy/ruleset_detail.html`
- Add "Created by" column/field showing:
- User's username if `created_by` exists and is not system user
- "System" if `is_system=True` or `created_by` is the system user
- Display as read-only information (not editable)
- Show in rule/ruleset detail pages and list views

### 7. Update Forms

- **File**: `src/frontend/forms.py`
- Ensure forms don't expose `created_by` or `is_system` fields to users
- These should be set programmatically in views
- **Important**: `created_by` is read-only - users cannot change who created a rule/ruleset

### 8. Update Tests

- **File**: `src/api/tests.py` or `src/frontend/tests_e2e.py`
- Update existing tests to account for `created_by` field
- Add tests for system rules creation
- Add tests verifying creator is saved on rule/ruleset creation

### 9. Integration

- Update `docker-entrypoint.sh` to optionally run system rules creation command
- Or add to migration/post_migrate signal to auto-create system rules

## Design Decisions

1. **System User Representation**: Create a special User object (username="system") that cannot log in (is_active=False, no password set)
2. **System Rules Generation Timing**: Create system rules automatically via data migration
3. **System Rules Editability**: System rules are read-only - users cannot edit or delete rules/rulesets with `is_system=True`

## Additional Implementation Details

### System User Creation

- Create system user in migration with:
- `username="system"`
- `is_active=False` (prevents login)
- `is_staff=False`
- `is_superuser=False`
- No password set (or set to unusable password)

### System Rules Protection

- **File**: `src/frontend/views.py`
- Add checks in `rule_update()` and `ruleset_update()` to prevent editing system rules/rulesets
- Add checks in `rule_delete()` (if exists) to prevent deleting system rules
- Return error message if user attempts to edit/delete system content

### UI Updates for Read-Only System Rules

- **Files**: Templates and JavaScript
- Disable edit/delete buttons for system rules/rulesets in UI
- Show visual indicator (badge/icon) that rule/ruleset is system-generated
- Display "System" as creator name in all views