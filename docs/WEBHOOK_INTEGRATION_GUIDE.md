# Webhook Integration Guide for Gamification

## ✅ **No Kafka Required!**

This system uses **HTTP webhooks** to receive customer events. **Kafka is optional** and only needed if you want to use it. The primary integration method is via HTTP POST requests.

---

## 📍 **Where to Configure**

### **Frontend UI:**
1. Navigate to: **Admin → Gamification Sources**
2. You'll see:
   - Webhook URL to send events to
   - List of configured data sources
   - Form to add/edit data sources

### **Backend API:**
- **Webhook Endpoint:** `POST /api/loyalty/v1/webhooks/customer-events/`
- **Data Sources API:** `/api/loyalty/v1/data-sources/`
- **Webhook Info:** `GET /api/loyalty/v1/webhooks/info/`

---

## 🔔 **How to Send Customer Events**

### **Option 1: Direct Webhook (Recommended)**

Send HTTP POST requests to the webhook endpoint:

```bash
POST /api/loyalty/v1/webhooks/customer-events/
Content-Type: application/json

{
  "source": "cdr",
  "source_name": "CDR System",  // Optional: name of configured data source
  "event": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "event_type": "data_usage",
    "timestamp": "2024-01-01T12:00:00Z",
    "value": 100.5,
    "metadata": {
      "data_mb": 100.5,
      "network_type": "4G"
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "event_id": "uuid-of-created-event",
  "customer_id": "123e4567-e89b-12d3-a456-426614174000",
  "event_type": "data_usage",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### **Option 2: Using Data Source Configuration**

1. **Configure Data Source in UI:**
   - Go to Admin → Gamification Sources
   - Click "Add Data Source"
   - Fill in:
     - Source Name: e.g., "CDR System"
     - Source Type: e.g., "CDR"
     - Event Mapping: Map your fields to normalized format
   - Save

2. **Send Events with Source Name:**
```json
{
  "source": "cdr",
  "source_name": "CDR System",  // Must match configured name
  "event": {
    "msisdn": "1234567890",  // Your field name
    "cdr_type": "data_usage",  // Your field name
    "event_time": "2024-01-01T12:00:00Z",  // Your field name
    "duration": 100.5
  }
}
```

The system will automatically map your fields using the configured mapping.

---

## 📋 **Supported Event Types**

- `data_usage` - Data usage events
- `recharge` - Recharge/payment events
- `app_login` - App login events
- `call_outgoing` - Outgoing call events
- `bundle_purchase` - Bundle purchase events
- `kyc_update` - KYC/profile update events
- `feature_usage` - Feature usage events
- `qoe_issue` - Quality of Experience issues
- `custom` - Custom events

---

## 🔧 **Event Mapping Configuration**

When configuring a data source, you can map your field names to the normalized format:

```json
{
  "customer_id_field": "msisdn",
  "event_type_field": "cdr_type",
  "timestamp_field": "event_time",
  "value_field": "duration"
}
```

This tells the system:
- Your `msisdn` field = `customer_id`
- Your `cdr_type` field = `event_type`
- Your `event_time` field = `timestamp`
- Your `duration` field = `value`

---

## ❓ **About Kafka**

### **Q: Do I need Kafka?**
**A: No!** Kafka is completely optional. The system works with HTTP webhooks.

### **Q: When would I use Kafka?**
**A:** Only if:
- You already have Kafka infrastructure
- You want high-throughput event streaming
- You need event replay capabilities

### **Q: How do I use Kafka if I want to?**
**A:** 
1. Install Kafka and `confluent-kafka` Python library
2. Configure Kafka connection in `DataSourceConfig`
3. Set up a Kafka consumer (separate service/script)
4. The consumer would call the webhook endpoint or use `EventNormalizerService` directly

**Note:** The current system doesn't include a Kafka consumer. You would need to build one that:
- Consumes from your Kafka topics
- Calls the webhook endpoint or uses `EventNormalizerService`
- Handles errors and retries

---

## 🚀 **Quick Start**

1. **Get Webhook URL:**
   ```bash
   GET /api/loyalty/v1/webhooks/info/
   ```

2. **Send a Test Event:**
   ```bash
   curl -X POST http://localhost:8001/api/loyalty/v1/webhooks/customer-events/ \
     -H "Content-Type: application/json" \
     -d '{
       "source": "custom",
       "event": {
         "customer_id": "test-customer-123",
         "event_type": "app_login",
         "timestamp": "2024-01-01T12:00:00Z"
       }
     }'
   ```

3. **Check Event Created:**
   ```bash
   GET /api/loyalty/v1/customer-events/?customer_id=test-customer-123
   ```

---

## 🔐 **Security (Future Enhancement)**

Currently, the webhook endpoint has no authentication. For production:

1. **Add API Key Authentication:**
   - Generate API keys for external systems
   - Validate in webhook middleware

2. **Add IP Whitelisting:**
   - Only allow requests from known IPs

3. **Add Rate Limiting:**
   - Prevent abuse

4. **Add Signature Verification:**
   - Verify request signatures (HMAC)

---

## 📝 **Summary**

✅ **Use HTTP webhooks** - No Kafka required  
✅ **Configure in Admin UI** - Admin → Gamification Sources  
✅ **Send POST requests** - Simple JSON format  
✅ **Automatic processing** - Events trigger behavior scoring and gamification  

**Kafka is optional** - Only use if you have existing Kafka infrastructure and want to build a consumer.

