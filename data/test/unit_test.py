from data.dataPipeline import get_path, get_lat_lon


def test_get_path():
    # arrange
    file_name = 'test.csv'
    # act
    result = get_path(file_name)
    # assert
    assert result.endswith('2023-saki/data/test.csv')


# should return the coordinates of address1
def test_get_lat_lon_first_try():
    # arrange
    address1 = 'Domkloster 4'
    address2 = 'XXX'
    # act
    result = get_lat_lon(address1, address2)
    # assert
    assert result == [50.941303500000004, 6.958137997831819]


# should return the coordinates of address2
def test_get_lat_lon_second_try():
    # arrange
    address1 = 'XXX'
    address2 = 'Domkloster 4'
    # act
    result = get_lat_lon(address1, address2)
    # assert
    assert result == [50.941303500000004, 6.958137997831819]


# should return None if both addresses could not be found
def test_get_lat_lon_none():
    # arrange
    address1 = 'XXX'
    address2 = 'YYY'
    # act
    result = get_lat_lon(address1, address2)
    # assert
    assert result == [None, None]
