"""Persistence layer via peewee ORM"""

import os
from typing import List

from peewee import *

from config import Config
from src import exceptions
from src import messages



# NOTE: we could use the same db as matrxi-nio, but we should open it with the
# same settings used by nio to avoid database corruptions (e.g. using two
# different journal types on the same db) as we would end up doing writings
# from two concurrent connections (internal nio and ratstalker) with different
# settings.
# see: https://www.sqlite.org/howtocorrupt.html
#
# currently, nio uses (https://github.com/poljar/matrix-nio/blob/0b26fbf2f8bc3cd989f43f01c296a717c3995ef4/nio/store/database.py#L88):
# pragmas={"foreign_keys": 1, "secure_delete": 1,}
#
# since it is not specifying them, it is using defaults for journal_mode and
# synchronous which should be DELETE and FULL (2) respectively (even if
# synchronous should not cause corruptions)
#
# To be totally safe and independent from nio choices (which may change over
# time without us knowing before it's too late to prevent data loss) we just
# use a separate db, without contraints on settings
db = SqliteDatabase(
        os.path.join(Config.Bot.store_dir, Config.Bot.bot_store_name),
        pragmas = {
                'journal_mode'              : 'wal',
                'cache_size'                : -1 * 16000,   # 16MB
                'foreign_keys'              : 1,
                'ignore_check_constraints'  : 0,
                'synchronous'               : 0})

class RatstalkerDatabase:
    """Database access facade"""

    def db_session(action):
        """Database session wrapper"""
        def wrap(*args):
            with db.connection_context():
                return action(*args)
        return wrap

    @classmethod
    @db_session
    def create_tables(cls):
        """Create database tables"""
        db.create_tables([
            StalkingRooms,
            StalkedPlayers,
            Stalkings],
            safe = True)

    @classmethod
    @db_session
    def count_stalked_players(cls, room: str) -> int:
        """Return the number of players stalked by the given room"""
        return (Stalkings.select()
                .join(StalkingRooms)
                .where(StalkingRooms.room == room)
                .count())

    @classmethod
    def _purge_unreferenced_players(cls):
        """Delete players who have no reference in the stalking table"""
        unreferenced_players = (
                StalkedPlayers.select()
                .join(Stalkings, JOIN.LEFT_OUTER)
                .where(Stalkings.room.is_null(True)))
        with db.atomic() as transaction:
            for player in unreferenced_players:
                player.delete_instance()

    @classmethod
    @db_session
    def add_stalkings(cls, room: str, players: List[str]):
        """Add stalked players to room"""
        with db.atomic() as transaction:
            room_entry, _ = StalkingRooms.get_or_create(
                    room = room)
            for player in players:
                # can't use get_or_create since for subsequent calls for an already
                # formattied player, it will try an insert but will violate unique
                try:
                    player_entry = StalkedPlayers.get(StalkedPlayers.player_text == player)
                except StalkedPlayers.DoesNotExist:
                    player_entry = StalkedPlayers.create(
                            player_text = player,
                            player_term = player,
                            player_html = player)
                Stalkings.insert(
                        room = room_entry, player = player_entry).on_conflict_ignore().execute()

    @classmethod
    @db_session
    def del_stalkings(cls, room: str, players: List[str]):
        """Delete stalked players from room"""
        stalked_players = (
                StalkedPlayers.select()
                .where(StalkedPlayers.player_text.in_(players)))
        stalking_room = StalkingRooms.get(StalkingRooms.room == room)
        with db.atomic() as transaction:
            (Stalkings.delete()
            .where(
                    (Stalkings.room == stalking_room) &
                    (Stalkings.player.in_(stalked_players)))
            .execute())
            cls._purge_unreferenced_players()

    @classmethod
    @db_session
    def clear_stalkings(cls, room: str):
        """Delete all stalked players from room"""
        stalking_room = StalkingRooms.get(StalkingRooms.room == room)
        with db.atomic() as transaction:
            (Stalkings.delete()
            .where(Stalkings.room == stalking_room)
            .execute())
            cls._purge_unreferenced_players()

    @classmethod
    @db_session
    def list_stalkings(cls, room: str):
        """List stalked players of room"""
        return (StalkedPlayers.select(
                    StalkedPlayers.player_text,
                    StalkedPlayers.player_term,
                    StalkedPlayers.player_html)
                .join(Stalkings)
                .where(StalkingRooms.room == room)
                .join(StalkingRooms)
                .order_by(fn.Lower(StalkedPlayers.player_text)))

    @classmethod
    @db_session
    def delete_rooms(cls, rooms: List[str]):
        """Delete rooms (and its associated stalk list)"""
        with db.atomic() as transaction:
            (StalkingRooms.delete()
            .where(StalkingRooms.room.in_(rooms))
            .execute())
            # CASCADE will take care of deleting entries in stalk_lists
            cls._purge_unreferenced_players()

    @classmethod
    @db_session
    def find_interested_rooms(cls, player: str) -> List[str]:
        """Find rooms interested in the given player"""
        return [entry.room for entry in (
                StalkingRooms.select(StalkingRooms.room)
                .join(Stalkings)
                .join(StalkedPlayers)
                .where(StalkedPlayers.player_text == player))]

    @classmethod
    @db_session
    def refresh_players_strings(cls, players: List[messages.FormattedString]):
        """Refresh the term/html formatted fields of the players"""
        with db.atomic() as transaction:
            for player in players:
                (StalkedPlayers.update(
                        player_term = player.get_term(),
                        player_html = player.get_html())
                .where(StalkedPlayers.player_text == player.get_text())
                .execute())



class BaseModel(Model):
    class Meta:
        database = db
        legacy_table_names = False

class StalkingRooms(BaseModel):
    room = CharField(unique=True)

class StalkedPlayers(BaseModel):
    player_text = CharField(unique=True)
    player_term = CharField()
    player_html = CharField()

    class Meta:
        # unique constraint, single fields uniqueness guaranteed by oaquery library
        indexes = ((('player_text', 'player_term', 'player_html'), True),)

class Stalkings(BaseModel):
    room = ForeignKeyField(StalkingRooms, backref="stalkings", on_delete='CASCADE', on_update='CASCADE')
    player = ForeignKeyField(StalkedPlayers, backref="stalkings", on_delete='CASCADE', on_update='CASCADE')

    class Meta:
        # unique constraint
        indexes = ((('room', 'player'), True),)
