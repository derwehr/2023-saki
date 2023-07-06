from urllib.request import urlretrieve
from zipfile import ZipFile
from pandas import read_csv

url = "https://gtfs.rhoenenergie-bus.de/GTFS.zip"

response = urlretrieve(url, "GTFS.zip")
with ZipFile("GTFS.zip") as zip:
    zip.extractall("ex5_data")

# Only the columns stop_id, stop_name, stop_lat, stop_lon, zone_id
cols = [0,2,4,5,6]
# Pick out only stops (from stops.txt)
df = read_csv('ex5_data/stops.txt', delimiter=',', usecols = cols)
# Only keep stops from zone 2001
df = df[df['zone_id'] == 2001]
# stop_lat/stop_lon must be a geographic coordinates between -90 and 90, including upper/lower bounds
df = df[(df['stop_lat'] >= -90) & (df['stop_lat'] <= 90)]
df = df[(df['stop_lon'] >= -90) & (df['stop_lon'] <= 90)]
# Write data into a SQLite database called “gtfs.sqlite”, in the table “stops”
df.to_sql('stops', 'sqlite:///gtfs.sqlite', if_exists='replace', index=False)
