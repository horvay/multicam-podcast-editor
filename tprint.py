import time
import functools
import sys

start_time = time.perf_counter()


def print_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = int(time.perf_counter() - start_time)
        sys.stdout.write(f"[{timestamp}s]: ")
        return func(*args, **kwargs)

    return wrapper
