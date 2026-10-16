# OnlyOffice Document Server Setup

OnlyOffice Document Server provides native Word/Office document editing in the browser with full fidelity (images, tables, fonts, formatting preserved).

## Quick Start (Docker)

### Prerequisites
- Docker Desktop installed on Windows
- Django app running at `http://127.0.0.1:8000`

### Step 1: Install OnlyOffice Document Server via Docker

```powershell
# Pull OnlyOffice Document Server image
docker pull onlyoffice/documentserver:latest

# Run OnlyOffice (maps to port 8080)
docker run -d -p 8080:80 --name onlyoffice-ds onlyoffice/documentserver:latest
```

**Verify it's running:**
```
http://127.0.0.1:8080
```

You should see the OnlyOffice welcome page.

### Step 2: Enable OnlyOffice in Django Settings

Edit `land_registry/settings.py`:

```python
# OnlyOffice Document Server Configuration
ONLYOFFICE_DS_URL = 'http://127.0.0.1:8080'  # or your server address
ONLYOFFICE_SECRET = 'your-secure-secret-key-here'  # Change this in production
ONLYOFFICE_ENABLED = True  # Enable the feature
```

### Step 3: Install Python Dependencies

```powershell
cd C:\Users\USER 2\Desktop\aiiagov\project1\project1\land_registry
pip install -r requirements.txt
```

This installs:
- `requests` - for downloading edited documents
- `PyJWT` - for token signing (if using advanced security)
- `mammoth` - for DOCX→HTML conversion fallback

### Step 4: Restart Django Server

```powershell
python manage.py runserver 0.0.0.0:8000
```

### Step 5: Test In-Browser Editing

1. Log in to the app
2. Navigate to a borrow folder with `.docx` files
3. Click "Edit" on any `.docx` file
4. OnlyOffice editor should load
5. Edit the document (add text, images, tables, change fonts)
6. OnlyOffice **auto-saves** to the Django system
7. Click "Done Editing" to return to folder

---

## How It Works

### Document Flow

```
User clicks "Edit" on .docx file
    ↓
Django loads `/onlyoffice/config/{borrow_id}/{file_id}/`
    ↓
View generates config + serves DOCX file via `/onlyoffice/file/...`
    ↓
OnlyOffice iframe loads and renders document in editor
    ↓
User edits (full Word features: images, tables, fonts, etc.)
    ↓
OnlyOffice calls `/onlyoffice/callback/...` with edited DOCX
    ↓
Django callback downloads edited DOCX and creates new CloudFileVersion
    ↓
New version stored in cloud_vault/ with version history
```

### Security

- **HMAC Signing:** Document config and callbacks are HMAC-SHA256 signed (if `ONLYOFFICE_SECRET` is set)
- **CSRF Protection:** Callbacks use `@csrf_exempt` (OnlyOffice server is external and can't provide CSRF tokens)
- **Permission Checks:** All views verify user is borrower with 'edit' permission
- **File Isolation:** Only files in the user's issued folder can be edited

---

## Troubleshooting

### Editor Not Loading
- Check `http://127.0.0.1:8080` — is OnlyOffice running?
- Check browser console for errors (F12 → Console)
- Ensure `ONLYOFFICE_ENABLED = True` in settings.py

### "Loading..." Never Completes
- Verify `ONLYOFFICE_DS_URL` points to correct address
- Check Docker logs: `docker logs onlyoffice-ds`
- Check Django console for errors

### Edited Document Not Saving
- Check Django console for callback errors
- Verify `onlyoffice_callback` view is being called (add prints/logging)
- Check `/media/cloud_vault/` — should have new version

### Port Already in Use
```powershell
# Stop existing container
docker stop onlyoffice-ds

# Remove it
docker rm onlyoffice-ds

# Start fresh
docker run -d -p 8080:80 --name onlyoffice-ds onlyoffice/documentserver:latest
```

---

## Production Deployment

For production, consider:

1. **Separate Server:** Run OnlyOffice on a dedicated machine/container
2. **HTTPS:** Use `ONLYOFFICE_DS_URL = 'https://your-domain:8080'`
3. **Strong Secret:** Change `ONLYOFFICE_SECRET` to a cryptographically random value
4. **SSL Certificates:** Install valid SSL certs on OnlyOffice server
5. **Firewall:** Restrict access to OnlyOffice to your Django app only
6. **Resource Limits:** Monitor CPU/memory usage; OnlyOffice is resource-intensive

---

## Docker Commands Reference

```powershell
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker logs onlyoffice-ds

# Stop container
docker stop onlyoffice-ds

# Start stopped container
docker start onlyoffice-ds

# Remove container
docker rm onlyoffice-ds

# Restart container
docker restart onlyoffice-ds

# Update image
docker pull onlyoffice/documentserver:latest
```

---

## Features Now Available

✅ Native Word editing (images, tables, fonts)
✅ Auto-save to Django system
✅ Full document fidelity (formatting preserved)
✅ Version history tracking
✅ Automatic DOCX roundtrip (no HTML conversion needed)
✅ Multi-user support (tracks who edited)
✅ HMAC-signed callbacks for security

---

## Next Steps

1. **Start Docker container** (see Step 1)
2. **Enable in settings** (see Step 2)
3. **Test on a document** (see Step 5)
4. **Monitor for errors** — check console logs

Enjoy native Word editing in your Django app! 🎉
