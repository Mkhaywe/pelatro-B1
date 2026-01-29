# Quick Reference - Customer Events Integration

## 🚀 **TL;DR (Too Long; Didn't Read)**

**What:** Publish JSON events to Kafka  
**Where:** Topic `customer-events`  
**When:** Whenever something happens to a customer  
**How:** See code examples below  

---

## 📝 **Event Format (Copy-Paste Ready)**

```json
{
  "source": "in",
  "customer_id": "1234567890",
  "event_type": "data_usage",
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 500.5,
  "metadata": {}
}
```

---

## 💻 **Python (5 Lines of Code)**

```python
from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers=['kafka-broker.yourcompany.com:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send event:
producer.send('customer-events', {
    'source': 'in',
    'customer_id': customer_id,
    'event_type': 'recharge',
    'timestamp': datetime.now().isoformat() + 'Z',
    'value': amount
})
producer.flush()
```

**Install:** `pip install kafka-python`

---

## ☕ **Java (10 Lines of Code)**

```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker.yourcompany.com:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

JSONObject event = new JSONObject();
event.put("source", "in");
event.put("customer_id", customerId);
event.put("event_type", "recharge");
event.put("timestamp", Instant.now().toString());
event.put("value", amount);

producer.send(new ProducerRecord<>("customer-events", event.toString()));
producer.flush();
```

**Maven:** Add `kafka-clients` dependency

---

## 🔧 **Event Types**

| Event Type | When to Send | Example |
|------------|--------------|---------|
| `data_usage` | Customer uses data | Data consumed: 500 MB |
| `recharge` | Customer pays/recharges | Recharge: $50 |
| `app_login` | Customer logs into app | User logged in |
| `call_outgoing` | Customer makes call | Call made: 5 min |
| `bundle_purchase` | Customer buys bundle | Bundle purchased |
| `kyc_update` | Profile updated | Profile changed |
| `custom` | Anything else | Custom event |

---

## ✅ **Checklist**

- [ ] Kafka client installed
- [ ] Producer configured
- [ ] Code added to send events
- [ ] Tested with sample event
- [ ] Production ready

---

## 📞 **Need Help?**

Email: [your-email]  
Slack: #loyalty-integration

---

**That's it!** Just publish JSON when events happen. Simple! 😊

