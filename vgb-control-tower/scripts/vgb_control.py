#!/usr/bin/env python3
"""Fail-closed coordination checks for the Vagabond repository."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def git(repo, *args):
    p = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def path_locks(repo):
    return repo / "vgb-control-tower" / "state" / "locks.json"


def load_locks(repo):
    try:
        data = json.loads(path_locks(repo).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("Không đọc được vgb-control-tower/state/locks.json: " + str(error))
    if not isinstance(data.get("locks"), list):
        raise RuntimeError("locks.json phải có mảng locks")
    return data


def save_locks(repo, data):
    path_locks(repo).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report(errors, warnings):
    for text in errors:
        print("ERROR: " + text)
    for text in warnings:
        print("WARN: " + text)
    print("KẾT QUẢ: " + ("DỪNG" if errors else "PASS"))


def preflight(repo, fetch=True):
    errors, warnings = [], []
    code, _ = git(repo, "rev-parse", "--is-inside-work-tree")
    if code:
        report(["Không phải Git repository. Dừng để tránh làm trên bản rời."], [])
        return 2
    if fetch:
        code, output = git(repo, "fetch", "origin")
        if code:
            errors.append("git fetch origin thất bại: " + output)
    code, status = git(repo, "status", "--porcelain")
    if code:
        errors.append("Không đọc được git status: " + status)
    elif status:
        errors.append("Working tree bẩn. Commit hoặc tách thay đổi trước khi làm.")
    code, _ = git(repo, "rev-parse", "--verify", "origin/main")
    if code:
        errors.append("Không có origin/main. Kiểm tra remote và fetch.")
    elif git(repo, "merge-base", "--is-ancestor", "origin/main", "HEAD")[0]:
        errors.append("HEAD không chứa origin/main. Rebase hoặc pull trước khi làm.")
    appver = repo / "vagabond/public/js/bep/12-van-don.js"
    patches = repo / "vagabond/patches.txt"
    if appver.exists() and patches.exists():
        versions = [x for x in appver.read_text(encoding="utf-8", errors="replace").splitlines() if "APPVER" in x]
        print("APPVER:", versions[0] if versions else "Không tìm thấy")
        print("patches.txt cuối tệp:")
        print("\n".join(patches.read_text(encoding="utf-8", errors="replace").splitlines()[-3:]))
    else:
        warnings.append("Không thấy cấu trúc app chuẩn, bỏ qua kiểm APPVER và patches.txt.")
    try:
        opened = len(load_locks(repo)["locks"])
        if opened:
            warnings.append(f"Có {opened} lock cục bộ đang mở. Kiểm tra GitHub Issue trước khi claim.")
    except RuntimeError as error:
        errors.append(str(error))
    report(errors, warnings)
    return 1 if errors else 0


def overlap(left, right):
    left, right = left.rstrip("/"), right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def claim(repo, task, owner, branch, scopes):
    if preflight(repo) != 0:
        print("Không claim khi preflight chưa đạt.")
        return 1
    data = load_locks(repo)
    for item in data["locks"]:
        for scope in scopes:
            if any(overlap(scope, existing) for existing in item.get("scopes", [])):
                print(f"ERROR: {scope} xung đột lock {item['task']} của {item['owner']}.")
                return 1
    data["locks"].append({"task": task, "owner": owner, "branch": branch,
                          "scopes": sorted(set(scopes)),
                          "claimed_at": datetime.now(timezone.utc).isoformat()})
    save_locks(repo, data)
    print(f"Đã claim {task} cho {owner}. Cập nhật cùng thông tin vào GitHub Issue.")
    return 0


def list_locks(repo):
    for item in load_locks(repo)["locks"]:
        print(f"{item['task']} | {item['owner']} | {item['branch']} | {', '.join(item['scopes'])}")
    if not load_locks(repo)["locks"]:
        print("Không có lock cục bộ đang mở.")
    return 0


def release(repo, task, owner):
    data = load_locks(repo)
    remain = [x for x in data["locks"] if not (x.get("task") == task and x.get("owner") == owner)]
    if len(remain) == len(data["locks"]):
        print(f"ERROR: Không có lock {task} của {owner}.")
        return 1
    data["locks"] = remain
    save_locks(repo, data)
    print(f"Đã release lock cục bộ {task} của {owner}.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Vagabond Control Tower")
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--repo", type=Path, default=Path("."))
    pre.add_argument("--skip-fetch", action="store_true")
    cl = sub.add_parser("claim")
    cl.add_argument("--repo", type=Path, default=Path("."))
    cl.add_argument("--task", required=True)
    cl.add_argument("--owner", choices=["claude", "codex", "human"], required=True)
    cl.add_argument("--branch", required=True)
    cl.add_argument("--scope", action="append", dest="scopes", required=True)
    li = sub.add_parser("list-locks")
    li.add_argument("--repo", type=Path, default=Path("."))
    re = sub.add_parser("release-lock")
    re.add_argument("--repo", type=Path, default=Path("."))
    re.add_argument("--task", required=True)
    re.add_argument("--owner", choices=["claude", "codex", "human"], required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.command == "preflight":
        return preflight(repo, not args.skip_fetch)
    if args.command == "claim":
        return claim(repo, args.task, args.owner, args.branch, args.scopes)
    if args.command == "list-locks":
        return list_locks(repo)
    return release(repo, args.task, args.owner)


if __name__ == "__main__":
    sys.exit(main())
