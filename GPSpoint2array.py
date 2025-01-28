import numpy as np

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
