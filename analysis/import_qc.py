# 导入 QC：orders 相关差异定位 + 全表行数核对
# 用法：ds_project 环境下运行
#   $env:MYSQL_PWD='你的密码'; python analysis/import_qc.py

import csv
import os
from collections import Counter

import pymysql

DB = dict(host="127.0.0.1", port=3306, user="root", password=os.environ["MYSQL_PWD"], database="olist")
CSV_DIR = "E:/03_Development/olist-data"

REVIEW_COLS = [
    "review_id", "order_id", "review_score", "review_comment_title",
    "review_comment_message", "review_creation_date", "review_answer_timestamp",
]


def norm(value):
    return None if value == "" else value


def csv_review_tuples():
    path = os.path.join(CSV_DIR, "olist_order_reviews_dataset.csv")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader)
        return [tuple(norm(v) for v in row) for row in reader]


def db_review_tuples(conn):
    cols = ", ".join(REVIEW_COLS)
    with conn.cursor() as cur:
        cur.execute(f"SELECT {cols} FROM order_reviews")
        return [tuple(None if v is None else str(v) for v in row) for row in cur.fetchall()]


def main():
    conn = pymysql.connect(**DB)
    csv_rows = csv_review_tuples()
    db_rows = db_review_tuples(conn)

    # 保留日期的字符串表示，避免 DATETIME 与字符串格式差异
    csv_c = Counter(csv_rows)
    db_c = Counter(db_rows)
    missing = csv_c - db_c
    extra = db_c - csv_c

    print(f"reviews: csv={len(csv_rows)} db={len(db_rows)}")
    print(f"csv rows not found in db (count): {sum(missing.values())}")
    for row, cnt in list(missing.items())[:5]:
        print("  MISSING:", row, "x", cnt)
    print(f"db rows not found in csv (count): {sum(extra.values())}")
    for row, cnt in list(extra.items())[:5]:
        print("  EXTRA  :", row, "x", cnt)

    conn.close()


if __name__ == "__main__":
    main()
