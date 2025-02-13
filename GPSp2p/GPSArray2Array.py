#This function will take in 2 arrays of GPS points and output an array the size of the larger of the two
#containing 1D index for the closest point of the input array
import numpy as np

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




