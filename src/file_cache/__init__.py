import types
import pickle
import asyncio
import hashlib
import functools

import aiofiles


def cache_to_file(f):
    def generate_file_name(*args, **kwargs):
        args = (str(pickle.dumps(a)) for a in args)
        args = sorted(args)

        file_name = hashlib.sha256("".join(args).encode()).hexdigest()

        return file_name

    @functools.wraps(f)
    async def async_wrapper(*args, **kwargs):
        nonlocal f
        cache_file_name = f"/tmp/{generate_file_name(*args)}"

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
        cache_file_name = f"/tmp/{generate_file_name(*args)}"

        try:
            with open(cache_file_name, "rb") as fh:
                return pickle.load(fh)
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
