from os import path
import data.dataPipeline as dp

def test_system():
    dp.offenses_file = 'test/test_data.csv'
    dp.output_db = 'test_data.sqlite'

    dp.main()
    
    # assert that the database was created
    assert path.isfile(dp.get_path(dp.output_db))

