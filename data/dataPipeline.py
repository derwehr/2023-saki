from datetime import timedelta
from os.path import abspath, dirname, isfile, join
from numpy import vstack
from urllib.request import urlretrieve
from geocoder import osm
from requests_cache import install_cache, uninstall_cache
from sys import exit
from pandas import read_csv, to_datetime
from meteostat import Hourly, Point

source_path = 'https://offenedaten-koeln.de/sites/default/files/'
offenses_file = 'Geschwindigkeit%C3%BCberwachung_Koeln_Gesamt_2017-2021.csv'
location_files = {
    'S-': 'Stationaerstandorte_2017-2019_0.csv',
    'M-': 'Mobilstandorte_2017-2019_0.csv'
}
loc_headers = ['year', 'location', 'allowed speed car',
               'allowed speed truck', 'address1', 'address2', 'address desc']
loc_cols = ['location', 'address1', 'address2']
location_sources = dict()
script_dir = dirname(abspath(__file__))


def get_path(filename):
    '''
    Returns the absolute path of a file in the same directory as this script.

    Parameters
    ----------
    filename : string
        The name of the file.

    Returns
    -------
    string
        The absolute path of the file.
    '''
    return join(script_dir, filename)


def download_file(file, target):
    '''
    Downloads a file from a source and saves it to target.

    Parameters
    ----------
    file : string
        The name of the file to be downloaded.
    target : string
        The path where the file should be saved.
    '''
    if not isfile(target):
        print('Downloading ' + file + ' from source.')
        urlretrieve(source_path + file, target)


def get_lat_lon(address1, address2):
    '''
    Takes two address strings and returns the coordinates of the first address
    that could be geocoded.

    Parameters
    ----------
    address1 : string
        The first address to be geocoded.
    address2 : string
        The second address to be geocoded.

    Returns
    -------
    tuple
        A tuple containing the latitude and longitude of the address.
    '''
    location = osm(address1 + 'Köln, Germany')
    if location.ok:
        return location.latlng
    else:
        # try address2
        location = osm(address2 + 'Köln, Germany')
        if location.ok:
            return location.latlng
    # return None if address could not be found
    return [None, None]


def process_location_file(prefix, file):
    '''
    Downloads a location file and adds latitude and longitude columns.

    Parameters
    ----------
    prefix : string
        The prefix of the location file.
    file : string
        The name of the location file.

    Returns
    -------
    '''
    target = get_path(file)
    if not isfile(target):
        print('Could not find ' + file)
        download_file(file, target)
        location_sources[prefix] = read_csv(target, sep=';', encoding='latin-1', names=loc_headers,
                                            skiprows=1, usecols=loc_cols)
        location_sources[prefix]['lat'], location_sources[prefix]['lon'] = zip(
            *location_sources[prefix].apply(
                lambda row: get_lat_lon(row['address1'], row['address2']), axis=1))
        location_sources[prefix] = location_sources[prefix].drop(['address1', 'address2'], axis=1)
        # drop rows with empty lat and lon
        location_sources[prefix] = location_sources[prefix][
            location_sources[prefix]['lat'].notnull()]
        location_sources[prefix].to_csv(target, index=False, sep=';', encoding='latin-1')
    else:
        print('Reading location data from ' + file)
        location_sources[prefix] = read_csv(target, sep=';', encoding='latin-1')


def get_location_data(row):
    '''
    Takes a row with location data and returns the coordinates of the location.

    Parameters
    ----------
    row : pandas.Series
        The row containing the location data.

    Returns
    -------
    tuple
        A tuple containing the latitude and longitude of the location.
    '''
    location2 = row['location2']
    location3 = row['location3']
    if location2.isnumeric():
        # On some rows the columns are shifted to the left
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


def get_weather_data(row):
    '''
    Takes a row with coordinates and returns the weather data for that location.

    Parameters
    ----------
    row : pandas.Series
        A row of the offenses dataframe.

    Returns
    -------
    '''
    point = Point(row['lat'], row['lon'])
    # find the weather station closest to the coordinates
    start = row['datetime'].to_pydatetime()
    end = start + timedelta(hours=2)
    hourly = Hourly(point, start=start, end=end).fetch()
    return [hourly['temp'].iloc[0], hourly['prcp'].iloc[0], hourly['wspd'].iloc[0]]


def main():
    # download the offenses file if it does not exist
    if not isfile(get_path(offenses_file)):
        print('Could not find ' + offenses_file)
        download_file(offenses_file, get_path(offenses_file))

    # enable cache for geocoder requests
    install_cache(get_path('geocoder_cache'), backend='sqlite', expire_after=3600)
    # download and process the location files
    for prefix, file in location_files.items():
        process_location_file(prefix, file)

    # disable cache for geocoder requests
    uninstall_cache()

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
    offenses = read_csv(get_path(offenses_file), low_memory=False, sep=';', encoding='latin-1',
                        names=col_names_offenses, skiprows=1, usecols=[2, 3, 6, 8, 9, 10],
                        keep_default_na=False)

    # drop rows where location2 is empty
    offenses = offenses[offenses['location2'] != '']

    # Parse date and time
    print('Parsing date and time')
    # zero pad date and time to length 6
    offenses['date'] = offenses['date'].apply('{:0>6}'.format)
    offenses['time'] = offenses['time'].apply('{:0>6}'.format)
    # convert date and time to datetime
    offenses['datetime'] = to_datetime(offenses['date'] + offenses['time'], format='%d%m%y%H%M%S')
    # drop date and time columns
    offenses = offenses.drop(['date', 'time'], axis=1)

    # loop through all offenses and add location data
    print('Adding coordinates to offenses')
    offenses[['lat', 'lon']] = vstack(
        offenses.apply(get_location_data, axis=1))

    # drop rows without address data
    offenses = offenses[offenses['lat'].notna()]

    # drop location columns
    offenses = offenses.drop(['location1', 'location2', 'location3'], axis=1)

    # Add weather data
    print('Adding weather data to offenses')
    offenses[['temperature', 'precipitation', 'wind speed']] = vstack(offenses.apply(
        get_weather_data, axis=1))

    # drop rows without weather data
    offenses = offenses[offenses['temperature'].notna()]

    # write data to sqlite database
    print('Writing data to database')
    offenses.to_sql('offenses', 'sqlite:///' + get_path('data.sqlite'), if_exists='replace',
                    index=False)
    print('Done')


if __name__ == "__main__":
    exit(main())
