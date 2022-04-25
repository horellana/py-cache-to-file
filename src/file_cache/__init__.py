import os
import time
import types
import pickle
import asyncio
import hashlib
import functools

import aiofiles


class CacheToFile:
    def __init__(self, ms_timeout=None):
        self.ms_timeout = ms_timeout

    def __call__(self, f):
        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            nonlocal f
            cache_file_name = f"/tmp/{self.generate_file_name(*args)}"

            try:
                async with aiofiles.open(cache_file_name, "rb") as fh:
                    content = await fh.read()
                    return pickle.loads(content.encode())
            except FileNotFoundError as e:
                async with aiofiles.open(cache_file_name, "wb") as fh:
                    value = await f(*args, **kwargs)

                    if isinstance(value, types.GeneratorType):
                        value = list(value)

                    value = pickle.dumps(value)

                    await fh.write(value)

                    return value

        @functools.wraps(f)
        def sync_wrapper(*args, **kwargs):
            nonlocal f
            cache_file_name = f"/tmp/{self.generate_file_name(*args)}"

            try:
                self.invalidate_cache(cache_file_name)

                with open(cache_file_name, "rb") as fh:
                    return pickle.load(fh)

            except EOFError:
                return f(*args, **kwargs)

            except FileNotFoundError as e:
                with open(cache_file_name, "wb") as fh:
                    value = f(*args, **kwargs)

                    if isinstance(value, types.GeneratorType):
                        value = list(value)

                    pickle.dump(value, fh)

                    return value

        if asyncio.iscoroutinefunction(f):
            return async_wrapper
        else:
            return sync_wrapper

    def invalidate_cache(self, cache_path):
        if self.ms_timeout is None:
            return

        last_modified_ts = int(os.path.getmtime(cache_path) * 1000)
        now = int(time.time() * 1000)
        dt = now - last_modified_ts

        if dt >= self.ms_timeout:
            os.remove(cache_path)

    def generate_file_name(self, *args, **kwargs):
        args = (str(pickle.dumps(a)) for a in args)
        args = sorted(args)

        file_name = hashlib.sha256("".join(args).encode()).hexdigest()

        return file_name
