from pathlib import Path

from ice.io import read_canonical_input


def test_read_canonical_input_generates_input_id(tmp_path: Path):
    path = tmp_path / "input.csv"
    path.write_text("MAIN_TEXT,COUNTRY,PG_name\nToy ABC,CZ,Figures\n", encoding="utf-8")
    df = read_canonical_input(path)
    assert df.loc[0, "input_id"] == "ROW_00001"
    assert df.loc[0, "country_code"] == "CZ"
    assert df.loc[0, "main_text"] == "Toy ABC"
