# Vagabond

App Frappe cho cong dat banh cua The Vagabond Patisserie.

Lam ba viec ma Server Script khong lam duoc, vi Server Script bi chan khong
goi duoc HTTP ra ngoai: hoi phi giao Ahamove, goi y dia chi Goong, va tra
khach cu tren Pancake theo so dien thoai. Ca ba deu can giu khoa o may chu.

## Cai dat

    bench get-app https://github.com/thevagabondpatisserie/vagabond
    bench --site <ten-site> install-app vagabond

Tren Frappe Cloud: Bench -> Apps -> Add App -> dan dia chi repo.

## Cau hinh

Mo **Vagabond Settings** trong ERPNext roi dien khoa Goong, Ahamove, Pancake
va toa do bep. Ba truong khoa deu la kieu Password nen Frappe ma hoa khi luu.

Toa do bep: 10.799141 / 106.669251

## Cac endpoint

Deu cho khach vang lai goi va deu co gioi han so lan goi moi phut, vi moi
lan goi la ton tien that.

| Duong dan | Viec |
|---|---|
| `vagabond.api.goi_y_dia_chi?q=` | goi y dia chi, uu tien quanh bep |
| `vagabond.api.chi_tiet_dia_chi?place_id=` | doi place_id thanh toa do |
| `vagabond.api.phi_giao?addr=` | phi giao da cong phu thu |
| `vagabond.api.tra_khach?phone=` | dia chi cu tren Pancake, da che so nha |
| `vagabond.api.tra_mst?mst=` | ten va dia chi cong ty theo ma so thue |
