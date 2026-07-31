# Vagabond

App Frappe cho cong dat banh cua The Vagabond Patisserie.

Lam ba viec ma Server Script khong lam duoc, vi Server Script bi chan khong
goi duoc HTTP ra ngoai: hoi phi giao Ahamove, goi y dia chi Goong, va tra
khach cu tren Pancake theo so dien thoai. Ca ba deu can giu khoa o may chu.

## Cai dat

    bench get-app https://github.com/thevagabondpatisserie/vagabond
    bench --site <ten-site> install-app vagabond

Tren Frappe Cloud: Bench -> Apps -> Add App -> dan dia chi repo. Deploy xong
app moi nam tren bench, phai vao Sites -> site -> Apps -> Install App nua.

## Cau hinh

Mo **Vagabond Settings** trong ERPNext roi dien khoa Goong, Ahamove, Pancake
va toa do bep. Ba truong khoa deu la kieu Password nen Frappe ma hoa khi luu.

Toa do bep: 10.799141 / 106.669251

## Cac endpoint

Deu cho khach vang lai goi va deu co gioi han so lan goi moi phut, vi moi
lan goi la ton tien that.

| Duong dan | Viec |
|---|---|
| `vagabond.dia_chi.goi_y_dia_chi?q=` | goi y dia chi, uu tien quanh bep |
| `vagabond.dia_chi.chi_tiet_dia_chi?place_id=` | doi place_id thanh toa do |
| `vagabond.giao_hang.phi_giao?addr=` | phi giao da cong phu thu |
| `vagabond.api.tra_khach?phone=` | dia chi cu tren Pancake, da che so nha |
| `vagabond.api.tra_mst?mst=` | ten va dia chi cong ty theo ma so thue |

Chua dien khoa thi cac duong dan tren tra ve `ly_do: chua_dien_khoa_...`
chu khong bao loi 500.

## Endpoint mo thi phai tu loc lai du lieu

`tra_khach` chi tra ve dia chi nao co dung so dien thoai vua tra. Pancake
tim kiem long tay, tra ve ca khach khac; khong loc lai la lo ten va dia chi
nha cua nguoi ta cho bat ky ai go bua mot so.
