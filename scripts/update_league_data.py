#!/usr/bin/env python3
"""
Pulls the live standings from ICN's own bot-maintained source page and
regenerates LEAGUE_DATA and ALL_PLAYERS in index.html to match.

Source: https://icnadmin.com/League2026.html -- this is what
impactcoachingnetwork.org/icnchessleague itself embeds via iframe, so it's
the same data ICN's own site shows, just reachable directly instead of
through their Squarespace wrapper.

Run manually with: python3 scripts/update_league_data.py
Normally run on a schedule by .github/workflows/update-league-data.yml.
"""
import re
import sys
import urllib.request

SOURCE_URL = "https://icnadmin.com/League2026.html"
INDEX_HTML = "index.html"

REGION_ORDER = ["overall", "manhattan", "brooklyn"]
REGION_LABELS = {"overall": "Overall", "manhattan": "Manhattan", "brooklyn": "Brooklyn"}
REGION_MAP = {"Overall": "overall", "Manhattan": "manhattan", "Brooklyn": "brooklyn"}
DIVISION_ORDER = ["k1", "primary", "elementary"]
DIVISION_MAP = {"K1": "k1", "Primary": "primary", "Elementary": "elementary"}
GRADE_MAP = {"Kindergarten": "K", "1st": "1", "2nd": "2", "3rd": "3", "4th": "4", "5th": "5"}

SECTION_RE = re.compile(r"<h2>====\s*([A-Za-z]+)(?:,\s*([A-Za-z0-9]+))?\s*====</h2>")
ROW_RE = re.compile(
    r"<strong>(\d+)\.\s*</div><div class='ib' style='width: 25px;'>"
    r"<img src='([^']+)'[^>]*></div><div class='ib' style='width: 180px;'>\s*([^<]+?)\s*</div>"
    r"<div class='ib' style='width: 80px; text-align: right;'>\s*([\d,]+)</strong><br></div></div>"
    r"<div id=(\w+) class='collapse'>(.*?)</div>"
)
PLAYER_RE = re.compile(r"<span style='white-space: pre'>\s*(.+?),\s*(\d+),\s*(\d+),\s*(\w+)\s*</span>")


def fetch_source():
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(content):
    league_data = {r: {d: [] for d in DIVISION_ORDER} for r in REGION_ORDER}
    all_players = []
    seen_players = set()

    sections = list(SECTION_RE.finditer(content))
    for i, m in enumerate(sections):
        region_raw, division_raw = m.group(1), m.group(2)
        if division_raw is None:
            continue
        region = REGION_MAP.get(region_raw)
        division = DIVISION_MAP.get(division_raw)
        if not region or not division:
            print(f"WARNING: unmapped region/division: {region_raw}/{division_raw}", file=sys.stderr)
            continue

        start = m.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(content)
        chunk = content[start:end]

        for row in ROW_RE.finditer(chunk):
            _rank, _icon_url, school_name, points_str, _collapse_id, detail_block = row.groups()
            points = int(points_str.replace(",", ""))
            league_data[region][division].append({"name": school_name, "points": points})

            for p in PLAYER_RE.finditer(detail_block):
                pname, _uscf_id, rating, grade_raw = p.groups()
                grade = GRADE_MAP.get(grade_raw)
                if grade is None:
                    print(f"WARNING: unmapped grade label {grade_raw!r} for {pname}", file=sys.stderr)
                    continue
                key = (pname.strip(), school_name, grade)
                if key not in seen_players:
                    seen_players.add(key)
                    all_players.append({
                        "name": pname.strip(),
                        "rating": int(rating),
                        "school": school_name,
                        "grade": grade,
                    })

    return league_data, all_players


def js_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_league_data(league_data):
    lines = ["  const LEAGUE_DATA = {", "    regions: ["]
    for ri, region in enumerate(REGION_ORDER):
        lines.append("      {")
        lines.append(f'        key: {js_string(region)}, label: {js_string(REGION_LABELS[region])},')
        lines.append("        divisions: {")
        for di, division in enumerate(DIVISION_ORDER):
            schools = league_data[region][division]
            entries = ", ".join(
                f'{{ name:{js_string(s["name"])}, points:{s["points"]} }}' for s in schools
            )
            comma = "," if di < len(DIVISION_ORDER) - 1 else ""
            lines.append(f"          {division}: [{entries}]{comma}")
        lines.append("        }")
        lines.append("      }" + ("," if ri < len(REGION_ORDER) - 1 else ""))
    lines.append("    ]")
    lines.append("  };")
    return "\n".join(lines)


def render_all_players(all_players):
    lines = ["  const ALL_PLAYERS = ["]
    for p in all_players:
        lines.append(
            f'    {{ name:{js_string(p["name"])}, rating:{p["rating"]}, '
            f'school:{js_string(p["school"])}, grade:{js_string(p["grade"])} }},'
        )
    lines.append("  ];")
    return "\n".join(lines)


def replace_block(html, const_name, new_block):
    pattern = re.compile(
        rf"  const {const_name} = (?:\{{|\[).*?\n  \}}\;|  const {const_name} = (?:\{{|\[).*?\n  \]\;",
        re.DOTALL,
    )
    new_html, count = pattern.subn(new_block, html, count=1)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {const_name} block, replaced {count}")
    return new_html


def main():
    print(f"Fetching {SOURCE_URL} ...")
    content = fetch_source()
    print(f"Fetched {len(content)} bytes")

    league_data, all_players = parse(content)

    total_schools = sum(len(league_data[r][d]) for r in REGION_ORDER for d in DIVISION_ORDER)
    print(f"Parsed {total_schools} school-section rows, {len(all_players)} unique players")
    if total_schools == 0 or len(all_players) == 0:
        print("ERROR: parsed zero schools or players -- source page structure may have changed. Aborting without writing changes.", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_HTML) as f:
        html = f.read()

    html = replace_block(html, "LEAGUE_DATA", render_league_data(league_data))
    html = replace_block(html, "ALL_PLAYERS", render_all_players(all_players))

    with open(INDEX_HTML, "w") as f:
        f.write(html)

    print("index.html updated.")


if __name__ == "__main__":
    main()
