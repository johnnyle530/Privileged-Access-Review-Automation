# Okta Privileged Access Review Automation (Quarterly)

This project generates a quarterly privileged access review report that helps an IT and security team prevent privilege creep, stay audit ready, and enforce least privilege.

Even without a live Okta tenant, this repo runs locally using sample JSON data and produces real CSV and JSON evidence files. In production, the same logic would be fed by Okta API and orchestrated by Okta Workflows on a 90 day schedule.

## What it does
- Takes a list of privileged groups (Okta admin groups, AWS admins, Google Workspace admins, etc.)
- Pulls members of those groups
- Enriches members with user details (department, manager, status)
- Outputs a review report:
  - CSV for auditors and managers
  - JSON for automation, dashboards, or future integrations

## Why this matters
Privileged access is high risk. Over time, people change roles and access can linger. A quarterly review:
- reduces security risk
- supports SOC 2 and ISO style controls
- creates repeatable evidence

## How this maps to Okta Workflows (design)
Trigger:
- Scheduled, run every 90 days

Workflow steps:
1) Read privileged group list (from a table, Workflows helper flow, or config file)
2) For each group, fetch group members
3) Enrich with user attributes and manager
4) Generate report (CSV and JSON)
5) Notify in Slack and create a Jira ticket for approvals

## Quick start (local)
Requirements:
- Python 3.10+

Run:
```bash
python3 scripts/generate_access_review.py --mode sample --config config/config.example.yaml

