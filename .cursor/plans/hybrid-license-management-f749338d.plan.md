<!-- f749338d-c15e-4678-b56d-c5fbfbbda1a4 4874d641-e779-48e0-9e44-54cda89783c0 -->
# Hybrid License Key Management System

## Overview

Implement flexible license key management supporting both shared license keys (with device limits) and unique per-device keys. Add Organization model structure for future multi-tenancy while maintaining single-tenant behavior.

## 1. Database Models & Migrations

### Add Organization Model

**File:** `src/api/models.py`

Add basic Organization model (single-tenant for now):

```python
class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
```

### Extend LicenseKey Model

**File:** `src/api/models.py`

Add new fields to LicenseKey:

```python
class LicenseKey(models.Model):
    licensekey = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)  # e.g., "Production servers" or "web-01"
    organization = models.ForeignKey(Organization, on_delete=CASCADE, null=True)
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    max_devices = models.IntegerField(null=True, blank=True)  # null=unlimited
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def device_count(self):
        return self.device_set.count()
    
    def has_capacity(self):
        if not self.is_active:
            return False
        if self.max_devices is None:
            return True
        return self.device_count() < self.max_devices
```

### Create Migration

**File:** `src/api/migrations/0010_add_organization_and_license_fields.py`

- Add Organization model
- Add fields to LicenseKey (name, organization, max_devices, expires_at, is_active)
- Add unique constraint on licensekey field
- Data migration: set `max_devices=null` for existing licenses (unlimited)
- Create default organization and link existing licenses to it

## 2. Backend Utilities

### License Generation Utility

**File:** `src/api/utils/license_utils.py` (new file)

Create utility functions:

```python
def generate_license_key():
    """Generate unique license key in format: xxxxxxxx-xxxxxxxx-xxxxxxxx"""
    
def validate_license(licensekey):
    """Check if license is valid, active, not expired"""
    
def check_license_capacity(licensekey):
    """Check if license can accept more devices"""
```

### Update Device Enrollment Logic

**File:** `src/api/views.py`

Update `upload_report()` function to validate license capacity before enrolling new devices:

- Check license exists and is active
- Check license not expired
- Check license has capacity (if new device)
- Return appropriate error if validation fails

## 3. Frontend Forms

### Create LicenseKeyForm

**File:** `src/frontend/forms.py`

Add form for license creation/editing:

```python
class LicenseKeyForm(forms.ModelForm):
    class Meta:
        model = LicenseKey
        fields = ['name', 'max_devices', 'expires_at', 'is_active']
```

## 4. Frontend Views & URLs

### License Management Views

**File:** `src/frontend/views.py`

Add views:

- `license_list(request)` - List all licenses
- `license_detail(request, license_id)` - Show license details and devices
- `license_create(request)` - Create new license
- `license_edit(request, license_id)` - Edit existing license
- `license_delete(request, license_id)` - Delete/deactivate license
- `enroll_device(request)` - New enrollment flow with license selection

### Update URLs

**File:** `src/frontend/urls.py`

Add URL patterns:

```python
path('licenses/', views.license_list, name='license_list'),
path('licenses/create/', views.license_create, name='license_create'),
path('license/<int:license_id>/', views.license_detail, name='license_detail'),
path('license/<int:license_id>/edit/', views.license_edit, name='license_edit'),
path('license/<int:license_id>/delete/', views.license_delete, name='license_delete'),
path('enroll/', views.enroll_device, name='enroll_device'),
```

## 5. Frontend Templates

### License List Template

**File:** `src/frontend/templates/license/license_list.html` (new)

Table showing:

- Name
- License Key (masked, click to reveal/copy)
- Devices (X/max_devices or X/unlimited)
- Expires
- Status (Active/Inactive/Expired)
- Actions (View, Edit, Delete, Enroll Device)

### License Detail Template

**File:** `src/frontend/templates/license/license_detail.html` (new)

Show:

- License information (name, key with copy button, capacity, expiration)
- Devices table using this license
- Actions: Edit License, Enroll Device, Deactivate

### License Form Template

**File:** `src/frontend/templates/license/license_form.html` (new)

Form for creating/editing license with fields: name, max_devices, expires_at, is_active

### Enroll Device Template

**File:** `src/frontend/templates/license/enroll_device.html` (new)

Two-step flow:

1. Create new unique license (default) or select existing license with capacity
2. Show enrollment script and instructions

### Update Base Template

**File:** `src/frontend/templates/base.html`

Update profile dropdown menu (line 94):

- Change `<a href="#"` to `<a href="{% url 'license_list' %}"` for "License keys"
- Make "Sign out" functional with `{% url 'logout' %}`

### Update Onboarding Template

**File:** `src/frontend/templates/onboarding.html`

- Add "Enroll Device" button that redirects to new enroll_device view
- Show license capacity info if using shared license

## 6. Admin Interface

### Update Admin

**File:** `src/api/admin.py`

- Register Organization model
- Update LicenseKeyAdmin to show new fields (name, devices, expires_at, is_active)
- Add filters for is_active, expires_at

## 7. Management Commands

### Update populate_db_licensekey

**File:** `src/api/management/commands/populate_db_licensekey.py`

Update to support new license fields:

- Add `--name` argument
- Add `--max-devices` argument
- Create default organization if needed
- Link license to organization

## 8. Testing

### Unit Tests

**File:** `src/api/tests.py`

Add tests:

- Test license validation (active, expired, capacity)
- Test device enrollment with capacity limits
- Test license generation uniqueness
- Test has_capacity() method

### Integration Tests

**File:** `src/api/tests_integration.py`

Add tests:

- Test full enrollment flow with new license creation
- Test enrollment rejection when license at capacity
- Test enrollment rejection with expired license

## 9. Documentation

### Update README

**File:** `README.md`

Add section on license management:

- How to create licenses
- How to set device limits
- How to enroll devices with specific licenses

### Update AGENTS.md

**File:** `AGENTS.md`

Document new license model structure and important constraints:

- Organization model (future multi-tenancy)
- License capacity checks
- Critical: Lynis API still uses `licensekey` field (no separate token)

### To-dos

- [x] Add Organization model and extend LicenseKey model with new fields, create and run migration
- [x] Create license utility functions and update device enrollment validation logic
- [x] Create LicenseKeyForm for license management
- [x] Implement license management views (list, detail, create, edit, delete, enroll)
- [x] Create license management templates and update base/onboarding templates
- [x] Add URL patterns for license management endpoints
- [x] Update Django admin to support Organization and extended LicenseKey model
- [x] Update populate_db_licensekey command to support new license fields
- [x] Write unit and integration tests for license validation and enrollment
- [x] Update README.md and AGENTS.md with license management documentation