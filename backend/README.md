# Label Lens backend

The service accepts one label image and a diet profile,
then returns the structured result consumed by the frontend.

## Scope

- `POST /api/v1/analyze` accepts a multipart image and JSON diet profile.
- The service sends the image and profile to Gemini/Gemma through the Google
  GenAI SDK.
- Photos and profiles are held only for the duration of the request.
- There is no database, account system, scan history, barcode lookup, or photo
  storage.

The Gemini API receives uploaded label images when this provider is enabled.
For allergy decisions, users must check the physical package; this tool is not
medical advice.

## Run locally

From `backend`:

```powershell
..\.venv\Scripts\python.exe -m pip install -e ".[test]"
$env:GEMINI_API_KEY = "your-key"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with OpenAPI documentation at
`/docs`.

## Request example

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/analyze `
  -F "image=@label.jpg" `
  -F 'profile={"dietary_choices":["vegetarian"],"allergens":["milk"],"goals":[]}'
```

On Windows PowerShell, `curl.exe` can strip JSON quotes while constructing a
multipart field. If the API reports invalid profile JSON, write the profile to
a UTF-8 JSON file and send its contents:

```powershell
$profilePath = Join-Path $env:TEMP "label-lens-profile.json"
[IO.File]::WriteAllText(
  $profilePath,
  '{"dietary_choices":["vegetarian"],"allergens":["milk"],"goals":[]}',
  [Text.UTF8Encoding]::new($false)
)
curl.exe -X POST http://127.0.0.1:8000/api/v1/analyze `
  -F "image=@D:\path\to\label.jpg;type=image/jpeg" `
  -F "profile=<$profilePath"
Remove-Item $profilePath
```
