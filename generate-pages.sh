#!/bin/bash

echo "** Installing dependencies **"
pip install --upgrade --upgrade-strategy eager -r requirements-nb.txt

echo "** running notebooks **"
mkdir -p public/
python3 build.py

echo "** preparing sites **"
curl https://ackee.coronapergemeente.nl/tracker.js > public/ackee-min.js
cp index.html public/
find public/ -type f -name '*.html' -print0 | xargs -0 sed -i 's|<title>|<script src="/ackee-min.js" data-ackee-server="https://ackee.coronapergemeente.nl" data-ackee-domain-id="19d8f555-2891-4d16-b859-0567133bbe66"></script><title>|'
find public/ -type f -name "*.png" -print0 | xargs -0 optipng -o5 -i7