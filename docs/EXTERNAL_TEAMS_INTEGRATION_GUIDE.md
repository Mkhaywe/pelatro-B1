# Integration Guide for External Systems

## 📧 **What to Send to External Teams**

Send this document to IN, CRM, DWH, Billing, and any other systems that need to send customer events.

---

## 🎯 **What We Need**

We need your system to publish customer events to a Kafka topic. When something happens to a customer (recharge, data usage, profile update, etc.), send us an event.

**That's it!** You just publish a JSON message. You don't need to:
- Wait for our response
- Handle retries
- Know if our system is up or down
- Integrate with our API

---

## 📋 **What We'll Give You**

1. **Kafka Server Address:** `kafka-broker.yourcompany.com:9092`
2. **Topic Name:** `customer-events`
3. **Event Format:** (see below)

---

## 📝 **Event Format**

When something happens to a customer, publish a JSON message like this:

```json
{
  "source": "in",
  "source_name": "IN System",
  "customer_id": "1234567890",
  "event_type": "data_usage",
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 500.5,
  "metadata": {
    "network_type": "4G",
    "location": "city_name"
  }
}
```

### **Field Descriptions:**

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `source` | **Yes** | System name: `in`, `crm`, `dwh`, `billing`, `app` | `"in"` |
| `source_name` | No | Human-readable name | `"IN System"` |
| `customer_id` | **Yes** | Customer ID (MSISDN or UUID) | `"1234567890"` |
| `event_type` | **Yes** | Type of event (see list below) | `"data_usage"` |
| `timestamp` | **Yes** | When it happened (ISO 8601 format) | `"2024-01-15T10:30:00Z"` |
| `value` | No | Numeric value (amount, MB, etc.) | `500.5` |
| `metadata` | No | Any additional info (JSON object) | `{"network": "4G"}` |

### **Event Types We Support:**

- `data_usage` - Customer used data
- `recharge` - Customer recharged/paid
- `app_login` - Customer logged into app
- `call_outgoing` - Customer made a call
- `bundle_purchase` - Customer bought a bundle
- `kyc_update` - Customer profile updated
- `feature_usage` - Customer used a feature
- `qoe_issue` - Quality of Experience issue
- `custom` - Any other event

---

## 💻 **Example Code**

### **Python Example:**

```python
from kafka import KafkaProducer
import json
from datetime import datetime

# Setup (do this once)
producer = KafkaProducer(
    bootstrap_servers=['kafka-broker.yourcompany.com:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# When event happens (call this whenever something happens)
def send_customer_event(customer_id, event_type, value=None, metadata=None):
    event = {
        'source': 'in',  # Change to your system name
        'source_name': 'IN System',
        'customer_id': customer_id,
        'event_type': event_type,
        'timestamp': datetime.now().isoformat() + 'Z',
        'value': value,
        'metadata': metadata or {}
    }
    
    producer.send('customer-events', event)
    producer.flush()  # Make sure it's sent

# Example: Customer used 500 MB of data
send_customer_event(
    customer_id='1234567890',
    event_type='data_usage',
    value=500.0,
    metadata={'network_type': '4G', 'location': 'city_name'}
)

# Example: Customer recharged $50
send_customer_event(
    customer_id='1234567890',
    event_type='recharge',
    value=50.0,
    metadata={'payment_method': 'credit_card'}
)
```

**Install library:**
```bash
pip install kafka-python
```

---

### **Java Example:**

```java
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.json.JSONObject;
import java.time.Instant;
import java.util.Properties;

// Setup (do this once)
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker.yourcompany.com:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

// When event happens (call this whenever something happens)
public void sendCustomerEvent(String customerId, String eventType, 
                              Double value, JSONObject metadata) {
    JSONObject event = new JSONObject();
    event.put("source", "in");  // Change to your system name
    event.put("source_name", "IN System");
    event.put("customer_id", customerId);
    event.put("event_type", eventType);
    event.put("timestamp", Instant.now().toString());
    if (value != null) event.put("value", value);
    if (metadata != null) event.put("metadata", metadata);
    else event.put("metadata", new JSONObject());
    
    producer.send(new ProducerRecord<>("customer-events", event.toString()));
    producer.flush();
}

// Example: Customer used 500 MB of data
JSONObject metadata = new JSONObject();
metadata.put("network_type", "4G");
metadata.put("location", "city_name");
sendCustomerEvent("1234567890", "data_usage", 500.0, metadata);

// Example: Customer recharged $50
JSONObject metadata2 = new JSONObject();
metadata2.put("payment_method", "credit_card");
sendCustomerEvent("1234567890", "recharge", 50.0, metadata2);
```

**Add dependency (Maven):**
```xml
<dependency>
    <groupId>org.apache.kafka</groupId>
    <artifactId>kafka-clients</artifactId>
    <version>3.5.0</version>
</dependency>
```

---

### **C# / .NET Example:**

```csharp
using Confluent.Kafka;
using Newtonsoft.Json;
using System;

// Setup (do this once)
var config = new ProducerConfig
{
    BootstrapServers = "kafka-broker.yourcompany.com:9092"
};

using var producer = new ProducerBuilder<string, string>(config).Build();

// When event happens (call this whenever something happens)
void SendCustomerEvent(string customerId, string eventType, 
                      double? value = null, Dictionary<string, object> metadata = null)
{
    var event = new
    {
        source = "in",  // Change to your system name
        source_name = "IN System",
        customer_id = customerId,
        event_type = eventType,
        timestamp = DateTime.UtcNow.ToString("o"),
        value = value,
        metadata = metadata ?? new Dictionary<string, object>()
    };
    
    var message = new Message<string, string>
    {
        Key = customerId,
        Value = JsonConvert.SerializeObject(event)
    };
    
    producer.Produce("customer-events", message);
    producer.Flush(TimeSpan.FromSeconds(10));
}

// Example: Customer used 500 MB of data
var metadata = new Dictionary<string, object>
{
    {"network_type", "4G"},
    {"location", "city_name"}
};
SendCustomerEvent("1234567890", "data_usage", 500.0, metadata);
```

**Install NuGet package:**
```
Install-Package Confluent.Kafka
```

---

## 🔧 **What You Need to Do**

1. **Install Kafka Client Library** (see examples above)

2. **Setup Producer** (one-time setup in your code)

3. **Publish Events** (whenever something happens):
   - Customer uses data → publish `data_usage` event
   - Customer recharges → publish `recharge` event
   - Customer logs into app → publish `app_login` event
   - Customer profile updates → publish `kyc_update` event
   - etc.

4. **That's it!** No need to:
   - Wait for our response
   - Handle errors (Kafka handles it)
   - Check if our system is up

---

## ❓ **Common Questions**

### **Q: What if your system is down?**
**A:** No problem! Kafka stores the events. When our system comes back up, we'll process them.

### **Q: What if I send a bad event?**
**A:** We'll log it and continue processing other events. You can fix it and resend.

### **Q: Do I need to wait for your response?**
**A:** No! Just publish and forget. Kafka handles delivery.

### **Q: How often should I send events?**
**A:** Send them as they happen (real-time). Or batch them if you prefer, but real-time is better.

### **Q: What if Kafka is down?**
**A:** Your producer will retry automatically. Just make sure your code handles the exception and retries.

### **Q: Can I send events in bulk?**
**A:** Yes! You can send multiple events. Just call `send()` multiple times, then `flush()` once.

---

## 📞 **Support**

If you have questions or need help:
- **Email:** [your-email@company.com]
- **Slack:** #loyalty-integration
- **Documentation:** [link to this doc]

---

## ✅ **Checklist for Your Team**

- [ ] Kafka client library installed
- [ ] Producer configured with bootstrap servers
- [ ] Code to publish events when things happen
- [ ] Tested with a few sample events
- [ ] Production deployment ready

---

## 🧪 **Testing**

Before going to production, test with a few events:

```python
# Test event
send_customer_event(
    customer_id='TEST-123',
    event_type='app_login',
    timestamp='2024-01-15T10:30:00Z'
)
```

Then let us know, and we'll verify we received it!

---

## 📋 **Summary**

**What we need:** Publish JSON events to Kafka topic `customer-events`

**When:** Whenever something happens to a customer

**Format:** See event format above

**That's it!** Simple, right? 😊

