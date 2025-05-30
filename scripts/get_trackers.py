import argparse
import dataclasses
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import parsel
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


class Exodus:
    def __init__(self) -> None:
        self.base_uri = "https://reports.exodus-privacy.eu.org"

    def trackers(self, id: str = None) -> str:
        response = requests.get(
            url=(self.base_uri + (id if id else "/en/trackers/?filter=apps"))
        )
        logger.info(f"{response.status_code} {response.url}")
        return response.text


class Parser:
    def trackers(self, html: str) -> list[list[str]]:
        trackers = []
        blocks = parsel.Selector(html).xpath('//div[@class="trackers"]')

        for block in blocks:
            a = block.xpath("./p[1]/a")
            href = a.xpath("./@href").get()
            text = a.xpath("normalize-space(string())").get()
            trackers.append([href, text.split("\xa0")[0].strip()])

        logger.info(f"Found {len(trackers)} trackers")
        return trackers

    def tracker_urls(self, html: str) -> list[str]:
        block = (
            parsel.Selector(html)
            .xpath('(//div[contains(@class, "col-md-8")]//code)[2]/text()')
            .get()
        )
        urls = [b.strip() for b in block.replace("\\", "").split("|")]
        urls = [u for u in urls if is_valid_url(u)]
        logger.info(f"Found {len(urls)} urls")

        return urls


@dataclasses.dataclass
class Tracker:
    name: str
    urls: list[str]
    exodus_link: str


def parse_trackers(workers: int, skip_empty: bool) -> list[Tracker]:
    exodus = Exodus()
    parser = Parser()

    trackers_raw = exodus.trackers()
    trackers = parser.trackers(trackers_raw)
    _trackers = []

    def process_tracker(tracker: list[str]) -> None:
        exodus_url, tracker_name = tracker
        tracker_urls_raw = exodus.trackers(id=exodus_url)
        tracker_urls = parser.tracker_urls(tracker_urls_raw)
        tracker = Tracker(
            name=tracker_name,
            urls=tracker_urls,
            exodus_link=(exodus.base_uri + exodus_url),
        )

        if skip_empty and len(tracker_urls) == 0:
            return None

        _trackers.append(tracker)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        executor.map(process_tracker, trackers)

    return _trackers


class TransformJson:
    @classmethod
    def transform(cls, trackers: list[Tracker]) -> str:
        import json

        return json.dumps(
            [dataclasses.asdict(t) for t in trackers],
            indent=4,
        )


class TransformCsv:
    @classmethod
    def transform(cls, trackers: list[Tracker]) -> str:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["name", "urls", "exodus_link"])

        for t in trackers:
            writer.writerow([t.name, ", ".join(t.urls), t.exodus_link])

        return output.getvalue()


class TransformDnsmasq:
    @classmethod
    def transform(cls, trackers: list[Tracker]) -> str:
        data = "# https://github.com/Vlad2030/trackers-block/\n\n"

        for tracker in trackers:
            data += f"# {tracker.name} {tracker.exodus_link}\n"
            data += "\n".join([f"address=/{u}/0.0.0.0" for u in tracker.urls])
            data += "\n\n"

        return data


def is_valid_url(url: str) -> bool:
    url_regex = re.compile(
        r"^(?!-)(?!.*--)[A-Za-z0-9-]{1,63}(?<!-)"
        r"(\.(?!-)(?!.*--)[A-Za-z0-9-]{1,63}(?<!-))*"
        r"\.[A-Za-z]{2,}$"
    )
    return bool(url_regex.fullmatch(url))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Script to parse trackers from exodus-privacy.eu.org"
            " and transform to conf files"
        ),
        add_help=True,
    )
    parser.add_argument(
        "--transform-to",
        type=str,
        choices=["json", "csv", "dnsmasq"],
        required=True,
        help="Format to transform the output into",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        required=False,
        help="Parse workers",
    )
    parser.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip trackers with no URLs",
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to save the transformed output",
    )

    args = parser.parse_args()
    trackers = parse_trackers(args.workers, args.skip_empty)
    trackers.sort(key=(lambda x: x.name))

    logger.info(
        f"Found total {len(trackers)} trackers"
        f" and {sum([len(t.urls) for t in trackers])} urls"
    )
    logger.info(f"Saving {args.transform_to} to {args.path}...")

    if args.transform_to == "json":
        data = TransformJson.transform(trackers)

    if args.transform_to == "csv":
        data = TransformCsv.transform(trackers)

    if args.transform_to == "dnsmasq":
        data = TransformDnsmasq.transform(trackers)

    with open(args.path, "w", encoding="utf-8") as f:
        f.write(data)
        logger.info("Successfully saved!")


if __name__ == "__main__":
    main()
