# API Endpoints

Complete reference for all API endpoints.

## Lynis Endpoints

### Upload Report

Upload a Lynis audit report.

**Endpoint:** `POST /api/lynis/upload/`

**Legacy:** `POST /api/v1/lynis/upload/`

**Request Format:** Form data

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `licensekey` | string | Yes | License key for authentication |
| `hostid` | string | Yes | Host identifier |
| `hostid2` | string | No | Secondary host identifier |
| `data` | string | Yes | Base64-encoded Lynis report data |

**Response:**

- `200 OK` - Report uploaded successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Invalid license key

**Example:**

```bash
curl -X POST https://yourserver:8001/api/lynis/upload/ \
  -F "licensekey=your-license-key" \
  -F "hostid=server-01" \
  -F "data=$(base64 -w 0 /var/log/lynis-report.dat)"
```

### Check License

Validate a license key.

**Endpoint:** `POST /api/lynis/license/`

**Legacy:** `POST /api/v1/lynis/license/`

**Request Format:** Form data

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `licensekey` | string | Yes | License key to validate |
| `collector_version` | string | No | Lynis collector version |

**Response:**

- `200 OK` - Valid license (Response: `Response 100`)
- `401 Unauthorized` - Invalid license (Response: `Response 500`)

**Example:**

```bash
curl -X POST https://yourserver:8001/api/lynis/license/ \
  -F "licensekey=your-license-key" \
  -F "collector_version=3.0.0"
```

!!! important "Lynis Compatibility"
    These endpoints maintain compatibility with Lynis clients. The response format (`Response 100` / `Response 500`) is required for Lynis compatibility.

## Next Steps

- [Authentication](authentication.md) - Learn about authentication

