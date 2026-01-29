# Email Template for External Teams

## 📧 **Subject: Integration Required - Customer Events to Kafka**

---

**Hi [Team Name] Team,**

We're deploying a new Loyalty & Gamification system that needs to receive customer events from your system.

**What we need:** Your system to publish customer events to a Kafka topic when things happen (recharges, data usage, profile updates, etc.).

**Good news:** It's very simple! You just publish a JSON message. No complex integration needed.

---

## 📋 **What We'll Provide:**

1. **Kafka Server:** `kafka-broker.yourcompany.com:9092`
2. **Topic Name:** `customer-events`
3. **Event Format:** See attached document

---

## 💻 **What You Need to Do:**

1. Install Kafka client library (Python/Java/C# - your choice)
2. Setup producer (one-time code setup)
3. Publish events when things happen (add a few lines of code)

**Time estimate:** 1-2 days for your team

---

## 📝 **Example (Python):**

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['kafka-broker.yourcompany.com:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# When customer recharges:
producer.send('customer-events', {
    'source': 'in',
    'customer_id': customer_id,
    'event_type': 'recharge',
    'timestamp': '2024-01-15T10:30:00Z',
    'value': 50.0
})
producer.flush()
```

**That's it!** Just publish JSON when events happen.

---

## 📄 **Full Documentation:**

See attached: `EXTERNAL_TEAMS_INTEGRATION_GUIDE.md`

It includes:
- Complete event format
- Code examples (Python, Java, C#)
- Common questions
- Testing guide

---

## 🗓️ **Timeline:**

- **Week 1:** We provide Kafka details and documentation
- **Week 2:** Your team implements and tests
- **Week 3:** Production deployment

---

## ❓ **Questions?**

- **Email:** [your-email@company.com]
- **Slack:** #loyalty-integration
- **Meeting:** Let's schedule a 30-min call to discuss

---

**Thanks!** Looking forward to working with you.

[Your Name]  
Loyalty Team

---

**Attachments:**
- `EXTERNAL_TEAMS_INTEGRATION_GUIDE.md` - Complete integration guide

