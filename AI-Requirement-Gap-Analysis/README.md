# AI Requirement Gap Detector

A complete software-only requirement analysis web application.

## Features
- Login / signup demo authentication
- Dashboard with project history
- Create projects and analyze requirements
- Detect missing, ambiguous, incomplete, conflicting and weak requirements
- Security/validation and acceptance-criteria gap checks
- Edge-case detection
- Requirement quality score
- Clarification questions
- Suggested improved requirements
- TXT, PDF and DOCX upload support
- JSON report export
- Local browser persistence for projects
- FastAPI backend
- Optional OpenAI-compatible AI integration
- Works without Node.js

## Run on Windows
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Open Terminal.
4. Run:
   `python -m pip install -r backend/requirements.txt`
5. Run:
   `python backend/main.py`
6. Open: http://127.0.0.1:8000

Optional AI:
- Set `AI_API_KEY` in the environment.
- Optional `AI_API_URL` defaults to `https://api.openai.com/v1/chat/completions`.
- Without an API key, the built-in rule-based analyzer works.

Demo login: any email/password combination is accepted by the frontend demo login.
