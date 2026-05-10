"""AutoCoder Web Interface"""
import os
import uuid
import tempfile
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from auto_coder.agent import CodeGenerationAgent
from auto_coder.github import GitHubPusher

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1MB max for prompts

# Initialize agent
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "")

agent = CodeGenerationAgent(
    llm_api_key=MINIMAX_KEY,
    github_token=GITHUB_TOKEN
)

# In-memory job storage
jobs = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    description = data.get("description", "").strip()
    language = data.get("language", "python")
    framework = data.get("framework", "")
    github_repo = data.get("github_repo", "").strip()

    if not description:
        return jsonify({"error": "请输入项目描述"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "description": description, "started_at": datetime.now().isoformat()}

    try:
        # Generate project
        result = agent.generate(
            description=description,
            language=language,
            framework=framework,
            output_dir=f"/tmp/auto-coder-{job_id}"
        )

        quality_score = result.get("quality_score", 0)
        files = result.get("files", [])

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["quality_score"] = quality_score
        jobs[job_id]["file_count"] = len(files)

        # Push to GitHub if requested
        if github_repo and GITHUB_TOKEN:
            pusher = GitHubPusher(GITHUB_TOKEN)
            push_result = pusher.push_project(
                repo_name=github_repo,
                files=files,
                description=description
            )
            jobs[job_id]["github_url"] = push_result.get("url")

        return jsonify({
            "job_id": job_id,
            "status": "complete",
            "quality_score": quality_score,
            "file_count": len(files),
            "files": [{"name": f["name"], "path": f["path"]} for f in files[:20]],
            "github_url": jobs[job_id].get("github_url")
        })

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        return jsonify({"job_id": job_id, "status": "error", "error": str(e)}), 500

@app.route("/job/<job_id>")
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job_id": job_id, **job})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
