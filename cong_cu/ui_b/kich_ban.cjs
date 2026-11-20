/* Danh sách màn máy chụp mở được. Mỗi màn: tên, cách mở, và đã chuyển sang giao diện
 * mới hay chưa (chua_chuyen: true thì khi bật chỉ ghi "Chưa chuyển", không chấm chuẩn mới). */
'use strict';
module.exports = [
  { ten: 'trang-chu', cho: '.gwrap' },
  { ten: 'dang-nhap', cho: '#vgb .lgw', du_lieu: { 'frappe.auth.get_logged_user': { message: 'Guest' } } },
  { ten: 'tai-khoan', cho: '.gwrap', mo: async function (t) { await t.click('#vgbAcc'); await t.waitForSelector('#acOut'); } },
  { ten: 'nhom-ban-hang', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="BH"]'); await t.waitForSelector('#vgbBack'); } },
  { ten: 'hop-xac-nhan', cho: '.gwrap', mo: async function (t) { await t.click('#vgbAcc'); await t.waitForSelector('#acOut'); await t.click('#acOut'); await t.waitForSelector('.sh [data-y]'); } },
  { ten: 'nhom-khach-hang', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="KHG"]'); await t.waitForSelector('#vgbBack'); } },
  { ten: 'viec-can-lam', cho: '.gwrap', chua_chuyen: true, mo: async function (t) { await t.click('.gt.vcl'); await t.waitForSelector('#vgbBack'); await t.waitForTimeout(300); } },
  { ten: 'tim-nghiep-vu', cho: '.gwrap', mo: async function (t) { await t.fill('.vgbtim', 'công nợ'); await t.waitForSelector('#vgbKQ .hub'); } },
  { ten: 'ghim-da-co', cho: '.vgbgo', du_lieu: { 'vagabond.ghim.lay': { message: { ghim: ['POS', 'VD', 'KK', 'CN'] } } } },
  { ten: 'so-tay', cho: '.gwrap', chua_chuyen: true, mo: async function (t) { await t.click('.gt[data-nhom="SOTAY"]'); await t.waitForSelector('#vgbBack'); await t.waitForTimeout(300); } },
  /* Đầu trang đủ bốn nút với tiêu đề dài: ca khó của điện thoại hẹp (bản 4 mục 4). Thân màn thuộc PR 5. */
  { ten: 'dau-trang-bon-nut', cho: '.gwrap', chua_chuyen: true, mo: async function (t) {
    await t.click('.gt[data-nhom="KHAC"]'); await t.waitForSelector('[data-go="CDTDH"]'); await t.click('[data-go="CDTDH"]'); await t.waitForSelector('#vgbAct'); await t.waitForTimeout(300); } },
  /* Màn thuộc PR 2, chưa chuyển: máy chụp vẫn mở để lấy đường chuẩn và bắt lỗi do nền chung gây ra. */
  { ten: 'tinh-tien-chon-quay', cho: '.gwrap', chua_chuyen: true, mo: async function (t) {
    await t.click('.gt[data-nhom="BH"]'); await t.waitForSelector('[data-go="POS"]'); await t.click('[data-go="POS"]'); await t.waitForTimeout(500); } },
  { ten: 'nhom-ke-toan', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="KT"]'); await t.waitForSelector('#vgbBack'); } }
];
