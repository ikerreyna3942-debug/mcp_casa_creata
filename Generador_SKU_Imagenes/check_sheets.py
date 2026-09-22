from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds_path = Path("credentials.json")
scopes = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_file(str(creds_path), scopes=scopes)
service = build("drive", "v3", credentials=creds)

results = service.files().list(
    pageSize=30,
    fields="files(id, name, mimeType, modifiedTime)"
).execute()

files = results.get("files", [])
print(f"TOTAL ARCHIVOS ACCESIBLES: {len(files)}")
for f in files:
    print(f"[{f.get('mimeType')}] {f.get('name')} -> ID: {f.get('id')}")
