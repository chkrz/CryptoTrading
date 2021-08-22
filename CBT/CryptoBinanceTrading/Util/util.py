import asyncio
import concurrent.futures
import logging


def check_result(result, retry_on_result):
    return result is retry_on_result


def retry(times, retry_on_result):
    def func_wrapper(f):
        async def wrapper(*args, **kwargs):
            for time in range(times):
                try:
                    if check_result(await f(*args, **kwargs), retry_on_result):
                        continue
                    else:
                        break
                except Exception as exc:
                    pass
        return wrapper
    return func_wrapper 


executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def info(msg, *args):
    executor.submit(logging.info, str(msg), *args)

