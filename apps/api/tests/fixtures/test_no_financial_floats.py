import json
import shutil

import pytest

from fixture_support import FixtureError, ROOT, load_fixture_set, read_json, scalars, validate_fixture_set


@pytest.mark.parametrize("number", ["0.1", "1e2", "NaN", "Infinity", "-Infinity"])
def test_json_parser_refuses_nested_floats_and_constants(tmp_path, number):
    path = tmp_path / "bad.json"
    path.write_text('{"outer": [{"amount": ' + number + '}]}')
    with pytest.raises(FixtureError, match="floats/constants forbidden"):
        read_json(path)


@pytest.mark.parametrize("value", [1, True, None, "NaN", "1,500.00", "1e3", " 1500", "１５００", 0.1])
def test_financial_types_and_text_are_strict(fixtures, value):
    fixtures.references["purchase_orders"][0]["lines"][0]["unit_price"] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("field", ["amount", "accepted_quantity", "allowance_amount", "eligible_nights", "tax_rate", "quantity_tolerance"])
def test_recursive_financial_field_check_even_outside_record_schemas(field):
    with pytest.raises(FixtureError):
        scalars({"one": [{"two": {field: 1.5}}]})
    with pytest.raises(FixtureError, match="decimal text"):
        scalars({"one": [{"two": {field: 1}}]})


def test_exact_decimal_text_survives_json_round_trip():
    value = {"amount": "0.100000000000000000001", "currency": "INR", "quantity": "2.0000"}
    decoded = json.loads(json.dumps(value))
    scalars(decoded)
    assert decoded == value


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "ambiguous.json"
    path.write_text('{"amount": "1.00", "amount": "2.00"}')
    with pytest.raises(FixtureError, match="duplicate JSON key"):
        read_json(path)


@pytest.fixture
def isolated_dataset(tmp_path):
    shutil.copytree(ROOT / "data", tmp_path / "data")
    (tmp_path / "docs").mkdir()
    for name in ("test_coverage.md", "AP_Exception_Assistant_Codex_Spec.md"):
        shutil.copyfile(ROOT / "docs" / name, tmp_path / "docs" / name)
    return tmp_path


def test_missing_reference_file_is_rejected(isolated_dataset):
    (isolated_dataset / "data/synthetic/reference/vendors.json").unlink()
    with pytest.raises(FixtureError, match="reference file set"):
        load_fixture_set(isolated_dataset)


def test_unlisted_golden_file_is_rejected(isolated_dataset):
    shutil.copyfile(isolated_dataset / "data/golden_cases/vendor/clean.json", isolated_dataset / "data/golden_cases/vendor/unlisted.json")
    with pytest.raises(FixtureError, match="unlisted/missing"):
        load_fixture_set(isolated_dataset)


def test_manifest_cannot_read_outside_golden_directory(isolated_dataset):
    path = isolated_dataset / "data/golden_cases/manifest.json"
    content = json.loads(path.read_text())
    content["cases"][0]["path"] = "../../outside.json"
    path.write_text(json.dumps(content))
    with pytest.raises(FixtureError, match="unsafe/unexpected manifest path"):
        load_fixture_set(isolated_dataset)
