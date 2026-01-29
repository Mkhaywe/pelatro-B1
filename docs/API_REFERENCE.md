# API Reference

## Base URLs

- **Internal API**: `http://localhost:8000/api/loyalty/v1/`
- **TMF API**: `http://localhost:8000/tmf-api/loyaltyManagement/v4/`
- **Dashboard API**: `http://localhost:8000/api/loyalty/v1/dashboard/`
- **Config API**: `http://localhost:8000/api/loyalty/v1/config/`

---

## Core Loyalty Endpoints

### Programs

```
GET    /api/loyalty/v1/loyaltyPrograms/          # List programs
POST   /api/loyalty/v1/loyaltyPrograms/          # Create program
GET    /api/loyalty/v1/loyaltyPrograms/{id}/     # Get program
PUT    /api/loyalty/v1/loyaltyPrograms/{id}/     # Update program
DELETE /api/loyalty/v1/loyaltyPrograms/{id}/     # Delete program
GET    /api/loyalty/v1/loyaltyPrograms/{id}/analytics/  # Program analytics
```

### Accounts

```
GET    /api/loyalty/v1/loyaltyAccounts/          # List accounts
POST   /api/loyalty/v1/loyaltyAccounts/          # Create account
GET    /api/loyalty/v1/loyaltyAccounts/{id}/     # Get account
PUT    /api/loyalty/v1/loyaltyAccounts/{id}/     # Update account
```

### Transactions

```
GET    /api/loyalty/v1/loyaltyTransactions/     # List transactions
POST   /api/loyalty/v1/loyaltyTransactions/     # Create transaction
GET    /api/loyalty/v1/loyaltyTransactions/{id}/ # Get transaction
```

---

## Campaign Management

### Campaigns

```
GET    /api/loyalty/v1/campaigns/                 # List campaigns
POST   /api/loyalty/v1/campaigns/                # Create campaign
GET    /api/loyalty/v1/campaigns/{id}/           # Get campaign
PUT    /api/loyalty/v1/campaigns/{id}/           # Update campaign
POST   /api/loyalty/v1/campaigns/{id}/activate/  # Activate campaign
POST   /api/loyalty/v1/campaigns/{id}/pause/    # Pause campaign
GET    /api/loyalty/v1/campaigns/{id}/performance/ # Campaign metrics
```

### Campaign Executions

```
GET    /api/loyalty/v1/campaignExecutions/       # List executions
GET    /api/loyalty/v1/campaignExecutions/{id}/   # Get execution
```

---

## Segmentation

### Segments

```
GET    /api/loyalty/v1/segments/                  # List segments
POST   /api/loyalty/v1/segments/                  # Create segment
GET    /api/loyalty/v1/segments/{id}/             # Get segment
PUT    /api/loyalty/v1/segments/{id}/             # Update segment
POST   /api/loyalty/v1/segments/{id}/recalculate/ # Recalculate members
GET    /api/loyalty/v1/segments/{id}/metrics/     # Segment analytics
```

### Segment Members

```
GET    /api/loyalty/v1/segmentMembers/           # List members
POST   /api/loyalty/v1/segmentMembers/           # Add member
DELETE /api/loyalty/v1/segmentMembers/{id}/      # Remove member
```

---

## ML & DWH

### ML Predictions

```
POST   /api/loyalty/v1/dwh/ml/nbo/               # Next Best Offer
POST   /api/loyalty/v1/dwh/ml/churn/             # Churn prediction
POST   /api/loyalty/v1/dwh/ml/rfm/               # RFM calculation
```

**Request:**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### DWH Integration

```
GET    /api/loyalty/v1/dwh/customers/{id}/features/  # Get customer features
POST   /api/loyalty/v1/dwh/batch/features/            # Batch get features
```

---

## Configuration

### System Configuration

```
GET    /api/loyalty/v1/config/get_all/            # Get all config
PUT    /api/loyalty/v1/config/update/             # Update config
GET    /api/loyalty/v1/config/xiva/test/          # Test Xiva connection
GET    /api/loyalty/v1/config/dwh/test/           # Test DWH connection
GET    /api/loyalty/v1/config/ml/status/          # ML system status
POST   /api/loyalty/v1/config/ml/test/           # Test ML prediction
```

---

## Dashboard

### Dashboard Stats

```
GET    /api/loyalty/v1/dashboard/stats/          # Dashboard statistics
```

**Response:**
```json
{
    "total_programs": 5,
    "total_campaigns": 12,
    "total_segments": 8,
    "total_customers": 1000,
    "active_campaigns": 3
}
```

---

## Authentication

All endpoints require authentication (except public endpoints).

**Header:**
```
Authorization: Bearer {token}
```

Or use session authentication (for browser).

---

## Response Format

### Success Response

```json
{
    "id": 1,
    "name": "Program Name",
    "description": "Description",
    ...
}
```

### Error Response

```json
{
    "error": "Error message",
    "detail": "Detailed error information"
}
```

---

## Pagination

List endpoints support pagination:

```
GET /api/loyalty/v1/campaigns/?page=1&page_size=20
```

**Response:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/loyalty/v1/campaigns/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## Filtering

Most list endpoints support filtering:

```
GET /api/loyalty/v1/campaigns/?status=active&program=1
```

---

## Next Steps

- See [USER_GUIDE.md](USER_GUIDE.md) for usage examples
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for workflow
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

