"""F21: đột biến trong bản sao tạm, không sửa checkout, không gọi site."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

GOC = Path(__file__).resolve().parents[1]
FOCUS = """import sys
from vagabond.khung.kiem_thu import nen, thu_ton_don_web_593
nen.CA[:]=[(n,f) for n,f in nen.CA if n.startswith('F21')]
sys.exit(bool(nen.chay_het()))
"""
with tempfile.TemporaryDirectory(prefix="f21-dot-bien-") as td:
    goc=Path(td)/"repo"
    shutil.copytree(GOC,goc,ignore=shutil.ignore_patterns('.git','__pycache__','node_modules'))
    env=dict(os.environ,PYTHONPATH=str(goc),PYTHONPYCACHEPREFIX=str(Path(td)/"pycache"))
    py=[sys.executable,'-c',FOCUS]
    def chay(ten,cmd,hong):
        r=subprocess.run(cmd,cwd=goc,env=env,capture_output=True,text=True,timeout=120)
        if (r.returncode != 0) != hong:
            print(r.stdout+r.stderr)
            raise AssertionError(ten)
        print(ten,':',r.stdout.strip().splitlines()[-1])
    chay('Nền backend',py,False)
    for ten,tep,cu,moi,cmd in [
        ('Bỏ chặn tồn','vagabond/ton_don_web.py','if h["quantity"] > con:','if False:',py),
        ('Hỏi tồn trước nonce','vagabond/don_hang.py','trung = don_web.tim_trung(khoa)',
         'from vagabond import ton_don_web\n\tton_don_web.kiem(hang, ngay)\n\ttrung = don_web.tim_trung(khoa)',py),
    ]:
        p=goc/tep;s=p.read_text();assert cu in s,ten
        p.write_text(s.replace(cu,moi,1))
        try: chay(ten,cmd,True)
        finally: p.write_text(s)
