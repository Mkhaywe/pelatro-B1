# Documentation Cleanup Plan

## Current Status

### Files in Root Directory (Potentially Duplicate)

1. **DWH_EXPLAINED.md** - DWH explanation
   - **Status**: Duplicate/Outdated
   - **Action**: Delete (content merged into `docs/DWH_INTEGRATION.md`)
   - **Reason**: `docs/DWH_INTEGRATION.md` has more comprehensive and updated content

2. **DWH_SETUP_GUIDE.md** - DWH setup instructions
   - **Status**: Duplicate/Outdated
   - **Action**: Delete (content merged into `docs/DWH_INTEGRATION.md`)
   - **Reason**: Setup instructions are in `docs/DWH_INTEGRATION.md`

3. **SYSTEM_WORKFLOW_GUIDE.md** - System workflow
   - **Status**: Duplicate
   - **Action**: Delete (content merged into `docs/WORKFLOW_GUIDE.md`)
   - **Reason**: `docs/WORKFLOW_GUIDE.md` is the updated version

4. **ML_TRAINING_STEP_BY_STEP.md** - ML training guide
   - **Status**: Partially Duplicate
   - **Action**: Review and merge unique content, then delete
   - **Reason**: `docs/ML_GUIDE.md` has comprehensive ML guide, but this might have unique step-by-step details

5. **QUICK_ANSWERS.md** - Quick Q&A
   - **Status**: Unique Content
   - **Action**: Keep or move to `docs/` if useful
   - **Reason**: Contains specific Q&A that might be useful

6. **FIXES_APPLIED.md** - Fix log
   - **Status**: Outdated/Historical
   - **Action**: Delete (historical fixes, not needed)
   - **Reason**: Historical fix log, current fixes should be in `docs/TROUBLESHOOTING.md`

---

## Recommended Actions

### Immediate Deletion (Duplicates)

These files are duplicates and can be safely deleted:

1. ✅ **DWH_EXPLAINED.md** → Content in `docs/DWH_INTEGRATION.md`
2. ✅ **DWH_SETUP_GUIDE.md** → Content in `docs/DWH_INTEGRATION.md`
3. ✅ **SYSTEM_WORKFLOW_GUIDE.md** → Content in `docs/WORKFLOW_GUIDE.md`
4. ✅ **FIXES_APPLIED.md** → Historical, not needed

### Review and Merge

1. **ML_TRAINING_STEP_BY_STEP.md**
   - Check if it has unique detailed steps not in `docs/ML_GUIDE.md`
   - If yes, merge unique content into `docs/ML_GUIDE.md`
   - Then delete

2. **QUICK_ANSWERS.md**
   - Review if content is still relevant
   - If useful, either:
     - Move to `docs/QUICK_ANSWERS.md`
     - Or merge relevant Q&A into appropriate docs
   - Then delete from root

---

## Final Structure

After cleanup, root directory should only have:
- **README.md** - Main project README (references docs/)
- **requirements.txt** - Python dependencies
- **manage.py** - Django management script
- Configuration files (`.env`, etc.)

All documentation should be in `docs/` directory.

---

**Last Updated**: 2026-01-02

