from io import BytesIO

from app import app
from barcode_studio.aamva import fill_template
from test_aamva import sample_fields


def test_generate_decode_and_parse_preserve_pdf417_payload(tmp_path, monkeypatch):
    monkeypatch.setattr("app.OUTPUT_DIR", tmp_path)
    client = app.test_client()
    generated = client.post(
        "/api/generate",
        json={
            "fields": sample_fields(),
            "record_source": "test",
            "settings": {"width": 900, "height": 240},
        },
    )

    assert generated.status_code == 200
    result = generated.get_json()
    assert result["round_trip"] == {"payload_preserved": True, "aamva_valid": True}
    assert result["record_source"] == "test"
    assert "<last e=\"DCS\">Doe</last>" in result["xml"]
    barcode = (tmp_path / "pdf417_barcode.png").read_bytes()

    decoded = client.post(
        "/api/decode",
        data={"image": (BytesIO(barcode), "barcode.png")},
        content_type="multipart/form-data",
    )
    assert decoded.status_code == 200
    assert decoded.get_json()["decoded_text"] == result["encoded_text"]
    assert decoded.get_json()["is_aamva"] is True

    parsed = client.post("/api/parse", json={"payload": result["encoded_text"]})
    assert parsed.status_code == 200
    assert parsed.get_json()["aamva_record"]["aamva_valid"] is True


def test_raw_payload_parse_reports_generic_data_as_not_aamva():
    response = app.test_client().post("/api/parse", json={"payload": "generic barcode text"})

    assert response.status_code == 422
    assert response.get_json()["is_aamva"] is False


def test_upload_reports_unreadable_images():
    response = app.test_client().post(
        "/api/decode",
        data={"image": (BytesIO(b"not an image"), "invalid.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert "Unable to decode PDF417" in response.get_json()["errors"][0] or "cannot identify image" in response.get_json()["errors"][0]
