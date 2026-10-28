from xml.etree import ElementTree

import pytest

from barcode_studio.aamva import (
    fill_template,
    generate_xml,
    normalize_height,
    parse_aamva,
    parse_aamva_record,
    validate_fields,
)


def sample_fields():
    return {
        "license_number": "A1234567",
        "first_name": "John",
        "middle_name": "Mark",
        "last_name": "Doe",
        "address": "123 Main Street",
        "city": "Denver",
        "state": "CO",
        "zip_code": "800120000",
        "license_class": "C",
        "sex": "M",
        "birth_date": "01011970",
        "issue_date": "10202025",
        "expiry_date": "10202030",
        "height": "69",
        "eye_color": "BRO",
        "country": "USA",
    }


def test_fill_template_replaces_name_fields():
    text = fill_template(sample_fields())

    assert "DACJOHN" in text
    assert "DADMARK" in text
    assert "DCSDOE" in text


def test_parse_aamva_reads_known_tags():
    parsed = parse_aamva(fill_template(sample_fields()))

    assert parsed["first_name"] == "JOHN"
    assert parsed["last_name"] == "DOE"
    assert parsed["license_number"] == "A1234567"


def test_validation_requires_letter_plus_seven_digit_license_number():
    fields = sample_fields()
    fields["license_number"] = "123"

    assert "DL number must match the selected county format." in validate_fields(fields)


def test_height_accepts_feet_and_inches_without_misreading_the_digits():
    fields = sample_fields()
    fields["height"] = "5'9\""
    payload = fill_template(fields)

    assert "DAU069 IN" in payload
    assert parse_aamva_record(payload)["fields"]["height"] == "69"
    assert normalize_height("5 ft 9 in") == "069 IN"


def test_validation_rejects_non_text_field_values():
    fields = sample_fields()
    fields["first_name"] = {"unexpected": "object"}

    assert "First name must be provided as text." in validate_fields(fields)


def test_authorized_external_records_are_not_limited_to_synthetic_patterns():
    fields = sample_fields()
    fields["license_number"] = "CUSTOM-RECORD-42"
    fields["issue_date"] = "01011990"
    fields["expiry_date"] = "01011995"

    assert validate_fields(fields, record_source="external") == []


def test_generated_header_uses_actual_subfile_byte_offset_and_length():
    payload = fill_template(sample_fields())
    record = parse_aamva_record(payload)
    subfile = record["subfiles"][0]
    raw = payload.encode("ascii")

    assert raw[subfile["offset"]:subfile["offset"] + subfile["length"]].startswith(b"DAQ")
    assert subfile["offset"] + subfile["length"] == len(raw)
    assert record["version"] == "09"
    assert record["fields"]["birth_date"] == "1970-01-01"
    assert record["unsupported_fields"] == {}
    assert parse_aamva(payload)["first_name"] == "JOHN"


def test_parser_accepts_scanner_line_ending_normalization_without_losing_offsets():
    payload = fill_template(sample_fields())
    header = payload.encode("ascii")
    directory_end = 2 + len(b"ANSI ") + 6 + 2 + 2 + 2 + 10
    scanner_payload = header[:directory_end] + header[directory_end:].replace(b"\r\n", b"\n")

    record = parse_aamva_record(scanner_payload.decode("ascii"))

    assert record["transport_normalized"] is True
    assert record["raw_fields"]["DAQ"] == "A1234567"
    assert record["subfiles"][0]["offset"] == 31


def test_parser_preserves_original_raw_field_spacing():
    payload = fill_template(sample_fields())
    record = parse_aamva_record(payload)
    subfile = record["subfiles"][0]
    directory = f"DL{subfile['offset']:04d}{subfile['length']:04d}"
    payload = payload.replace(directory, f"DL{subfile['offset']:04d}{subfile['length'] + 1:04d}", 1)
    payload = payload.replace("DCSDOE\r\n", "DCSDOE \r\n", 1)

    record = parse_aamva_record(payload)

    assert record["raw_fields"]["DCS"] == "DOE "
    assert record["fields"]["last_name"] == "DOE"


def test_parser_rejects_unsupported_versions_and_invalid_subfile_lengths():
    payload = fill_template(sample_fields())

    with pytest.raises(ValueError, match="not supported"):
        parse_aamva_record(payload.replace("63602009", "63602008", 1))
    record = parse_aamva_record(payload)
    subfile = record["subfiles"][0]
    directory = f"DL{subfile['offset']:04d}{subfile['length']:04d}"
    malformed = payload.replace(directory, f"DL{subfile['offset']:04d}9999", 1)
    with pytest.raises(ValueError, match="invalid offset or length"):
        parse_aamva_record(malformed)


def test_xml_escapes_values_marks_missing_fields_and_preserves_unknown_tags():
    fields = sample_fields()
    fields["first_name"] = "A&B <C>"
    fields["XYZ"] = "CUSTOM&VALUE"
    record = parse_aamva_record(fill_template(fields))
    xml = generate_xml(record)
    root = ElementTree.fromstring(xml)

    first = root.find("./user/first")
    assert first is not None and first.text == "A&B <C>"
    assert root.find("./user/height").text == "5'9\""
    assert root.find("./user/weight").attrib["missing"] == "true"
    assert root.find("./subfile/element[@id='XYZ']").text == "CUSTOM&VALUE"
    assert [child.tag for child in root] == ["user", "head", "subfile"]
    assert "\n  <user>" in xml


def test_custom_xml_schema_supports_element_labels_and_rejects_invalid_mappings():
    record = parse_aamva_record(fill_template(sample_fields()))
    schema = [{"element": "last", "id": "DCS", "field": "last_name", "name": "Family name"}]
    root = ElementTree.fromstring(generate_xml(record, schema))

    assert root.find("./user/last").attrib == {"e": "DCS", "name": "Family name"}

    with pytest.raises(ValueError, match="field names must be strings"):
        generate_xml(record, [{"element": "last", "id": "DCS", "name": 1}])
    with pytest.raises(ValueError, match="field IDs cannot be empty"):
        generate_xml(record, [{"element": "last", "id": ""}])


def test_xml_uses_expected_head_and_preserves_optional_subfile_fields():
    dl = b"DAQX596653\r\nDCSCORDELL\r\n"
    zw = b"A\r\nB\r\nCY\r\nD\r\nE\r\n"
    prefix = b"@\nANSI 636061090002"
    directory_length = 20
    dl_offset = len(prefix) + directory_length + 2
    zw_offset = dl_offset + len(dl)
    directory = (
        f"DL{dl_offset:04d}{len(dl):04d}"
        f"ZW{zw_offset:04d}{len(zw):04d}"
    ).encode("ascii")
    payload = (prefix + directory + b"\r\n" + dl + zw).decode("ascii")

    record = parse_aamva_record(payload)
    root = ElementTree.fromstring(generate_xml(record))

    assert root.findtext("./head/filetype") == "ANSI"
    assert root.findtext("./head/issuer") == "636061"
    assert root.find("./subfile[@designator='ZW']/element[@id='C']").text == "Y"
    assert root.find("./subfile[@designator='ZW']/element[@id='A']").attrib["name"] == "Optional field A"


def test_missing_required_element_is_reported_and_left_missing_in_xml():
    fields = sample_fields()
    fields.pop("first_name")
    record = parse_aamva_record(fill_template(fields))
    root = ElementTree.fromstring(generate_xml(record))

    assert record["aamva_valid"] is False
    assert "DAC" in record["validation_errors"][0]
    assert root.find("./user/first").attrib["missing"] == "true"
