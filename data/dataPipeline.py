import os.path
import pandas as pd
import numpy as np
import urllib.request

source_path = 'https://offenedaten-koeln.de/sites/default/files/'
source_files = {
    'offenses': 'Geschwindigkeit%C3%BCberwachung_Koeln_Gesamt_2017-2021.csv',
    'stationary': 'Stationaerstandorte_2017-2019_0.csv',
    'mobile': 'Mobilstandorte_2017-2019_0.csv',
    'combo': 'Kombistandorte_Geschwindigkeit-und_oder_Rotlichtfaelle%202017-2019_0.csv'
}
script_dir = os.path.dirname(os.path.abspath(__file__))

# download sources if not already downloaded, as these files are static
# and dont need to be requested every time the script is run
for file in source_files.values():
    target = os.path.join(script_dir, file)
    if not os.path.isfile(target):
        print('Could not find ' + file + ', downloading from source.')
        urllib.request.urlretrieve(source_path + file, target)

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

# Read data from source
print('Reading data from ' + source_files['offenses'])
offenses = pd.read_csv(os.path.join(script_dir, source_files['offenses']), low_memory=False,
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

# read location files
print('Reading location files')
loc_headers = ['year', 'location', 'allowed speed car',
               'allowed speed truck', 'address1', 'address2', 'address3']
loc_cols = ['location', 'address1', 'address2']
loc_stat = pd.read_csv(os.path.join(script_dir, source_files['stationary']), sep=';',
                       encoding='latin-1', names=loc_headers, skiprows=1, usecols=loc_cols)
loc_mob = pd.read_csv(os.path.join(script_dir, source_files['mobile']), sep=';',
                      encoding='latin-1', names=loc_headers, skiprows=1, usecols=loc_cols)
loc_combo = pd.read_csv(os.path.join(script_dir, source_files['combo']), sep=';',
                        encoding='latin-1', names=loc_headers, skiprows=1, usecols=loc_cols)

# to improve performce, load each sources' location values into a set
loc_stat_set = set(loc_stat['location'].astype(int))
loc_mob_set = set(loc_mob['location'].astype(int))
loc_combo_set = set(loc_combo['location'].astype(int))

# create a mapping of location prefixes to location sources
location_sources = {
    'S-': loc_stat,
    'M-': loc_mob,
    'K-': loc_combo
}


def get_location_data(row, location_sources):
    location2 = row['location2']
    location3 = row['location3']
    if location2.isnumeric():
        # On some tables the columns are shifted to the left
        location2 = row['location1']
        location3 = row['location2']
    # use the corresponding location source based on the prefix
    source = location_sources[location2[:2]]
    # search for the location in the source
    location = int(location3)
    idx = np.where(source['location'].values == location)[0]
    if len(idx) > 0:
        # return the address data if the location is found
        return source.iloc[idx[0]][['address1', 'address2']].values
    # return None if no location data is found
    return [None, None]


# loop through all offenses and add location data
print('Adding location data to offenses')
offenses[['address1', 'address2']] = np.vstack(
    offenses.apply(get_location_data, axis=1, location_sources=location_sources))

# drop rows without address data
offenses = offenses[offenses['address1'].notna()]

# drop location columns
offenses = offenses.drop(['location1', 'location2', 'location3'], axis=1)

# write data to sqlite database
print('Writing data to database')
offenses.to_sql('offenses', 'sqlite:///' + os.path.join(script_dir, 'data.db'),
                if_exists='replace', index=False)
print('Done')
