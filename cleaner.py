import pandas as pd
import constants

import main

def renameColumns(df):
    """
    """
    df = df.rename(
        columns={'Departure': 'departure',
                'Return': 'return',
                'Departure station id': 'departure_id',
                'Departure station name': 'departure_name',
                'Return station id': 'return_id',
                'Return station name': 'return_name',
                'Covered distance (m)': 'distance (m)',
                'Duration (sec.)': 'duration (sec.)',
                })
    return df

def missingNames(df, df1):
    """
    This function prints the list of stations that are present in the first input dataframe but absent in the second.
    Stations can be missing if they are renamed. 
    The Renamed station and their new name should be added to RENAMED_STATIONS dictionary in constants.py
    """
    new_name = []
    # Dropping duplicates
    df_temp = df.drop_duplicates(subset = "departure_name") 

    # Comparing the station names in two dataframes writing them to a new column
    df_temp["Unique"] = df_temp["departure_name"][~df_temp["departure_name"].isin(df1["name"])]

    # Droping NAN values
    df_temp.dropna(inplace = True)

    # Converting unique column to a list
    new_name = df_temp["Unique"].tolist()
    print("-------------------------------------------------------")
    print(f"{len(new_name)} stations did not match with station_coordinates.csv.\nMissing stations are:")
    for station in new_name:
        print(station)
    print("-------------------------------------------------------")

def replaceMissingStations(df):
    """
    This Function replaces the old station names with new names as defined by RENAMED_STATIONS dictionary in constants.py.
    """
    df["departure_name"].replace(constants.RENAMED_STATIONS, inplace = True)
    df["return_name"].replace(constants.RENAMED_STATIONS, inplace = True)
    return df

def dropStations(df):
    """
    This functions returns a dataframe with dropped maintenance stations.
    """
    stations_to_drop = ('Workshop', " ", "Bike Production", "Pop-Up")
    df = df[~df['departure_name'].astype(str).str.startswith(stations_to_drop)]
    df = df[~df['return_name'].astype(str).str.startswith(stations_to_drop)]
    return df

def mapCoordinates(dataframe, stations_df):
    """
    This function adds coordinates from station_coordinates.csv to every row of the dataframe.
    """
    coordinates = {}
    keys = stations_df["name"].tolist()
    lon_values = stations_df["longitude"].tolist()
    lat_values = stations_df["latitude"].tolist()

    values = list(zip(lat_values,lon_values))
    for i in range(len(keys)):
        key = keys[i]
        coordinates[key] = values[i]

    df = dataframe.copy()
    df["departure_coordinates"] = df["departure_name"].map(coordinates)
    df["return_coordinates"] = df["return_name"].map(coordinates)
    return df

def weatherConverter(dataframe):
    """
    This function converts raw weather data into the right timezone and timestamp format.
    """
    df = dataframe.copy()
    df["Timestamp"] = df["Year"].astype(str) + "-" + df["m"].astype(str) + "-" + df["d"].astype(str) + " " + df["Time"].astype(str)
    # Droping extra columns
    df.drop(columns = ["Year", "m", "d","Time", "Time zone"], inplace = True)
    # Converting to pd.datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # Converting UTC to Helsinki time
    df["Timestamp"] = df["Timestamp"] + pd.Timedelta('02:00:00')

    # reordering columns
    df = df[["Timestamp", "Air temperature (degC)"]]
    return df

def weatherAdd(dataframe, weather_df):
    """
    This function merges weather data with the main  O-D dataframe.
    """
    df1 = dataframe.copy()
    df2 = weather_df.copy()
    df1.sort_values(by=["departure"], inplace = True)
    df1['departure'] = pd.to_datetime(df1['departure'], errors='coerce')

    df2.rename(columns={"Timestamp": "departure"}, inplace = True)
    df2['departure'] = pd.to_datetime(df2['departure'])
    df2.sort_values(by=["departure"])

    new_df = pd.merge_asof(df1, df2, on='departure')

    return new_df

def dataTypes(dataframe):
    """
    This function corrects the datatypes of the main dataframe and adds a column Speed
    """
    df = dataframe.copy()
    df.columns = map(str.lower, df.columns)
    
    df['departure'] = pd.to_datetime(df['departure'])
    df['return'] = pd.to_datetime(df['return'])

    df["departure_name"] = df["departure_name"].str.strip()
    df["return_name"] = df["return_name"].str.strip()

    df["avg_speed (km/h)"] = (df["distance (m)"] / df["duration (sec.)"]) * 0.06
    #print(df.dtypes)
    return df

def main():
    """
    """
    year = input("\nPlease select the year:(2016-present)\n")

    dataframe = main.open_csv(f"data/combined_data/{year}.csv")
    weather_df = main.open_csv(f"data/weather/helsinki_weather_{year}.csv")
    stations_df = main.open_csv("data/downloaded_data/station_coordinates.csv")

    # More usable names for columns
    dataframe = renameColumns(dataframe)
    # Identifying missing/renamed stations
    missingNames(dataframe, stations_df)
    # Replace missing stations from constants.py
    df = replaceMissingStations(dataframe)
    # Drop Service stations
    df = dropStations(df)
    # Correct Datatypes
    df = dataTypes(df)
    # Add station coordinates
    df = mapCoordinates(df, stations_df)
    # Fixing weather files
    weather_df = weatherConverter(weather_df)
    # Adding weather to the main dataframe
    df = weatherAdd(df, weather_df)

    df.to_csv(f"data/datasets/{year}.csv", index=False)

if __name__ == "__main__":
    main()
