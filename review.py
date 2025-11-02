#!/usr/bin/env python3
import os
import requests
from google import genai

GCP_PROJECT = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GCP_MODEL = os.getenv("GCP_MODEL", "gemini-2.5-flash")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_SHA = os.getenv("GITHUB_SHA") or os.getenv("COMMIT_SHA")

GITHUB_API = "https://api.github.com"

def get_owner_repo():
    if not GITHUB_REPOSITORY:
        print("GITHUB_REPOSITORY missing")
        return None, None
    try:
        owner, repo = GITHUB_REPOSITORY.split("/", 1)
        return owner, repo
    except Exception:
        print("GITHUB_REPOSITORY is malformed:", GITHUB_REPOSITORY)
        return None, None

def list_commit_files(owner, repo, sha):
    if not owner or not repo or not sha:
        return []
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        print("Failed to fetch commit info:", r.status_code, r.text)
        return []
    data = r.json()
    files = data.get("files", [])
    results = []
    for f in files:
        filename = f.get("filename")
        raw_url = f.get("raw_url") or f.get("blob_url") or f.get("contents_url")
        results.append({"filename": filename, "raw_url": raw_url})
    return results

def fetch_raw_content(owner, repo, sha, raw_url, path):
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    if raw_url and raw_url.startswith("http"):
        try:
            r = requests.get(raw_url, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            print(f"Failed to fetch from raw_url {raw_url}: {e}")

    fallback = f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}"
    try:
        r = requests.get(fallback, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.text
        else:
            print(f"Fallback raw fetch failed for {path}: {r.status_code}")
    except Exception as e:
        print(f"Fallback fetch error for {path}: {e}")

    return ""

def genai_review(file_path, file_content):
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
    prompt = (
        f"You are a senior software engineer reviewing code. "
        f"Provide concise, actionable review comments for `{file_path}`. "
        f"Highlight bugs, security issues, and style improvements.\n\n"
        f"```{file_content}```"
    )
    try:
        resp = client.models.generate_content(model=GCP_MODEL, contents=prompt)
        return getattr(resp, "text", getattr(resp, "output_text", str(resp)))
    except Exception as e:
        return f"GenAI model call failed: {e}"

def post_commit_comment(owner, repo, sha, body):
    if not owner or not repo or not sha:
        print("Missing commit info — cannot post comment")
        return
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    payload = {"body": body}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        print("Comment posted to commit")
    else:
        print("Failed to post comment to commit:", r.status_code, r.text)

def main():
    owner, repo = get_owner_repo()
    if not owner:
        print("No repository info — exiting")
        return

    sha = GITHUB_SHA
    if not sha:
        print("GITHUB_SHA not set. Try to get latest commit of default branch")
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        r = requests.get(repo_url, headers=headers, timeout=30)
        if r.status_code == 200:
            default_branch = r.json().get("default_branch")
            if default_branch:
                commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{default_branch}"
                r2 = requests.get(commits_url, headers=headers, timeout=30)
                if r2.status_code == 200:
                    sha = r2.json().get("sha")
        if not sha:
            print("Could not determine commit SHA. Set GITHUB_SHA or run in Actions.")
            return

    files = list_commit_files(owner, repo, sha)
    if not files:
        print("No files found in commit to review")
        return

    reviews = []
    for f in files:
        filename = f.get("filename")
        raw_url = f.get("raw_url")
        if not filename:
            continue
        content = fetch_raw_content(owner, repo, sha, raw_url, filename)
        if not content:
            print(f"Cannot fetch content for {filename}")
            continue
        if len(content) > 25000:
            content = content[:25000] + "\n\n...truncated..."
        review_text = genai_review(filename, content)
        reviews.append(f"**File:** `{filename}`\n{review_text}\n")

    if reviews:
        comment_body = f"## Vertex AI — Automated Code Review for commit `{sha}`\n\n" + "\n---\n".join(reviews)
        if len(comment_body) > 64000:
            comment_body = comment_body[:64000] + "\n\n...truncated..."
        post_commit_comment(owner, repo, sha, comment_body)
    else:
        print("No reviews generated.")

if __name__ == "__main__":
    main()
