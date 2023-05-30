from os import path
import sqlalchemy
import data.dataPipeline as dp

def test_system():
    dp.offenses_file = 'test/test_data.csv'
    dp.output_db = 'test_data.sqlite'
    columns = ('exceedance', 'datetime', 'lat', 'lon', 'temperature', 'precipitation', 'wind speed')
    values = (13, '2017-01-01 00:00:28.000000', 50.958512, 6.9243939, -3.7, 0, 10.1)

    dp.main()
    
    # assert that the database was created
    output_file = dp.get_path(dp.output_db)
    assert path.exists(output_file)
    # assert that the table was created
    engine = sqlalchemy.create_engine(f'sqlite:///{output_file}')
    assert sqlalchemy.inspect(engine).has_table('offenses')
    # assert that the table has the correct columns
    connection = engine.connect()
    output = connection.execute(sqlalchemy.text('SELECT * FROM offenses'))
    assert output.keys() == columns
    # assert that the table has the correct number of rows
    output_rows = output.fetchall()
    assert len(output_rows) == 1
    # assert that the table has the correct values
    assert output_rows[0] == values
