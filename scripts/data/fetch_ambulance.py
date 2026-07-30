# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)


from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

from _overpass_utils import (
    build_arg_parser,
    build_india_query,
    fetch_elements,
    normalize_row,
    write_rows,
)

DEFAULT_OUTPUT = ROOT_DIR / 'chatbot_service' / 'data' / 'emergency' / 'ambulance_stations.csv'
SELECTORS = [
    'node["emergency"="ambulance_station"](area.searchArea);',
    'way["emergency"="ambulance_station"](area.searchArea);',
    'relation["emergency"="ambulance_station"](area.searchArea);',
    'node["amenity"="ambulance_station"](area.searchArea);',
    'way["amenity"="ambulance_station"](area.searchArea);',
    'relation["amenity"="ambulance_station"](area.searchArea);',
    'node["healthcare"="ambulance_station"](area.searchArea);',
    'way["healthcare"="ambulance_station"](area.searchArea);',
    'relation["healthcare"="ambulance_station"](area.searchArea);',
]


def main() -> None:
    parser = build_arg_parser('Fetch India ambulance station data from Overpass.', DEFAULT_OUTPUT)
    args = parser.parse_args()

    query = build_india_query(SELECTORS, timeout=args.timeout)
    elements = fetch_elements(query, endpoint=args.endpoint, timeout=args.timeout)
    rows = [
        row
        for element in elements
        if (row := normalize_row(element, default_type='ambulance', fallback_name='Unnamed ambulance station')) is not None
    ]
    count = write_rows(args.output, rows)
    LOGGER.info(f'Saved {count} ambulance station records to {args.output}')


if __name__ == '__main__':
    main()
