# Bo phong Vagabond Sans

Bon tep `VagabondSans-*.ttf` trong thu muc nay la ban sua ten cua
**Liberation Sans 2.1.5**, lay tu goi `fonts-liberation2`.

## Vi sao mang phong theo trong ung dung

Server Frappe Cloud da co Liberation Sans san, nhung la **ban 1.07.4**.
Ban do khong co cac chu cai tieng Viet co dau thanh (bang Unicode Latin
Extended Additional, U+1EA0 den U+1EFF). Khi in hop dong, wkhtmltopdf
lay Liberation Sans cho chu khong dau roi tu dong muon **DejaVu Sans**
rieng cho cac chu co dau. Hai kieu chu lech nhau ngay trong cung mot tu,
va do dung la loi phong ma anh Viet bao.

Ban 2.1.5 co du tieng Viet. Do cac chi so chieu ngang cua Liberation Sans
trung khop voi Arial nen chu in ra dan trang y het Arial.

## Vi sao doi ten

Neu giu nguyen ten ho `Liberation Sans` thi tren server se co hai ban
trung ten, fontconfig chon ban nao la chuyen hen xui. Doi ten ho thanh
`Vagabond Sans` thi khong con nham lan.

Ngoai ra giay phep SIL Open Font License 1.1 **bat buoc** ban sua doi
khong duoc dung ten danh rieng "Liberation". Nen viec doi ten vua la nhu
cau ky thuat vua la dieu giay phep doi hoi.

## Giay phep

Liberation Fonts, ban quyen (c) 2012 Red Hat, Inc., du lieu so hoa
(c) 2010 Google Corporation. Phat hanh theo SIL Open Font License 1.1.
Toan van giay phep o `OFL.txt` canh day.

## Dung lai bo phong

	python3 dung_phong.py

Chi chay khi can nang len ban Liberation moi hon. Binh thuong khong dong
den.
