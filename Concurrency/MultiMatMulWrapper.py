import multiprocessing.queues
import numpy as np
import queue
import threading
import multiprocessing

# Required for macOS compatibility
multiprocessing.set_start_method("spawn", force=True)


def worker(task_queue, result_queue):
    """Standalone worker function that processes matrix multiplication tasks."""
    while True:
        try:
            matrices = task_queue.get(timeout = .1)
            if matrices is None:
                break  # Stop signal

            A, B = matrices
            result = np.matmul(A, B)
            result_queue.put_nowait(result)
            print(result)
        except multiprocessing.queues.Empty:
            break

class MatmulWrapper:
    def __init__(self, workers=4, use_multiprocessing=True, QueueSize = 100):
        self.workers = workers
        self.use_multiprocessing = use_multiprocessing
        self.manager = multiprocessing.Manager() if use_multiprocessing else None

        self.task_queue = self.manager.Queue(maxsize=QueueSize) if use_multiprocessing else queue.Queue(maxsize=QueueSize)
        self.result_queue = self.manager.Queue() if use_multiprocessing else queue.Queue()

        self._workers = []

    def start_workers(self):
        """Starts the worker threads or processes."""
        for _ in range(self.workers):
            if self.use_multiprocessing:
                p = multiprocessing.Process(target=worker, args=(self.task_queue, self.result_queue))
                p.start()
                self._workers.append(p)
            else:
                t = threading.Thread(target=self.thread_worker)
                t.start()
                self._workers.append(t)

    def thread_worker(self):
        """Thread-based worker."""
        while True:
            try:
                matrices = self.task_queue.get(timeout=1)
                if matrices is None:
                    break
                A, B = matrices
                result = np.matmul(A, B)
                self.result_queue.put_nowait(result)
            except queue.Empty:
                break

    def stop_workers(self):
        """Stops all workers gracefully."""
        for _ in range(self.workers):
            pass #self.task_queue.put(None)  # Stop signal

        for worker in self._workers:
            worker.join()

    def add_task(self, A, B):
        """Adds a matrix multiplication task to the queue."""
        if self.task_queue.full(): 
            return False 
        try:
            self.task_queue.put_nowait((A, B))
            self.start_workers()
            return True
        except:
            return False



    def get_results(self):
        """Retrieves all results from the queue."""
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        return results


