#!/usr/bin/env python3
"""Render language proportions for an account's public, non-fork repositories."""

import html
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ACCOUNT = "arthurschuelter"
API = "https://api.github.com"
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "languages.svg"
COLORS = ["#bd93f9", "#8be9fd", "#50fa7b", "#ffb86c", "#ff79c6", "#f1fa8c", "#ff5555"]


def get_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "language-widget"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def collect_languages():
    totals = {}
    page = 1
    while True:
        repos = get_json(f"{API}/users/{ACCOUNT}/repos?type=owner&per_page=100&page={page}")
        for repo in repos:
            if repo["fork"] or repo["private"]:
                continue
            for language, size in get_json(repo["languages_url"]).items():
                totals[language] = totals.get(language, 0) + size
        if len(repos) < 100:
            break
        page += 1
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def render(languages):
    total = sum(size for _, size in languages)
    if not total:
        raise ValueError("No language data returned; refusing to overwrite the widget")
    # Keep the card compact while retaining every language in the total.
    shown = languages[:6]
    if len(languages) > 6:
        shown.append(("Other", sum(size for _, size in languages[6:])))
    height = 105 + len(shown) * 29
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height}" viewBox="0 0 460 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Languages used across public repositories</title>',
        '<desc id="desc">Percentages based on GitHub language byte counts for public, non-fork repositories.</desc>',
        f'<rect x="0.5" y="0.5" width="459" height="{height - 1}" rx="12" fill="#282a36" stroke="#44475a"/>',
        '<text x="24" y="36" fill="#f8f8f2" font-family="Arial, sans-serif" font-size="18" font-weight="bold">Languages</text>',
        '<text x="24" y="57" fill="#a9a9b3" font-family="Arial, sans-serif" font-size="12">Public repositories · share of code by bytes</text>',
        '<clipPath id="bar"><rect x="24" y="72" width="412" height="9" rx="4.5"/></clipPath>',
        '<g clip-path="url(#bar)">',
    ]
    offset = 24.0
    for index, (_, size) in enumerate(shown):
        width = 412 * size / total
        svg.append(f'<rect x="{offset:.4f}" y="72" width="{width:.4f}" height="9" fill="{COLORS[index]}"/>')
        offset += width
    svg.append('</g>')
    for index, (language, size) in enumerate(shown):
        y = 109 + index * 29
        name = html.escape(language)
        svg.extend([
            f'<circle cx="29" cy="{y - 4}" r="5" fill="{COLORS[index]}"/>',
            f'<text x="43" y="{y}" fill="#f8f8f2" font-family="Arial, sans-serif" font-size="13">{name}</text>',
            f'<text x="436" y="{y}" text-anchor="end" fill="#f8f8f2" font-family="Arial, sans-serif" font-size="13">{size / total:.1%}</text>',
        ])
    svg.append('</svg>')
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    content = render(collect_languages())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
