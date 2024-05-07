from  import convert_to_unix
from  import destructure_message


def test_unix_conversion():
    sample = "2024-04-09T11:00:00Z"
    result = 1712660400
    assert convert_to_unix(sample) == result


def test_geojson_to_ndarray():
    pass


def test_destructure_message():
    message = 'mat_request:{"passenger_id": "661fc362bc83e7536732d787", "driver_ids": ["661fc59bbc83e7536732d788", "661fc5c0bc83e7536732d789"]}'
    type_info, payload = destructure_message(message)
    assert type_info == "mat_request"
    assert payload != None
