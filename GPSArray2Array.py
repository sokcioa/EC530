#This function will take in 2 arrays of GPS points and output an array the size of the larger of the two
#containing 1D index for the closest point of the input array
import numpy as np
import math

def p2p_dist(point1, point2, Rad=0): 
  '''
  Takes in 2 Lat, Lon points and whether they are in radians or degrees 
  Converts to radians if need be, then using hahversine formula to compute the distance
  ChatGPT pointed me to haversine formula as longitudinal distance changes based on lat
  found here: https://www.movable-type.co.uk/scripts/latlong.html
  '''
  assert len(point1) == 2, "invalid first point"
  assert len(point2) == 2, "invalid second point"
  assert isinstance(point1, (list, tuple)), "Point one must be a list or tuple"
  assert isinstance(point2, (list, tuple)), "Point two must be a list or tuple"
  assert all(isinstance(xy1, (float)) for xy1 in point1), "All elements must be float"
  assert all(isinstance(xy2, (float)) for xy2 in point2), "All elements must be float"
  #use haversine formula for GPS distance
  #compute delta lat/lon
  if Rad:
    dlat = point1[0] - point2[0]
    dlon = point1[1] - point2[1]
    theta1 = point1[0]
    theta2 = point2[0]
  else: #convert to Rad if need be
    dlat = (point1[0] - point2[0])*math.pi/180
    dlon = (point1[1] - point2[1])*math.pi/180
    theta1 = point1[0]*math.pi/180
    theta2 = point2[0]*math.pi/180
    phi1 = point1[1]*math.pi/180
    phi2 = point2[1]*math.pi/180
  # Latitude and longitude range validity check
  assert -math.pi/2 <= theta1 <= math.pi/2, f"Latitude of point1 invalid or you did not specify degrees: { point1 }"
  assert -math.pi/2 <= theta2 <= math.pi/2, f"Longitude of point2 invalid or you did not specify degrees: { point2 }"
  assert -math.pi <= phi1 <= math.pi, f"Longitude of point1 invalid or you did not specify degrees: { point1 }"
  assert -math.pi <= phi2 <= math.pi, f"Longitude of point2 invalid or you did not specify degrees: { point2 }"

  a = math.sin(dlat / 2)**2 + math.cos(theta1) * math.cos(theta2) * math.sin(dlon / 2)**2
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

  return c*6371000
  


def p2arr_dist(point, refarray, rad=0):
  assert isinstance(refarray, np.ndarray), "Ref Array must be np array"
  assert refarray.size > 0, "Ref array must not be empty"
  dist_arr = np.zeros(refarray.shape[0])
  for idx in range(refarray.shape[0]):
    dist_arr[idx] = p2p_dist(point, tuple(refarray[idx]), rad)
  return dist_arr


def arr2arr_match(arr1, arr2, rad):
  assert isinstance(arr1, np.ndarray), "Ref Array must be np array"
  assert arr1.size > 0, "Ref array must not be empty"
  assert isinstance(arr2, np.ndarray), "Ref Array must be np array"
  assert arr2.size > 0, "Ref array must not be empty"
  if arr2.size > arr1.size:
    min_dist_idxs = np.zeros(arr2.shape[0], 'int')
    idxes = range(arr2.shape[0])
    for idx2 in idxes: 
      distlist = p2arr_dist(tuple(arr2[idx2]), arr1, rad)
      min_index = np.argmin(distlist)
      min_dist_idxs[idx2] = min_index
  else:
    min_dist_idxs = np.zeros_like(arr1.shape[0])
    idxes = range(arr1.shape[0])
    for idx1 in idxes: 
      distlist = p2arr_dist(tuple(arr1[idx1]), arr2, rad)
      min_index = np.argmin(distlist)
      min_dist_idxs[idx1] = min_index
  return min_dist_idxs

def correct_test():
  BostonMA = (42.3601, -71.0589)
  JawsBridgeMA = (41.4164, -70.5482)
  DorchesterMA = (42.3016, -71.0677)
  RumneyNH = (43.8073, -71.8159)
  PlymouthNH = (43.7570, -71.6887)
  CambridgeMA = (42.3736,- 71.1097)
  CapeCodMA = (41.6688, -70.2962)
  ArlingtonMA = (42.4154, -71.1565)
  QuincyMA = (42.2529, -71.0023)
  BangorME = (44.8012, -68.7778)
  arr1 = np.array([BostonMA, RumneyNH, CapeCodMA])
  arr2 = np.array([DorchesterMA,CambridgeMA,ArlingtonMA,BangorME,PlymouthNH,QuincyMA, JawsBridgeMA])
  answer = np.array([0, 0, 0, 1, 1, 0, 2], 'int')
  print(f"{arr2arr_match(arr1, arr2, 0)}\n{answer}")

def fail_test1(): 
  BostonMA = (42.3601, -71.0589)
  JawsBridgeMA = (41.4164, -270.5482)
  DorchesterMA = (42.3016, -71.0677)
  RumneyNH = (43.8073, -71.8159)
  PlymouthNH = (43.7570, -71.6887)
  CambridgeMA = (42.3736,- 71.1097)
  CapeCodMA = (41.6688, -70.2962)
  ArlingtonMA = (42.4154, -71.1565)
  QuincyMA = (42.2529, -71.0023)
  BangorME = (44.8012, -68.7778)
  arr1 = np.array([BostonMA, RumneyNH, CapeCodMA])
  arr2 = np.array([DorchesterMA,CambridgeMA,ArlingtonMA,BangorME,PlymouthNH,QuincyMA, JawsBridgeMA])
  arr2arr_match(arr1, arr2, 0)

def fail_test2(): 
  BostonMA = (42.3601, -71.0589)
  JawsBridgeMA = (41.4164, None)
  DorchesterMA = (42.3016, -71.0677)
  RumneyNH = (43.8073, -71.8159)
  PlymouthNH = (43.7570, -71.6887)
  CambridgeMA = (42.3736,- 71.1097)
  CapeCodMA = (41.6688, -70.2962)
  ArlingtonMA = (42.4154, -71.1565)
  QuincyMA = (42.2529, -71.0023)
  BangorME = (44.8012, -68.7778)
  arr1 = np.array([BostonMA, RumneyNH, CapeCodMA])
  arr2 = np.array([DorchesterMA,CambridgeMA,ArlingtonMA,BangorME,PlymouthNH,QuincyMA, JawsBridgeMA])
  arr2arr_match(arr1, arr2, 0)

def fail_test3(): 
  BostonMA = ("42.3601", "-71.0589")
  JawsBridgeMA = (41.4164, -70.5482)
  DorchesterMA = (42.3016, -71.0677)
  RumneyNH = ("43.8073", "-71.8159")
  PlymouthNH = (43.7570, -71.6887)
  CambridgeMA = (42.3736,- 71.1097)
  CapeCodMA = ("41.6688", "-70.2962")
  ArlingtonMA = (42.4154, -71.1565)
  QuincyMA = (42.2529, -71.0023)
  BangorME = (44.8012, -68.7778)
  arr1 = np.array([BostonMA, RumneyNH, CapeCodMA])
  arr2 = np.array([DorchesterMA,CambridgeMA,ArlingtonMA,BangorME,PlymouthNH,QuincyMA, JawsBridgeMA])
  arr2arr_match(arr1, arr2, 0)

def test():
  correct_test()
  try:
    fail_test1()
  except Exception as e: 
    print(f"fail_test1 failed: {e}")
  try:
    fail_test2()
  except Exception as e: 
    print(f"fail_test2 failed: {e}")
  try:
    fail_test3()
  except Exception as e: 
    print(f"fail_test3 failed: {e}")

if __name__ == "__main__":
    # Run the test function
    test()




