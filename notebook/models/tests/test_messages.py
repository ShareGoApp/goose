import pytest
from datetime import datetime

# functions to test
from models.messages import MatchRequest
from models.messages import GeoRequest
from models.messages import SaveRequest


@pytest.fixture
def valid_match_request_data():
    return {"passenger_id": "passenger_123", "driver_ids": ["driver_1", "driver_2"]}


@pytest.fixture
def invalid_match_request_data():
    return {"passenger_id": "passenger_123", "driver_ids": "invalid_data"}


@pytest.fixture
def valid_geo_request_data():
    return {"passenger_id": "passenger_123", "max_radius": 10}


@pytest.fixture
def invalid_geo_request_data():
    return {"passenger_id": "passenger_123", "max_radius": "invalid_data"}


@pytest.fixture
def valid_save_request_data():
    return {
        "created_at": datetime.now(),
        "passenger_id": "passenger_123",
        "driver_id": "driver_123",
        "min_err": 0.5,
    }


@pytest.fixture
def invalid_save_request_data():
    return {
        "created_at": "invalid_data",
        "passenger_id": "passenger_123",
        "driver_id": "driver_123",
        "min_err": 0.5,
    }


def test_valid_match_request(valid_match_request_data):
    assert MatchRequest(**valid_match_request_data)


def test_invalid_match_request(invalid_match_request_data):
    with pytest.raises(ValueError):
        MatchRequest(**invalid_match_request_data)


def test_valid_geo_request(valid_geo_request_data):
    assert GeoRequest(**valid_geo_request_data)


def test_invalid_geo_request(invalid_geo_request_data):
    with pytest.raises(ValueError):
        GeoRequest(**invalid_geo_request_data)


def test_valid_save_request(valid_save_request_data):
    assert SaveRequest(**valid_save_request_data)


def test_invalid_save_request(invalid_save_request_data):
    with pytest.raises(ValueError):
        SaveRequest(**invalid_save_request_data)
