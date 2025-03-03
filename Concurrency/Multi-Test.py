import time
import numpy as np
import queue
import threading
import multiprocessing
from MultiMatMulWrapper import *

if __name__ == "__main__":
    import time

    size = 1
    num_tasks = 2
    reps = 3

    tasks = [(np.random.rand(size, size), np.random.rand(size, size)) for _ in range(2*num_tasks)]

    print("Testing Multi-threading...")
    matmul_threaded = MatmulWrapper(workers=2, use_multiprocessing=False)


    i = 1
    t = 1    
    start_time = time.time()
    while i<reps:
        for A,B in tasks: 
            success = matmul_threaded.add_task(A, B)
            if success: 
                t+=1
                success = False
                if t >= num_tasks:
                    t = 0
                    i+=1
                    tasks = [(np.random.rand(size, size), np.random.rand(size, size)) for _ in range(num_tasks)]

    matmul_threaded.stop_workers()
    print(f"Multi-threading Time: {time.time() - start_time:.4f} seconds")

    print("\nTesting Multi-processing...")
    matmul_multiprocess = MatmulWrapper(workers=2, use_multiprocessing=True)
    for A, B in tasks:
        matmul_multiprocess.add_task(A, B)

    start_time = time.time()
    matmul_multiprocess.start_workers()
    matmul_multiprocess.stop_workers()
    print(f"Multi-processing Time: {time.time() - start_time:.4f} seconds")

