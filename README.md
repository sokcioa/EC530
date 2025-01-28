# EC530
EC530 Spring 2025 repo

Inputs if csv must have header row with collumn titles 

ImportFromCSV.py: import_coordinates_from_csv(filename)
    grabs lat and long from csv, parses them to floats and returns as a np.array 

GPSArray2Array.py, arr2arr_match(arr1, arr2) 
    takes in lists or points and returns and array of the same size as arr1. 
    this array contains the index of the closest point in arr2