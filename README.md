# 🤖 AutoCoder

> 用自然语言描述需求，AI自动生成完整项目代码并推送到GitHub。

[Live Demo](https://auto-coder.vercel.app) · [Discord](https://discord.gg/auto-coder) · [Sponsor](https://afdian.com/auto-coder)

## 核心能力

- **自然语言 → 完整项目**: 描述你想做什么，5秒生成可运行代码
- **多语言支持**: Python / JavaScript / TypeScript / HTML / Go / Rust
- **一键推送GitHub**: 生成完直接推到你的仓库，无需手动复制
- **项目模板库**: 社区模板市场，直接复用别人分享的项目
- **AI评测打分**: 生成的代码有质量评分，不满意可以重生成

## 快速开始

### Web界面（最简单）

直接在 [https://auto-coder.vercel.app](https://auto-coder.vercel.app) 输入需求即可。

### 命令行

```bash
# 安装
npm install -g auto-coder-cli

# 生成项目
auto-coder new "一个待办事项App，支持分类和提醒"

# 推送
auto-coder push --github
```

### Python API

```python
from auto_coder import AutoCoder

agent = AutoCoder(github_token="ghp_xxx")
project = agent.generate(
    description="一个股票行情看板，实时显示A股数据",
    language="python",
    framework="flask"
)
project.save("/output/stock-dashboard")
project.push("my-github-username/stock-dashboard")
```

## 工作原理

1. **理解需求** → LLM分析描述，拆解技术栈和功能点
2. **生成代码** → 分层生成：架构设计 → 核心逻辑 → 前端UI → 配置
3. **质量检测** → 语法检查 + 依赖解析 + 简单测试
4. **推送部署** → GitHub API 创建仓库 + 推送代码

## 支持的框架

| 语言 | 框架 |
|------|------|
| Python | Flask, FastAPI, Django, Streamlit, Gradio |
| JavaScript | React, Vue, Next.js, Express |
| HTML | 纯HTML, Bootstrap, TailwindCSS |
| Go | Gin, Echo, Fiber |
| Rust | Actix, Axum, Rocket |

## 评分算法

生成质量从4个维度打分（0-100）：

- **代码完整性** - 是否包含所有声明的功能
- **语法正确性** - 能否通过语言解析器
- **依赖合理性** - package.json/requirements.txt 是否完整
- **架构合理性** - 模块划分是否清晰

总分 >= 70 分才算"通过"，否则自动重生成。

## License

MIT
