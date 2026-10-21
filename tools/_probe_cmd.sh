set -x
python3 tools/test_propose_country.py
python3 tools/propose_country.py --country PT --country-qid Q45 \
  --article "1=2026–27 Primeira Liga" --article "2=2026–27 Liga Portugal 2" \
  --langs pt --write-partial
