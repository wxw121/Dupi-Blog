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
| `render_hand_drawn_infographic.py` | 从 `prompts/*.md` 渲染 hand-drawn-edu 风格 PNG（1536×1024） |

## AI Agent 系列（214–254）配图

```bash
# 一键：生成 prompts + PNG + 正文引用
python scripts/scaffold_agent_infographics_214_254.py

# 仅重绘某个 slug 的 PNG
python scripts/render_hand_drawn_infographic.py --slug rag-to-agent-transition
```

## 单张流程图（非教程流水线）

仓库根目录 `diagram/gen_flowchart.py` 用 Pillow 生成 `image/python-tool-choice.png`，与上述 manifest 流程无关：

```bash
python diagram/gen_flowchart.py
```

## 说明

- 步骤 3 的多个 `copy-*.py` 为历史批次脚本；新图优先用 **`sync-assets-to-manifest.py`**（文件名与 manifest 一致即可）。
- 所有脚本路径均相对仓库根目录，可在任意机器 clone 后运行。
