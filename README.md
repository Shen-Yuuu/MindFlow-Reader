# MindFlow Reader

MindFlow Reader 是一个功能完整的 Web 应用，旨在通过 AI 模型辅助提升文献阅读体验，并关注用户的心流状态。本项目包含基于 Vue.js 的前端和基于 Python FastAPI 的后端。

本文档基于 `mvp.md` 中的项目规划进行更新。

## 技术栈

### 前端 (Vue.js + Vite)

- **框架:** Vue.js 3
- **构建工具:** Vite
- **状态管理:** Pinia
- **UI组件库:** Vuetify
- **路由:** Vue Router
- **TypeScript:** 支持
- **PDF渲染:** `@tato30/vue-pdf` (基于 `pdfjs-dist`)
- **图表可视化:** `D3.js`, `ECharts`
- **数学公式:** `KaTeX`
- **HTTP客户端:** `axios`

### 后端 (Python + FastAPI)

- **框架:** FastAPI
- **PDF处理:** PyMuPDF
- **AI 和 NLP:**
  - `HanLP (通过 RESTful API)`: 用于中文核心概念识别 (NER)。
  - `wikipedia` (Python 库): 辅助术语验证/过滤 (配合本地语料库)。
  - (注意: `mvp.md` 中提及的其他本地AI/NLP库如 `spaCy`, `sentence-transformers` 等目前未在后端核心集成)
- **知识图谱/数据存储:**
  - 当前使用 **内存模拟知识存储** (Python 字典/列表)。
  - (远期规划: `Neo4j` 用于图数据管理, `PostgreSQL` 和 `Redis` 用于其他数据存储和缓存，当前未集成)。
- **API 服务:**
  - `uvicorn`: 用于运行 FastAPI 应用。

## 推荐 IDE 设置

- **VSCode:** [Visual Studio Code](https://code.visualstudio.com/)
  - **Vue.js:** [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (请禁用 Vetur).
  - **Python:** [Python extension for Visual Studio Code](https://marketplace.visualstudio.com/itemdetails?itemName=ms-python.python).

## 项目结构概览

```
mindflow-reader/
├── .git/
├── .vscode/
├── backend/              # 后端 FastAPI 应用 (Python)
│   ├── (例如: main.py, api/, models/, services/)
│   └── (例如: requirements.txt) # 后端依赖
├── node_modules/         # (被 .gitignore 忽略)
├── pyenv/                # (被 .gitignore 忽略 - Python 虚拟环境)
├── public/               # Vite public 静态资源
├── src/                  # 前端 Vue.js 源码
│   ├── assets/
│   ├── components/
│   ├── router/
│   ├── stores/ (Pinia)
│   ├── views/
│   ├── App.vue
│   └── main.ts           # Vue 应用入口
├── .gitattributes
├── .gitignore
├── .prettierrc.json
├── env.d.ts
├── index.html            # 前端入口 HTML
├── mvp.md                # 项目细化方案
├── package-lock.json
├── package.json          # 前端项目元数据和依赖
├── README.md             # 本文档
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts        # Vite 配置文件
```

## 先决条件

- Node.js (版本 ^18.0.0 || ^20.0.0，或根据 `package.json` engines 字段调整，若无则推荐最新LTS)
- Python (推荐 3.8+ 版本, 用于后端)
- pip (Python 包管理器)

## 项目设置与运行

### 1. 克隆仓库 (如果尚未克隆)

```bash
git clone <repository-url>
cd mindflow-reader
```

### 2. 前端 (Vue.js + Vite)

前端代码位于项目根目录。

**安装依赖:**

```bash
npm install
```

**开发模式 (热重载):**

```bash
npm run dev
```

默认运行在 `http://localhost:5173` (或 Vite 指定的其他端口)。

**类型检查, 编译和压缩 (生产模式):**

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 3. 后端 (Python + FastAPI)

后端代码位于 `backend/` 目录。

**a. 设置 Python 虚拟环境:**

```bash
# 进入后端目录 (可选，取决于您希望在哪里管理虚拟环境命令)
# cd backend

# 创建虚拟环境 (例如，在项目根目录下创建名为 pyenv 的虚拟环境)
python -m venv pyenv

# 激活虚拟环境
# Windows (在项目根目录运行):
pyenv\\Scripts\\activate
# macOS / Linux (在项目根目录运行):
source pyenv/bin/activate

# 返回项目根目录 (如果之前 cd 到 backend)
# cd ..
```

_重要提示: `.gitignore` 文件已配置忽略 `pyenv/` 和 `node_modules/` 目录，它们不应被提交到版本控制系统。_

**b. 安装 Python 依赖:**

后端依赖项应列在 `backend/requirements.txt` 文件中。
(如果 `backend/requirements.txt` 文件不存在，您需要根据 `mvp.md` 中的规划和您在后端实际使用的库来创建它。`global_packages.txt` 文件可能包含一些全局安装的包，但项目特定的依赖应在 `requirements.txt` 中明确列出。)

```bash
# 确保虚拟环境已激活
pip install -r backend/requirements.txt
```

**c. 启动后端 FastAPI 服务:**

假设您的 FastAPI 应用主文件位于 `backend/main.py`，应用实例名为 `app` (例如: `app = FastAPI()`)。

```bash
# 确保虚拟环境已激活
# 从项目根目录运行:
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 或者直接: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 完成后可 cd .. 返回项目根目录
```

后端服务通常会运行在 `http://localhost:8000`。

## `.gitignore` 配置

重要：`node_modules/` 目录 (前端依赖) 和 Python 虚拟环境目录 (如 `pyenv/`) 已被添加到 `.gitignore`，因此这些文件夹中的内容不会被提交到远程 Git 仓库。这是标准做法，以避免仓库臃肿，并确保每位协作者都在其本地环境中自行安装和管理这些依赖。

## 其他配置

- **TypeScript 支持:** 前端项目通过 `vue-tsc` (`npm run build` 的一部分) 进行类型检查。详情请参阅 `tsconfig.json` 和 `tsconfig.app.json`。
- **Vite 配置:** 前端构建和开发服务器的配置位于 `vite.config.ts`。
- **代码格式化:** 项目使用 Prettier 进行代码格式化，配置见 `.prettierrc.json`。

## 部署 (参考 `mvp.md`)

根据 `mvp.md` 的规划：

- **容器化:** 考虑使用 Docker。
- **前端托管:** Vercel 或 Netlify。
- **后端托管:** AWS Lambda 或 Google Cloud Run。

详细部署方案请参考 `mvp.md` 文档。
