# Olist 电商自动数据分析 Skills

基于 [Olist 巴西电商公开数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 的 **Cursor Agent Skills** 套件：自动生成经营巡检周报、延迟诊断、差评归因、卖家风险扫描、品类体验审计，并支持报告二次总结与 Word 导出。

适用于 Cursor IDE Agent 模式下的自动化数据分析工作流。

## 功能概览

| Skill | 说明 |
|-------|------|
| [weekly-ops-report](weekly-ops-report/SKILL.md) | 主流程：多表 Join → 周报 + 图表 + 明细表 |
| [delay-diagnosis](delay-diagnosis/SKILL.md) | 履约延迟趋势与卖家/品类/区域下钻 |
| [review-issue-locator](review-issue-locator/SKILL.md) | 差评与物流、价格、运费、品类、卖家关联分析 |
| [seller-risk-scan](seller-risk-scan/SKILL.md) | 高销量高风险卖家识别与风险评分 |
| [category-experience-audit](category-experience-audit/SKILL.md) | 规模大但体验差的问题品类审计 |
| [report-assets-summary](report-assets-summary/SKILL.md) | 基于 charts/tables 生成结构化 summary |
| [olist-data-reference](olist-data-reference/reference.md) | 表结构、Join 路径与指标口径（参考文档） |

推荐执行顺序：

```
数据校验 → weekly-ops-report → report-assets-summary → export_report_docx（可选）
```

## 安装

### 方式一：Cursor 远程导入（推荐，Cursor 2.4+）

1. 打开 Cursor Settings（`Ctrl+Shift+J` / `Cmd+Shift+J`）
2. 进入 **Rules** 标签页
3. 点击 **Add Rule** → **Remote Rule (GitHub)**
4. 填入本仓库 URL，选择需要的 skill 导入

### 方式二：手动复制到项目

将本仓库中各 skill 目录复制到项目的 `.cursor/skills/` 下：

```bash
git clone https://github.com/<your-org>/olist-data-analysis-skills.git
cp -r olist-data-analysis-skills/* your-project/.cursor/skills/
```

Windows PowerShell：

```powershell
git clone https://github.com/<your-org>/olist-data-analysis-skills.git
Copy-Item -Recurse olist-data-analysis-skills\* your-project\.cursor\skills\
```

### 方式三：全局安装（所有项目可用）

```bash
cp -r weekly-ops-report report-assets-summary delay-diagnosis review-issue-locator seller-risk-scan category-experience-audit olist-data-reference ~/.cursor/skills/
```

## 环境要求

- Python 3.10+
- Cursor IDE（Agent 模式）
- Olist CSV 数据文件（见下方数据准备）

### Python 依赖

```bash
pip install -r requirements.txt
```

| 包 | 用途 |
|----|------|
| pandas | 数据清洗、Join、聚合 |
| matplotlib / seaborn | 图表生成 |
| python-docx | Word 报告导出（可选） |
| scipy | 相关性分析（可选） |

### 中文字体

图表脚本依赖系统中文字体。Windows 默认使用微软雅黑；Linux/macOS 请安装 [Noto Sans CJK SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC)。

验证字体配置：

```bash
python weekly-ops-report/scripts/chart_zh_font.py
# 期望输出: OK: using font 'Microsoft YaHei'（或本机已安装的中文字体名）
```

## 数据准备

从 Kaggle 下载 Olist 数据集，将 CSV 放入同一目录。脚本会自动识别 `olist_` 前缀文件名：

| 逻辑名 | 常用文件名 | 必选 |
|--------|-----------|------|
| orders | olist_orders_dataset.csv | 是 |
| order_items | olist_order_items_dataset.csv | 是 |
| reviews | olist_order_reviews_dataset.csv | 是 |
| payments | olist_order_payments_dataset.csv | 推荐 |
| products | olist_products_dataset.csv | 推荐 |
| sellers | olist_sellers_dataset.csv | 可选 |
| customers | olist_customers_dataset.csv | 可选 |

表结构与指标口径详见 [olist-data-reference/reference.md](olist-data-reference/reference.md)。

## 快速开始

### 1. 校验数据表

```bash
python weekly-ops-report/scripts/validate_tables.py <data_dir>
```

### 2. 生成巡检周报

在 Cursor Agent 中描述需求，例如：

> 用 weekly-ops-report 分析 `./data` 目录，生成最近一周的经营巡检周报。

Agent 会按 [weekly-ops-report/SKILL.md](weekly-ops-report/SKILL.md) 流程产出 `report.md`、`charts/`、`tables/`。

也可手动调用子模块脚本（路径相对于本仓库根目录）：

```bash
python weekly-ops-report/scripts/validate_tables.py ./data
```

### 3. 总结报告资产

```bash
python report-assets-summary/scripts/summarize_report_assets.py ./reports/weekly_20180830
```

产出 `summary.csv`（结构化，必选）与 `summary.md`（可读版）。

### 4. 导出 Word（可选）

首次使用需生成模板：

```bash
python report-assets-summary/scripts/create_word_template.py
```

导出报告：

```bash
python report-assets-summary/scripts/export_report_docx.py ./reports/weekly_20180830
```

### 5. 生成 Skill 工具清单文档

```bash
python scripts/export_skills_catalog_docx.py
```

## 目录结构

```
.
├── weekly-ops-report/          # 主流程 skill
│   ├── SKILL.md
│   └── scripts/
│       ├── validate_tables.py
│       └── chart_zh_font.py
├── delay-diagnosis/
├── review-issue-locator/
├── seller-risk-scan/
├── category-experience-audit/
├── report-assets-summary/
│   ├── SKILL.md
│   └── scripts/
├── olist-data-reference/
│   └── reference.md
├── scripts/
│   └── export_skills_catalog_docx.py
├── requirements.txt
├── LICENSE
└── README.md
```

## 在 Cursor 中使用

Skills 安装后会被 Agent 自动发现。也可在 Agent 对话中手动调用：

```
/weekly-ops-report
```

或自然语言描述分析需求，Agent 会根据各 skill 的 `description` 字段自动匹配。

各 skill 的 `SKILL.md` 中包含完整执行流程、输入输出定义、失败条件与人工接管点。

## 输出示例

一次完整周报流程的典型产出：

```
reports/weekly_20180830/
├── report.md
├── charts/
│   ├── delay_trend.png
│   ├── delay_top_sellers.png
│   └── bad_review_by_delay_bins.png
├── tables/
│   ├── seller_risk_list.csv
│   ├── problem_categories.csv
│   └── weekly_delay_trend.csv
├── summary.csv
├── summary.md
└── inspection_report.docx    # 可选
```

## 注意事项

- 涉及卖家处罚、下架、赔偿等建议仅作参考，须人工确认后执行
- 分析窗口内有效订单数 < 30 时，结论可靠性不足，skill 会中止
- 图表中文显示须在作图前调用 `setup_chinese_chart()`，详见 weekly-ops-report skill

## 许可证

[MIT License](LICENSE)

## 致谢

数据来源于 [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)。
