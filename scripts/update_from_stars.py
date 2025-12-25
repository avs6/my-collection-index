#!/usr/bin/env python3
"""
Star-to-table auto-updater for Awesome-Abi README.

- Fetches starred repos for a user via GitHub REST API.
- Categorizes using simple heuristics (topics/language/name/description).
- Updates README.md between markers:
    <!-- AUTO-MANAGED:START -->
    ...
    <!-- AUTO-MANAGED:END -->

Usage:
  python scripts/update_from_stars.py --user <username> --write
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import urllib.request
import json

GITHUB_API = "https://api.github.com"


@dataclass
class Repo:
    full_name: str
    html_url: str
    description: str
    language: str
    topics: List[str]
    stargazers_count: int


def gh_get(url: str, token: Optional[str]) -> Tuple[List[dict], dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "awesome-abi-updater",
    }
    # Topics require preview header historically; modern Accept typically OK, but keep topics header:
    headers["Accept"] = "application/vnd.github+json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = resp.read().decode("utf-8")
        # GitHub uses Link header for pagination
        meta = {k.lower(): v for k, v in resp.headers.items()}
        return json.loads(data), meta


def parse_next_link(link_header: str) -> Optional[str]:
    # Example: <https://api.github.com/...page=2>; rel="next", <...>; rel="last"
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if 'rel="next"' in p:
            m = re.search(r"<([^>]+)>", p)
            if m:
                return m.group(1)
    return None


def fetch_starred(user: str, token: Optional[str], limit: int = 2000) -> List[Repo]:
    url = f"{GITHUB_API}/users/{user}/starred?per_page=100"
    repos: List[Repo] = []
    while url and len(repos) < limit:
        page, meta = gh_get(url, token)
        for r in page:
            repos.append(
                Repo(
                    full_name=r.get("full_name", ""),
                    html_url=r.get("html_url", ""),
                    description=(r.get("description") or "").strip(),
                    language=(r.get("language") or "").strip(),
                    topics=r.get("topics") or [],
                    stargazers_count=int(r.get("stargazers_count") or 0),
                )
            )
        url = parse_next_link(meta.get("link", ""))
    return repos


def categorize(repo: Repo) -> str:
    text = " ".join([repo.full_name, repo.description, repo.language, " ".join(repo.topics)]).lower()

    def has(*keys: str) -> bool:
        return any(k in text for k in keys)

    # Tailored buckets for Abi: agentic AI, infra, trading, plus genai/mlops/datasets/viz/tools/examples
    if has("agent", "langgraph", "autogen", "crew", "mcp", "tool calling", "planner", "orchestration"):
        return "Agentic AI"
    if has("llm", "rag", "embedding", "vllm", "inference", "transformer", "diffusion", "genai"):
        return "GenAI"
    if has("mlops", "mlflow", "kubeflow", "dvc", "feature store", "model registry", "drift"):
        return "MLOps"
    if has("kubernetes", "k8s", "helm", "operator", "docker", "container", "prometheus", "grafana", "cilium", "istio", "storage", "ceph"):
        return "Infra / Kubernetes / Docker"
    if has("quant", "trading", "backtest", "backtesting", "portfolio", "alpha", "risk", "market"):
        return "Trading / Quant"
    if has("dataset", "datasets", "data set", "benchmark", "corpus"):
        return "Datasets"
    if has("visual", "visualization", "dashboard", "plot", "graph", "chart"):
        return "Visualization"
    if has("automation", "workflow", "ci", "cd", "github action", "pipeline"):
        return "Automation"
    if has("example", "tutorial", "cookbook", "sample"):
        return "Coding Examples"
    return "Tools"


def render_tables(grouped: Dict[str, List[Repo]], top_n: int = 50) -> str:
    order = [
        "Agentic AI",
        "GenAI",
        "MLOps",
        "Infra / Kubernetes / Docker",
        "Trading / Quant",
        "Datasets",
        "Coding Examples",
        "Automation",
        "Visualization",
        "Tools",
    ]
    lines: List[str] = []
    for cat in order:
        repos = grouped.get(cat, [])
        if not repos:
            continue
        repos = sorted(repos, key=lambda r: r.stargazers_count, reverse=True)[:top_n]
        lines.append(f"### ⭐ Auto-curated: {cat}\n")
        lines.append("| Repo | Why it matters (fill later) | Link |\n|---|---|---|\n")
        for r in repos:
            lines.append(f"| `{r.full_name}` |  | {r.html_url} |\n")
        lines.append("\n")
    return "".join(lines).rstrip() + "\n"


def update_readme(readme_path: str, block: str, write: bool) -> str:
    with open(readme_path, "r", encoding="utf-8") as f:
        text = f.read()

    start = "<!-- AUTO-MANAGED:START -->"
    end = "<!-- AUTO-MANAGED:END -->"
    if start not in text or end not in text:
        raise RuntimeError("AUTO-MANAGED markers not found in README.md")

    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = start + "\n" + block.strip() + "\n" + end
    new_text = pattern.sub(replacement, text)

    if write:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_text)

    return new_text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="GitHub username (owner of stars)")
    ap.add_argument("--readme", default="README.md", help="Path to README.md")
    ap.add_argument("--limit", type=int, default=2000, help="Max starred repos to fetch")
    ap.add_argument("--top", type=int, default=50, help="Max repos per category in table")
    ap.add_argument("--dry-run", action="store_true", help="Do not write, just print summary")
    ap.add_argument("--write", action="store_true", help="Write changes to README")
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN")

    repos = fetch_starred(args.user, token, limit=args.limit)
    grouped: Dict[str, List[Repo]] = {}
    for r in repos:
        cat = categorize(r)
        grouped.setdefault(cat, []).append(r)

    block = render_tables(grouped, top_n=args.top)

    # Always produce output; write only if --write and not --dry-run
    do_write = bool(args.write) and not bool(args.dry_run)
    updated = update_readme(args.readme, block, write=do_write)

    # Print quick stats
    counts = {k: len(v) for k, v in grouped.items()}
    print("Starred repos fetched:", len(repos))
    for k in sorted(counts, key=lambda x: (-counts[x], x)):
        print(f"  {k}: {counts[k]}")
    if do_write:
        print(f"\n✅ Updated {args.readme} between AUTO-MANAGED markers.")
    else:
        print("\nℹ️ Dry run (no write). Use --write to update README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
