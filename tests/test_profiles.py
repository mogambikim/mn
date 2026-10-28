import re

import app as application


def test_six_jurisdiction_profiles_are_registered_in_existing_selectors():
    templates = application.load_templates()
    counties = application.load_counties()

    assert set(application.JURISDICTION_PROFILES) <= set(templates)
    assert {
        profile_id
        for profile_id, config in templates.items()
        if config.get("jurisdictionProfile")
    } >= set(application.JURISDICTION_PROFILES)
    assert {
        item["template"] for item in counties if item.get("template")
    } >= set(application.JURISDICTION_PROFILES)


def test_profile_pages_render_selector_and_profile_specific_form_configuration():
    client = application.app.test_client()
    counties = {item["template"]: item["name"] for item in application.load_counties() if item.get("template")}

    for profile_id, profile in application.JURISDICTION_PROFILES.items():
        response = client.get(f"/studio?county={counties[profile_id].replace(' ', '%20')}")
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert f"data-template=\"{profile_id}\"" in page
        assert profile["name"] in page
        assert "synthetic-profile-warning" in page
        assert "id=\"profile-picker\"" in page


def test_each_profile_generates_a_round_trip_synthetic_barcode(tmp_path, monkeypatch):
    client = application.app.test_client()
    templates = application.load_templates()

    for profile_id, profile in application.JURISDICTION_PROFILES.items():
        output_dir = tmp_path / profile_id
        output_dir.mkdir()
        monkeypatch.setattr(application, "OUTPUT_DIR", output_dir)
        generated_record = client.get(f"/api/random-record?profile={profile_id}").get_json()
        fields = generated_record["fields"]
        config = templates[profile_id]

        assert re.fullmatch(
            re.escape(config["syntheticIdPrefix"]) + r"[A-F0-9]{8}",
            fields["license_number"],
        )
        assert fields["state"] == profile["abbreviation"]
        fields = {name: value for name, value in fields.items() if name in config["activeFields"]}
        fields.pop("middle_name", None)
        fields.pop("suffix", None)
        hidden_hair_color = "hair_color" not in config["activeFields"]
        if hidden_hair_color:
            fields["hair_color"] = "SHOULD_NOT_BE_ENCODED"

        response = client.post(
            "/api/generate",
            json={
                "fields": fields,
                "profile": profile_id,
                "record_source": "test",
                "settings": {"width": 900, "height": 240},
            },
        )

        assert response.status_code == 200, (profile_id, response.get_json())
        result = response.get_json()
        assert result["profile"] == profile_id
        assert result["round_trip"]["payload_preserved"] is True
        if hidden_hair_color:
            assert result["aamva_record"]["raw_fields"].get("DAZ") != "SHOULD_NOT_BE_ENCODED"
        assert result["aamva_record"]["fields"]["license_number"] == fields["license_number"]
        assert result["png_url"].endswith(".png")
        assert result["xml"].startswith("<AAMVA>")


def test_each_profile_rejects_missing_required_values_but_accepts_optional_values_absent():
    client = application.app.test_client()
    templates = application.load_templates()

    for profile_id in application.JURISDICTION_PROFILES:
        config = templates[profile_id]
        fields = client.get(f"/api/random-record?profile={profile_id}").get_json()["fields"]
        fields = {name: value for name, value in fields.items() if name in config["activeFields"]}
        fields.pop("middle_name", None)
        fields.pop("last_name")

        response = client.post(
            "/api/generate",
            json={"fields": fields, "profile": profile_id, "record_source": "test"},
        )

        assert response.status_code == 400
        assert any("Last name is required" in error for error in response.get_json()["errors"])


def test_profile_test_ids_are_validated_and_unknown_profiles_are_rejected():
    client = application.app.test_client()
    fields = client.get("/api/random-record?profile=florida").get_json()["fields"]
    fields["license_number"] = "H123456789012"

    invalid_id = client.post(
        "/api/generate",
        json={"fields": fields, "profile": "florida", "record_source": "test"},
    )
    unknown_profile = client.get("/api/random-record?profile=not-registered")

    assert invalid_id.status_code == 400
    assert "synthetic prefix" in invalid_id.get_json()["errors"][0]
    assert unknown_profile.status_code == 400
