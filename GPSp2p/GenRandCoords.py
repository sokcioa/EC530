import numpy as np

def generate_random_gps(n):
    latitudes = np.random.uniform(-90, 90, n)
    longitudes = np.random.uniform(-180, 180, n)
    return np.column_stack((latitudes, longitudes))  # Shape (n, 2)
