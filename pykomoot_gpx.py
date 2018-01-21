#!/usr/bin/env python
"""Download all planned or recorded tours from Komoot in the gpx format.

The directory will be created if does not exist. The name of the gpx files
follows the scheme <date>_<tour_id>.gpx. Tours which are already present
in the given directory are not downloaded again.

The tour overview page (tours.html) is stored in the current directory.
"""
import argparse
import getpass
import os

import requests

from pykomoot_tours import KomootTours

_URLS = {
    'user_exists': 'https://www.komoot.de/api/v007/account/user_exists?email={email}',
    'login': 'https://www.komoot.de/webapi/v006/auth/cookie',
    'private': 'https://www.komoot.de/api/v006/users/{username}/private',
    'profile': 'https://www.komoot.de/api/v006/users/{username}/private/profile',
    'tours': 'https://www.komoot.de/user/{username}/tours',
    'download': 'https://www.komoot.de/tour/{tourname}/download',
}


def _save_response(response, file_name):
    """Save requests response to file."""
    with open(file_name, 'wb') as file:
        file.write(response.content)


class PyKomoot(object):
    """PyKomoot"""
    def __init__(self, email, password):
        """Login to komoot.de and get tour data.

        :param email: Login email adress.
        :param password: Login password.
        """
        self.email = email
        self.session = requests.Session()
        self.username = None  # actually user ID as obtained from Komoot
        self.response_tours = None  # requests response of tour overview page
        self.tours = {'recorded': [], 'planned': []}
        # login
        session = self.session
        response = session.get(_URLS['user_exists'].format(email=email))
        response.raise_for_status()
        response = session.post(_URLS['login'], data={'username': email, 'password': password})
        response.raise_for_status()
        # get username (user ID) from komoot
        response = session.get(_URLS['login'])
        self.username = response.json()['username']
        # get tour overview page
        response = session.get(_URLS['tours'].format(username=self.username))
        response.raise_for_status()
        self.response_tours = response
        ktours = KomootTours(response.text)
        self.tours['planned'] = [t for t in ktours.json_data['tours'] if t['type'] == 'planned']
        self.tours['recorded'] = [t for t in ktours.json_data['tours'] if t['type'] == 'recorded']

    def __str__(self):
        ret = []
        ret.append('User:           {} ({})'.format(self.email, self.username))
        ret.append('Tours planned:  {}'.format(len(self.tours['planned'])))
        # get total distance
        distances = (float(t['distance']) for t in self.tours['recorded'])
        ret.append('Tours recorded: {} (total distance: {:.0f} km)'.format(len(self.tours['recorded']), sum(distances) / 1000))
        return '\n'.join(ret)

    def download_tour(self, tourname):
        """Download one tour and return text response.

        :param tourname: ID of tour to download.
        :returns: GPX file as text (type: str)
        """
        response = self.session.get(_URLS['download'].format(tourname=str(tourname)))
        return response.text

    def __del__(self):
        self.session.close()


def main():
    """Example program to download gpx tracks."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('email', help='login email address for Komoot')
    parser.add_argument('password', nargs='?', help='will be prompted if not given')
    parser.add_argument('-p', '--planned', help='directory to download planned tours to')
    parser.add_argument('-r', '--recorded', help='directory to download recored tours to')
    args = parser.parse_args()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Komoot password: ')
    tour_type = 'planned' if args.planned else 'recorded'
    download_dir = args.planned if args.planned else args.recorded
    komoot = PyKomoot(args.email, password)
    print(komoot)
    if komoot.response_tours:
        _save_response(komoot.response_tours, 'tours.html')
        print('Saved tour overview page to "tours.html"')
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        files_skipped = 0
        for tour in komoot.tours[tour_type]:
            tourname = tour['id']
            tourdate = tour['recordedAt'].split()[0]  # get date from string '2016-12-17 13:08:39 +0000'
            out_file_path = os.path.join(download_dir, '{}_{}.gpx'.format(tourdate, tourname))
            if os.path.exists(out_file_path):
                files_skipped += 1
                continue
            gpx = komoot.download_tour(tourname)
            with open(out_file_path, 'w') as out_file:
                out_file.write(gpx)
            print('  ', out_file_path)
        if files_skipped:
            print('Skipped downloading of {} files'.format(files_skipped))


if __name__ == '__main__':
    main()
