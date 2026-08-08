# 脚本生成报告（本地产物）

本目录存放审计、扫描等脚本的**输出报告**，默认 **不提交**（见根目录 `.gitignore`）。

| 子目录 / 文件 | 来源 | 说明 |
|---------------|------|------|
| `audit/` | `scripts/_audit_*.py` 等 | 教程批量审计 JSON（历史多轮 after-50 / round7 等） |
| `body-term-first-use-scan.md` | `scan_body_term_first_use.py --write-report` | Agent 214–254 正文首现术语扫描 |
| `scan_61plus_result.txt` | 一次性厚度扫描 | 教程 61+ 字数统计（历史） |

重新生成示例：

```bash
python scripts/scan_body_term_first_use.py --write-report scripts/reports/body-term-first-use-scan.md
python scripts/_audit_image_usage.py    # → scripts/reports/audit/audit-image-usage-report.json
```
