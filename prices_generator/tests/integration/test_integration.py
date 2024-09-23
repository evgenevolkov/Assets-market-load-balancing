"""Ingegration tests suite"""

import uuid
from fastapi.testclient import TestClient
from fastapi import Response, status
import pytest

from app.app import app


BASE_URL = "/price"
STATUS_UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
STATUS_OK = status.HTTP_200_OK


@pytest.fixture(name="client", scope="function")
def client_fixture():
    """Get FastAPI testclient"""
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
        "market, asset_name", [
            ("US", "Oil"),
            ("UK", "Oil"),
        ]
    )
def test_valid_price_quote_returns_expected_response(
    market: str, asset_name: str, client: TestClient
    ):
    """Simulate a valid API request and verify the response structure
    and content. Asumes an endpoint to generates price for asset 'Oil' 
    at 'US' and 'UK' markets.
    """
    response = client.get(
        f"{BASE_URL}?market={market}&asset_name={asset_name}")
    assert "application/json" in response.headers["Content-Type"], (
            "Expected JSON response")

    response_json = convert_to_json(response)

    expected_keys = ['name', 'market', 'price']
    assert_dict_contains_keys(expected_keys=expected_keys,
                              dict_obj=response_json)

    assert response.status_code == STATUS_OK
    assert response_json["name"] == asset_name
    assert response_json["market"] == market

    # price expected to be convertible to int or float and be greater than 0
    price = response_json["price"]
    assert isinstance(price, (int, float)), (
        f"Expected `price` be of type int or float, got: {type(price)}")
    assert 0 < float(price), (
        f"Expected `price` value greater than 0, got: {price}")

    # price_quote_id should be a UUID
    price_quote_id = response_json["price_quote_id"]
    assert isinstance(price_quote_id, str), (
        f"Expected `price_quote_id` to be of type str,"
        f" got: {type(price_quote_id)}")
    try:
        uuid.UUID(price_quote_id)
    except ValueError as e:
        raise AssertionError(
            f"Expected `price_quote_id` to be a valid UUID,"
            f" got: {price_quote_id}, error message: {e}"
        ) from e


def check_invalid_price_quote_response(
        response: Response,
        expected_status_code: int,
        expected_detail: dict
        ) -> None:
    """Validates response of price quote with incomplete or empty
    parameters. It does not validate invalid parameters or non-existing
    values. 
    
    Parameters:
        response: raw FastAPI test client call response
        expected_status_code: status code that is expected in response
        expected_detail: dictionary with expected keys and values in
        'detail' field of the JSON response. Response 'detail' is
        expected to be a list. Test is passed if at least one element
        containt expected field with expected values.
    """
    assert response.status_code == expected_status_code, (
        f"Expected status code {expected_status_code},"
        f" got {response.status_code}")
    response_json = convert_to_json(response)

    # check for presence and type of `detail` key in response
    assert_dict_contains_keys(
        expected_keys=['detail'],
        dict_obj=response_json)
    assert isinstance(response_json['detail'], list), (
        f"Expected 'detail' field of response to be a list,"
        f" got: {type(response_json['detail'])} type,"
        f" value: {response_json['detail']}. Response: {response.text}")

    # check that at least one element of `detail` list matches expected content
    if expected_detail:
        assert any(
            detail.get('type', None) == expected_detail['type']
            and detail.get('loc', None) == expected_detail['loc']
            for detail in response_json['detail']), (
            f"Expected at least one detail element with {expected_detail}"
            f", but not found. Got details list: {response_json['detail']}")


def convert_to_json(response: Response) -> dict:
    """Convert input to JSON, assert failure otherwise"""
    try:
        return response.json()
    except ValueError as e:
        assert False, (
            f"Expected response to be a valid JSON, got: {response.text},"
            f" Error message: {e}")


@pytest.mark.parametrize(
        "incomplete_query_params, missing_field", [
            # tests for incomplete parameters
            ("market=US", "asset_name"),
            ("asset_name=Oil", "market"),
            # tests for empty parameters
            ("market=", "asset_name"),
            ("asset_name=", "market"),
            # tests for missing both parameters
            ("", "market"),
            ("", "asset_name"),
        ]
    )
def test_missing_field_in_price_qoute_request(
        incomplete_query_params: str,
        missing_field: str,
        client: TestClient
        ) -> None:
    """Tests to check correct handling of queries with no or partially 
    passed parameters.
    """
    response = client.get(f"{BASE_URL}?{incomplete_query_params}")
    expected_status_code = STATUS_UNPROCESSABLE_ENTITY
    expected_detail = {
        'type': 'missing',
        'loc': ['query', missing_field],
        'msg': 'Field required',
        'input': None
    }
    check_invalid_price_quote_response(response, expected_status_code,
                                       expected_detail)


def assert_dict_contains_keys(expected_keys: list[str], dict_obj: dict) -> set:
    """Assert that all elements of expected_keys in exist in the
    dictionary dict_obj"""
    missing_keys = set(expected_keys) - set(dict_obj.keys())
    assert not missing_keys, (
        f"Missing expected keys {missing_keys} in response: {dict_obj}")
