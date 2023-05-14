import os.path
import pandas as pd
import numpy as np
import urllib.request
import geocoder
import requests_cache

source_path = 'https://offenedaten-koeln.de/sites/default/files/'
offenses_file = 'Geschwindigkeit%C3%BCberwachung_Koeln_Gesamt_2017-2021.csv'
location_files = {
    'S-': 'Stationaerstandorte_2017-2019_0.csv',
    'M-': 'Mobilstandorte_2017-2019_0.csv'
}
script_dir = os.path.dirname(os.path.abspath(__file__))


def get_path(filename):
    return os.path.join(script_dir, filename)


# download sources if not already downloaded, as these files are static
# and dont need to be requested every time the script is run

# download the offenses file if it does not exist
if not os.path.isfile(get_path(offenses_file)):
    print('Could not find ' + offenses_file + ', downloading from source.')
    urllib.request.urlretrieve(source_path + offenses_file, get_path(offenses_file))    


# download location files and add lat and lon columns to csv
def get_lat_lon(address1, address2):
    location = geocoder.osm(address1 + 'Köln, Germany')
    if location.ok:
        return location.latlng
    else:
        # try address2
        location = geocoder.osm(address2 + 'Köln, Germany')
        if location.ok:
            return location.latlng
        else:
            # return None if address could not be found
            return [None, None]


loc_headers = ['year', 'location', 'allowed speed car',
               'allowed speed truck', 'address1', 'address2', 'address desc']
loc_cols = ['location', 'address1', 'address2']

# cache geocoder requests
requests_cache.install_cache(get_path('geocoder_cache'), backend='sqlite', expire_after=3600)

location_sources = dict()

for prefix, file in location_files.items():
    target = get_path(file)
    if not os.path.isfile(target):
        print('Could not find ' + file + ', downloading from source.')
        urllib.request.urlretrieve(source_path + file, target)
        location_sources[prefix] = pd.read_csv(target, sep=';', encoding='latin-1',
                                               names=loc_headers, skiprows=1, usecols=loc_cols)
        location_sources[prefix]['lat'], location_sources[prefix]['lon'] = zip(
            *location_sources[prefix].apply(lambda row: get_lat_lon(row['address1'], row['address2']), axis=1))
        location_sources[prefix] = location_sources[prefix].drop(
            ['address1', 'address2'], axis=1)
        # drop rows with empty lat and lon
        location_sources[prefix] = location_sources[prefix][
            location_sources[prefix]['lat'].notnull()]
        location_sources[prefix].to_csv(target, index=False, sep=';', encoding='latin-1')
    else:
        print('Reading location data from ' + file)
        location_sources[prefix] = pd.read_csv(target, sep=';', encoding='latin-1')

requests_cache.uninstall_cache()

# Read offenses data
col_names_offenses = [
    'year',
    'month',
    'date',
    'time',
    'location-license plate',
    'speed',
    'exceedance',
    'vehicle type',
    'location1',
    'location2',
    'location3'
]

print('Reading data from ' + offenses_file)
offenses = pd.read_csv(get_path(offenses_file), low_memory=False,
                       sep=';', encoding='latin-1', names=col_names_offenses, skiprows=1,
                       usecols=[2, 3, 6, 8, 9, 10], keep_default_na=False)

# drop rows where location2 is empty
offenses = offenses[offenses['location2'] != '']

# Parse date and time
print('Parsing date and time')
# zero pad date and time to length 6
offenses['date'] = offenses['date'].apply('{:0>6}'.format)
offenses['time'] = offenses['time'].apply('{:0>6}'.format)
# convert date and time to datetime
offenses['datetime'] = pd.to_datetime(offenses['date'] + offenses['time'], format='%d%m%y%H%M%S')
# drop date and time columns
offenses = offenses.drop(['date', 'time'], axis=1)


def address_to_coords(address):
    '''
    Takes a row with address data and returns the coordinates of the address.

    Parameters
    ----------
    address : string
        The address to be geocoded.

    Returns
    -------
    tuple
        A tuple containing the latitude and longitude of the address.
    '''
    g = geocoder.osm(address)

    if g.ok:
        # return coordinates if address was found
        return g.latlng
    else:
        # return None if address was not found
        return None


def get_location_data(row):
    location2 = row['location2']
    location3 = row['location3']
    if location2.isnumeric():
        # On some tables the columns are shifted to the left
        location2 = row['location1']
        location3 = row['location2']
    # use the corresponding location source based on the prefix
    if location2[:2] not in location_sources:
        return [None, None]
    source = location_sources[location2[:2]]
    # search for the location in the source
    location_data = source[source['location'] == int(location3)]
    if len(location_data) > 0:
        # return the coordinates if the location was found
        return [location_data['lat'].iloc[0], location_data['lon'].iloc[0]]
    # return None if no location data is found
    return [None, None]


# loop through all offenses and add location data
print('Adding coordinates to offenses')
offenses[['lat', 'lon']] = np.vstack(
    offenses.apply(get_location_data, axis=1))

# drop rows without address data
offenses = offenses[offenses['lat'].notna()]

# drop location columns
offenses = offenses.drop(['location1', 'location2', 'location3'], axis=1)

# write data to sqlite database
print('Writing data to database')
offenses.to_sql('offenses', 'sqlite:///' + get_path('data.sqlite'),
                if_exists='replace', index=False)
print('Done')
