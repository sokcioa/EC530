import csv
import re
import numpy as np

def parse2float(degree_str):
    """
    Convert a latitude/longitude string in various formats to decimal degrees.
    Handles formats like:
    - Decimal Degrees: 45.91
    - Degrees and Minutes: 40 42.8 (degrees and minutes)
    - Degrees, Minutes, and Seconds: 45° 15' 36''
    - Handles N/S/E/W for direction 
        S and W are negative! 
    - Handles 'degrees' word in place of degree symbol
    """
    #get rid of extra stupid characters and names etc

    degree_str = degree_str.strip()
    degree_str = degree_str.replace("minutes", " ").replace("seconds", " ")
    degree_str = degree_str.replace("Minutes", " ").replace("Seconds", " ")
    degree_str = degree_str.replace("minute", " ").replace("second", " ")
    degree_str = degree_str.replace("Minute", " ").replace("Second", " ")
    degree_str = degree_str.replace("'", " ").replace("\"", " ")
    degree_str = degree_str.replace("North", "N").replace("north", "N")
    degree_str = degree_str.replace("South", "S").replace("south", "S")
    degree_str = degree_str.replace("East", "E").replace("east", "E")
    degree_str = degree_str.replace("West", "W").replace("west", "W")
    degree_str = degree_str.replace("Degrees", " ").replace("degrees", " ").replace("°", " ").replace("Degree", " ").replace("degree", " ")
    degree_str = re.sub(r'(\d+)\s(Degrees|degrees|°|Degree|degree)\s*(\d+)\s*(\d+(\.\d+)?)?', r'\1 \3 \4', degree_str)
    # the line above is a lot to process BUT I'll break it down
    ''' 
        - (\d+) :this defines the first group '\1' as any number of digits
        - (degrees|°)\s*: this is the second group '\2' has the degree work or symbol if present and ignores any number of spaces following it 
        - from here you should see the next \d grabs the minutes in group 3, ignores spaces or minute sympbol 
        - and grabs seconds in group 4
    '''

    match = re.match(r"^(-?\d+(\.\d+)?)(?:\s+(\d+(\.\d+)?))?(?:\s+(\d+(\.\d+)?))?\s+?([NSEWnsew])?$", degree_str)
    ''' 
        - ^ must start with a match 
        - -? grab a negative if present
        - \d+(\.\d+)? grab integer digits and optionally grabs another group for the decimal of the degree input  
        - (?: not captured and optional group for minutes, minute descimal optional as well 
        - the same is done for the seconds 
        - groups 1 3 and 5 also contain 2 4 and 6, IE decimal values are contained in them.
        - group 7 is NSEW 
    '''
    try:
        return(float(degree_str))
    except: 
        pass

    if match:
        degrees = float(match.group(1))  # Degrees (including decimal part)
        # If minutes are present, process them
        minutes = float(match.group(3)) if match.group(3) else 0  # Minutes
        # IF seconds are present, process them
        seconds = float(match.group(5)) if match.group(5) else 0  # Seconds
        # the result in decimal degrees
        number = degrees + (minutes / 60) + (seconds / 3600)
        if match.group(7) in ['S', 'W']:
            number = -number
        return number

def import_coordinates_from_csv(filename):
    """
    Import coordinates from CSV file and convert them to decimal
    """
    coordinates = []
    with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            normalized_row = {k.strip().lower(): v for k, v in row.items()} #ChatGPT told me this work make the collumn keys lower case
            #reader makes key and value pairs, this ignores case on the key
            latitude = normalized_row['latitude']
            longitude = normalized_row['longitude']
            # Add to list if both lat and long are valid
            if latitude is not None and longitude is not None:
                # Convert latitude and longitude to decimal degrees
                latitude_decimal = parse2float(latitude)
                longitude_decimal = parse2float(longitude)
                coordinates.append([latitude_decimal, longitude_decimal])

    return np.array(coordinates)



