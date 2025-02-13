from GPSArray2Array import *
from ImportFromCSV import *
from testGPSA2A import testgps2arr
from GPSp2p.GenRandCoords import generate_random_gps
from line_profiler import LineProfiler as LP

BP = "/Users/thomas/Documents/EC530"
RA_FP = "five_cities.csv"  #Reference Array
RA = import_coordinates_from_csv(BP+'/'+ RA_FP)
TA_FP = "five_airports.csv"  #Target Array
TA = import_coordinates_from_csv(BP+'/'+ TA_FP)
#TA = generate_random_gps(10)
#RA = generate_random_gps(1000000)
#lp = LP()
#lp.add_function(arr2arr_match)
#lp.enable()
MA = arr2arr_match(RA,TA)
print(MA)
#lp.disable()
#lp.print_stats()

#testgps2arr()


#for i in range(10):
#    print(RA[i])
#    idx = MA[i]
#    print(TA[idx])

