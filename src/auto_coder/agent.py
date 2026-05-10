"""Code Generation Agent using LLM"""
import os
import re
import json
import tempfile
import subprocess
from pathlib import Path

MINIMAX_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

LANGUAGE_TEMPLATES = {
    "python": {
        "frameworks": {
            "flask": {"files": ["app.py", "requirements.txt", "README.md"], "prompt_addon": "使用Flask框架，包含路由和基本的错误处理"},
            "fastapi": {"files": ["main.py", "requirements.txt", "README.md"], "prompt_addon": "使用FastAPI框架，包含Pydantic模型和类型提示"},
            "streamlit": {"files": ["app.py", "requirements.txt", "README.md"], "prompt_addon": "使用Streamlit，包含交互式UI组件"},
            "gradio": {"files": ["app.py", "requirements.txt", "README.md"], "prompt_addon": "使用Gradio，包含demo界面"},
        },
        "default_files": ["main.py", "requirements.txt", "README.md", ".gitignore"]
    },
    "javascript": {
        "frameworks": {
            "react": {"files": ["package.json", "src/App.jsx", "src/main.jsx", "index.html"], "prompt_addon": "使用React 18 + Vite"},
            "vue": {"files": ["package.json", "src/App.vue", "src/main.js", "index.html"], "prompt_addon": "使用Vue 3 + Vite"},
            "express": {"files": ["package.json", "src/index.js", "src/routes.js", "README.md"], "prompt_addon": "使用Express.js，包含中间件和路由"},
        },
        "default_files": ["package.json", "index.js", "README.md", ".gitignore"]
    },
    "html": {
        "frameworks": {
            "bootstrap": {"files": ["index.html", "styles.css", "script.js"], "prompt_addon": "使用Bootstrap 5"},
            "tailwind": {"files": ["index.html", "script.js"], "prompt_addon": "使用TailwindCSS CDN"},
        },
        "default_files": ["index.html", "styles.css", "script.js", "README.md"]
    }
}

class CodeGenerationAgent:
    def __init__(self, llm_api_key: str, github_token: str = ""):
        self.llm_api_key = llm_api_key
        self.github_token = github_token

    def generate(self, description: str, language: str = "python",
                 framework: str = "", output_dir: str = "") -> dict:
        """Generate a complete project from natural language description."""

        # Determine files to generate
        lang_config = LANGUAGE_TEMPLATES.get(language, LANGUAGE_TEMPLATES["python"])
        if framework and framework in lang_config.get("frameworks", {}):
            files_to_generate = lang_config["frameworks"][framework]["files"]
            framework_context = lang_config["frameworks"][framework]["prompt_addon"]
        else:
            files_to_generate = lang_config.get("default_files", ["main.py", "README.md"])
            framework_context = f"语言: {language}"

        # Build generation prompt
        prompt = self._build_prompt(description, language, framework_context, files_to_generate)

        # Call LLM to generate code for each file
        generated_files = []
        for filename in files_to_generate:
            code = self._generate_file(prompt, filename, language)
            if code:
                generated_files.append({"name": filename, "content": code})

        # Calculate quality score
        quality_score = self._calculate_quality_score(generated_files, description)

        return {
            "files": generated_files,
            "quality_score": quality_score,
            "language": language,
            "framework": framework,
            "description": description
        }

    def _build_prompt(self, description: str, language: str, framework_context: str, files: list) -> str:
        return f"""你是一个专业的{language}开发工程师。请根据以下需求生成完整的、可运行的代码。

需求描述：{description}

技术栈：{framework_context}
语言：{language}

需要生成的文件：{', '.join(files)}

要求：
1. 每个文件都要有完整的、可运行的代码，不能是模板或占位符
2. 代码要有适当的注释和错误处理
3. 所有依赖要完整（requirements.txt / package.json等）
4. 遵循该语言的最佳实践和代码风格

请为每个文件生成完整代码，格式：
===FILE: filename.ext===
[文件完整内容]
===END===

请开始生成："""

    def _generate_file(self, prompt: str, filename: str, language: str) -> str:
        """Call LLM API to generate a single file."""
        import requests

        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": "qwen-plus",
            "messages": messages,
            "temperature": 0.3
        }
        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

            # Extract file content from response
            pattern = f"===FILE: {re.escape(filename)}===\n([\s\S]*?)(?:===END===|$)"
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
            return content
        except Exception as e:
            return f"# Generation failed: {e}\n# Please implement this file manually."

    def _calculate_quality_score(self, files: list, description: str) -> int:
        """Calculate quality score 0-100."""
        if not files:
            return 0

        score = 0
        reasons = []

        # Completeness: each file has substantial content
        avg_lines = sum(f["content"].count("\n") for f in files) / max(len(files), 1)
        if avg_lines > 20:
            score += 30
            reasons.append(f"avg {avg_lines:.0f} lines/file")
        elif avg_lines > 5:
            score += 15

        # Has README
        has_readme = any("readme" in f["name"].lower() for f in files)
        if has_readme:
            score += 20
        else:
            reasons.append("no README")

        # Has dependencies file
        has_deps = any(f["name"] in ["requirements.txt", "package.json", "go.mod", "Cargo.toml"] for f in files)
        if has_deps:
            score += 20

        # README has substantial content
        for f in files:
            if "readme" in f["name"].lower() and len(f["content"]) > 200:
                score += 15
                reasons.append("good README")
                break

        # Has main entry file
        has_entry = any(f["name"] in ["app.py", "main.py", "index.js", "index.html", "main.go"] for f in files)
        if has_entry:
            score += 15

        return min(100, score)
