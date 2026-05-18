from fastapi import FastAPI, Request
import httpx
import os
import boto3
import json
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print(f"GITHUB TOKEN LOADED: {GITHUB_TOKEN}")  # add this line

# AWS Bedrock client
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"  # change to your AWS region
)

@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"message": "Invalid payload"}

    # Only handle PR opened or updated
    if payload.get("action") not in ["opened", "synchronize"]:
        return {"message": "Ignored"}

    repo_full_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    diff_url = payload["pull_request"]["diff_url"]

    # Step 1 — Fetch the code diff from GitHub
    async with httpx.AsyncClient() as client:
        diff_response = await client.get(
            diff_url,
            headers={"Authorization": f"token {GITHUB_TOKEN}"}
        )
        code_diff = diff_response.text

    # Step 2 — Send to Claude via AWS Bedrock
    prompt = f"""You are an expert code reviewer. Review the following code diff and provide:
1. Security issues
2. Performance problems  
3. Bad coding practices
4. Specific suggestions to fix each issue

Be specific and clear. Use ⚠ for warnings and ✅ for suggestions.

Code diff:
{code_diff}"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    response = bedrock.invoke_model(
        modelId="us.anthropic.claude-sonnet-4-6",
        body=body
    )

    response_body = json.loads(response["body"].read())
    review_comment = response_body["content"][0]["text"]

    # Step 3 — Post comment back to GitHub PR
    # Step 3 — Post comment back to GitHub PR
    async with httpx.AsyncClient() as client:
        github_response = await client.post(
            f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments",
            json={"body": review_comment},
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        print(f"GitHub response status: {github_response.status_code}")
        print(f"GitHub response body: {github_response.text}")

    return {"message": "Review posted successfully"}
