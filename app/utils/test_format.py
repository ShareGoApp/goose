from format import convert_to_unix


def test_unix_conversion():
    sample = "2024-04-09T11:00:00Z"
    result = 1712660400
    assert convert_to_unix(sample) == result
