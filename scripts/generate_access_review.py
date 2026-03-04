The script that generates the CSV and JSON
import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip3 install pyyaml")


@dataclass
class ReviewRow:
    group_name: str
    privilege_level: str
    user_id: str
    user_email: str
    user_name: str
    user_status: str
    department: str
    manager_email: str
    review_due_date: str
    notes: str


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_output_dir(out_dir: str) -> None:
    Path(out_dir).mkdir(parents=True, exist_ok=True)


def today_str() -> str:
    return date.today().isoformat()


def compute_due_date(interval_days: int) -> str:
    return (date.today() + timedelta(days=interval_days)).isoformat()


def build_index_users(users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {u["id"]: u for u in users}


def build_index_groups(groups: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {g["id"]: g for g in groups}


def build_group_name_to_id(groups: List[Dict[str, Any]]) -> Dict[str, str]:
    return {g["name"]: g["id"] for g in groups}


def generate_rows_sample(config: Dict[str, Any]) -> List[ReviewRow]:
    groups = load_json("data/sample_groups.json")
    group_members = load_json("data/sample_group_members.json")
    users = load_json("data/sample_users.json")

    users_by_id = build_index_users(users)
    groups_by_id = build_index_groups(groups)
    group_name_to_id = build_group_name_to_id(groups)

    privileged_group_names = config["review"]["privileged_groups"]
    exclude_users = set(config.get("notes", {}).get("exclude_users", []))
    interval_days = int(config["review"]["review_interval_days"])
    privilege_map = config.get("notes", {}).get("privilege_level_map", {})

    due_date = compute_due_date(interval_days)

    members_by_group_id = {gm["group_id"]: gm["user_ids"] for gm in group_members}

    rows: List[ReviewRow] = []

    for group_name in privileged_group_names:
        group_id = group_name_to_id.get(group_name)
        if not group_id:
            continue

        user_ids = members_by_group_id.get(group_id, [])
        privilege_level = privilege_map.get(group_name, "High")

        for uid in user_ids:
            user = users_by_id.get(uid)
            if not user:
                continue

            if user["email"] in exclude_users:
                continue

            rows.append(
                ReviewRow(
                    group_name=group_name,
                    privilege_level=privilege_level,
                    user_id=user["id"],
                    user_email=user["email"],
                    user_name=user["name"],
                    user_status=user.get("status", "UNKNOWN"),
                    department=user.get("department", ""),
                    manager_email=user.get("manager_email", ""),
                    review_due_date=due_date,
                    notes="Quarterly access validation required"
                )
            )

    # Sort for clean output
    rows.sort(key=lambda r: (r.group_name.lower(), r.user_email.lower()))
    return rows


def write_csv(path: str, rows: List[ReviewRow]) -> None:
    fieldnames = [
        "group_name",
        "privilege_level",
        "user_id",
        "user_email",
        "user_name",
        "user_status",
        "department",
        "manager_email",
        "review_due_date",
        "notes",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r.__dict__)


def write_json(path: str, rows: List[ReviewRow]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.__dict__ for r in rows], f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate quarterly privileged access review report.")
    parser.add_argument("--mode", choices=["sample"], default="sample", help="Data source mode.")
    parser.add_argument("--config", required=True, help="Path to config YAML.")
    args = parser.parse_args()

    config = load_config(args.config)

    out_dir = config["output"]["directory"]
    prefix = config["output"]["file_prefix"]
    ensure_output_dir(out_dir)

    stamp = today_str()
    csv_path = os.path.join(out_dir, f"{prefix}_{stamp}.csv")
    json_path = os.path.join(out_dir, f"{prefix}_{stamp}.json")

    if args.mode == "sample":
        rows = generate_rows_sample(config)
    else:
        raise SystemExit("Unsupported mode")

    write_csv(csv_path, rows)
    write_json(json_path, rows)

    print(f"Generated {len(rows)} rows")
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
