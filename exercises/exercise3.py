import pandas as pd

url = 'https://www-genesis.destatis.de/genesis/downloads/00/tables/46251-0021_00.csv'
path = 'cars.sqlite'
table_name = 'cars'

headers = ['date', 'CIN', 'name', 'petrol', 'diesel', 'gas', 'electro', 'hybrid', 'plugInHybrid', 'others']
cols = [0, 1, 2, 12, 22, 32, 42, 52, 62, 72]
df = pd.read_csv(url, skiprows=7, skipfooter=4, sep=';', encoding='latin1', names=headers, usecols=cols)

# validate data
df.dropna(subset=['date', 'name', 'CIN'], inplace=True)
df['date'] = df['date'].astype(str)
df['name'] = df['name'].astype(str)
df['CIN'] = df['CIN'].astype(str).str.zfill(5)

# all other columns should be positive integers > 0
numeric_cols = ['petrol', 'diesel', 'gas', 'electro', 'hybrid', 'plugInHybrid', 'others']
df = df.dropna(subset=numeric_cols)
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=numeric_cols)
df = df[(df[numeric_cols] > 0).all(axis=1)]

# use fitting SQLite data types
dtypes = {'date': 'string', 'CIN': 'string', 'name': 'string', 'petrol': 'int', 'diesel': 'int', 'gas': 'int',
          'electro': 'int', 'hybrid': 'int', 'plugInHybrid': 'int', 'others': 'int'}
df = df.astype(dtypes)

df.to_sql(table_name, 'sqlite:///' + path, if_exists='replace', index=False)
