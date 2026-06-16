#!/usr/bin/env python3
"""Summarize charts/ and tables/ into summary.md + summary.csv."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

CHART_CAPTIONS = {
    "delay_trend": "近 N 周订单延迟率走势，用于判断履约是否恶化。",
    "delay_top_sellers": "延迟率最高的卖家 TOP 列表，优先巡检对象。",
    "bad_review_by_delay_bins": "按物流延迟天数分箱的差评率，验证「延迟越久差评越多」。",
    "seller_risk_scatter": "卖家订单量 vs 延迟率散点，颜色越深差评率越高。",
    "category_health_matrix": "品类规模与体验矩阵，识别规模大但体验差的类目。",
}

TABLE_HINTS = {
    "weekly_delay_trend": "按周延迟率趋势明细",
    "seller_risk_list": "卖家风险得分与等级清单",
    "problem_categories": "规模大且体验差的问题品类",
    "delay_by_seller": "卖家维度延迟率排名",
    "delay_by_category": "品类维度延迟率排名",
    "delay_by_region": "客户所在州/区域延迟率排名",
    "review_by_delay_bins": "延迟分箱与差评率交叉表",
}

CSV_COLUMNS = [
    "类别",
    "子类",
    "指标名称",
    "指标值",
    "对象ID",
    "说明",
    "数据来源",
    "优先级",
    "需人工确认",
]


def _pct(x: float) -> str:
    if pd.isna(x):
        return "N/A"
    return f"{x * 100:.1f}%"


def _row(
    category: str,
    sub: str,
    metric: str,
    value: str,
    obj_id: str = "",
    note: str = "",
    source: str = "",
    priority: str = "中",
    manual: str = "否",
) -> dict:
    return {
        "类别": category,
        "子类": sub,
        "指标名称": metric,
        "指标值": value,
        "对象ID": obj_id,
        "说明": note,
        "数据来源": source,
        "优先级": priority,
        "需人工确认": manual,
    }


def collect_summary_rows(report_dir: Path, tables: dict[str, pd.DataFrame]) -> list[dict]:
    rows: list[dict] = []
    report_name = report_dir.name

    # --- 执行摘要：核心指标 ---
    t = tables.get("weekly_delay_trend")
    if t is not None and len(t) >= 2 and "late_rate" in t.columns:
        cur, prev = t.iloc[-1], t.iloc[-2]
        lr, pr = cur.get("late_rate"), prev.get("late_rate")
        if pd.notna(lr) and pd.notna(pr):
            delta = (lr - pr) * 100
            trend = "上升" if delta > 0.5 else ("下降" if delta < -0.5 else "持平")
            rows.append(
                _row("执行摘要", "履约", "本周延迟率", _pct(lr), note=f"较前一周{trend}（{delta:+.1f}pp）",
                     source="tables/weekly_delay_trend.csv", priority="高")
            )
        if "bad_review_rate" in cur.index and pd.notna(cur["bad_review_rate"]):
            br = cur["bad_review_rate"]
            brp = prev.get("bad_review_rate")
            note = ""
            if pd.notna(brp):
                note = f"较前一周 {(br - brp) * 100:+.1f}pp"
            rows.append(
                _row("执行摘要", "体验", "本周差评率", _pct(br), note=note,
                     source="tables/weekly_delay_trend.csv", priority="高")
            )
        if "orders" in cur.index:
            rows.append(
                _row("执行摘要", "规模", "本周订单量", str(int(cur["orders"])),
                     source="tables/weekly_delay_trend.csv")
            )
        if "gmv" in cur.index:
            rows.append(
                _row("执行摘要", "规模", "本周GMV", f"{cur['gmv']:,.0f}",
                     source="tables/weekly_delay_trend.csv")
            )

    # --- 卖家风险 ---
    s = tables.get("seller_risk_list")
    if s is not None and len(s):
        rows.append(_row("执行摘要", "风险", "纳入评估卖家数", str(len(s)), source="tables/seller_risk_list.csv"))
        if "risk_level" in s.columns:
            n_high = (s["risk_level"].astype(str) == "高").sum()
            rows.append(
                _row("执行摘要", "风险", "高风险卖家数", str(int(n_high)),
                     source="tables/seller_risk_list.csv", priority="高" if n_high else "低")
            )
        top = s.sort_values("risk_score", ascending=False).iloc[0] if "risk_score" in s.columns else s.iloc[0]
        rows.append(
            _row("执行摘要", "风险", "风险最高卖家", str(top.get("risk_level", "")),
                 obj_id=str(top.get("seller_id", "")),
                 note=f"风险分 {top.get('risk_score', 0):.0f}" if pd.notna(top.get("risk_score")) else "",
                 source="tables/seller_risk_list.csv", priority="高", manual="是")
        )

    # --- 延迟卖家 TOP ---
    ds = tables.get("delay_by_seller")
    if ds is not None and len(ds):
        for i, r in ds.head(3).iterrows():
            rows.append(
                _row("数据明细", "卖家延迟", "延迟率", _pct(r.get("late_rate")),
                     obj_id=str(r.get("seller_id", "")),
                     note=f"订单量 {int(r.get('order_count', 0))}",
                     source="tables/delay_by_seller.csv",
                     priority="高" if i == ds.index[0] else "中", manual="是")
            )

    # --- 品类 / 区域 ---
    dc = tables.get("delay_by_category")
    if dc is not None and len(dc):
        t0 = dc.iloc[0]
        rows.append(
            _row("数据明细", "品类延迟", "延迟率", _pct(t0.get("late_rate")),
                 obj_id=str(t0.get("product_category_name", "")),
                 source="tables/delay_by_category.csv")
        )
    dr = tables.get("delay_by_region")
    if dr is not None and len(dr):
        t0 = dr.iloc[0]
        region_col = "customer_state" if "customer_state" in dr.columns else dr.columns[0]
        rows.append(
            _row("数据明细", "区域延迟", "延迟率", _pct(t0.get("late_rate")),
                 obj_id=str(t0.get(region_col, "")),
                 source="tables/delay_by_region.csv")
        )

    # --- 差评分箱 ---
    rb = tables.get("review_by_delay_bins")
    if rb is not None and len(rb):
        for _, r in rb.iterrows():
            rows.append(
                _row("数据明细", "差评归因", "差评率", _pct(r.get("bad_review_rate")),
                     obj_id=str(r.get("delay_bin", "")),
                     note=f"订单数 {int(r.get('orders', 0))}",
                     source="tables/review_by_delay_bins.csv",
                     priority="高" if r.get("bad_review_rate", 0) >= 0.5 else "中")
            )

    # --- 问题品类 ---
    pc = tables.get("problem_categories")
    if pc is not None:
        rows.append(
            _row("执行摘要", "品类", "问题品类数", str(len(pc)), source="tables/problem_categories.csv")
        )
        for _, r in pc.head(3).iterrows():
            rows.append(
                _row("数据明细", "问题品类", "优先级",
                     f"{r.get('priority', '')}",
                     obj_id=str(r.get("product_category_name", "")),
                     note=f"延迟{_pct(r.get('late_rate'))} 差评{_pct(r.get('bad_review_rate'))}",
                     source="tables/problem_categories.csv", manual="是")
            )

    # --- 图表清单 ---
    charts_dir = report_dir / "charts"
    if charts_dir.is_dir():
        for png in sorted(charts_dir.glob("*.png")):
            cap = CHART_CAPTIONS.get(png.stem, "业务分析图")
            rows.append(
                _row("图表解读", png.stem, "图表文件", png.name,
                     note=cap, source=f"charts/{png.name}", priority="中")
            )

    # --- 行动建议 ---
    actions = [
        ("对高延迟卖家开展履约复盘", "高延迟卖家", "tables/delay_by_seller.csv"),
        ("对高差评但低延迟卖家做商品/服务归因", "非物流差评", "tables/seller_risk_list.csv"),
        ("优化高延迟品类预计送达与描述", "品类治理", "tables/delay_by_category.csv"),
        ("处罚/下架/赔偿须人工审批", "合规", ""),
    ]
    for i, (act, sub, src) in enumerate(actions, 1):
        rows.append(
            _row("行动建议", sub, f"建议{i}", act, source=src, priority="高", manual="是")
        )

    rows.insert(0, _row("元信息", "报告", "报告目录", report_name, source=str(report_dir)))
    return rows


def summarize_dataframe(name: str, df: pd.DataFrame) -> list[str]:
    lines = [f"### {name}", "", TABLE_HINTS.get(name, ""), ""]
    if df.empty:
        lines.append("_（无数据）_")
        lines.append("")
        return lines

    if name == "weekly_delay_trend":
        if "late_rate" in df.columns and len(df) >= 2:
            latest, prev = df.iloc[-1], df.iloc[-2]
            lr, pr = latest.get("late_rate"), prev.get("late_rate")
            if pd.notna(lr) and pd.notna(pr):
                delta = (lr - pr) * 100
                trend = "上升" if delta > 0.5 else ("下降" if delta < -0.5 else "持平")
                lines.append(f"- 最近一周延迟率 **{_pct(lr)}**，较前一周 **{trend}**（{delta:+.1f}pp）")
        lines.append("")
        lines.append(df.tail(5).to_markdown(index=False))
    elif name == "seller_risk_list":
        high = df[df["risk_level"].astype(str) == "高"] if "risk_level" in df.columns else df.head(0)
        lines.append(f"- 共 **{len(df)}** 个卖家纳入评估，高风险 **{len(high)}** 个")
        lines.append("")
        lines.append(df.head(10).to_markdown(index=False))
    elif name == "problem_categories":
        lines.append(f"- 识别 **{len(df)}** 个问题品类" if len(df) else "- 未识别到问题品类")
        lines.append("")
        if len(df):
            lines.append(df.head(10).to_markdown(index=False))
    elif name == "review_by_delay_bins":
        if "bad_review_rate" in df.columns:
            worst = df.loc[df["bad_review_rate"].idxmax()]
            lines.append(f"- 差评率最高分箱：**{worst['delay_bin']}**（{_pct(worst['bad_review_rate'])}）")
        lines.append("")
        lines.append(df.to_markdown(index=False))
    elif name == "delay_by_seller" and len(df):
        t = df.iloc[0]
        lines.append(f"- 延迟最高：`{t.get('seller_id', '')}`，延迟率 {_pct(t.get('late_rate'))}")
        lines.append("")
        lines.append(df.head(10).to_markdown(index=False))
    elif name == "delay_by_category" and len(df):
        t = df.iloc[0]
        lines.append(f"- 延迟最高品类：`{t.get('product_category_name', '')}`，延迟率 {_pct(t.get('late_rate'))}")
        lines.append("")
        lines.append(df.head(10).to_markdown(index=False))
    elif name == "delay_by_region" and len(df):
        t = df.iloc[0]
        region_col = "customer_state" if "customer_state" in df.columns else df.columns[0]
        lines.append(f"- 延迟最高区域：`{t.get(region_col, '')}`，延迟率 {_pct(t.get('late_rate'))}")
        lines.append("")
        lines.append(df.head(10).to_markdown(index=False))
    else:
        lines.append(f"- 行数：**{len(df)}**")
        lines.append("")
        lines.append(df.head(10).to_markdown(index=False))

    lines.append("")
    return lines


def build_summary_csv(report_dir: Path, tables: dict[str, pd.DataFrame], csv_name: str = "summary.csv") -> Path:
    rows = collect_summary_rows(report_dir, tables)
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    out_path = report_dir / csv_name
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path


def build_summary_md(
    report_dir: Path,
    tables: dict[str, pd.DataFrame],
    table_files: list[Path],
    md_name: str = "summary.md",
    csv_name: str = "summary.csv",
) -> Path:
    charts_dir = report_dir / "charts"
    out_path = report_dir / md_name

    lines = [
        f"# 巡检结果总结 | {report_dir.name}",
        "",
        f"> 自动生成自 `{report_dir}` 下的 `tables/` 与 `charts/`。",
        f"> 结构化总结见 **`{csv_name}`**。",
        "",
        "## 执行摘要",
        "",
    ]

    bullets: list[str] = []
    t = tables.get("weekly_delay_trend")
    if t is not None and len(t) >= 2 and "late_rate" in t.columns:
        lr, pr = t.iloc[-1]["late_rate"], t.iloc[-2]["late_rate"]
        if pd.notna(lr) and pd.notna(pr):
            bullets.append(f"- 延迟率周趋势：{_pct(lr)}（前一周 {_pct(pr)}）")
    s = tables.get("seller_risk_list")
    if s is not None and "risk_level" in s.columns:
        n_high = (s["risk_level"].astype(str) == "高").sum()
        if n_high:
            bullets.append(f"- 高风险卖家 **{n_high}** 个，需优先巡检")
    pc = tables.get("problem_categories")
    if pc is not None and len(pc):
        bullets.append(f"- 问题品类 **{len(pc)}** 个")

    lines.extend(bullets or ["- _（见 summary.csv 与下方明细）_"])
    lines.extend(["", "## 图表解读", ""])

    if charts_dir.is_dir():
        for png in sorted(charts_dir.glob("*.png")):
            lines.extend([
                f"### {png.stem}",
                "",
                f"![{png.stem}](charts/{png.name})",
                "",
                f"**说明**：{CHART_CAPTIONS.get(png.stem, '业务分析图')}",
                "",
            ])
    else:
        lines.append("_（无 charts）_")

    lines.extend(["", "## 数据明细摘要", ""])
    for csv_path in table_files:
        lines.extend(summarize_dataframe(csv_path.stem, tables[csv_path.stem]))

    lines.extend([
        "",
        "## 行动建议（待人工确认）",
        "",
        "详见 `summary.csv` 中「行动建议」类别行。",
        "",
        "## 输出",
        "",
        f"- Markdown：`{md_name}`",
        f"- CSV：`{csv_name}`",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def build_summary(
    report_dir: Path,
    md_name: str = "summary.md",
    csv_name: str = "summary.csv",
) -> tuple[Path, Path]:
    report_dir = report_dir.resolve()
    tables_dir = report_dir / "tables"
    charts_dir = report_dir / "charts"

    if not tables_dir.is_dir() and not charts_dir.is_dir():
        raise FileNotFoundError(f"未找到 tables/ 或 charts/：{report_dir}")

    table_files = sorted(tables_dir.glob("*.csv")) if tables_dir.is_dir() else []
    tables = {p.stem: pd.read_csv(p) for p in table_files}

    csv_path = build_summary_csv(report_dir, tables, csv_name)
    md_path = build_summary_md(report_dir, tables, table_files, md_name, csv_name)
    return md_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description="总结 report 目录下 charts 与 tables")
    parser.add_argument("report_dir", help="含 charts/ 与 tables/ 的目录")
    parser.add_argument("--md", default="summary.md", help="Markdown 输出文件名")
    parser.add_argument("--csv", default="summary.csv", help="CSV 总结输出文件名（必选交付）")
    args = parser.parse_args()
    try:
        md_path, csv_path = build_summary(Path(args.report_dir), args.md, args.csv)
        print(f"OK: {md_path}")
        print(f"OK: {csv_path}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
