import os
import zipfile

import yaml
import pandas as pd
from tqdm import tqdm

import requests

pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 30)
pd.set_option('display.max_colwidth', 500)
pd.set_option('display.precision', 2)
pd.set_option('display.float_format',  '{:,}'.format)


def load_config() -> dict:
    config_path = os.path.join('..', 'config.yaml')
    with open(config_path) as file:
        config = yaml.safe_load(file)
    return config


def download_od_data(year: int, zip_file_path: str,  chunk_size: int = 128) -> None:
    """
    This function downloads the OD dataset and saves it in the specified folder.
    """
    url = f"https://dev.hsl.fi/citybikes/od-trips-{year}/od-trips-{year}.zip"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(zip_file_path, 'wb') as fd:
            for chunk in tqdm(response.iter_content(chunk_size=chunk_size)):
                fd.write(chunk)
    elif response.status_code == 404:
        print(f'Data for {year} does not exist.')
        raise FileNotFoundError
    else:
        raise FileNotFoundError


def convert_to_dataframe(year: int, zip_file_path: str) -> pd.DataFrame:
    """
    This function merges zipped monthly data into a single .csv file for the entire year.
    """
    yearly_df = pd.DataFrame()
    with zipfile.ZipFile(zip_file_path, 'r') as zip_object:
        list_of_files = zip_object.namelist()
        for csv_file_name in list_of_files:
            month_df = pd.read_csv(zip_object.open(csv_file_name))
            yearly_df = pd.concat([yearly_df, month_df])
    return yearly_df


def rename_columns(source_df: pd.DataFrame):
    columns = {
        'Departure': 'departure',
        'Return': 'return',
        'Departure station id': 'departure_id',
        'Departure station name': 'departure_name',
        'Return station id': 'return_id',
        'Return station name': 'return_name',
        'Covered distance (m)': 'distance (m)',
        'Duration (sec.)': 'duration (sec.)',
    }

    source_df.rename(columns=columns, inplace=True)
    return source_df


def download_station_coordinates() -> dict:
    url = "https://www.cityfillarit.fi/stage-ajax/hslCityBikes?stage-language=en"
    response = requests.get(url)
    if response.status_code == 200:
        raw_json = response.json()
        stations = raw_json['stations']
        stations_dict = {}
        for station in stations:
            station_id = int(station['id'])
            longitude = station['x']
            latitude = station['y']
            stations_dict[station_id] = (longitude, latitude)
        return stations_dict
    elif response.status_code == 404:
        print(f'Stations coordinates could not be found.')
        raise FileNotFoundError
    else:
        raise FileNotFoundError


def map_stations_to_coordinates(input_df: pd.DataFrame, stations: dict) -> pd.DataFrame:
    input_df['departure_coordinates'] = input_df['departure_id'].map(stations)
    input_df['return_coordinates'] = input_df['return_id'].map(stations)
    return input_df


def scraper_main() -> None:

    with open("config.yaml", "r") as stream:
        configs = yaml.safe_load(stream)

    year = configs['year']
    zip_file_name = f'raw_data_{year}.zip'
    zip_file_path = os.path.join('..', 'data', 'downloads', zip_file_name)
    download_od_data(year=year, zip_file_path=zip_file_path)

    yearly_df = convert_to_dataframe(year=year, zip_file_path=zip_file_path)
    yearly_df = rename_columns(source_df=yearly_df)

    stations_dict = download_station_coordinates()
    yearly_df = map_stations_to_coordinates(input_df=yearly_df, stations=stations_dict)

    csv_file_name = f'od_helsinki_city_bikes_{year}.csv'
    csv_file_path = os.path.join('..', 'data', 'datasets', csv_file_name)
    yearly_df.to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    scraper_main()
