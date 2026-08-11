# 博客配图维护脚本

本目录脚本用于维护教程 Markdown 与 `image/` 配图，**读者阅读教程不需要运行**。仅在新增/修改教程、批量换图时使用。

## 前置

- Python 3.10+
- 仓库根目录下存在 `image/_inventory.json`、`image/manifest.json`（由步骤 1 生成或已提交）
- AI 生成图放入 **`assets/`**（仓库根目录，已 gitignore），或设置环境变量：

```powershell
$env:BLOG_ASSETS_DIR = "路径\到\你的\生成图目录"
```

## 推荐调用顺序

```
1. build-infographic-manifest.py   扫描教程，更新 manifest（含 prompt）
        ↓
2. （外部）按 manifest 用 baoyu-infographic 等生成 PNG → 放入 assets/
        ↓
3. sync-assets-to-manifest.py      按 manifest 文件名自动复制（首选）
   或 copy-generated-images.py     按固定映射表复制（asyncio 等首批）
   或 copy-custom-assets.py        REST / WebSocket 等自定义映射
   或 copy-latest-batch.py         单批 SSE / WebSocket 补图
   或 copy-final-batch.py          剩余批次补图
        ↓
4. update-markdown-images.py       将 MD 中 ASCII 图块替换为 ![...](image/...)
        ↓
5. fix-markdown-image-paths.py     按 manifest 修正 MD 路径与 alt
   或 align-paths.py               对齐 inventory ↔ manifest ↔ MD（与上类似）
        ↓
6. dedupe-markdown-images.py       删除重复/过期图片引用行
```

## 各脚本说明

| 脚本 | 作用 |
|------|------|
| `build-infographic-manifest.py` | 从 `_inventory.json` 生成 `manifest.json` |
| `sync-assets-to-manifest.py` | `assets/` 中 PNG 按 manifest  basename 匹配复制到 `image/` |
| `copy-generated-images.py` | asyncio 等早期图的硬编码映射复制 |
| `copy-custom-assets.py` | REST API / WebSocket 等自定义映射复制 |
| `copy-latest-batch.py` | 单批 SSE、WebSocket 补图 |
| `copy-final-batch.py` | 其余批次补图 |
| `update-markdown-images.py` | ASCII 示意图 → Markdown 图片引用 |
| `fix-markdown-image-paths.py` | 修正 MD 与 inventory 中的 `img_path`、alt |
| `align-paths.py` | inventory / manifest / MD 三方路径对齐 |
| `dedupe-markdown-images.py` | 清理 `1–9.*.md` 中重复或错误图片行 |
| `scaffold_agent_infographics_214_254.py` | 为 AI Agent 教程 214–254 生成 README、prompts、PNG 并插入正文引用 |
| `regen_agent_infographics_214_254.py` | 增强 214–254 prompts、生成 baoyu-image-gen 批量 JSON |
| `export_agent_gen_manifest.py` | 导出紧凑生成描述 manifest |
| `apply_gen_images.py` | 将 `assets/` 中生成的 PNG 复制到 `image/{slug}/`（支持 `index:filename` 批量参数） |
| `status_agent_infographics.py` | 检查 214–254 系列 AI 图 vs 占位图进度 |
| `render_hand_drawn_infographic.py` | **已废弃占位渲染**（Pillow 色块，非 hand-drawn-edu） |
| `scan_body_term_first_use.py` | Agent 214–254 正文首现术语扫描 → `scripts/reports/` |
| `spot_check_agent_tutorials.py` | Agent 教程结构/术语/02-flow 一键验收 |
| `generate_interview_questions.py` | 从教程技术内容生成 `docs/interview/*` **开发向**面试题 |
| `interview_question_config.py` | 面试题热点篇目与题量配置 |

生成报告与本地 manifest 默认不提交，见 [`reports/README.md`](reports/README.md) 与根目录 `.gitignore`。

## AI Agent 系列（214–254）配图

风格约定见 `.baoyu-skills/baoyu-infographic/EXTEND.md`：`hand-drawn-edu` · 16:9 · 中文。

```bash
# 一键：生成/更新 prompts + README + 正文引用（不渲染 PNG）
python scripts/scaffold_agent_infographics_214_254.py

# 增强 prompts 并生成 baoyu-image-gen 批量文件
python scripts/regen_agent_infographics_214_254.py --enhance-prompts --write-batch

# AI 批量出图（需配置 API Key，见 baoyu-image-gen EXTEND.md）
npx -y bun ~/.codex/skills/baoyu-image-gen/scripts/main.ts --batchfile scripts/_agent_batch_214_254.json --jobs 4

# 将 assets/ 中的生成图复制到 image/ 并更新进度
python scripts/apply_gen_images.py

# 检查重生成进度
python scripts/status_agent_infographics.py
```

**勿用** `render_hand_drawn_infographic.py`——该脚本仅生成 Pillow 色块占位图，不符合 `hand-drawn-edu` 风格。

> **注意**：多个 slug 共用 `03-concept-map.png` 文件名。批量生成到 `assets/` 时请使用唯一名（如 `03-concept-map-{slug}.png`），再用 `apply_gen_images.py 索引:assets文件名` 复制到目标路径。

## 单张流程图（非教程流水线）

仓库根目录 `diagram/gen_flowchart.py` 用 Pillow 生成 `image/python-tool-choice.png`，与上述 manifest 流程无关：

```bash
python diagram/gen_flowchart.py
```

## 说明

- 步骤 3 的多个 `copy-*.py` 为历史批次脚本；新图优先用 **`sync-assets-to-manifest.py`**（文件名与 manifest 一致即可）。
- 所有脚本路径均相对仓库根目录，可在任意机器 clone 后运行。
