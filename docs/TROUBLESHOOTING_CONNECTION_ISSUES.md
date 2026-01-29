# Troubleshooting: Frontend Can't Connect to Backend

## 🔴 **Error: ECONNREFUSED**

This means the frontend (Vite) can't connect to the backend (Django).

---

## ✅ **Quick Fixes**

### **1. Check if Backend is Running**

```powershell
# Check if port 8001 is listening
netstat -ano | findstr :8001

# Should show: LISTENING
```

### **2. Restart Backend**

```powershell
# Stop backend
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | 
    Select-Object OwningProcess | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Start backend
.\start_backend.ps1
```

### **3. Check Backend Logs**

Look for errors in the Django console output:
- Database connection errors
- Import errors
- Port already in use

### **4. Test Backend Directly**

```powershell
# Test if backend responds
curl http://localhost:8001/api/loyalty/v1/config/get_all/

# Or in browser:
# http://localhost:8001/api/loyalty/v1/config/get_all/
```

---

## 🔍 **Common Issues**

### **Issue 1: Backend Crashed**

**Symptoms:**
- Port 8001 shows TIME_WAIT connections
- Frontend gets ECONNREFUSED

**Fix:**
```powershell
# Kill and restart
Get-Process python | Where-Object {$_.Path -like "*venv*"} | Stop-Process -Force
.\start_backend.ps1
```

### **Issue 2: Backend Not Started**

**Symptoms:**
- No process on port 8001
- Frontend can't connect

**Fix:**
```powershell
.\start_backend.ps1
```

### **Issue 3: Port Conflict**

**Symptoms:**
- "Address already in use" error
- Backend won't start

**Fix:**
```powershell
# Find and kill process using port 8001
Get-NetTCPConnection -LocalPort 8001 | 
    Select-Object OwningProcess | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Then restart
.\start_backend.ps1
```

### **Issue 4: Database Connection Error**

**Symptoms:**
- Backend starts but crashes on first request
- Database connection errors in logs

**Fix:**
```powershell
# Check PostgreSQL is running
# Or use SQLite for development:
$env:USE_POSTGRES="False"
.\start_backend.ps1
```

### **Issue 5: Vite Proxy Configuration**

**Symptoms:**
- Backend works but frontend can't connect
- Wrong port in proxy config

**Fix:**
Check `frontend/vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8001',  // Must match backend port
    changeOrigin: true,
  },
}
```

---

## 🚀 **Complete Restart**

If nothing works, do a complete restart:

```powershell
# 1. Stop everything
Get-NetTCPConnection -LocalPort 8001,5173 -ErrorAction SilentlyContinue | 
    Select-Object OwningProcess | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# 2. Wait a moment
Start-Sleep -Seconds 2

# 3. Start everything
.\start_all.ps1
```

---

## 📋 **Checklist**

- [ ] Backend is running (port 8001 listening)
- [ ] Frontend is running (port 5173 listening)
- [ ] Backend responds to direct requests
- [ ] Vite proxy config is correct
- [ ] No port conflicts
- [ ] Database is accessible

---

## 🆘 **Still Not Working?**

1. **Check Django logs** for errors
2. **Check Vite logs** for proxy errors
3. **Try accessing backend directly** in browser
4. **Restart both servers** completely
5. **Check firewall** isn't blocking connections

---

## ✅ **Expected Behavior**

When working correctly:
- Backend: `http://localhost:8001` responds
- Frontend: `http://localhost:5173` loads
- API calls from frontend work
- No ECONNREFUSED errors

