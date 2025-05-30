python3 scripts/get_trackers.py \
    --transform-to json \
    --skip-empty \
    --workers 64 \
    trackers/trackers.json

python3 scripts/get_trackers.py \
    --transform-to csv \
    --skip-empty \
    --workers 64 \
    trackers/trackers.csv

python3 scripts/get_trackers.py \
    --transform-to dnsmasq \
    --skip-empty \
    --workers 64 \
    trackers/dnsmasq.conf
