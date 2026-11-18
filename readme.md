# Student Timetable Optimizer – Algorithm Explorer

A full-stack Flask web application that creates and compares student study timetables using four algorithms: Brute Force, Greedy, Dynamic Programming, and Backtracking.

## Important: GitHub Pages is not the deployment host for this project

This project requires a Python Flask backend (`app.py`) and an API endpoint (`/api/optimize`). GitHub Pages only serves static files and cannot run Flask. Upload the source code to a GitHub repository, then deploy the app on Render.

## 1. Upload this project to GitHub

1. Create a new repository on GitHub.
2. Extract this project ZIP file.
3. Open the extracted project folder. You should see `app.py`, `requirements.txt`, `render.yaml`, `templates/`, `static/`, and `algorithms/` directly inside it.
4. Upload the **contents** of that folder to the top level of your GitHub repository (not an extra nested project folder).
5. Commit the files to the `main` branch.

## 2. Deploy the website on Render

1. Sign in to [Render](https://render.com/).
2. Choose **New** → **Blueprint** (or create a **New Web Service**).
3. Connect your GitHub account and select this repository.
4. If using Blueprint, Render will read `render.yaml` automatically. If creating a Web Service manually, set:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Deploy the service and wait until its status is **Live**.
6. Open the `https://...onrender.com` URL provided by Render.

The `render.yaml` file in this repository contains the deployment settings.

## 3. Run locally in VS Code

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS / Linux:
```bash
source venv/bin/activate
```

Install dependencies and start the server:

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Troubleshooting

- **The page loads but optimization fails:** Make sure the app is deployed as a Render Python web service, not GitHub Pages. The `/api/optimize` route is served by Flask.
- **Build fails:** Check the Render build logs and confirm `requirements.txt` is at the repository root.
- **Service is not live:** Check the deploy logs for Python dependency or startup errors.
- **Charts do not load:** The comparison charts use Chart.js from a CDN and require an internet connection.
- **First visit is slow:** Free web services may take time to wake after inactivity.

## Project structure

```text
.
├── algorithms/
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
└── readme.md
```
