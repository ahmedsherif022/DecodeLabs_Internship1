# Deploy Student Career Advisor Publicly

Recommended host: Render, because this project is a Flask web app and Render can run it directly from GitHub.

## 1. Prepare GitHub

1. Create a new GitHub repository.
2. Push this project folder to GitHub.
3. Do not upload `.env` or `results.csv`.
4. Keep `student_advisor_data.json`; the website needs it at runtime.

## 2. Deploy on Render

1. Go to `https://render.com`.
2. Create a new `Web Service`.
3. Connect your GitHub repository.
4. Use these settings:
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add this environment variable:
   - `GEMINI_API_KEY`: your Google Gemini API key
6. Click `Deploy`.

Render will give you a public URL like:

```text
https://student-career-advisor.onrender.com
```

Use that link in your LinkedIn post.

## 3. Important Notes

- If `GEMINI_API_KEY` is missing, the site still opens, but the chat runs in fallback/mock mode.
- The raw `results.csv` file is large and is not needed by the live app.
- The live app only needs `app.py`, `static/`, `student_advisor_data.json`, and the deployment files.

## 4. Quick Local Run

After installing dependencies locally:

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```
