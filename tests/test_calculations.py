from barcode_studio.calculations import calculate_dd, calculate_icn, document_number_from_license, expiry_from_issue


def test_expiry_uses_same_month_day_plus_five_years():
    assert expiry_from_issue("10202025") == "10202030"


def test_dd_uses_issue_date_document_number_and_expiry_year():
    assert calculate_dd("10202025", "10202030", "29400") == "10/20/202529400/AAFD/30"


def test_icn_uses_issue_year_day_of_year_document_and_suffix():
    assert calculate_icn("10202025", "D1234567") == "25293D12345670401"


def test_document_number_can_be_derived_from_license():
    assert document_number_from_license("D1234567") == "34567"
