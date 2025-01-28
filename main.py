from GPSArray2Array import *
from ImportFromCSV import *
BP = "/Users/thomas/Documents/EC530"
RA_FP = "Major_Cities_GPS.csv"  #Reference Array
TA_FP = "iata-icao.csv"  #Target Array
RA = import_coordinates_from_csv(BP+'/'+ RA_FP)
TA = import_coordinates_from_csv(BP+'/'+ TA_FP)
MA = arr2arr_match(RA,TA)

#for i in range(10):
#    print(RA[i])
#    idx = MA[i]
#    print(TA[idx])

