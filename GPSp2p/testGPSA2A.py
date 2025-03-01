from GPSArray2Array import *

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
  print(f"{arr2arr_match(arr2, arr1, 0)}\n{answer}")

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

def testgps2arr():
  correct_test()
  try:
    fail_test1()
  except Exception as e:
    pass
  try:
    fail_test2()
  except Exception as e:
    pass
  try:
    fail_test3()
  except Exception as e:
    pass

