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
import sys

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
    def __init__(self):
        self.email = None
        self.session = requests.Session()
        self.username = None  # actually user ID as obtained from Komoot
        self.response_tours = None  # requests response of tour overview page

    def login(self, email, password):
        """Login to komoot.de and get username (ID).

        :param email: Login email address.
        :param password: Login password.
        """
        # login
        self.email = email
        session = self.session
        response = session.get(_URLS['user_exists'].format(email=self.email))
        response.raise_for_status()
        response = session.post(_URLS['login'], data={'username': self.email, 'password': password})
        response.raise_for_status()
        # get username (user ID) from komoot
        response = session.get(_URLS['login'])
        self.username = response.json()['username']

    def get_tour_overview(self):
        """Download tour overview page and create KomootTours object.

        :returns: Instance of KomootTours
        """
        self.response_tours = None
        session = self.session
        response = session.get(_URLS['tours'].format(username=self.username))
        response.raise_for_status()
        self.response_tours = response
        return KomootTours(response.text)

    def __str__(self):
        ret = []
        if self.username:
            ret.append('User:           {} ({})'.format(self.email, self.username))
        else:
            ret.append('User:           Not logged in.')
        return '\n'.join(ret)

    def download_tour(self, tourname):
        """Download one tour and return as requests response.

        :param tourname: ID of tour to download.
        :returns: GPX file as text (type: str)
        """
        response = self.session.get(_URLS['download'].format(tourname=str(tourname)))
        response.raise_for_status()
        return response

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
    download_dir = args.planned if args.planned else args.recorded
    komoot = PyKomoot()
    ktours = None
    try:
        komoot.login(args.email, password)
    except requests.exceptions.HTTPError:
        print('Failed to log in to komoot.de. Check given mail and password.')
        sys.exit(1)
    try:
        ktours = komoot.get_tour_overview()
    except requests.exceptions.HTTPError:
        print('Failed to download komoot tour overview page.')
        sys.exit(1)
    finally:
        # If we successfuly got a tour overview page save it in any case.
        if komoot.response_tours:
            _save_response(komoot.response_tours, 'tours.html')
            print('Saved tour overview page to "tours.html"')
    print('')
    print(komoot)
    print(ktours)
    if download_dir:
        print('Downloading GPX files:')
        os.makedirs(download_dir, exist_ok=True)
        files_skipped = 0
        tours = ktours.planned if args.planned else ktours.recorded
        for tour in tours:
            tourname = tour['id']
            tourdate = tour['recordedAt'].split()[0]  # get date from string '2016-12-17 13:08:39 +0000'
            out_file_path = os.path.join(download_dir, '{}_{}.gpx'.format(tourdate, tourname))
            if os.path.exists(out_file_path):
                files_skipped += 1
                continue
            try:
                response_gpx = komoot.download_tour(tourname)
            except requests.exceptions.HTTPError:
                print('  Failed to download: ', out_file_path)
                continue
            _save_response(response_gpx, out_file_path)
            print('  ', out_file_path)
        if files_skipped:
            print('Skipped downloading of {} files which are already present.'.format(files_skipped))


if __name__ == '__main__':
    main()
