from sales_summary import parse_sales_csv, total_by_customer, top_customer


CSV_TEXT = """customer,item,quantity,unit_price
Alice,Notebook,2,4.50
Bob,Pen,10,1.20
Alice,Backpack,1,35.00
Charlie,Notebook,3,4.50
Bob,Notebook,1,4.50
"""


def test_parse_sales_csv_returns_records():
    records = parse_sales_csv(CSV_TEXT)

    assert records == [
        {
            "customer": "Alice",
            "item": "Notebook",
            "quantity": 2,
            "unit_price": 4.50,
            "total": 9.00,
        },
        {
            "customer": "Bob",
            "item": "Pen",
            "quantity": 10,
            "unit_price": 1.20,
            "total": 12.00,
        },
        {
            "customer": "Alice",
            "item": "Backpack",
            "quantity": 1,
            "unit_price": 35.00,
            "total": 35.00,
        },
        {
            "customer": "Charlie",
            "item": "Notebook",
            "quantity": 3,
            "unit_price": 4.50,
            "total": 13.50,
        },
        {
            "customer": "Bob",
            "item": "Notebook",
            "quantity": 1,
            "unit_price": 4.50,
            "total": 4.50,
        },
    ]


def test_total_by_customer():
    records = parse_sales_csv(CSV_TEXT)

    assert total_by_customer(records) == {
        "Alice": 44.00,
        "Bob": 16.50,
        "Charlie": 13.50,
    }


def test_top_customer():
    records = parse_sales_csv(CSV_TEXT)

    assert top_customer(records) == ("Alice", 44.00)


def test_empty_input():
    assert parse_sales_csv("") == []
    assert total_by_customer([]) == {}
    assert top_customer([]) is None