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
../env/bin/python -m vagabond.khung.staging.phuc_vu_ci > "$VGB_ARTIFACTS/web.log" 2>&1 &
web_pid=$!
trap 'kill "$web_pid" 2>/dev/null || true; wait "$web_pid" 2>/dev/null || true' EXIT
for lan in $(seq 1 60); do
  kill -0 "$web_pid" || { cat "$VGB_ARTIFACTS/web.log"; exit 1; }
  if curl --silent --fail http://127.0.0.1:8000/api/method/ping > /dev/null; then break; fi
  sleep 1
done
curl --silent --fail http://127.0.0.1:8000/api/method/ping
cd "$GITHUB_WORKSPACE"
node vagabond/khung/staging/kiem_man.cjs
node vagabond/khung/staging/kiem_van_don.cjs
cd "$VGB_BENCH/sites"
../env/bin/python -m vagabond.khung.staging.van_don_ci
cd "$GITHUB_WORKSPACE"
node vagabond/khung/staging/kiem_nhan_hang.cjs
cd "$VGB_BENCH/sites"
../env/bin/python -m vagabond.khung.staging.nhan_hang_ci
cd "$GITHUB_WORKSPACE"
node vagabond/khung/staging/kiem_san_xuat.cjs
cd "$VGB_BENCH/sites"
../env/bin/python -m vagabond.khung.staging.san_xuat_ci
