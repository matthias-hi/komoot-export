#!/usr/bin/env python
"""Extract tour data from raw json data and store as csv file.

Use pykomoot_gpx.py to download raw json data.
"""
import argparse
import json
import csv
from collections import defaultdict

# This list contains fields (columns) which are omitted when
# writing the csv file. Comment lines if you want to include them.
EXCLUDE_FIELDS = [
    '_embedded',
    '_links',
    'constitution',
    'difficulty',  # {'grade': 'moderate', 'explanation_technical': 'dm#t2', 'explanation_fitness': 'd#c2'}
    'map_image',
    'map_image_preview',
    'path',
    'query',
    'segments',
    'source',
    'start_point',  # "{'location': {'lat': xx.xxxxxx, 'lng': xx.xxxxxx, 'alt': xx.xxxxxx}}"
    'summary',
    'tour_information',  # [{'type': 'OFF_GRID', 'segments': [{'from': 146, 'to': 159}, {'from': 193, 'to': 200}]}]
]


class KomootTours(object):
    """KomootTours class"""

    def __init__(self, raw_json_str):
        """Parse json data and get all fields (columns).

        :param raw_json_str: Tour overview json data as returned by komoot API (type: str).
        """
        self.json_data = []
        self.all_fields = set()
        list_json_data = json.loads(raw_json_str)
        # print(json.dumps(self.json_data, indent=2, sort_keys=True))
        for list_entry in list_json_data:
            self.json_data += list_entry['_embedded']['tours']
        # Not all tours have the same fields. "tour_recorded" and "tour_planned"
        # have different fields and some fields seem to have changed
        # over the years. Find them all:
        for tour in self.json_data:
            self.all_fields |= set(tour.keys())

    @property
    def planned(self):
        return (t for t in self.json_data if t['type'] == 'tour_planned')

    @property
    def recorded(self):
        return (t for t in self.json_data if t['type'] == 'tour_recorded')

    def __str__(self):
        ret = []
        ret.append('Tours planned:  {}'.format(sum(1 for _ in self.planned)))
        distances = [float(t['distance']) for t in self.recorded]
        total_distance = sum(distances) / 1000  # in km
        ret.append('Tours recorded: {} (total distance: {:.0f} km)'.format(len(distances),
                                                                           total_distance))
        return '\n'.join(ret)

    def to_csv(self, csv_file_path, exclude_fields=None):
        """Write tour data to a CSV file.

        :param csv_file_path: File path of CSV file (type: str)
        :param exclude_fields: (optional) List of fields (columns) to ommit
        """
        try:
            exclude_fields = set(exclude_fields)
        except TypeError:
            exclude_fields = set()
        with open(csv_file_path, mode='w', encoding='utf-8') as _f:
            fields = self.all_fields - exclude_fields
            writer = csv.DictWriter(_f, dialect='excel', fieldnames=sorted(fields))
            writer.writeheader()
            for tour in self.json_data:
                filtered_tour = {key: value for (key, value) in tour.items() if key in fields}
                writer.writerow(defaultdict(lambda: '', filtered_tour))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('tours_json', help='Komoot tours raw json file')
    args = parser.parse_args()
    json_text = None
    try:
        with open(args.tours_json) as json_file:
            json_text = json_file.read()
    except FileNotFoundError:
        print('Could not open {}.'.format(args.tours_json))
    if json_text:
        ktours = KomootTours(json_text)
        print(ktours)
        ktours.to_csv('tours.csv', exclude_fields=EXCLUDE_FIELDS)
        print('Converted {} to CSV file "tours.csv".'.format(args.tours_json))


if __name__ == '__main__':
    main()
