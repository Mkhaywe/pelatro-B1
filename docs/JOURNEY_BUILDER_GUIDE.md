# Journey Builder Guide

## Overview

The Journey Builder is a visual tool for creating customer journeys - automated workflows that guide customers through personalized experiences based on their behavior and segment membership.

---

## How Journeys Work

### Journey Execution Flow

1. **Entry**: Customer enters journey based on:
   - Entry segment membership
   - Entry rules (JSONLogic)
   - Manual trigger

2. **State Machine**: Journey follows a state machine:
   - `NOT_STARTED` → `IN_PROGRESS` → `WAITING` → `COMPLETED` / `FAILED`

3. **Node Execution**: Each node type executes differently:
   - **Start**: Entry point
   - **Action**: Executes an action (email, SMS, points, campaign)
   - **Condition**: Evaluates JSONLogic rule, routes to different paths
   - **Wait**: Pauses execution (time-based or event-based)
   - **End**: Completes journey

4. **Context**: Execution context is passed between nodes:
   ```python
   {
     'customer_id': 'uuid',
     'journey_id': 'uuid',
     'action_result_<node_id>': {...},  # Results from previous actions
     # ... DWH features available for conditions
   }
   ```

---

## Action Types

### Available Action Types

#### 1. **Send Email** (`send_email`)

**Config:**
```json
{
  "action_type": "send_email",
  "subject": "Welcome to our Loyalty Program!",
  "template": "welcome_email",
  "variables": {
    "customer_name": "{{customer.first_name}}",
    "points_balance": "{{account.points_balance}}"
  }
}
```

**Execution:**
- Fetches customer email from DWH/Xiva
- Renders email template with variables
- Sends via email service (SendGrid, AWS SES, etc.)
- Logs email sent event

**Status**: ⚠️ **Partially Implemented** - Currently logs only. Requires email service integration.

---

#### 2. **Send SMS** (`send_sms`)

**Config:**
```json
{
  "action_type": "send_sms",
  "message": "You've earned {{points}} points!",
  "template": "points_notification",
  "variables": {
    "points": 100
  }
}
```

**Execution:**
- Fetches customer phone from DWH/Xiva
- Renders SMS template with variables
- Sends via SMS service (Twilio, AWS SNS, etc.)
- Logs SMS sent event

**Status**: ⚠️ **Partially Implemented** - Currently logs only. Requires SMS service integration.

---

#### 3. **Send Push Notification** (`send_push`)

**Config:**
```json
{
  "action_type": "send_push",
  "title": "New Offer Available!",
  "body": "Check out our latest promotion",
  "data": {
    "offer_id": "123",
    "deep_link": "/offers/123"
  }
}
```

**Execution:**
- Fetches customer device tokens from DWH
- Sends push via FCM/APNS
- Logs push sent event

**Status**: ⚠️ **Partially Implemented** - Currently logs only. Requires push notification service integration.

---

#### 4. **Award Points** (`award_points`)

**Config:**
```json
{
  "action_type": "award_points",
  "points": 100,
  "program_id": 1,  // Optional, uses default if not specified
  "reason": "Welcome bonus"
}
```

**Execution:**
- ✅ **Fully Implemented**
- Finds or creates loyalty account
- Awards points using `PointsService.earn_points()`
- Creates transaction record
- Returns new balance

**Code Location**: `loyalty/services/journey_actions.py` → `_award_points()`

---

#### 5. **Trigger Campaign** (`trigger_campaign`)

**Config:**
```json
{
  "action_type": "trigger_campaign",
  "campaign_id": 5,
  "channel": "email"  // Optional channel override
}
```

**Execution:**
- ✅ **Fully Implemented**
- Finds campaign by ID
- Delivers campaign to customer using `CampaignDeliveryService`
- Creates `CampaignExecution` record
- Returns execution details

**Code Location**: `loyalty/services/journey_actions.py` → `_trigger_campaign()`

---

## Where Action Code Lives

### Backend Action Execution

**Main Executor**: `loyalty/services/journey_actions.py`
- `JourneyActionExecutor` class
- `execute_action()` - Main entry point
- Individual methods: `_send_email()`, `_send_sms()`, `_send_push()`, `_award_points()`, `_trigger_campaign()`

**Journey Engine Integration**: `loyalty/engines/journey_engine.py`
- `JourneyStateMachine.execute_node()` calls `JourneyActionExecutor`
- Action results stored in execution context
- Available to subsequent nodes

### Frontend Action Configuration

**Journey Builder**: `frontend/src/views/Journeys/JourneyBuilder.vue`
- Action type dropdown in Properties panel
- Config stored in `node.data.actionType`
- Saved to `JourneyNode.config` as JSON

---

## Adding New Action Types

### Step 1: Add to Frontend

**File**: `frontend/src/views/Journeys/JourneyBuilder.vue`

```vue
<select v-model="selectedNode.data.actionType" @change="updateNode">
  <option value="send_email">Send Email</option>
  <option value="send_sms">Send SMS</option>
  <option value="send_push">Send Push Notification</option>
  <option value="award_points">Award Points</option>
  <option value="trigger_campaign">Trigger Campaign</option>
  <option value="your_new_action">Your New Action</option>  <!-- Add here -->
</select>
```

### Step 2: Implement Backend Handler

**File**: `loyalty/services/journey_actions.py`

```python
def execute_action(self, action_type: str, config: Dict, context: Dict) -> Dict:
    # ... existing code ...
    elif action_type == 'your_new_action':
        return self._your_new_action(config, context)
    # ...

def _your_new_action(self, config: Dict, context: Dict) -> Dict:
    """Your custom action implementation"""
    customer_id = context.get('customer_id')
    # Your logic here
    return {
        'success': True,
        'action': 'your_new_action',
        'customer_id': str(customer_id),
        # ... your result data
    }
```

### Step 3: Test

1. Create journey with new action type
2. Start journey for test customer
3. Check execution logs
4. Verify action result in context

---

## Visual Node Rendering

### Custom Node Components

**Location**: `frontend/src/components/JourneyNodes/`

- `StartNode.vue` - Green start node with rocket icon
- `ActionNode.vue` - Orange action node with lightning icon
- `ConditionNode.vue` - Blue condition node with branch icon
- `WaitNode.vue` - Gray wait node with clock icon
- `EndNode.vue` - Red end node with flag icon

### Node Styling

Each node component has:
- Custom background color
- Border styling
- Icon display
- Handle positions (top/bottom for connections)
- Responsive sizing

**Issue Fixed**: Previously nodes showed as plain text. Now they render as proper visual components with icons, colors, and handles.

---

## Journey Execution Examples

### Example 1: Welcome Journey

```
Start → Send Welcome Email → Wait 1 Day → Check Engagement → 
  [If Engaged] → Award Points → End
  [If Not Engaged] → Send Reminder SMS → End
```

**Backend Flow:**
1. Customer joins segment "New Customers"
2. Journey auto-starts (entry segment match)
3. Email sent (action node)
4. Wait 1 day (wait node)
5. Condition checks engagement (condition node)
6. Routes to appropriate path
7. Points awarded or SMS sent
8. Journey completes

### Example 2: Retention Journey

```
Start → Check Churn Risk → 
  [High Risk] → Send Retention Offer → Trigger Campaign → End
  [Low Risk] → Award Loyalty Points → End
```

**Backend Flow:**
1. Customer enters "At Risk" segment
2. Journey starts
3. Condition evaluates churn risk (uses ML prediction from context)
4. Routes based on risk level
5. Executes appropriate actions
6. Journey completes

---

## Journey Execution API

### Start Journey

```http
POST /api/loyalty/v1/journeys/{journey_id}/start/
Content-Type: application/json

{
  "customer_id": "uuid",
  "context": {
    "custom_data": "value"
  }
}
```

### Continue Journey (for wait nodes)

```http
POST /api/loyalty/v1/journeys/executions/{execution_id}/continue/
Content-Type: application/json

{
  "event_data": {
    "event_type": "customer.purchase",
    "amount": 100
  }
}
```

### Get Journey Analytics

```http
GET /api/loyalty/v1/journeys/{journey_id}/analytics/
```

---

## Troubleshooting

### Nodes Not Rendering Properly

**Issue**: Nodes show as text labels instead of visual components

**Solution**: 
- Ensure custom node components are imported in `JourneyBuilder.vue`
- Check `nodeTypeMap` uses component references, not strings
- Verify Vue Flow is properly initialized

### Actions Not Executing

**Issue**: Action nodes log but don't actually execute

**Solution**:
- Check `JourneyActionExecutor.execute_action()` is called
- Verify action type matches frontend dropdown
- Check action config is properly saved in `JourneyNode.config`
- Review execution logs for errors

### Condition Nodes Not Routing

**Issue**: Condition nodes don't route to different paths

**Solution**:
- Verify condition JSONLogic is valid
- Check context has required data (DWH features)
- Ensure edges have proper conditions set
- Test condition with `safe_json_logic()` directly

---

## Related Documentation

- **`API_REFERENCE.md`** - Journey API endpoints
- **`ML_GUIDE.md`** - Using ML predictions in journey conditions
- **`DWH_INTEGRATION.md`** - DWH features for journey context
- **`ARCHITECTURE.md`** - System architecture

---

---

## Summary

### What Was Fixed

1. ✅ **Visual Node Rendering**: Created custom Vue Flow node components (`StartNode.vue`, `ActionNode.vue`, etc.) so nodes display properly with icons and colors instead of plain text
2. ✅ **Action Execution**: Implemented actual execution code for all action types in `loyalty/services/journey_actions.py`
3. ✅ **Model Fields**: Added missing fields to `JourneyExecution` model (`state`, `current_node_id`, `context`) to support state machine

### Action Implementation Status

| Action Type | Status | Implementation |
|------------|--------|----------------|
| `send_email` | ⚠️ Partial | Logs only - needs email service integration |
| `send_sms` | ⚠️ Partial | Logs only - needs SMS service integration |
| `send_push` | ⚠️ Partial | Logs only - needs push service integration |
| `award_points` | ✅ Full | Fully implemented - awards points via `PointsService` |
| `trigger_campaign` | ✅ Full | Fully implemented - triggers campaign via `CampaignDeliveryService` |

### Next Steps for Full Implementation

1. **Email Service**: Integrate SendGrid/AWS SES in `_send_email()`
2. **SMS Service**: Integrate Twilio/AWS SNS in `_send_sms()`
3. **Push Service**: Integrate FCM/APNS in `_send_push()`
4. **Database Migration**: Run `python manage.py makemigrations` and `migrate` to add new fields

---

**Last Updated**: 2026-01-02

