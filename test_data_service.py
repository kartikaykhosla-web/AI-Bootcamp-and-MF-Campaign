from data_service import extract_records, mask_contact, normalize_records


def test_extracts_supplied_envelope():
    payload = {"success": True, "data": {"currentPage": 1, "totalPages": 2, "dataList": [{"id": 1}]}}
    rows, meta = extract_records(payload)
    assert rows == [{"id": 1}]
    assert meta["totalPages"] == 2


def test_normalizes_money_status_and_dates():
    frame = normalize_records([{"id": 1, "payable_amount": "499.50", "payment_status": "Success", "created_at": "2026-08-17T16:25:42.000Z"}])
    assert frame.loc[0, "payable_amount"] == 499.5
    assert frame.loc[0, "payment_status"] == "success"
    assert str(frame.loc[0, "created_at"].tzinfo) == "UTC"


def test_masks_contacts():
    assert mask_contact("someone@example.com", "email") == "so***@example.com"
    assert mask_contact("9876543210", "phone") == "******3210"
