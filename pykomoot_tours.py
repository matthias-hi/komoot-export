#!/usr/bin/env python
"""Extract tour data from tour overview page and store as csv file.

Use pykomoot_gpx.py to download tours overview page or download
https://www.komoot.de/user/{username}/tours manually with your browser.
"""
import argparse
import json
import re
import csv
from collections import defaultdict

# This list contains fields (columns) which are omitted when
# writing the csv file. Comment lines if you want to include them.
EXCLUDE_FIELDS = [
    '_converted',  # Seems to be always "True"
    'altDiff',  # Seems to be always "0"
    'compactpath',  # cryptic string
    'constitution',  # integer number
    'content',  # "{'hasImage': False}""
    'creator',  # "{'username': 'xxxxxxxxxxx'}""
    'difficulty',  # "{'grade': 'easy', 'titlekey': 'easy_touringbicycle', 'explanationFitness': 'db#t1', 'explanationTechnical': 'd#c1'}""
    'mobile',  # "False"
    'numComments',
    'numLikes',
    'path',  # "[]"
    'poorQuality',  # "False"
    'recordSource',  # e.g. "Android" or empty
    'roundtrip',  # seems to be always "False"
    'score',  # "0" or empty
    'startpoint',  # "{'location': {'lat': xx.xxxxxx, 'lng': xx.xxxxxx, 'alt': xx.xxxxxx}}"
    'summary',  # info about surfaces
    'tags',  # e.g. "['!@sport/touringbicycle']"
    'trackSourceDevice',  # e.g. s3://backend-geodata-eu-komootproduction/saved/xxxxxxxx_xxKHht.json
    'usersetting',  # e.g. {'creator': 'xxxxxxxxxxx', 'status': 'PRIVATE', 'label': 'TODO'}
]


class KomootTours(object):
    """KomootTours class"""

    # Regular expression to match json data in tours overview page
    TOURS_REGEX = r'kmtBoot.setProps\("(.*)"\)'

    def __init__(self, tours_html):
        """Parse json data and get all fields (columns).

        :param tours_html: Tours overview html page (type: str).
        """
        self.json_data = None
        self.all_fields = set()
        match = re.search(self.TOURS_REGEX, tours_html)
        if not match:
            raise Exception('RegEx did not find tour data.')
        # remove extra escape characters from strings
        # e.g.:  \"string \\\"quoted string\\\" string continues\"
        #  =>     "string \"quoted string\" string continues"
        raw_data = match.group(1).replace(r'\"', r'"')
        raw_data = raw_data.replace(r'\\', '\\')  # replace "\\" with "\"
        self.json_data = json.loads(raw_data)
        # Not all tours have the same fields. "recorded" and "planned"
        # have different fields and some fields seem to have changed
        # over the years. Find them all:
        for tour in self.json_data['tours']:
            self.all_fields |= set(tour.keys())

    @property
    def planned(self):
        return (t for t in self.json_data['tours'] if t['type'] == 'planned')

    @property
    def recorded(self):
        return (t for t in self.json_data['tours'] if t['type'] == 'recorded')

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
            for tour in self.json_data['tours']:
                filtered_tour = {key: value for (key, value) in tour.items() if key in fields}
                writer.writerow(defaultdict(lambda: '', filtered_tour))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('tours_html', help='Komoot tours html file')
    args = parser.parse_args()
    html_text = None
    try:
        with open(args.tours_html) as html_file:
            html_text = html_file.read()
    except FileNotFoundError:
        print('Could not open {}.'.format(args.tours_html))
    if html_text:
        ktours = KomootTours(html_text)
        print(ktours)
        ktours.to_csv('tours.csv', exclude_fields=EXCLUDE_FIELDS)
        print('Converted {} to CSV file "tours.csv".'.format(args.tours_html))


if __name__ == '__main__':
    main()
