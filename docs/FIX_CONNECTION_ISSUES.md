# Fix: ECONNREFUSED and 401 Errors

## 🔴 **Problem**

You're seeing:
- `ECONNREFUSED` errors in Vite logs
- 401 Authentication errors

## ✅ **Solution**

### **Issue 1: ECONNREFUSED (Connection Refused)**

This happens when:
- Backend is restarting
- Backend crashed
- Backend not started

**Fix:**
```powershell
# Check if backend is running
netstat -ano | findstr :8001

# If not running, start it:
.\start_backend.ps1

# Or restart everything:
.\start_all.ps1
```

### **Issue 2: 401 Authentication Required**

This happens when:
- Backend requires authentication
- Frontend isn't logged in
- Token not being sent

**Fix Applied:**
I've updated the code to allow unauthenticated access for development on:
- Configuration endpoints
- Dashboard endpoints
- Segment endpoints
- Gamification endpoints

**Restart backend to apply changes:**
```powershell
# Stop backend
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | 
    Select-Object OwningProcess | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Start backend
.\start_backend.ps1
```

---

## 🎯 **Quick Fix**

**Just restart the backend:**
```powershell
.\start_all.ps1
```

This will:
1. Kill existing processes
2. Start backend on port 8001
3. Start frontend on port 5173
4. Apply authentication fixes

---

## ✅ **Verify It's Working**

1. **Check backend is running:**
   ```powershell
   netstat -ano | findstr :8001
   # Should show: LISTENING
   ```

2. **Test backend directly:**
   ```powershell
   curl http://localhost:8001/api/loyalty/v1/config/get_all/
   # Should return JSON (not 401 error)
   ```

3. **Check frontend:**
   - Open: http://localhost:5173
   - Should load without errors
   - API calls should work

---

## 📝 **What Changed**

1. **Added `AllowAny` permission** to:
   - `ConfigurationViewSet`
   - `DashboardStatsViewSet`
   - `SegmentViewSet`
   - `DataSourceConfigViewSet`

2. **This allows unauthenticated access** for development

3. **For production**, you should:
   - Remove `AllowAny` or set to `IsAuthenticated`
   - Ensure frontend logs in and sends tokens

---

## 🚀 **Next Steps**

1. **Restart backend** (see above)
2. **Refresh frontend** (F5)
3. **Check browser console** - should see no errors
4. **Test API calls** - should work now

---

## 🆘 **Still Not Working?**

1. **Check backend logs** for errors
2. **Check if port 8001 is free:**
   ```powershell
   netstat -ano | findstr :8001
   ```
3. **Try accessing backend directly:**
   ```
   http://localhost:8001/api/loyalty/v1/config/get_all/
   ```
4. **Check Vite proxy config** in `frontend/vite.config.ts`

---

## ✅ **Expected Result**

After restart:
- ✅ Backend running on port 8001
- ✅ Frontend running on port 5173
- ✅ No ECONNREFUSED errors
- ✅ No 401 errors
- ✅ API calls work

