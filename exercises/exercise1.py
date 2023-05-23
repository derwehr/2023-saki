from pandas import read_csv
from sqlalchemy import create_engine

url = 'https://opendata.rhein-kreis-neuss.de/api/v2/catalog/datasets/rhein-kreis-neuss-flughafen-weltweit/exports/csv'
path = 'airports.sqlite'

# Get data
data = read_csv(url, sep=';')

# Create sqlite engine
engine = create_engine('sqlite:///' + path)

# write data to sqlite database
data.to_sql('airports', engine, if_exists='replace', index=False)
