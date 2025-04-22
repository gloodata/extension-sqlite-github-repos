import aiosql
import aiosqlite
import logging
from enum import Enum
from glootil import DynEnum, identity

log = logging.getLogger("state")


class SQLState:
    def __init__(self, driver_adapter, queries_path="queries.sql"):
        self.conn = None
        self.queries = None
        self.queries_path = queries_path
        self.driver_adapter = driver_adapter

    async def connect(self):
        log.warning("connect not implemented")

    async def disconnect(self):
        log.warning("disconnect not implemented")

    async def setup(self):
        self.queries = aiosql.from_path(self.queries_path, self.driver_adapter)
        await self.connect()

    async def dispose(self):
        await self.disconnect()

    async def query_to_tuple(self, query_name_, query_args_=None, **kwargs):
        return await self.query(
            query_name_, query_args_, keyseq_to_tuple(list(kwargs.items()))
        )

    async def query(self, name, args=None, map=identity, verbose=False):
        args = args if args is not None else {}
        query_args = {key: to_query_arg(value) for key, value in args.items()}

        if verbose:
            log.info("running %s: %s", name, query_args)

        query_fn = getattr(self.queries, name)
        if query_fn:
            rows = map(await query_fn(self.conn, **query_args))
        else:
            log.warning("Query '%s' not found", name)
            rows = []

        if verbose:
            log.debug("result: %s", rows)

        return rows


class SQLiteState(SQLState):
    def __init__(self, db_path, queries_path="queries.sql"):
        super().__init__("aiosqlite", queries_path)
        self.db_path = db_path

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = dict_factory

    async def disconnect(self):
        if self.conn:
            await self.conn.close()
            self.conn = None


def dict_factory(cursor, row):
    r = {}
    i = 0
    for column in cursor.description:
        key = column[0]
        r[key] = row[i]
        i += 1

    return r


def keys_to_tuple(**keys):
    keyseq = list(keys.items())
    return keyseq_to_tuple(keyseq)


def columns_info_to_tuple(cols):
    keyseq = [(col.get("id"), col.get("default")) for col in cols]
    return keyseq_to_tuple(keyseq)


def keyseq_to_tuple(keyseq):
    def key_selector(row):
        return [row.get(key, defval) for key, defval in keyseq]

    def f(r):
        if isinstance(r, list):
            return [key_selector(row) for row in r]
        else:
            return key_selector(r)

    return f


def to_query_arg(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    elif isinstance(value, (Enum, DynEnum)):
        return value.name
    else:
        return str(value)
