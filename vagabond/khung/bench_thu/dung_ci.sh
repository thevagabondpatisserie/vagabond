#!/usr/bin/env bash
# Chi dung trong runner GitHub dung mot lan. Khong nhan site san xuat.
set -euo pipefail
: "${GITHUB_ACTIONS:?Chi chay tren GitHub Actions}"
: "${VGB_BENCH:?}"
: "${VGB_ARTIFACTS:?}"
mkdir -p "$VGB_ARTIFACTS"
exec > >(tee "$VGB_ARTIFACTS/dung-bench.log") 2>&1
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends libmariadb-dev pkg-config libldap2-dev libsasl2-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 redis-tools
python -m pip install 'frappe-bench @ git+https://github.com/frappe/bench.git@c9d12503d9d7fbfd94086c3de3cd4ac23dd44823'
npm install --global yarn@1.22.22
nguon="$RUNNER_TEMP/vgb-core"
mkdir -p "$nguon"
git clone --branch version-16 --single-branch https://github.com/frappe/frappe.git "$nguon/frappe"
git -C "$nguon/frappe" checkout -b vgb-pinned f33ac3f00ab818e21b25ddbec93efb653fd9aa1b
git clone --branch version-16 --single-branch https://github.com/frappe/erpnext.git "$nguon/erpnext"
git -C "$nguon/erpnext" checkout -b vgb-pinned de591661b9ba0bd3f62ac25b99b5c85c723515f6
bench init "$VGB_BENCH" --python "$(command -v python)" --frappe-path "$nguon/frappe" --frappe-branch vgb-pinned --skip-assets --skip-redis-config-generation --no-backups
cd "$VGB_BENCH"
bench set-config -g redis_cache redis://127.0.0.1:6379/0
bench set-config -g redis_queue redis://127.0.0.1:6379/1
bench set-config -g redis_socketio redis://127.0.0.1:6379/2
# Banking build đọc ../../../sites theo vị trí vật lý. Clone vào apps,
# không soft-link ra ngoài bench khiến Vite tìm nhầm common_site_config.
bench get-app --skip-assets --branch vgb-pinned "$nguon/erpnext"
bench get-app --skip-assets --soft-link "$GITHUB_WORKSPACE"
bench new-site bench-ci.localhost --db-host 127.0.0.1 --db-port 3306 --mariadb-user-host-login-scope '%' --db-root-password bench-only-password --admin-password bench-only-admin
bench --site bench-ci.localhost set-config vagabond_bench_thu 1
bench --site bench-ci.localhost set-config mute_emails 1
bench --site bench-ci.localhost set-config disable_scheduler 1
bench --site bench-ci.localhost set-config server_script_enabled 1
bench --site bench-ci.localhost install-app erpnext
bench --site bench-ci.localhost install-app vagabond
bench --site bench-ci.localhost execute vagabond.khung.bench_thu.nen_bench.dung
bench --site bench-ci.localhost execute vagabond.khung.bench_thu.nang_cap_ci.chuan_bi
for luot in 1 2; do
  bench --site bench-ci.localhost migrate 2>&1 | tee "$VGB_ARTIFACTS/migrate-$luot.log"
done
bench --site bench-ci.localhost execute vagabond.khung.bench_thu.nang_cap_ci.doi_chieu 2>&1 | tee "$VGB_ARTIFACTS/doi-chieu-migrate.log"
bench build --apps frappe,erpnext,vagabond --force 2>&1 | tee "$VGB_ARTIFACTS/build-assets.log"
python - <<'PY'
import json, os, subprocess
from pathlib import Path
ket = {ten: subprocess.check_output(['git', '-C', noi, 'rev-parse', 'HEAD'], text=True).strip()
       for ten, noi in [('vagabond', os.environ['GITHUB_WORKSPACE']), ('frappe', 'apps/frappe'), ('erpnext', 'apps/erpnext')]}
Path(os.environ['VGB_ARTIFACTS'], 'sha.json').write_text(json.dumps(ket, indent=2))
print(json.dumps(ket))
PY
