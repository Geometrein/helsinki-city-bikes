import os
import requests
import json
import zipfile
import datetime
from tqdm import tqdm
import pandas as pd

import scraper
import cleaner
import constants

def openCsv(filename):
    """
    Opening the CSV files & converting to Pandas DataFrames
    """
    try:
        df = pd.read_csv("{}".format(filename), delimiter = "," )
        print(" ✔ Dataframe {} loaded successfully.".format(filename))
        return df
    except:
        print(" X Loading {} failed.".format(filename))

def joinAll():
    """
    Join all .CSV files in datasets folder into one 
    """
    print("Joining all .csv files")
    path = "data/datasets"
    all_files = os.listdir(path)
    files = list(filter(lambda f: f.endswith('.csv'), all_files))
    combined_csv = pd.concat([pd.read_csv(f"{path}/{filename}") for filename in files ])
    combined_csv.to_csv( "data/database.csv", index=False, encoding='utf-8-sig')
    print("database.csv successfully created")

def main():
    """
    Downloads and formats O-D trips for specified year.
    """
    year = input("\nPlease select the year you wish to download:(2016-present)\n")

    ##### Scraping data #####
    url = scraper.linkGen(year)
    download_path =f"data/downloaded_data/{year}.zip"
    scraper.downloader(url, download_path, chunk_size=128)

    # Folder structure changed after 2018
    if int(year) > 2018:
        unzip_path = "data/downloaded_data"
    else:
        unzip_path = f"data/downloaded_data/od-trips-{year}"
    
    # Unzip downloaded files
    scraper.unzipper(download_path, unzip_path)
    # Join separate months into single file
    scraper.joiner(unzip_path, year)
    # Download latest station coordinates into a .CSV
    scraper.coordinateScraper()

    #### Cleaning & Formatting ####
    dataframe = openCsv(f"data/combined_data/{year}.csv")
    weather_df = openCsv(f"data/weather/helsinki_weather_{year}.csv")
    stations_df = openCsv("data/downloaded_data/station_coordinates.csv")

    # More usable names for columns
    dataframe = cleaner.renameColumns(dataframe)
    # Identifying missing/renamed stations
    cleaner.missingNames(dataframe, stations_df)
    # Replace missing stations from constants.py
    df = cleaner.replaceMissingStations(dataframe)
    # Drop Service stations
    df = cleaner.dropStations(df)
    # Correct Datatypes
    df = cleaner.dataTypes(df)
    # Add station coordinates
    df = cleaner.mapCoordinates(df, stations_df)
    # Fixing weather files
    weather_df = cleaner.weatherConverter(weather_df)
    # Adding weather to the main dataframe
    df = cleaner.weatherAdd(df, weather_df)

    df.to_csv(f"data/datasets/{year}.csv", index=False)

    # Data info
    print(df.info(), df.isna().sum())
    print(f"{year} has been downloaded and cleaned")
    
if __name__=="__main__":
    main()
    #joinAll()