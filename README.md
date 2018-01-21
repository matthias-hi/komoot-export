# komoot-export

Export GPS tracks and tour data from komoot.de

## Disclaimer

This repository is in NO way affiliated to Komoot. It uses non-publicly documented APIs to extract user data and will cease to work as soon as their APIs change.

## Overview

The repository contains two scripts

* __pykomoot_gpx.py__ Download GPX tracks of planned and recorded tours.
* __pykomoot_tours.py__ Store tour data (e.g. creation time, duration, name, ...) in a CSV file.

## Requirements

* Recent version of Python 3
* requests

E.g. with [Conda](https://conda.io/docs/ "Conda") installed, run

```
$ git clone https://github.com/matthias-hi/komoot-export.git komoot-export
$ cd komoot-export
$ source activate pykomoot-env
```

## pykomoot_gpx.py

### Limitations

* Only login via mail + password has been implemented and tested (means no Facebook login).
* The script has been tested with an account having the "Complete Package" (all regions) unlocked.

### Examples

Download all "recorded" tours into directory "gpx_download/recorded/"
```
$ ./pykomoot_gpx.py -r gpx_download/recorded/ <email>
```

Download all "planned" tours into directory "gpx_download/planned/"
```
$ ./pykomoot_gpx.py -p gpx_download/planned/ <email>
```

Only download tours.html used as input for pykomoot_tours.py
```
$ ./pykomoot_gpx.py <email>
```

## pykomoot_tours.py

### Examples

Convert tours.html to tours.csv
```
$ ./pykomoot_tours.py tours.html
```

Get tours.html either by running pykomoot_gpx.py or by downloading the page manually. To download manually navigate to "Profile" -> "Tours" page and download this page with your browser.
