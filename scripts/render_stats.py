#!/usr/bin/env python3
"""Render assets/stats.svg for the profile README from the GitHub API."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOGIN = "Nezerkill"
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "stats.svg"

BG = "#0E1223"
BORDER = "#73798C"
MUTED = "#AAB1D3"
ACCENT = "#E5BAFF"
TEAL = "#81C8BE"
GLOW = "#CA9EE6"


def token() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    config = Path.home() / ".config" / "gh" / "hosts.yml"
    if config.exists():
        match = re.search(r"oauth_token:\s*(\S+)", config.read_text())
        if match:
            return match.group(1)
    raise SystemExit("no GitHub token found")


def request(url: str, data: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "nezerkill-profile",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def plural(count: int, forms: tuple[str, str, str]) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return forms[1]
    return forms[2]


def collect() -> dict:
    query = (
        '{ user(login: "%s") {'
        " contributionsCollection { contributionCalendar { totalContributions } } } }"
    ) % LOGIN
    data = request(f"{API}/graphql", {"query": query})["data"]["user"]
    return {
        "contributions": data["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ],
        "repos": request(f"{API}/users/{LOGIN}")["public_repos"],
        "followers": request(f"{API}/users/{LOGIN}")["followers"],
        "repos_stars": sum(
            repo["stargazers_count"]
            for repo in request(f"{API}/users/{LOGIN}/repos?per_page=100&type=owner")
        ),
    }


def render(stats: dict) -> str:
    width, height = 880, 168
    metrics = [
        (stats["repos"], ("публичный репозиторий", "публичных репозитория",
                          "публичных репозиториев")),
        (stats["contributions"], ("контрибуция", "контрибуции", "контрибуций")),
        (stats["repos_stars"], ("звезда", "звезды", "звёзд")),
        (stats["followers"], ("подписчик", "подписчика", "подписчиков")),
    ]
    updated = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Статистика GitHub профиля {LOGIN}">',
        f"<title>Статистика GitHub профиля {LOGIN}</title>",
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="880" y2="168" '
        'gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="{BG}"/><stop offset="1" stop-color="#090D19"/></linearGradient>',
        '<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        'gradientTransform="translate(120 0) rotate(90) scale(280)">'
        f'<stop stop-color="{GLOW}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient>',
        '<clipPath id="card"><rect width="880" height="168" rx="24"/></clipPath>',
        "</defs>",
        '<g clip-path="url(#card)">',
        '<rect width="880" height="168" fill="url(#bg)"/>',
        '<rect width="880" height="168" fill="url(#glow)"/>',
        "</g>",
        f'<rect x=".5" y=".5" width="879" height="167" rx="23.5" fill="none" '
        f'stroke="{BORDER}" stroke-opacity=".28"/>',
    ]

    mono = "ui-monospace,SFMono-Regular,Menlo,monospace"
    sans = "'Segoe UI',system-ui,-apple-system,sans-serif"

    parts.append(
        f'<text x="44" y="44" font-family="{mono}" font-size="14" '
        f'fill="{TEAL}">~/github · профиль</text>'
    )
    parts.append(
        f'<text x="{width - 44}" y="44" text-anchor="end" font-family="{mono}" '
        f'font-size="13" fill="{MUTED}">обновлено {updated}</text>'
    )

    for index, (value, forms) in enumerate(metrics):
        x = 44 + index * 200
        parts.append(
            f'<text x="{x}" y="106" font-family="{sans}" font-size="42" '
            f'font-weight="700" fill="{ACCENT}">{value}</text>'
        )
        parts.append(
            f'<text x="{x + 2}" y="132" font-family="{sans}" font-size="14" '
            f'fill="{MUTED}">{plural(value, forms)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.write_text(render(collect()))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
