# run_all_sql.py | 一键重跑 sql/01-09 并导出结果 CSV
# 用法：$env:MYSQL_PWD='你的密码'; python analysis/run_all_sql.py
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(ROOT, "sql")
EXPORTER = os.path.join(ROOT, "analysis", "run_sql_export.py")

files = sorted(f for f in os.listdir(SQL_DIR) if re.fullmatch(r"0[1-9]_.*\.sql", f))
if not files:
    print("no analysis sql files found (01-09)")
    sys.exit(1)
print("will run:", *files, sep="\n  ")
for f in files:
    print("=== running", f, "===", flush=True)
    subprocess.run([sys.executable, EXPORTER, f], check=True)
print("ALL SQL FILES DONE")