# trackers-block

A script to parse and convert tracker data from [Exodus Privacy](https://reports.exodus-privacy.eu.org) into various formats like `json`, `csv`, and `dnsmasq` configs — ready for blocking.

## What it does

This tool fetches known trackers from Exodus, parses their associated domains, and exports the data into formats you can use for analysis or DNS-level blocking.

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/trackers-block.git
cd trackers-block
pip install -r requirements.txt
```

## Usage

Run the script to fetch and export trackers:

```bash
python scripts/get_trackers.py --transform-to dnsmasq ./trackers/dnsmasq.conf
```

### Optional flags

- `--transform-to`: Format to export (json, csv, dnsmasq)
- `--workers`: Number of threads for parsing (default: 16)
- `--skip-empty`: Include to skip trackers with no URLs
- `path`: Output file path

Example:

```bash
python scripts/get_trackers.py --transform-to csv --workers 32 --skip-empty ./trackers/trackers.csv
```

Or just run the included shell script:

```bash
bash scripts/update_trackers.sh
```

# Output preview

- [trackers.json](https://github.com/Vlad2030/trackers-block/blob/main/trackers/trackers.json): Full tracker metadata

- [trackers.csv](https://github.com/Vlad2030/trackers-block/blob/main/trackers/trackers.csv): Simplified CSV view

- [dnsmasq.conf](https://github.com/Vlad2030/trackers-block/blob/main/trackers/dnsmasq.conf): DNS blocklist for use with Pi-hole or dnsmasq
