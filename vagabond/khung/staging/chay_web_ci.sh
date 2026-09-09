#!/usr/bin/env bash
# #257: lifecycle web CI riêng, dừng server kể cả khi kiểm hỏng.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == "true" ]] || { echo 'Chỉ dùng runner CI riêng.'; exit 1; }
: "${VGB_BENCH:?}"
: "${VGB_ARTIFACTS:?}"
: "${GITHUB_WORKSPACE:?}"
cd "$VGB_BENCH"
cd sites
export VGB_STAGING_VAN_DON=1
export VGB_STAGING_NHAN=1
export VGB_STAGING_SAN_XUAT=1
export VGB_STAGING_HANG_TANG=1
export VGB_STAGING_THANH_TOAN=1
../env/bin/python -m vagabond.khung.staging.phuc_vu_ci > "$VGB_ARTIFACTS/web.log" 2>&1 &
web_pid=$!
trap 'kill "$web_pid" 2>/dev/null || true; wait "$web_pid" 2>/dev/null || true' EXIT
for lan in $(seq 1 60); do
  kill -0 "$web_pid" || { cat "$VGB_ARTIFACTS/web.log"; exit 1; }
  if curl --silent --fail http://127.0.0.1:8000/api/method/ping > /dev/null; then break; fi
  sleep 1
done
curl --silent --fail http://127.0.0.1:8000/api/method/ping
hong=0
cd "$GITHUB_WORKSPACE"
node vagabond/khung/staging/kiem_man.cjs || hong=1
# Cac fixture dung ma rieng. Thu bang chung tung cua ke ca cua truoc do,
# nhung van tra ma loi cuoi; khong bo qua failure de lam CI xanh.
for cua in van_don nhan_hang san_xuat hang_tang thanh_toan; do
  cd "$GITHUB_WORKSPACE"
  node "vagabond/khung/staging/kiem_${cua}.cjs" || hong=1
  cd "$VGB_BENCH/sites"
  ../env/bin/python -m "vagabond.khung.staging.${cua}_ci" 2>&1 | tee "$VGB_ARTIFACTS/${cua}-kiem-db.log" || hong=1
done
# Kiểm bánh tự đồng bộ nguồn: chạy sau verifier vận đơn để log đối chiếu
# ba bước của vận đơn vẫn độc lập. Mọi lỗi vẫn làm gate đỏ.
cd "$GITHUB_WORKSPACE"
node vagabond/khung/staging/kiem_kiem_banh.cjs || hong=1
node vagabond/khung/staging/kiem_vai.cjs || hong=1
exit "$hong"
