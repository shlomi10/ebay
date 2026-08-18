from utils.price_parser import parse_items_total, parse_price


def test_parse_usd_with_comma():
    assert parse_price("US $1,234.56") == 1234.56


def test_parse_range_takes_minimum():
    assert parse_price("$10.00 to $25.50") == 10.0


def test_parse_european_decimal():
    assert parse_price("EUR 12,99") == 12.99


def test_parse_empty():
    assert parse_price("") is None
    assert parse_price(None) is None


def test_parse_items_total_ignores_shipping():
    text = "Order summary\nItems (3) ILS 17.78\nShipping ILS 432.15\nSubtotal ILS 449.93"
    assert parse_items_total(text) == 17.78

