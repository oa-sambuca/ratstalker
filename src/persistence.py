"""Persistence layer via peewee ORM"""

import os

from peewee import *

from config import Config



db = SqliteDatabase(
        os.path.join(Config.Bot.store_dir, Config.Bot.store_name),
        pragmas = {
                'journal_mode'              : 'wal',
                'cache_size'                : -1 * 16000,   # 16MB
                'foreign_keys'              : 1,
                'ignore_check_constraints'  : 0,
                'synchronous'               : 0})

class BaseModel(Model):
    class Meta:
        database = db
        legacy_table_names = False

# keep it simple for now, until we really need to split tables
class RatstalkerStalkLists(BaseModel):
    room_id = CharField()
    player = CharField()

    class Meta:
        # unique constraint
        indexes = ((('room_id', 'player'), True),)
