# 通用 SQL 导出：把 sql/ 下的脚本按语句拆分执行，SELECT 结果写入 results/
# 用法（ds_project 环境）：
#   $env:MYSQL_PWD='你的密码'; python analysis/run_sql_export.py sql/01_大盘总览.sql

import csv
import os
import re
import sys

import pymysql

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = dict(host="127.0.0.1", port=3306, user="root", password=os.environ["MYSQL_PWD"], database="olist")


def split_statements(text):
    # 本项目 SQL 脚本里分号只出现在语句结尾，按分号拆分足够
    return [s.strip() for s in text.split(";") if s.strip()]


def main():
    if len(sys.argv) < 2:
        print("usage: python analysis/run_sql_export.py sql/xxx.sql")
        return 1
    sql_path = os.path.join(ROOT, sys.argv[1])
    base = os.path.splitext(os.path.basename(sql_path))[0]
    out_dir = os.path.join(ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)

    with open(sql_path, encoding="utf-8") as fh:
        statements = split_statements(fh.read())

    conn = pymysql.connect(**DB)
    written = 0
    with conn.cursor() as cur:
        for idx, stmt in enumerate(statements, start=1):
            cur.execute(stmt)
            if cur.description is None:
                continue
            rows = cur.fetchall()
            out_path = os.path.join(out_dir, f"{base}_q{idx}.csv")
            with open(out_path, "w", encoding="utf-8-sig", newline="") as out:
                writer = csv.writer(out)
                writer.writerow([d[0] for d in cur.description])
                writer.writerows(rows)
            print(f"wrote {out_path}: {len(rows)} rows")
            written += len(rows)
    conn.close()
    print(f"done, total {written} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
