#This function will take in 2 arrays of GPS points and output an array the size of the larger of the two
#containing 1D index for the closest point of the input array
import numpy as np
import traceback

def p2arr_dist(point, refarray, rad=0):
  assert isinstance(refarray, np.ndarray), "Ref Array must be np array"
  assert refarray.size > 0, "Ref array must not be empty"  
  assert refarray.ndim == 2 and refarray.shape[1] == 2, "Ref array must be Nx2."
  assert len(point) == 2, "point must have two coordinates (latitude, longitude)."
  assert isinstance(point, (list, tuple, np.ndarray)), "point must be a list, tuple, or numpy array."

  if not rad: #make radian for trig
      point = np.radians(point)
      refarray = np.radians(refarray)
  #parse for easy reference
  lat1, lon1 = point
  lat2, lon2 = refarray[:, 0], refarray[:, 1]
  
  # Latitude and longitude range validity check
  assert -np.pi/2 <= lat1 <= np.pi/2, f"Latitude of point1 invalid: {lat1}"
  assert np.all((-np.pi/2 <= lat2) & (lat2 <= np.pi/2)), "Invalid latitudes in refarray."
  assert -np.pi <= lon1 <= np.pi, f"Longitude of point1 invalid: {lon1}"
  assert np.all((-np.pi <= lon2) & (lon2 <= np.pi)), "Invalid longitudes in refarray."

  # haversine formula
  dlat = lat2 - lat1  #should be same N as refarray
  dlon = lon2 - lon1  #should be same N as refarray
  a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2 #should be same N as refarray
  c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)) #should be same N as refarray
  R = 6371000  # Earth radius in meters
  dist_arr = R * c
  return dist_arr

def arr2arr_match(arr1, arr2, rad=0):
  assert arr1.dtype == float, "arr1 must not contain non-numeric values like None or Strings"
  assert arr2.dtype == float, "arr2 must not contain non-numeric values like None or Strings"
  assert not np.any(np.isnan(arr1)), "arr1 must not contain NaN values."
  assert not np.any(np.isnan(arr2)), "arr2 must not contain NaN values."
  assert isinstance(arr1, np.ndarray), "arr1 Array must be np array"
  assert arr1.size > 0, "arr1 array must not be empty"
  assert isinstance(arr2, np.ndarray), "arr2 Array must be np array"
  assert arr2.size > 0, "arr2 array must not be empty"
  assert arr1.ndim == 2 and arr1.shape[1] == 2, "arr1 array must be Nx2."
  assert arr2.ndim == 2 and arr2.shape[1] == 2, "arr2 array must be Mx2."

  if not rad: #make radian for trig
      arr1 = np.radians(arr1)
      arr2 = np.radians(arr2)
  #parse for easy reference
  lat1, lon1 = arr1[:,0], arr1[:, 1]
  lat2, lon2 = arr2[:,0], arr2[:, 1]
  
  # Latitude and longitude range validity check
  assert np.all((-np.pi/2 <= lat1) & (lat1 <= np.pi/2)), "1 or more latitudes in arr1 are invalid."
  assert np.all((-np.pi/2 <= lat2) & (lat2 <= np.pi/2)), "1 or more latitudes in arr2 are invalid."
  assert np.all((-np.pi <= lon1) & (lon1 <= np.pi)), "1 or more longitudes in arr1 are invalid."
  assert np.all((-np.pi <= lon2) & (lon2 <= np.pi)), "1 or more longitudes in arr2 are invalid."
  #reshape for array opperations
  lat1 = lat1[:, np.newaxis]  # Shape (M, 1)
  lon1 = lon1[:, np.newaxis]  # Shape (M, 1)
  dlat = lat2[np.newaxis,:] - lat1  #should be  MxN 
  dlon = lon2[np.newaxis,:] - lon1  #should be same MxN 
  # haversine formula
  a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2 #should be same MxN
  c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)) #should be same MxN as refarray
  R = 6371000  # Earth radius in meters
  dist_arr = R * c
  min_dist_idxs = np.argmin(dist_arr, axis=1)
  return min_dist_idxs  


  correct_test()
  try:
    fail_test1()
  except Exception as e: 
    print(f"fail_test1 failed: {e}")
    #traceback.print_exc()
  try:
    fail_test2()
  except Exception as e: 
    print(f"fail_test2 failed: {e}") 
    #traceback.print_exc()
  try:
    fail_test3()
  except Exception as e: 
    print(f"fail_test3 failed: {e}")
    #traceback.print_exc()





