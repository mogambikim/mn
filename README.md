# AAMVA PDF417 Barcode Studio

A local Flask application for editing authorized driver's-license-style records, generating PDF417 barcodes, decoding PDF417 images, validating supported AAMVA records, and exporting parsed data as XML. Use synthetic data for testing and externally supplied records only when you are authorized to handle them. Barcode decoding and format validation do **not** authenticate a document or verify its issuer.

## Requirements and installation

- Python 3.10 or later
- Java runtime for the ZXing image-decoder fallback
- ZBar native library is optional; when installed, `pyzbar` is tried first

From the repository directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000/studio>. The root page links to the existing county/template editors. Run automated tests with:

```powershell
python -m pip install pytest
python -m pytest -q
```

## Use

1. Select one of the six new jurisdictions in the studio's **Jurisdiction** selector, or use its link on the landing page. The shared form is configured to show and order the fields visible in the supplied screenshots.
2. Select **Test data**, then choose **Random record** to create synthetic values. New profile test IDs use `TEST-FL-`, `TEST-IL-`, `TEST-MS-`, `TEST-NY-`, `TEST-WA-`, or `TEST-DC-` followed by random hex digits. These are not official license numbers.
3. Use **Generate Barcode** when ready. The preview, PNG/PDF downloads, encoded payload, parsed field table, XML, and round-trip scan status are shown.
4. To scan an existing barcode, choose the intended profile before scanning. The app does not infer a jurisdiction from the address or claim issuer verification. Parsed AAMVA field values remain inspectable and editable before generation.
5. Switch between **Manual Entry** and **Scan Existing Barcode**. Select an image to preview it, then use **Scan Barcode**. Review the raw payload and decoded field-ID table; **Update Fields** copies the parsed values into the existing form without generating a barcode. Missing values are cleared, not filled with invented defaults. **Clear Fields** clears the form.
6. Alternatively, use the physical scanner/raw payload input. A keyboard-wedge scanner can type into the input; press Ctrl+Enter or use **Parse payload**.
7. Edit the XML schema JSON to configure user element names and field IDs. Each schema entry supports `element`, `id`, optional `field` (the internal parsed-field key), and optional `name` (an additional XML attribute). XML values are escaped, missing requested values are explicitly marked `missing="true"`, and unknown AAMVA data elements are preserved.

The PDF417 encoder is `pdf417gen` 0.8.1. Image decoding tries `pyzbar`/ZBar, the native `zxing-cpp` binding, then the Java ZXing fallback. Scanned field values that do not match a dropdown option are retained as explicit scan-derived options; fields unavailable in the selected profile remain visible in the decoded-field table. Height conversion accepts either inches or feet-and-inches notation. The existing rectangle dimensions, canvas placement, and PDF export controls remain available.

## AAMVA support and validation

Generation and strict structured parsing support the **AAMVA DL/ID standard data format version 09** (`ANSI` header, issuer ID, jurisdiction version, subfile directory, and `DL` subfile). The DL subfile byte offset and length are calculated from the generated ASCII payload; the parser checks header shape, supported version, directory entry count, subfile bounds, and field identifiers/delimiters. Unknown three-character element IDs are retained.

`/api/decode` reports successful generic PDF417 decoding separately from whether the decoded payload passes AAMVA v09 validation. `/api/parse` validates a raw payload; issuer authentication is deliberately not performed. Image decoding uses its bundled `zxing-cpp` dependency; ZBar and Java are optional fallback runtimes.

The six profile layouts and visible tooltip notes were transcribed from the provided PDF screenshots. The PDF does not show Florida revision-date selector options, and jurisdiction-specific ID-generation rules and issuer metadata have not been independently verified. These rules are not implemented; generated IDs are synthetic `TEST-XX-...` markers. REAL ID, Safe Driver, and Veteran selections are UI-only because a verified AAMVA field mapping was not provided. No profile-specific physical-scanner fixture was supplied; the generic AAMVA v09 decoder remains shared.

## HTTP endpoints

- `POST /api/generate` — JSON object with `fields`, optional `profile` (one of the six profile IDs), `settings`, XML schema (`xml_schema`), and `record_source`.
- `POST /api/decode` — multipart image upload in field `image`.
- `POST /api/parse` — JSON object with raw `payload` and optional `xml_schema`.
- `GET /api/random-record?profile=<profile-id>` and `GET /api/random-field/<field>?profile=<profile-id>` — generate conspicuously synthetic profile test identifiers; `POST /api/calculate` remains the derived-field helper.

## Notes

- Records and generated files are processed by this local app; there is no issuer lookup or identity verification.
- Scanned information is sensitive personal data. Avoid uploading data unless you have authorization, and delete generated/downloaded files when no longer needed.
- `OUTPUT_DIR` can be set to change where generated files are stored.
