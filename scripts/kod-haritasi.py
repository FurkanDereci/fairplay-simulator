"""Kod grafiğinden **ürün haritası** üretir (ADR-0020).

Girdi: `graphify-out/graph.json` (`graphify extract . --code-only --no-label` ile üretilir; yerel
AST, API anahtarı gerekmez). Çıktı: `docs/85-kod-haritasi.md` — her topluluğu **baskın modülüne**
göre adlar ve kilit sembolleri listeler. Amaç: `graphify` çıktısındaki "Community 0..N"
yer tutucularını okunur hâle getirmek (devir/oriyantasyon).

Deterministik ve LLM'sizdir; topluluk adları grafikteki düğümlerin `source_file`'larından
türetilir. Grafik commit'e bağlı bir **anlık görüntüdür**; başlıkta kaynağı yazılıdır.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "docs" / "85-kod-haritasi.md"


def _module(source_file: str) -> str:
    prefix = "src/fairplay_simulator/"
    name = source_file[len(prefix):] if source_file.startswith(prefix) else source_file
    return name[:-3] if name.endswith(".py") else name


def _keys(
    members: list[str], degree: Counter[str], nodes: dict[str, dict[str, object]]
) -> list[str]:
    """Topluluğun en bağlı (kilit) sembollerini döndürür."""
    ranked = sorted(members, key=lambda m: (-degree[m], str(nodes[m].get("label", ""))))[:5]
    return [str(nodes[k].get("label", k)) for k in ranked]


def main() -> int:
    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data["nodes"]}
    degree: Counter[str] = Counter()
    for edge in data["links"]:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1

    communities: dict[int, list[str]] = defaultdict(list)
    for node_id, node in nodes.items():
        if node.get("community") is not None:
            communities[node["community"]].append(node_id)

    rows = []
    for community in sorted(communities):
        members = communities[community]
        mods = Counter(m for m in (_module(nodes[m].get("source_file", "")) for m in members) if m)
        total = len(members)
        if not mods:
            rows.append((community, "(modülsüz)", total, 0, _keys(members, degree, nodes)))
            continue
        dominant, count = mods.most_common(1)[0]
        cohesion = count / total
        if cohesion >= 0.5:
            name = dominant
        else:
            top_two = [m for m, _ in mods.most_common(2) if m]
            name = " + ".join(top_two)
        rows.append((community, name, total, round(cohesion * 100), _keys(members, degree, nodes)))

    built = data.get("built_at_commit", "?")
    lines = [
        "# Kod Haritası (ürün haritası)",
        "",
        "> **Üretilir, elle yazılmaz.** `graphify` grafiğindeki topluluklar **baskın modülüne**",
        "> göre adlanır (ADR-0020). Grafik commit'e bağlı bir **anlık görüntüdür**; başlıktaki",
        "> commit geçerlidir. Yeniden üretim: `graphify extract . --code-only --no-label` →",
        "> `python3 scripts/kod-haritasi.py`.",
        "",
        f"**Kaynak commit:** `{built}` · **Topluluk:** {len(rows)} · "
        f"**Düğüm:** {len(nodes)} · **Kenar:** {len(data['links'])}",
        "",
        "| Topluluk | Ad (baskın modül) | Düğüm | Uyum | Kilit semboller |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for community, name, total, cohesion, labels in rows:
        lines.append(
            f"| C{community} | `{name}` | {total} | %{cohesion} | {', '.join(labels)} |"
        )
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"yazıldı: {OUT} ({len(rows)} topluluk)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
