import asyncio
import time

from aries_store.bindings import generate_raw_key, version
from aries_store import Store, UpdateEntry

PASS_KEY = "test-password"

PERF_ROWS = 10000


def log(*args):
    print(*args, "\n")


async def basic_test():
    key = generate_raw_key()
    print("Generated key:", key)

    async with Store.provision("sqlite://test.db", "raw", key) as store:
        log(f"Provisioned store: {store}")

        entry = UpdateEntry(
            "category", "name", b"value", {"~plaintag": "a", "enctag": "b"}
        )
        await store.update([entry])

        print("row count:", await store.count("category"))

        entry = await store.fetch("category", "name")
        print(entry)

        async for row in store.scan("category", {"~plaintag": "a", "enctag": "b"}):
            print("scan result", row)

        lock_entry = UpdateEntry(
            "category", "name", b"value", {"~plaintag": "a", "enctag": "b"}
        )

        async with store.create_lock(lock_entry) as lock:
            print(lock.entry)

            entry2 = UpdateEntry("category2", "name2", b"value2")
            await lock.update([entry2])


async def perf_test():
    key = generate_raw_key()

    async with Store.provision(
        #        "postgres://postgres:pgpass@localhost:5432/postgres4", "raw", key
        "sqlite://test.db",
        # "sqlite://:memory:",
        "raw",
        key,
    ) as store:
        insert_start = time.perf_counter()
        for idx in range(PERF_ROWS):
            entry = UpdateEntry(
                "category", f"name-{idx}", b"value", {"~plaintag": "a", "enctag": "b"}
            )
            await store.update([entry])
        dur = time.perf_counter() - insert_start
        print(f"insert duration ({PERF_ROWS} rows): {dur:0.2f}s")

        tags = 0
        fetch_start = time.perf_counter()
        for idx in range(PERF_ROWS):
            entry = await store.fetch("category", f"name-{idx}")
            tags += len(entry.tags)
        dur = time.perf_counter() - fetch_start
        print(f"fetch duration ({PERF_ROWS} rows, {tags} tags): {dur:0.2f}s")

        rc = 0
        tags = 0
        scan_start = time.perf_counter()
        async for row in store.scan("category"):
            rc += 1
            tags += len(row.tags)
        dur = time.perf_counter() - scan_start
        print(f"scan duration ({rc} rows, {tags} tags): {dur:0.2f}s")


if __name__ == "__main__":
    log("aries-store-kv version:", version())

    asyncio.get_event_loop().run_until_complete(perf_test())

    print("done")
