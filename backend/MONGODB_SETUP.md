# MongoDB Setup

This backend can optionally use MongoDB for logs and behavioral events. SQLite remains the primary store for core entities, but when MongoDB is configured the app mirrors logs to Mongo for easier analysis and scaling.

## 1) Configure environment variables

Set these before starting the backend:

- `MONGODB_URI` – Connection string to your MongoDB (Atlas or local). Examples:
  - Atlas: `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority`
  - Local: `mongodb://localhost:27017`
- `MONGODB_DB_NAME` – Database name (default: `election_db`).
- `FRONTEND_ORIGIN` – Frontend URL for CORS with credentials (default: `http://localhost:3000`).

On Windows PowerShell:

```powershell
$env:MONGODB_URI = "mongodb://localhost:27017"
$env:MONGODB_DB_NAME = "election_db"
$env:FRONTEND_ORIGIN = "http://localhost:3000"
```

## 2) Run MongoDB locally

- Docker (recommended):

```powershell
docker run -d --name mongo -p 27017:27017 -v mongo_data:/data/db mongo:7
```

- Or install MongoDB Community Server from mongodb.com and run the Windows service.

## 3) Start the backend

```powershell
& "D:/Desktop folder/Major Project clg/.venv/Scripts/python.exe" backend/app.py
```

You'll see `MongoDB connected: db='election_db'` if the connection succeeds.

If you see `mongo_configured: false`, set `MONGODB_URI`.
If `mongo_connected: false` with `querySrv ENOTFOUND`, either:
- Switch to a standard connection string (non-SRV) from Atlas driver page, or
- Use local MongoDB: `MONGODB_URI = "mongodb://localhost:27017"`.

## 4) Verify

Open in browser or with curl:

```
GET http://localhost:5000/api/health
```

You should get a JSON response with:

```json
{
  "status": "ok",
  "mongo_configured": true,
  "mongo_connected": true,
  "mongo_error": null
}
```

## Notes
- MongoDB is optional. If `MONGODB_URI` isn't set or connectivity fails, the app continues to function using SQLite and file logs.
- Current Mongo integration mirrors:
  - `security_logs` (collection: `security_logs`)
  - `behavioral_logs` (collection: `behavioral_logs`)
- You can expand this to store votes/election data in Mongo by adding similar inserts where the data is created.
