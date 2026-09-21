#!/usr/bin/env python3
"""Asset-coverage audit: walk the concept ladder for a noun list per native colour pack and report
how each concept is drawn (exact / synonym / hypernym / composite / typographic / numeric).

    python3 tools/audit_coverage.py                       # built-in cross-domain list, every pack
    python3 tools/audit_coverage.py --pack icon.icon-park-color --nouns my_nouns.txt --show
    python3 tools/audit_coverage.py --glyph ICON        # what a bare icon (no housing) can draw

The built-in list is a deliberately broad spread of explainer nouns — products, food, finance,
software, health, home, travel, industry — not any one film's vocabulary. Exit status is 0; the
audit informs, the compiler gate decides.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'compiler'))

from editorial_plan_compiler.illustration import IllustrationRegistry  # noqa: E402
from editorial_plan_compiler.lexicon import AssetFinder, NounLexicon  # noqa: E402

NOUNS = """
almond, apple, avocado, bread, butter, cereal, cheese, chocolate, coffee, egg, espresso, honey, milk,
oat milk, pizza, rice, salt, sugar, tea, tomato, wine, yogurt,
bicycle, bus, car, ferry, motorcycle, scooter, train, truck, airplane, rocket,
camera, headphones, keyboard, laptop, microphone, monitor, phone, printer, router, speaker, tablet, watch,
battery, cable, charger, drone, lightbulb, sensor, thermostat,
bank, budget, cash, coin, credit card, invoice, ledger, loan, mortgage, payroll, receipt, revenue, salary,
savings, stock, subscription, tax, wallet,
algorithm, api, browser, bug, cloud, code, database, email, firewall, kubernetes cluster, password, server,
spreadsheet, startup, terminal, website,
calendar, clipboard, contract, document, folder, notebook, pencil, report, stamp,
bandage, brain, heart, hospital, medicine, nurse, pill, stethoscope, syringe, tooth, vaccine,
bed, chair, door, key, lamp, mirror, pillow, sofa, table, window,
backpack, hotel, luggage, map, passport, tent, ticket, umbrella,
crane, factory, hammer, hard hat, pipe, screw, toolbox, warehouse, wrench,
guitar, piano, violin, vinyl record, trophy, football, basketball,
dog, cat, bird, fish, tree, flower, mountain, sun, moon,
sneaker, dress, hat, shirt, glasses, ring,
12%, $4.2M, 3x, 1200, 48h
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--nouns', type=Path, help='newline-separated concepts (default: built-in list)')
    ap.add_argument('--pack', action='append', help='native pack id, repeatable (default: every native pack)')
    ap.add_argument('--glyph', default='TILE', choices=('TILE', 'CHIP', 'BADGE', 'ICON'), help='housing to resolve for (default TILE)')
    ap.add_argument('--show', action='store_true', help='print every resolution, not just the histogram')
    ap.add_argument('--json', type=Path, help='write the full report here')
    args = ap.parse_args()

    raw = args.nouns.read_text().splitlines() if args.nouns else NOUNS.replace(',', '\n').splitlines()
    nouns = [n.strip() for n in raw if n.strip()]
    reg = IllustrationRegistry()
    finder = AssetFinder(reg.items, NounLexicon(), reg.quarantined)
    packs = args.pack or sorted({AssetFinder.pack_of(a) for a, it in reg.items.items()
                                 if it.get('colour') == 'native' and it.get('family') != 'brand'})

    report = {}
    for pack in packs:
        rows = [finder.resolve(n, pack, args.glyph != 'ICON', True, args.glyph == 'CHIP').as_dict() for n in nouns]
        hist = collections.Counter(r['via'] for r in rows)
        drawn = sum(1 for r in rows if r['asset_ref'])
        report[pack] = {'histogram': dict(hist), 'drawn': drawn, 'total': len(rows), 'rows': rows}
        print(f"{pack:28s} drawn {drawn:3d}/{len(rows)}  " + '  '.join(f'{k}={v}' for k, v in sorted(hist.items())))
        if args.show:
            for r in rows:
                print(f"    {r['concept']:20s} {r['via']:12s} {r['asset_ref'] or '-':45s} {' > '.join(r['path'])}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
