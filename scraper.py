import os
import requests
import zipfile
import datetime
from tqdm import tqdm
import pandas as pd

def linkGen(year):
    """
    This function generates the download links based on user input.
    """
    current_year = datetime.datetime.now().year
    try:
        if (int(year) >= 2016) and (int(year) <= int(current_year)):
            url = f"http://dev.hsl.fi/citybikes/od-trips-{year}/od-trips-{year}.zip"
            return url
        else:
            raise ValueError      
    except:
        print(f"Incorrect input.\nThe value should be an integer between 2016 and {current_year}")
        quit()

def downloader(url, download_path, chunk_size=128) :
    """
    This function dowloads the OD dataset and saves it in the specified foolder.
    """
    try:
        r = requests.get(url, stream=True)
        with open(download_path, 'wb') as fd:
            print("Download Initiated")
            for chunk in tqdm(r.iter_content(chunk_size=chunk_size)):
                fd.write(chunk)
        print("Download Complete")
    except:
        print("Experienced a problem with downloading the files")

def unzipper(path_to_zip_file, directory_to_extract_to):
    """
    This function unzips the downloaded files
    """
    try:
        print("Unzipping files")
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)
        print("Files successfully unzipped")
    except:
        print("Experienced a problem with unzipping the files")

def joiner(path, year):
    """
    This function joins .csv's from each month into a single .csv file for the year
    """

    try:
        if int(year) > 2018:
            path += f"/od-trips-{year}"
            
        all_files = os.listdir(path)
        combined_csv = pd.concat([pd.read_csv(f"{path}/{filename}") for filename in all_files ])
        combined_csv.to_csv( f"data/combined_data/{year}.csv", index=False, encoding='utf-8-sig')
        print("Files successfully combined")
    except:
        print("Experienced a problem with combining the files")

def coordinateScraper():
    """
    This Function Downloads the station Names and coordinates from 
    digitransit.fi API and saves them as a .CSV.
    """
    try:
        response = requests.get("https://api.digitransit.fi/routing/v1/routers/hsl/bike_rental")
        json = response.json()

        columns = ["name", "longitude", "latitude"]
        lst = []
        for station in json["stations"]:
            lst.append([station["name"], station["x"], station["y"]])
        df = pd.DataFrame(lst, columns=columns)
        print("Station Coordinates downloaded")
    except:
        print("Experienced a problem dowloading station information")
        quit()

    try:
        df.to_csv("data/downloaded_data/station_coordinates.csv", header = True, encoding='utf-8-sig')
        print("Station Coordinates saved")
    except:
        print("Experienced a problem saving station information to .CSV")


def main():
    """
    """
    year = input("\nPlease select the year:(2016-present)\n")

    url = linkGen(year)

    download_path =f"data/downloaded_data/{year}.zip"
    downloader(url, download_path, chunk_size=128)

    # Folder structure changed after 2018
    if int(year) > 2018:
        unzip_path = "data/downloaded_data"
    else:
        unzip_path = f"data/downloaded_data/od-trips-{year}"

    # Unzip downloaded files
    unzipper(download_path, unzip_path)
    # Join separate months into single file
    joiner(unzip_path, year)
    # Download latest station coordinates into a .CSV
    coordinateScraper()
    # Join all years into a single .CSV file
    #joinAll()

if __name__ == "__main__":
    main()
