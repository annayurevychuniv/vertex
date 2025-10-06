Vertex AI Automated Code Review

This repository contains a GitHub Action that uses Vertex AI to automatically review pull requests. It comments on potential bugs, security issues, and style improvements for your code.

📂 Files in this repository
review.py — main Python script that fetches PR files, calls Vertex AI to review code, and posts comments back to GitHub.
requirements.txt — Python dependencies: requests and google-genai.
.github/workflows/code-review.yml — GitHub Actions workflow configuration.\

Copy the following files into your repository:
review.py
requirements.txt
.github/workflows/code-review.yml

In your repository, go to Settings → Secrets and variables → Actions → New repository secret and add:
GCP_KEY_JSON	- Service account key - JSON downloaded from GCP
GCP_PROJECT_ID - Your Google Cloud project ID
GCP_LOCATION - Vertex AI location (default: us-central1)
GCP_MODEL - Vertex AI model name (default: gemini-2.5-flash)

Optional: Configure target branches. By default, the workflow runs on: main, test

To add or remove branches, edit .github/workflows/code-review.yml under push → branches.

🚀 How it works
When a pull request is opened, synchronized, or reopened, or when code is pushed to target branches, the workflow triggers.
review.py fetches the changed files from the PR.
The script calls Vertex AI with a prompt asking for actionable review comments.
Comments are posted directly to the PR on GitHub.

⚡ Notes
Files larger than 25,000 characters are truncated.
If no PR information is available (e.g., running manually), the script will skip review.
Make sure your service account has permissions to use Vertex AI models.
