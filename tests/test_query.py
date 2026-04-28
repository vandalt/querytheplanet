from datetime import datetime
import itertools

import numpy as np
import pandas as pd
import pytest

from querytheplanet import query

# A few known planets to test
PLANETS = ["hr8799b", "hr8799e", "betapicb", "51erib"]

# Columns returned by the query
POS_COLS = [
    "RA",
    "Dec",
    "Separation",
    "PA",
]
ERR_COLS = [
    "RA_err",
    "Dec_err",
    "Separation_err",
    "PA_err",
]
OTHER_COLS = ["Reference", "Planet"]
NUMERIC_COLS = POS_COLS + ERR_COLS
ALL_COLS = NUMERIC_COLS + OTHER_COLS

# Define lists of planets and dates for the query tests
PLANETS_LIST = ["betapicb", PLANETS]
DATES_LIST = [None, "2025-01-01", "2040-01-01", ["2025-01-01", "2026-05-01"]]



def test_fetch_available_planets():
    assert query._CACHED_PLANETS is None

    all_planets = query.fetch_available_planets()

    # Check that the caching worked
    assert query._CACHED_PLANETS is not None
    assert all_planets == query._CACHED_PLANETS

    # Check that there are at least 10 planets (i.e. the query worked)
    assert len(all_planets) > 10

    # And check for a few known planets
    for planet in PLANETS:
        assert planet in all_planets



@pytest.mark.parametrize("planets,dates", itertools.product(PLANETS_LIST, DATES_LIST))
def test_query_planet_locations(planets, dates):

    df = query.query_planet_locations(planets, dates=dates)

    # Format inputs for the checks
    if isinstance(planets, str):
        planets = [planets]
    if dates is None:
        dates = datetime.now().strftime("%Y-%m-%d")
    if isinstance(dates, str):
        dates = [dates]

    # We should have a dataframe with nplanets * ndates rows
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(planets) * len(dates)

    # Check the planets and dates are the ones we expect
    assert df.Planet.unique().tolist() == planets
    assert df.Date.unique().tolist() == dates


    for col in ALL_COLS:
        assert col in df.columns
        if col in NUMERIC_COLS:
            assert df[col].dtype == "float"
        elif col in OTHER_COLS:
            assert df[col].dtype == "str"


def test_planet_location_values():
    # manually fetched  from the website for hd206893c on 2022-10-26
    ref_pos = {
        "RA": -1.312,
        "RA_err": 1.033,
        "Dec": -90.362,
        "Dec_err": 1.421,
        "Separation": 90.363,
        "Separation_err": 1.427,
        "PA": 180.833,
        "PA_err": 0.650,
    }
    pos = query._query_planet_location("hd206893c", "2022-10-26")
    for col in POS_COLS:
        err_col = f"{col}_err"
        diff_err = np.sqrt(ref_pos[err_col] ** 2 + pos[err_col] ** 2)
        diff = ref_pos[col] - pos[col]
        assert (np.abs(diff) < diff_err).all(), f"Poistion {pos[col]} not equal to reference {ref_pos[col]} within precision limit {diff_err}"

@pytest.mark.parametrize("planet", PLANETS)
def test_query_planet_location(planet):
    result = query._query_planet_location(planet, None)

    # Check that individual queries return a dict with the expected keys
    assert isinstance(result, dict)
    for col in NUMERIC_COLS:
        assert col in result.keys()

    # Check that passing a date works and changes the result
    result_date = query._query_planet_location(planet, "2025-01-01")
    assert result_date["RA"] != result["RA"]
    assert result_date["reference"] == result["reference"]

    # Check that invalid names cause an error
    with pytest.raises(ValueError, match="Invalid planet name"):
        query._query_planet_location("allo", None)


def test_write_to_csv_roundtrip(tmp_path, data_dir):
    filename = "results.csv"
    ref_df = pd.read_csv(data_dir / filename)
    out_path = tmp_path / filename
    query.write_to_csv(out_path, ref_df)
    df = pd.read_csv(data_dir / filename)
    pd.testing.assert_frame_equal(ref_df, df)


def test_write_to_csv_consistency(tmp_path, data_dir):
    filename = "results.csv"
    out_path = tmp_path / filename
    dates = ["2025-01-01", "2026-05-01"]

    df = query.query_planet_locations(PLANETS, dates=dates)
    query.write_to_csv(out_path, df)

    ref_df = pd.read_csv(data_dir / filename)

    # Test that the format of new queries is consistent with the reference
    pd.testing.assert_index_equal(ref_df.columns, df.columns)
    pd.testing.assert_index_equal(ref_df.index, df.index)
    other_cols = [col for col in ref_df.columns if col not in NUMERIC_COLS]
    pd.testing.assert_frame_equal(ref_df[other_cols], df[other_cols])

    # Check that the positions are consistent within uncertainties
    for col in POS_COLS:
        err_col = f"{col}_err"
        diff_err = np.sqrt(ref_df[err_col] ** 2 + df[err_col] ** 2)
        diff = ref_df[col] - df[col]
        assert (diff.abs() < diff_err).all()
