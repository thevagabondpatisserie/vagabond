#!/usr/bin/env python3
"""Bằng chứng trình duyệt thật (Chromium): nút và chữ thường cùng bộ chữ (v636).
Cách dùng: python3 cong_cu/kiem_font_nut_636.py vagabond/public/js/app_bep.js
Dựng trang có quy tắc thật của Frappe đọc trên site (html,body opsz 24; reboot
button font-family inherit) + toàn bộ CSS của app lấy từ app_bep.js, vẽ chip
bằng đúng khuôn posChipNut, so mọi thuộc tính chữ của nút với một div cạnh bên."""
import re, sys, json, subprocess
from playwright.sync_api import sync_playwright
app = open(sys.argv[1], encoding='utf-8').read()
css = re.search(r"var CSS = `([\s\S]*?)`;", app).group(1)
chip = subprocess.run(['node', '-e', '''
const s=require("fs").readFileSync(process.argv[1],"utf8");
const m=s.match(/function posChipNut\\([\\s\\S]*?\\n\\}/)[0]; eval(m);
process.stdout.write(posChipNut('data-dscc="tt|"','Mọi điểm nhận',true,false,'#4338ca'));''', sys.argv[1]], capture_output=True, text=True).stdout
frappe = 'html,body{font-family:-apple-system,"system-ui",sans-serif;font-variation-settings:"opsz" 24}body{letter-spacing:.02em;-webkit-font-smoothing:antialiased}button,input,optgroup,select,textarea{margin:0;font-family:inherit;font-size:inherit;line-height:inherit}'
html = '<style>%s</style><style>%s</style><div id=d style="font-size:14px;font-weight:800">Mọi điểm nhận</div>%s' % (frappe, css, chip)
P = ['font-family','font-style','font-stretch','font-variation-settings','font-optical-sizing','font-feature-settings','-webkit-font-smoothing']
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.set_content(html)
    r = pg.evaluate("P=>{const a=getComputedStyle(document.querySelector('button')),d=getComputedStyle(document.getElementById('d'));return P.filter(k=>a.getPropertyValue(k)!==d.getPropertyValue(k)).map(k=>k+': nut='+a.getPropertyValue(k)+' | chu='+d.getPropertyValue(k))}", P)
    b.close()
print(json.dumps(r, ensure_ascii=False)); sys.exit(1 if r else 0)
