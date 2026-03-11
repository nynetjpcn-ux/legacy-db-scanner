"""
legacy_db_scanner.py
====================
レガシー経理システムのデータを自動スキャンし、
移行可否レポートを生成するツール。

対応形式: CSV / SQLite (.db) / Excel (.xlsx, .xls)
出力:     コンソール表示 + report.md（Markdownレポート）

使い方:
    python legacy_db_scanner.py --path ./data/
    python legacy_db_scanner.py --file sales.csv
"""

import os
import sys
import argparse
import csv
import sqlite3
import datetime

# オプション依存（なくても動く）
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


# ─────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────

def detect_encoding(filepath):
    """日本語ファイルの文字コードを自動判定"""
    encodings = ["utf-8", "utf-8-sig", "shift_jis", "cp932", "euc_jp"]
    for enc in encodings:
        try:
            with open(filepath, encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"  # フォールバック


def null_rate(values):
    """NULL率（空白・None）を計算"""
    if not values:
        return 0.0
    nulls = sum(1 for v in values if v is None or str(v).strip() == "")
    return round(nulls / len(values) * 100, 1)


def detect_type(values):
    """カラムの推定データ型"""
    non_null = [v for v in values if v is not None and str(v).strip() != ""]
    if not non_null:
        return "不明（全NULL）"
    date_hits = sum(1 for v in non_null if _is_date(str(v)))
    num_hits  = sum(1 for v in non_null if _is_number(str(v)))
    if date_hits / len(non_null) > 0.7:
        return "日付"
    if num_hits / len(non_null) > 0.7:
        return "数値"
    return "文字列"


def _is_date(s):
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            datetime.datetime.strptime(s.strip(), fmt)
            return True
        except ValueError:
            continue
    return False


def _is_number(s):
    s = s.replace(",", "").replace("¥", "").replace("￥", "").strip()
    try:
        float(s)
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────
# スキャナー本体
# ─────────────────────────────────────────

class TableReport:
    def __init__(self, name):
        self.name      = name
        self.row_count = 0
        self.columns   = []   # [{name, type, null_rate, sample}]
        self.warnings  = []

    def add_warning(self, msg):
        self.warnings.append(msg)


def scan_csv(filepath):
    enc = detect_encoding(filepath)
    report = TableReport(os.path.basename(filepath))

    with open(filepath, encoding=enc, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    report.row_count = len(rows)
    if not rows:
        report.add_warning("データが0件です")
        return report

    for col in rows[0].keys():
        values  = [r.get(col) for r in rows]
        nr      = null_rate(values)
        dtype   = detect_type(values)
        samples = [str(v) for v in values if v and str(v).strip()][:3]
        report.columns.append({
            "name": col, "type": dtype,
            "null_rate": nr, "sample": ", ".join(samples)
        })
        if nr > 30:
            report.add_warning(f"カラム「{col}」のNULL率が{nr}%と高い")

    return report


def scan_sqlite(filepath):
    reports = []
    conn = sqlite3.connect(filepath)
    cur  = conn.cursor()

    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    for table in tables:
        report = TableReport(table)
        rows   = cur.execute(f"SELECT * FROM [{table}]").fetchall()
        cols   = [d[0] for d in cur.execute(
            f"SELECT * FROM [{table}] LIMIT 0").description or []]

        report.row_count = len(rows)
        for i, col in enumerate(cols):
            values  = [r[i] for r in rows]
            nr      = null_rate(values)
            dtype   = detect_type(values)
            samples = [str(v) for v in values if v is not None][:3]
            report.columns.append({
                "name": col, "type": dtype,
                "null_rate": nr, "sample": ", ".join(samples)
            })
            if nr > 30:
                report.add_warning(f"カラム「{col}」のNULL率が{nr}%と高い")
        reports.append(report)

    conn.close()
    return reports


def scan_excel(filepath):
    if not EXCEL_SUPPORT:
        print("⚠ openpyxl が未インストールです: pip install openpyxl")
        return []

    reports = []
    wb = openpyxl.load_workbook(filepath, data_only=True)

    for sheet_name in wb.sheetnames:
        ws     = wb[sheet_name]
        report = TableReport(sheet_name)
        data   = list(ws.values)
        if not data:
            continue

        headers = [str(h) if h is not None else f"col_{i}"
                   for i, h in enumerate(data[0])]
        rows    = data[1:]
        report.row_count = len(rows)

        for i, col in enumerate(headers):
            values  = [r[i] if i < len(r) else None for r in rows]
            nr      = null_rate(values)
            dtype   = detect_type(values)
            samples = [str(v) for v in values if v is not None][:3]
            report.columns.append({
                "name": col, "type": dtype,
                "null_rate": nr, "sample": ", ".join(samples)
            })
            if nr > 30:
                report.add_warning(f"カラム「{col}」のNULL率が{nr}%と高い")
        reports.append(report)

    return reports


# ─────────────────────────────────────────
# レポート出力
# ─────────────────────────────────────────

def print_report(reports):
    if not isinstance(reports, list):
        reports = [reports]
    for r in reports:
        print(f"\n{'='*60}")
        print(f"  テーブル/シート: {r.name}  ({r.row_count:,} 件)")
        print(f"{'='*60}")
        print(f"  {'カラム名':<20} {'型':<8} {'NULL率':>7}  サンプル")
        print(f"  {'-'*56}")
        for c in r.columns:
            print(f"  {c['name']:<20} {c['type']:<8} {c['null_rate']:>6}%  {c['sample'][:30]}")
        if r.warnings:
            print(f"\n  ⚠ 警告:")
            for w in r.warnings:
                print(f"    - {w}")


def save_markdown(reports, output="report.md"):
    if not isinstance(reports, list):
        reports = [reports]

    lines = [
        "# レガシーDB スキャンレポート",
        f"\n生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"\n対象テーブル数: {len(reports)}\n",
    ]
    for r in reports:
        lines += [
            f"## {r.name}",
            f"\n- レコード件数: **{r.row_count:,} 件**",
            f"- カラム数: {len(r.columns)}\n",
            "| カラム名 | 型 | NULL率 | サンプル |",
            "|---|---|---|---|",
        ]
        for c in r.columns:
            lines.append(
                f"| {c['name']} | {c['type']} | {c['null_rate']}% | {c['sample'][:40]} |"
            )
        if r.warnings:
            lines.append("\n**⚠ 警告**\n")
            for w in r.warnings:
                lines.append(f"- {w}")
        lines.append("")

    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 レポートを保存しました: {output}")


# ─────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────

def scan_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return [scan_csv(filepath)]
    elif ext in (".db", ".sqlite", ".sqlite3"):
        return scan_sqlite(filepath)
    elif ext in (".xlsx", ".xls"):
        return scan_excel(filepath)
    else:
        print(f"⚠ 未対応の形式です: {ext}")
        return []


def scan_directory(dirpath):
    all_reports = []
    for fname in os.listdir(dirpath):
        fpath = os.path.join(dirpath, fname)
        if os.path.isfile(fpath):
            results = scan_file(fpath)
            all_reports.extend(results)
    return all_reports


def main():
    parser = argparse.ArgumentParser(
        description="レガシーDBスキャナー｜データ移行前の品質チェックツール"
    )
    parser.add_argument("--file", help="スキャンするファイルのパス")
    parser.add_argument("--path", help="スキャンするフォルダのパス")
    parser.add_argument("--output", default="report.md", help="出力レポートのファイル名")
    args = parser.parse_args()

    if not args.file and not args.path:
        parser.print_help()
        sys.exit(1)

    reports = []
    if args.file:
        reports = scan_file(args.file)
    elif args.path:
        reports = scan_directory(args.path)

    if not reports:
        print("スキャン対象が見つかりませんでした。")
        sys.exit(1)

    print_report(reports)
    save_markdown(reports, args.output)


if __name__ == "__main__":
    main()
