# Segment Snapshots Explained

## What Are Snapshots?

**Segment Snapshots** are historical records that capture the state of a segment at a specific point in time. They store:
- **Member count** - How many customers were in the segment
- **Member IDs** - List of customer IDs at that moment
- **Snapshot date** - When the snapshot was taken

### Purpose

Snapshots enable you to:
1. **Track trends** - See how segment membership changes over time
2. **Analyze growth** - Understand if segments are growing or shrinking
3. **Historical analysis** - Compare segment size across different periods
4. **Audit trail** - Know exactly who was in a segment at any given time

---

## When Are Snapshots Created?

### Automatic Creation (✅ Now Implemented)

Snapshots are **automatically created** when:
- A segment is **recalculated** (via "Recalculate" button)
- Segment membership is **updated** via `update_segment_membership()`

**Code Location**: `loyalty/services/segmentation.py`
- `update_segment_membership()` now calls `SegmentSnapshotService.create_snapshot()` after updating members

### Manual Creation

You can also create snapshots manually via API:

```http
POST /api/loyalty/v1/segment-engine/create-snapshot/
Content-Type: application/json

{
  "segment_id": 6
}
```

---

## Why Was Your Snapshot Array Empty?

Your segment had **no snapshots** because:

1. **Snapshots weren't automatically created** (this is now fixed)
2. **No manual snapshots were created**
3. **Segment was never recalculated** after the fix

### How to Get Snapshots Now

1. **Recalculate the segment**:
   - Go to Segment Detail page
   - Click "Recalculate" button
   - This will:
     - Update membership
     - Create a snapshot automatically
     - Update `last_calculated` timestamp

2. **Check metrics again**:
   - The `snapshots` array will now contain at least one entry
   - Each recalculation creates a new snapshot

---

## Snapshot Data Structure

### API Response

```json
{
  "total_members": 11,
  "inactive_members": 0,
  "last_calculated": "2026-01-02T14:30:00Z",
  "snapshots": [
    {
      "date": "2026-01-02T14:30:00Z",
      "member_count": 11
    },
    {
      "date": "2026-01-01T10:00:00Z",
      "member_count": 9
    }
  ],
  "segment_id": 6,
  "segment_name": "Premium Service Users",
  "is_dynamic": true,
  "is_rfm": false
}
```

### Database Model

**Table**: `loyalty_segmentsnapshot`

**Fields**:
- `segment` - ForeignKey to Segment
- `snapshot_date` - DateTime when snapshot was taken
- `member_count` - Number of members at that time
- `member_ids` - JSON array of customer UUIDs

**Unique Constraint**: One snapshot per segment per date

---

## Snapshot Retention

### Current Behavior

- **All snapshots are kept** - No automatic deletion
- **Last 10 snapshots** are returned in metrics API (for performance)
- **Full history** available via snapshots API

### Best Practices

1. **Regular Recalculation**: Recalculate segments regularly to build history
2. **Scheduled Jobs**: Set up cron jobs to recalculate segments daily/weekly
3. **Cleanup**: Periodically archive old snapshots if needed

---

## RFM Segments (`is_rfm`)

### What is RFM?

**RFM** stands for:
- **R**ecency - How recently did the customer purchase?
- **F**requency - How often do they purchase?
- **M**onetary - How much do they spend?

### RFM Segmentation

RFM segments are **automatically calculated** based on customer behavior:
- Each customer gets an RFM score (e.g., "555", "432", "111")
- Segments are created based on RFM score ranges
- Examples:
  - **"555"** = Champions (recent, frequent, high value)
  - **"111"** = Lost customers (not recent, infrequent, low value)
  - **"451"** = At risk (recent, frequent, but low value)

### `is_rfm: false` Meaning

Your segment **"Premium Service Users"** has `is_rfm: false` because:

1. **It's a custom segment** - Defined by JSONLogic rules, not RFM scores
2. **Not an RFM segment** - Uses your own criteria (e.g., `total_revenue > 1000`)
3. **Set during creation** - The `is_rfm` flag is set when you create the segment

### When to Use RFM Segments

Set `is_rfm: true` when:
- You want segments based on RFM analysis
- You need standard RFM segments (Champions, Loyal, At Risk, etc.)
- You want automatic RFM-based segmentation

**Note**: RFM segments still use JSONLogic rules, but the rules are based on RFM scores from `MLInferenceService.calculate_rfm()`.

---

## Example: Creating an RFM Segment

### Via Frontend

1. Go to **Segments** → **Create Segment**
2. Set **Name**: "RFM Champions"
3. Set **is_rfm**: `true` (checkbox)
4. Set **Rules**: 
   ```json
   {
     "==": [
       {"var": "rfm_segment"},
       "555"
     ]
   }
   ```
5. Click **Save**

### Via API

```http
POST /api/loyalty/v1/segments/
Content-Type: application/json

{
  "name": "RFM Champions",
  "description": "Top customers (555 RFM score)",
  "is_rfm": true,
  "rfm_config": {
    "min_score": "555",
    "max_score": "555"
  },
  "rules": [
    {
      "==": [
        {"var": "rfm_segment"},
        "555"
      ]
    }
  ],
  "is_dynamic": true
}
```

---

## Summary

| Question | Answer |
|----------|--------|
| **What are snapshots?** | Historical records of segment membership at specific times |
| **Why were they empty?** | Snapshots weren't automatically created (now fixed) |
| **When are they created?** | Automatically when segment is recalculated |
| **What is `is_rfm`?** | Flag indicating if segment is based on RFM analysis |
| **Why is it `false`?** | Your segment uses custom JSONLogic rules, not RFM scores |

---

**Last Updated**: 2026-01-02

