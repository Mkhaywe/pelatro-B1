# Customer Prediction Data Analysis

## Customer: a0d35428-691f-4375-9118-d2bdf6811426

### **Prediction Result**
- **Churn Probability:** 0.00%
- **Risk Level:** LOW
- **Model Input Vector:** `[207.58, 31.0, 22.0, 56.99, 2603.22, 0.0, 0.0, 0.0, 0.0, 0.0]`

---

## **Raw Customer Data**

### **From DWH:**
- Account Age: 645 days
- Active Products: 3
- Average Transaction Value: $56.99
- Churn Score (DWH): 0.3954 (39.54% - this is from DWH, not our model)
- Credit Utilization: 42.59%
- Customer Status: active
- Data Usage: 10,794.92 MB
- Days Since Last Transaction: 22
- Lifetime Value: $2,603.22
- Total Revenue: $1,766.61
- Transaction Count: 31

### **From Feature Store (Enhanced):**
- Outstanding Amount: **$0.00** ✓
- Payment Ratio: **315.5%** ✓ (excellent - paying more than required)
- Current Month Spend: **$894.84**
- Monthly Average Spend: **$17.30** (calculated from total_revenue $207.58 / 12)
- Days Since Last Transaction: **22 days**
- Active Services: **3/3** ✓ (all active)
- Usage Records: **0** ⚠ (no usage records found)

---

## **Prediction Analysis**

### **Why 0% Churn Probability?**

The model predicts 0% churn based on:

1. **Strong Payment Indicators:**
   - No outstanding balance ($0.00)
   - Excellent payment ratio (315.5% - paying 3x more than required)
   - Last payment: $600.00

2. **Service Status:**
   - All 3 services are active
   - Customer status: "active"

3. **Revenue Pattern:**
   - Lifetime value: $2,603.22
   - 31 transactions (good transaction frequency)
   - Average transaction: $56.99

### **Potential Concerns (Not Reflected in 0% Prediction):**

1. **No Usage Records:** 
   - `usage_records_count: 0`
   - `current_month_usage_spend: $0.00`
   - This could indicate inactivity, but model doesn't weight it heavily

2. **Spending Spike:**
   - Current month: $894.84
   - Monthly average: $17.30
   - **51x increase** - likely a one-time purchase
   - Model may interpret this as positive (high spending)

3. **Recency:**
   - Last transaction: 22 days ago
   - Not "within last week" as explanation suggests
   - This is a **bug in the explanation logic** (being fixed)

4. **Data Discrepancy:**
   - DWH shows `total_revenue: $1,766.61`
   - Feature Store shows `total_revenue: $207.58`
   - This suggests data sync issues or different calculation methods

---

## **Model Input Vector Breakdown**

The model receives 10 features:
1. `207.58` - total_revenue
2. `31.0` - transaction_count
3. `22.0` - days_since_last_transaction
4. `56.99` - avg_transaction_value
5. `2603.22` - lifetime_value
6. `0.0` - (padded/truncated feature)
7. `0.0` - (padded/truncated feature)
8. `0.0` - (padded/truncated feature)
9. `0.0` - (padded/truncated feature)
10. `0.0` - (padded/truncated feature)

**Note:** The model is only using 5 real features, the rest are zeros (padding).

---

## **Prediction Accuracy Assessment**

### **Is 0% Churn Realistic?**

**Arguments FOR 0% prediction:**
- ✓ No outstanding balance
- ✓ Excellent payment history (315% payment ratio)
- ✓ All services active
- ✓ Good transaction history (31 transactions)
- ✓ High lifetime value ($2,603)

**Arguments AGAINST 0% prediction:**
- ⚠ No usage records (0 usage records)
- ⚠ 22 days since last transaction (not recent)
- ⚠ Data inconsistency (DWH vs Feature Store revenue mismatch)
- ⚠ Model may be too optimistic (placeholder model trained on dummy data)

### **Recommendation:**

The **0% prediction is likely too optimistic**. A more realistic assessment would be:
- **5-15% churn risk** (LOW-MEDIUM)
- Reasons:
  - No usage activity is concerning
  - 22 days since last transaction is moderate risk
  - However, excellent payment history and active services are strong positive indicators

---

## **Data Quality Issues**

1. **Missing Usage Data:**
   - `usage_records_count: 0` suggests usage data may not be syncing properly

2. **Revenue Discrepancy:**
   - DWH: $1,766.61
   - Feature Store: $207.58
   - Need to investigate which is correct

3. **Feature Mapping:**
   - Only 5 features are non-zero
   - Model expects 10 features
   - Missing features may impact prediction accuracy

---

## **How to Improve Prediction Accuracy**

1. **Fix Data Sync:**
   - Ensure usage records are being captured
   - Resolve revenue discrepancy between DWH and Feature Store

2. **Train Model on Real Data:**
   - Current model is trained on dummy/placeholder data
   - Train on actual historical churn data for better accuracy

3. **Add More Features:**
   - Include usage patterns
   - Add engagement metrics
   - Include service-specific data

4. **Fix Explanation Logic:**
   - Correct "Recent activity (within last week)" when it's actually 22 days
   - Better match explanations to actual data

---

## **Conclusion**

The **0% churn prediction is based on strong payment indicators**, but may be **overly optimistic** due to:
- Missing usage data
- Model trained on placeholder data
- Data quality issues

**Recommendation:** Treat this as **LOW risk (5-15%)** rather than 0%, and investigate the missing usage records and data discrepancies.

