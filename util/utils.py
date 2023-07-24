# coding=utf-8
import multiprocessing
import time


def cts():
    return int(time.time() * 1000)


class MultiProcessExecutor:
    def __init__(self):
        self.tasks = []
        self.pool = None

    def add_task(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))

    def execute(self):
        self.pool = multiprocessing.Pool(processes=len(self.tasks))

        results = []
        for task in self.tasks:
            func, args, kwargs = task
            result = self.pool.apply_async(func, args=args, kwds=kwargs)
            results.append(result)

        self.pool.close()
        self.pool.join()

        return [result.get() for result in results]
