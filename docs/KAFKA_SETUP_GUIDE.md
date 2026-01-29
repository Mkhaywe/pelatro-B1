# Kafka Setup Guide for Gamification

## 🎯 **Quick Answer: It's NOT a Big Project!**

**Complexity: MEDIUM (2-3 weeks)**
- **Producers (External Systems):** EASY - Just publish JSON
- **Consumer (Your System):** MEDIUM - Build consumer service
- **Coordination:** MEDIUM - Work with external teams

---

## 📋 **Step-by-Step Implementation**

### **Step 1: Setup Kafka (1-2 days)**

#### **Option A: Docker (Development/Testing)**
```yaml
# docker-compose.yml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
  
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

```bash
docker-compose up -d
```

#### **Option B: Managed Service (Production)**
- **AWS MSK:** Managed Kafka on AWS
- **Confluent Cloud:** Fully managed Kafka
- **Azure Event Hubs:** Kafka-compatible

**Recommended:** Start with Docker for development, move to managed for production.

---

### **Step 2: Create Topics (1 hour)**

```bash
# Create topic for customer events
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic customer-events \
  --partitions 3 \
  --replication-factor 1

# Or use Python:
from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(
    bootstrap_servers=['localhost:9092']
)

topic = NewTopic(
    name='customer-events',
    num_partitions=3,
    replication_factor=1
)

admin_client.create_topics([topic])
```

**Topics to Create:**
- `customer-events` - All customer events (main topic)
- `cdr-events` - Call Detail Records (optional, separate topic)
- `billing-events` - Billing events (optional)
- `crm-events` - CRM updates (optional)

---

### **Step 3: Configure Settings (30 minutes)**

Add to `loyalty_project/settings.py`:

```python
# Kafka Configuration
KAFKA_ENABLED = os.environ.get('KAFKA_ENABLED', 'False').lower() == 'true'
KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    'KAFKA_BOOTSTRAP_SERVERS',
    'localhost:9092'
).split(',')
KAFKA_CUSTOMER_EVENTS_TOPICS = ['customer-events']
KAFKA_CONSUMER_GROUP = 'loyalty-gamification-consumer'

# Install kafka-python:
# pip install kafka-python
```

---

### **Step 4: Build Consumer (3-5 days)**

**Already Created:** `loyalty/integration/kafka_consumer_service.py`

**Run Consumer:**
```bash
# As Django management command:
python manage.py run_kafka_consumer

# Or as a service:
python -m loyalty.integration.kafka_consumer_service
```

**Deploy as Service:**
- Systemd service (Linux)
- Windows Service
- Docker container
- Kubernetes deployment

---

### **Step 5: Tell External Systems (1-2 days per system)**

**Share with External Teams:**

#### **Documentation:**
```
Kafka Topic: customer-events
Bootstrap Servers: kafka-broker:9092
Event Format:
{
  "source": "in|crm|dwh|billing",
  "source_name": "IN System",  // Optional
  "customer_id": "uuid-or-msisdn",
  "event_type": "data_usage|recharge|app_login|...",
  "timestamp": "2024-01-01T12:00:00Z",
  "value": 100.5,  // Optional
  "metadata": {}   // Optional
}
```

#### **Example Code (Python):**
```python
from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers=['kafka-broker:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# When event happens:
producer.send('customer-events', {
    'source': 'in',
    'source_name': 'IN System',
    'customer_id': customer_id,
    'event_type': 'data_usage',
    'timestamp': datetime.now().isoformat(),
    'value': data_mb,
    'metadata': {
        'network_type': '4G',
        'location': 'city'
    }
})

producer.flush()  # Ensure message is sent
```

#### **Example Code (Java):**
```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

// When event happens:
JSONObject event = new JSONObject();
event.put("source", "in");
event.put("customer_id", customerId);
event.put("event_type", "data_usage");
event.put("timestamp", Instant.now().toString());
event.put("value", dataMb);

producer.send(new ProducerRecord<>("customer-events", event.toString()));
producer.flush();
```

**Complexity for External Teams: LOW** - They just publish JSON!

---

## 🔄 **Event Flow Example**

### **IN System Publishes Event:**
```python
# IN System code (their responsibility)
producer.send('customer-events', {
    'source': 'in',
    'customer_id': '1234567890',
    'event_type': 'data_usage',
    'timestamp': '2024-01-01T12:00:00Z',
    'value': 500.0,  # MB
    'metadata': {'network': '4G'}
})
```

### **Your Consumer Receives:**
```python
# Your consumer (loyalty/integration/kafka_consumer_service.py)
# Automatically:
# 1. Normalizes event
# 2. Updates behavior scores
# 3. Checks mission progress
# 4. Awards badges
# 5. Updates leaderboards
```

---

## 📊 **Complexity Breakdown**

| Task | Complexity | Time | Who |
|------|-----------|------|-----|
| **Kafka Setup** | LOW-MEDIUM | 1-2 days | DevOps/You |
| **Topic Creation** | LOW | 1 hour | You |
| **Consumer Development** | MEDIUM | 3-5 days | You |
| **Error Handling** | MEDIUM | 2-3 days | You |
| **Testing** | LOW | 1-2 days | You |
| **External Coordination** | MEDIUM | 1-2 days/system | You + External Teams |
| **Documentation** | LOW | 1 day | You |
| **Total** | **MEDIUM** | **2-3 weeks** | - |

---

## 🎯 **Key Points**

### **1. Producers Are EASY ✅**
- External systems just publish JSON
- No complex integration needed
- They don't need to know about your system
- They don't need to handle retries
- They don't need to wait for your response

### **2. Consumer is MEDIUM ✅**
- You build it once
- Logic already exists (EventNormalizerService, BehaviorScoringService)
- Just wrap in Kafka consumer
- Handle errors and scaling

### **3. Coordination is the Main Challenge**
- Getting external teams to publish
- Standardizing event format
- Testing integration
- Monitoring

### **4. It's NOT a Big Project**
- Standard telecom architecture
- Well-documented approach
- Existing libraries and tools
- 2-3 weeks for full implementation

---

## 🚀 **Quick Start**

1. **Setup Kafka:**
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. **Install Python Library:**
   ```bash
   pip install kafka-python
   ```

3. **Create Topic:**
   ```bash
   kafka-topics --create --bootstrap-server localhost:9092 --topic customer-events
   ```

4. **Start Consumer:**
   ```bash
   python manage.py run_kafka_consumer
   ```

5. **Test with Producer:**
   ```python
   from kafka import KafkaProducer
   import json
   
   producer = KafkaProducer(
       bootstrap_servers=['localhost:9092'],
       value_serializer=lambda v: json.dumps(v).encode('utf-8')
   )
   
   producer.send('customer-events', {
       'source': 'test',
       'customer_id': 'test-123',
       'event_type': 'app_login',
       'timestamp': '2024-01-01T12:00:00Z'
   })
   producer.flush()
   ```

6. **Verify:**
   - Check logs for processed events
   - Check database for CustomerEvent records
   - Check behavior scores updated

---

## ✅ **Summary**

**Kafka IS the right approach for production!**

- **Producers:** EASY - External systems just publish JSON
- **Consumer:** MEDIUM - 3-5 days to build
- **Overall:** 2-3 weeks for full implementation
- **Complexity:** MEDIUM, not a big project
- **Recommendation:** Use Kafka for production, webhooks for testing

**The consumer code is already created!** Just:
1. Setup Kafka
2. Configure settings
3. Run consumer
4. Tell external systems to publish

That's it! 🎉

