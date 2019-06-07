import asyncio


def run(main):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(main)
    finally:
        loop.close()


# Prefer the run function from the standard library over the custom
# implementation.
run = asyncio.run if hasattr(asyncio, "run") else run
