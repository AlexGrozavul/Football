set -x
python3 tools/test_propose_country.py | tail -1
python3 tools/propose_country.py --country PT --country-qid Q45 \
  --article "1=2026–27 Primeira Liga" --article "2=2026–27 Liga Portugal 2" \
  --below "2026–27 Liga 3 (Portugal)" --below "2026–27 Campeonato de Portugal" \
  --langs pt --grounds --probe-slug --write-partial
