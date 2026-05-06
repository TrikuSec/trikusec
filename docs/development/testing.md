# Testing Guide

Complete guide to testing in TrikuSec.

## Test Structure

All tests use pytest (not Django's unittest):

- `src/api/tests.py` - Unit tests for API endpoints
- `src/api/tests_integration.py` - Integration tests
- `src/api/tests_middleware.py` - Middleware tests
- `src/api/tests_policy_security.py` - Policy security tests
- `src/frontend/tests_e2e.py` - End-to-end tests (Playwright)
- `src/conftest.py` - Shared pytest fixtures
- `src/frontend/conftest.py` - E2E test fixtures

## Running Tests

### All Tests

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test
```

### Unit Tests Only

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest -m "not integration and not e2e" -v
```

**Note:** E2E tests are automatically skipped if Playwright is not available. The `-m "not e2e"` marker explicitly excludes them for clarity.

### Integration Tests Only

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest -m integration -v
```

### Run Lynis Client Integration Flow Manually (Dev)

Use this when you want to validate the real enrollment/upload flow against your running dev stack.

1) Ensure services are running:

```bash
docker compose -f docker-compose.dev.yml up -d trikusec-manager trikusec-lynis-api
```

2) Create (or update) a license key in DB:

```bash
export TRIKUSEC_LICENSE_KEY=aaaaaaaa-bbbbbbbb-cccccccc

docker compose -f docker-compose.dev.yml exec trikusec-manager \
  python manage.py populate_db_licensekey "$TRIKUSEC_LICENSE_KEY" --name "Dev Integration License"
```

3) Run the Lynis client container once:

```bash
docker compose -f docker-compose.dev.yml run --rm \
  -e TRIKUSEC_LICENSE_KEY="$TRIKUSEC_LICENSE_KEY" \
  lynis-client
```

This should enroll/upload a device that appears in the **Devices** view.

### Seed Example Devices for Manual UI Testing

If you only need sample data quickly (without running full Lynis audit), post synthetic reports directly to the upload endpoint.

```bash
export TRIKUSEC_LICENSE_KEY=aaaaaaaa-bbbbbbbb-cccccccc

# Ensure the license exists
docker compose -f docker-compose.dev.yml exec trikusec-manager \
  python manage.py populate_db_licensekey "$TRIKUSEC_LICENSE_KEY" --name "Dev Seed License"

# Seed 12 demo devices
for i in $(seq 1 12); do
  REPORT=$(cat <<EOF
# Lynis Report
report_version_major=1
report_version_minor=0
hostname=demo-device-$i
os=Linux
os_fullname=Ubuntu 22.04 LTS
os_version=22.04
lynis_version=3.0.9
uptime_in_days=$((RANDOM % 120))
warning_count=$((RANDOM % 15))
vulnerable_packages_found=$((RANDOM % 8))
hardening_index=$((50 + RANDOM % 45))
report_datetime_end=2026-05-06 12:00:00
finish=true
EOF
)

  curl -sk -X POST "https://localhost:8001/api/lynis/upload/" \
    --data-urlencode "licensekey=${TRIKUSEC_LICENSE_KEY}" \
    --data-urlencode "hostid=demo-hostid-$i" \
    --data-urlencode "hostid2=demo-hostid2-$i" \
    --data-urlencode "data=${REPORT}" >/dev/null

  echo "Uploaded demo device $i"
done
```

This is the fastest way to populate the device list for manual feature validation.

### E2E Tests Only

E2E tests require Playwright and must be run in the `test-e2e` service:

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test-e2e pytest -m e2e -v
```

See [E2E Testing Documentation](e2e-testing.md) for detailed information.

### Specific Test File

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest api/tests.py -v
```

### Specific Test

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest api/tests.py::TestUploadReport::test_upload_report_valid_license_new_device -v
```

### With Coverage

```bash
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest --cov=api --cov=frontend --cov-report=html --cov-report=term-missing
```

## Test Types

### Unit Tests

Test individual components in isolation:

- API endpoints
- Models
- Forms
- Utilities

### Integration Tests

Test end-to-end workflows:

- Lynis report upload
- License validation
- Policy compliance

### Middleware Tests

Test custom middleware:

- Rate limiting
- Security headers
- Error handling

### E2E Tests

Test complete user workflows in a real browser:

- Frontend interactions
- Form submissions
- Sidebar state management
- User flows

See [E2E Testing Documentation](e2e-testing.md) for details.

## Test Fixtures

Fixtures are defined in `src/conftest.py`:

- `license_key` - Sample license key
- `device` - Sample device
- `lynis_report` - Mock Lynis report data

## Writing Tests

### Example Unit Test

```python
import pytest
from api.views import upload_report

def test_upload_report_valid_license(client, license_key):
    response = client.post('/api/lynis/upload/', {
        'licensekey': license_key.licensekey,
        'hostid': 'test-host',
        'data': 'base64-encoded-data'
    })
    assert response.status_code == 200
```

### Example Integration Test

```python
@pytest.mark.integration
def test_lynis_workflow(client, license_key):
    # Upload report
    response = client.post('/api/lynis/upload/', {...})
    assert response.status_code == 200
    
    # Check device created
    device = Device.objects.get(hostid='test-host')
    assert device is not None
```

## Test Database

The test container automatically:
- Runs migrations before tests
- Uses a separate test database
- Cleans up after tests

## Continuous Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests

CI runs three separate test jobs:
1. **Unit Tests** - Fast unit tests (excludes integration and E2E tests)
2. **Integration Tests** - End-to-end API workflows with Lynis client
3. **E2E Tests** - Browser-based frontend tests with Playwright

See `.github/workflows/test.yml` for CI configuration.

## Best Practices

- **Isolation** - Each test should be independent
- **Fixtures** - Use fixtures for common test data
- **Naming** - Use descriptive test names
- **Coverage** - Aim for high test coverage
- **Speed** - Keep tests fast

## Next Steps

- [Development Setup](setup.md) - Development environment
- [Contributing](contributing.md) - Contribution guidelines

