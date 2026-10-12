"""#310: asset có cache immutable một năm; đổi nội dung phải đổi URL trong HTML."""
from pathlib import Path
import hashlib
import re

GOC = Path(__file__).resolve().parent
TRANG = ('vagabond/trang/banh.html', 'vagabond/www/thanh-vien.html', 'vagabond/www/dat-ban.html', 'vagabond/www/bien-tap-web.html', 'vagabond/www/banh/xong.html', 'vagabond/www/chinh-sach.html')
TEP = tuple(p.name for p in (GOC / 'vagabond/public/web_order').iterdir() if p.suffix in ('.css', '.js'))


def dung():
    for ten in TRANG:
        p = GOC / ten
        s = p.read_text()
        for tep in TEP:
            duong = '/assets/vagabond/web_order/' + tep
            bam = hashlib.sha256((GOC / 'vagabond/public/web_order' / tep).read_bytes()).hexdigest()[:12]
            s = re.sub(re.escape(duong) + r'(?:\?v=[a-f0-9]+)?(?=[\"\'])', duong + '?v=' + bam, s)
        p.write_text(s)


if __name__ == '__main__':
    dung()
