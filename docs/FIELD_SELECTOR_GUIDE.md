# Field Selector Guide for Journey Conditions

## Overview

The **Field Selector** is a user-friendly component that helps users build JSONLogic conditions by showing all available customer fields from the DWH. Instead of manually typing field names, users can browse and select fields with descriptions.

---

## How It Works

### Location

The Field Selector appears in the **Journey Builder** when editing a **Condition** node:
- Select a Condition node
- The Properties panel shows "Condition Rule (JSONLogic)"
- The Field Selector appears on the right side of the condition textarea

### Features

1. **Categorized Fields**: Fields are organized by category:
   - **Financial**: `total_revenue`, `lifetime_value`, `avg_transaction_value`, `points_balance`
   - **Transaction**: `transaction_count`, `last_purchase_days_ago`, `avg_transaction_value`
   - **Loyalty**: `customer_tier`, `points_balance`, `segment`
   - **Profile**: `customer_status`, `email_verified`, `phone_verified`
   - **Demographic**: `city`, `region`, `country`, `age`, `gender`
   - **Engagement**: `last_login_days_ago`, `campaign_engagement_rate`, `preferred_channel`
   - **ML**: `churn_score`, `rfm_segment`
   - **Segmentation**: `segment`
   - **Service**: `active_products_count`, `has_data_service`
   - **DWH Columns**: Dynamically loaded from your DWH

2. **Search**: Type in the search box to filter fields by name or description

3. **Expandable Categories**: Click category headers to expand/collapse

4. **Field Information**: Each field shows:
   - **Name**: Formatted field name (e.g., "Total Revenue" for `total_revenue`)
   - **Type**: `number`, `string`, `boolean`, `date`, etc.
   - **Description**: What the field represents

5. **One-Click Insert**: Click any field to insert `{"var": "field_name"}` at cursor position

---

## Usage

### Step 1: Select a Condition Node

1. Click on a **Condition** node in your journey
2. The Properties panel opens on the left

### Step 2: Use Field Selector

1. **Browse fields**: Expand categories to see available fields
2. **Search**: Type in the search box to find specific fields
3. **Insert field**: Click a field to insert it into the condition textarea

### Step 3: Build Your Condition

The Field Selector inserts field references like:
```json
{"var": "total_revenue"}
```

You can then build complete conditions:
```json
{
  ">": [
    {"var": "total_revenue"},
    1000
  ]
}
```

Or combine multiple conditions:
```json
{
  "and": [
    {">": [{"var": "total_revenue"}, 1000]},
    {"==": [{"var": "customer_status"}, "active"]}
  ]
}
```

---

## Examples

### Example 1: High-Value Active Customers

```json
{
  "and": [
    {">": [{"var": "total_revenue"}, 1000]},
    {"==": [{"var": "customer_status"}, "active"]}
  ]
}
```

**Steps:**
1. Click "total_revenue" field → inserts `{"var": "total_revenue"}`
2. Type `{">": [{"var": "total_revenue"}, 1000]}`
3. Click "customer_status" field → inserts `{"var": "customer_status"}`
4. Complete: `{"and": [{">": [{"var": "total_revenue"}, 1000]}, {"==": [{"var": "customer_status"}, "active"]}]}`

### Example 2: Recent Purchasers

```json
{
  "<": [
    {"var": "last_purchase_days_ago"},
    30
  ]
}
```

**Steps:**
1. Click "last_purchase_days_ago" field
2. Type `{"<": [{"var": "last_purchase_days_ago"}, 30]}`

### Example 3: Churn Risk Customers

```json
{
  ">": [
    {"var": "churn_score"},
    0.7
  ]
}
```

**Steps:**
1. Click "churn_score" field
2. Type `{">": [{"var": "churn_score"}, 0.7]}`

---

## Field Categories Explained

### Financial Fields
- `total_revenue` - Total customer revenue
- `lifetime_value` - Customer lifetime value
- `avg_transaction_value` - Average transaction value
- `points_balance` - Current loyalty points balance

### Transaction Fields
- `transaction_count` - Number of transactions
- `last_purchase_days_ago` - Days since last purchase
- `avg_transaction_value` - Average transaction value

### Profile Fields
- `customer_status` - Customer status (active, inactive, etc.)
- `email_verified` - Email verification status (boolean)
- `phone_verified` - Phone verification status (boolean)

### ML Fields
- `churn_score` - Churn risk score (0-1)
- `rfm_segment` - RFM segment name (e.g., "555", "432")

### DWH Columns
- Dynamically loaded from your DWH `customer_features_view`
- Any column in your DWH can be used in conditions
- Fetched from `/api/loyalty/v1/dwh/columns/`

---

## JSONLogic Operators

### Comparison Operators
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `==` - Equals
- `!=` - Not equals

### Logical Operators
- `and` - All conditions must be true
- `or` - Any condition can be true
- `!` - Not (negation)

### Other Operators
- `in` - Check if value is in a list
- `{"var": "field_name"}` - Reference a field

---

## Tips

1. **Use Field Selector**: Don't type field names manually - use the selector to avoid typos
2. **Check Field Types**: The type indicator helps you know what operators to use
3. **Read Descriptions**: Field descriptions explain what each field represents
4. **Test Your Conditions**: Use the "Test Rule" button in Visual Rule Builder to verify
5. **Format JSON**: The textarea auto-formats JSON for readability

---

## Troubleshooting

### Field Selector Not Loading

**Issue**: Field Selector shows "Loading..." or error

**Solution**:
- Check DWH connection in Admin → Data Sources
- Verify `/api/loyalty/v1/dwh/columns/` endpoint is accessible
- Check browser console for errors

### Field Not Found

**Issue**: Field exists in DWH but not in selector

**Solution**:
- Field must be in `customer_features_view` table
- Run DWH setup script to populate features
- Check DWH column discovery in Admin

### Condition Not Working

**Issue**: Condition doesn't match customers

**Solution**:
- Verify field name matches DWH column name exactly
- Check field type matches operator (e.g., use `==` for strings, `>` for numbers)
- Test condition with sample data
- Check backend logs for JSONLogic evaluation errors

---

## API Reference

### Get Available Fields

```http
GET /api/loyalty/v1/dwh/columns/
```

**Response:**
```json
[
  {
    "name": "total_revenue",
    "type": "number",
    "description": "Total customer revenue",
    "category": "financial",
    "data_source": "dwh"
  },
  ...
]
```

---

**Last Updated**: 2026-01-02

