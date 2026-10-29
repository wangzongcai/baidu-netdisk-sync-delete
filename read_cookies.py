# -*- coding: utf-8 -*-
"""只读探测：列出主 Edge Default profile 里 pan.baidu.com 相关的 cookie 键名(不打印值)。"""
import sqlite3, os

DB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies")
if not os.path.exists(DB):
    print("no cookies db at", DB); raise SystemExit

con = sqlite3.connect(DB)
con.execute("PRAGMA query_only=ON")
cur = con.cursor()
# cookie 表常见列: host_key,name,encrypted_value
try:
    rows = cur.execute("SELECT host_key,name,length(encrypted_value) FROM cookies ORDER BY host_key").fetchall()
except Exception as e:
    # 可能是 cookies 表加锁，尝试事务只读
    con.commit()
    rows = cur.execute("SELECT host_key,name,length(encrypted_value) FROM cookies ORDER BY host_key").fetchall()
baidu = [r for r in rows if "baidu" in (r[0] or "").lower()]
print(f"总 cookie 行: {len(rows)}，其中 baidu 相关: {len(baidu)}")
for hk, name, ln in baidu:
    print(f"  {hk:45s} | {name:30s} | len={ln}")
con.close()