import json
import asyncio
import hashlib
import functools

import aiofiles


def cache_to_file(f):
    def generate_file_name(*args, **kwargs):
        return hashlib.sha256(json.dumps(args).encode()).hexdigest()

    @functools.wraps(f)
    async def async_wrapper(*args, **kwargs):
        nonlocal f
        cache_file_name = f"/tmp/{generate_file_name(*args)}"

        try:
            async with aiofiles.open(cache_file_name, "r") as fh:
                return json.loads(await fh.read())
        except Exception as e:
            async with aiofiles.open(cache_file_name, "w") as fh:
                value = await f(*args, **kwargs)

                if isinstance(value, types.GeneratorType):
                    value = list(value)

                await fh.write(json.dumps(value))

                return value

    @functools.wraps(f)
    def sync_wrapper(*args, **kwargs):
        nonlocal f
        cache_file_name = f"/tmp/{generate_file_name(*args)}"

        try:
            with open(cache_file_name, "r") as fh:
                return json.loads(fh.read())
        except Exception as e:
            with open(cache_file_name, "w") as fh:
                value = f(*args, **kwargs)

                if isinstance(value, types.GeneratorType):
                    value = list(value)

                fh.write(json.dumps(value))

                return value

    if asyncio.iscoroutinefunction(f):
        return async_wrapper
    else:
        return sync_wrapper
