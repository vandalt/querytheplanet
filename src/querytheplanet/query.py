from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://whereistheplanet.com/"
_CACHED_PLANETS = None


def write_to_csv(
    filepath: str | Path, results_df: pd.DataFrame, overwrite: bool = False
):
    """
    Write multiple query results to a CSV file using pandas.

    :param filepath: Path to CSV file
    :param results_list: List of result dictionaries from multiple planet queries
    """
    filepath = Path(filepath)

    if filepath.is_file() and not overwrite:
        raise FileExistsError(
            f"File {filepath} already exists. Use overwrite=True to overwrite."
        )

    df = results_df

    df.to_csv(filepath, index=False)
    print(f"\nResults for {len(results_df)} planet(s) saved to {filepath}")


def _parse_results_with_errors(html: str) -> dict:
    """
    Parse the HTML response to extract planet location data with errors.

    :param html: HTML response text from the website
    :return: Dictionary with keys: RA, RA_err, Dec, Dec_err, Separation, Separation_err, PA, PA_err, reference
    """
    soup = BeautifulSoup(html, "html.parser")
    import re

    results = {
        "RA": None,
        "RA_err": None,
        "Dec": None,
        "Dec_err": None,
        "Separation": None,
        "Separation_err": None,
        "PA": None,
        "PA_err": None,
        "reference": None,
    }

    # Find the paragraph containing results
    for p in soup.find_all("p"):
        text = p.get_text()
        # Look for lines with result data
        for line in text.split("\n"):
            line = line.strip()
            if "RA Offset" in line:
                match = re.search(r"([\d.]+)\s+\+/-\s+([\d.]+)", line)
                if match:
                    results["RA"] = float(match.group(1))
                    results["RA_err"] = float(match.group(2))
            elif "Dec Offset" in line:
                match = re.search(r"([\d.]+)\s+\+/-\s+([\d.]+)", line)
                if match:
                    results["Dec"] = float(match.group(1))
                    results["Dec_err"] = float(match.group(2))
            elif "Separation" in line and "=" in line:
                match = re.search(r"([\d.]+)\s+\+/-\s+([\d.]+)", line)
                if match:
                    results["Separation"] = float(match.group(1))
                    results["Separation_err"] = float(match.group(2))
            elif line.startswith("PA ") and "=" in line:
                match = re.search(r"([\d.]+)\s+\+/-\s+([\d.]+)", line)
                if match:
                    results["PA"] = float(match.group(1))
                    results["PA_err"] = float(match.group(2))
            elif "Reference:" in line:
                results["reference"] = line.replace("Reference: ", "").strip()

    return results


def fetch_available_planets() -> list[str]:
    """
    Query the website to fetch available planets from the dropdown menu.

    :return: List of available planet names
    :raises requests.RequestException: If unable to fetch the page
    :raises ValueError: If unable to parse available planets from the page
    """
    global _CACHED_PLANETS

    if _CACHED_PLANETS is not None:
        return _CACHED_PLANETS.copy()

    response = requests.get(BASE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the planet select dropdown
    select = soup.find("select", {"name": "planetname"})
    if not select:
        raise ValueError("Could not find planet dropdown in the website HTML")

    # Extract planet names from option elements
    planets = []
    for option in select.find_all("option"):
        value = option.get("value", "").strip()
        if value and value.lower() != "select a planet":
            planets.append(value)

    if not planets:
        raise ValueError("No planets found in the dropdown")

    _CACHED_PLANETS = planets
    return planets.copy()


def _query_planet_location(
    planet_name: str,
    date: Optional[str] = None,
) -> dict:
    """
    Query the planet location prediction for a given planet and date.

    :param planet_name: Name of the planet (must be one of available planets)
    :param date: Date in YYYY-MM-DD format (defaults to today)
    :return: Dictionary containing RA, Dec, Separation, PA, and reference with errors
    :raises ValueError: If planet_name is not valid
    """
    available_planets = fetch_available_planets()

    if planet_name not in available_planets:
        raise ValueError(
            f"Invalid planet name: {planet_name}\n"
            f"Available planets: {', '.join(available_planets)}"
        )

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "planetname": planet_name,
        "time": date,
    }

    print(f"Querying planet: {planet_name}, date: {date}")
    response = requests.post(BASE_URL, data=payload)
    response.raise_for_status()

    return _parse_results_with_errors(response.text)


def query_planet_locations(
    planets: str | list[str],
    dates: str | list[str] | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Query planet location for multiple planets and dates.

    :param planets: List of planets to query
    :param dates: List of dates to query for each planet
    :param verbose: Print the output to terminal if True
    :return: Dataframe with position information
    """
    # Determine the date to display and save in output
    dates = dates or datetime.now().strftime("%Y-%m-%d")
    if isinstance(planets, str):
        planets = [planets]
    if isinstance(dates, str):
        dates = [dates]

    # Collect results from all planets
    all_results = []
    for planet in planets:
        for date in dates:
            results = _query_planet_location(planet, date=date)
            if verbose:
                print(f"\n--- Planet Location Results: {planet} on {date} ---")
                print(f"RA: {results['RA']} +/- {results['RA_err']} mas")
                print(f"Dec: {results['Dec']} +/- {results['Dec_err']} mas")
                print(
                    f"Separation: {results['Separation']} +/- {results['Separation_err']} mas"
                )
                print(f"PA: {results['PA']} +/- {results['PA_err']} deg")
                print(f"Reference: {results['reference']}")

            all_results.append(
                {
                    "Planet": planet,
                    "Date": date,
                    "RA": results["RA"],
                    "RA_err": results["RA_err"],
                    "Dec": results["Dec"],
                    "Dec_err": results["Dec_err"],
                    "Separation": results["Separation"],
                    "Separation_err": results["Separation_err"],
                    "PA": results["PA"],
                    "PA_err": results["PA_err"],
                    "Reference": results["reference"],
                }
            )

    return pd.DataFrame(all_results)
