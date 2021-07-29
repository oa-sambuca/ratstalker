#!/usr/bin/env python3

"""RatStalker: a Matrix bot that stalks rats"""

import asyncio
import os
import sqlite3
import json

import nio
import aiofiles

from config import Config
from src import callbacks
from src import exceptions
from src import snapshot
from src import messages
from src import persistence



banner = """
░█▀▄░█▀█░▀█▀░█▀▀░▀█▀░█▀█░█░░░█░█░█▀▀░█▀▄
░█▀▄░█▀█░░█░░▀▀█░░█░░█▀█░█░░░█▀▄░█▀▀░█▀▄
░▀░▀░▀░▀░░▀░░▀▀▀░░▀░░▀░▀░▀▀▀░▀░▀░▀▀▀░▀░▀
           A Matrix bot that stalks rats
"""

class BotContext:
    """Bot context also shared with callbacks"""
    def __init__(self,
            client: nio.AsyncClient,
            last_snapshot: snapshot.GlobalSnapshot,
            monitor_wakeup_event: asyncio.Event):
        self.client = client
        self.last_snapshot = last_snapshot
        self.monitor_wakeup_event = monitor_wakeup_event

class RatStalker:
    """RatStalker bot class"""
    def __init__(self, client: nio.AsyncClient):
        self.context = BotContext(
                client,
                snapshot.GlobalSnapshot(),
                asyncio.Event())
        messages.MessageSender.client = client

    def _init_callbacks(self):
        self.context.client.add_event_callback(
                callbacks.RoomMessageCallback(self.context),
                nio.RoomMessageText)
        if not Config.Bot.bot_owned_rooms:
            self.context.client.add_event_callback(
                    callbacks.RoomInviteCallback(self.context),
                    nio.InviteEvent)
    
    async def start_stalking(self):
        """Start stalking!"""
        # create stalk list table if it doesn't exist
        persistence.db.create_tables([persistence.RatstalkerStalkLists])
        await self.context.client.login(Config.Matrix.passwd)
        await self.context.client.set_displayname(Config.Bot.name)
        while True:
            joined_rooms = await self.context.client.joined_rooms()
            if type(joined_rooms) is nio.JoinedRoomsResponse:
                break
            asyncio.sleep(10)
        if Config.Bot.admin_room not in joined_rooms.rooms:
            # make sure we join the admin room if not already
            res = await self.context.client.join(Config.Bot.admin_room)
            if type(res) is nio.JoinResponse:
                print("+ Joined admin room")
            else:
                print("- Unable to join admin room ({})".format(res.message))
        # dummy sync to consume events arrived while offline
        # TODO: better using first_sync_filter in sync_forever to filter offline events
        await self.context.client.sync(full_state=True)
        self._init_callbacks()
        try:
            await asyncio.gather(
                    self.context.client.sync_forever(
                        None, full_state=True, loop_sleep_time=Config.Bot.sync_time),
                    self._monitor_servers())
        except asyncio.CancelledError:
            # cleaning local stuff
            raise

    async def _monitor_servers(self):
        if Config.Bot.monitor:
            self.context.monitor_wakeup_event.set()
        while await self.context.monitor_wakeup_event.wait():
            try:
                snap = snapshot.GlobalSnapshot().capture(self.context.last_snapshot)
                await self._process_snapshots(snap)
                self.context.last_snapshot = snap
            except Exception:
                raise
            callbacks.RoomMessageCallback.reset_requests_count()
            await asyncio.sleep(Config.Bot.monitor_time * 60)

    async def _process_snapshots(self, snap: snapshot.GlobalSnapshot):
        for sid, ssnap in snap.servers_snaps.items():
            try:
                matched_rules = ssnap.compare(self.context.last_snapshot.servers_snaps[sid])
            except KeyError:
                # No snapshot with server id sid in last_snapshot (e.g. at start)
                # => compare against a DummyServerSnapshot
                matched_rules = ssnap.compare(snapshot.DummyServerSnapshot(ssnap.timestamp))
            rooms = (await self.context.client.joined_rooms()).rooms
            msgs = {}
            for rule in matched_rules:
                ruletype = type(rule)
                if ruletype is snapshot.OverThresholdRule:
                    msgs = {messages.OverThresholdNotification(ssnap) : rooms}
                elif ruletype is snapshot.UnderThresholdRule:
                    msgs = {messages.UnderThresholdNotification(ssnap) : rooms}
                elif ruletype is snapshot.DurationRule:
                    msgs = {messages.DurationNotification(ssnap) : rooms}
                elif ruletype is snapshot.StalkEnterRule:
                    msgs = dict(zip(
                        [messages.StalkEnterNotification([player], ssnap) for player in rule.stalked_players.keys()],
                        rule.stalked_players.values()))
                elif ruletype is snapshot.StalkLeaveRule:
                    msgs = dict(zip(
                        [messages.StalkLeaveNotification([player], ssnap) for player in rule.stalked_players.keys()],
                        rule.stalked_players.values()))
                else:
                    print("! Unable to handle rule: {}".format(ruletype))
                    continue

                for msg in msgs.keys():
                    print(msg.term)
                    await messages.MessageSender.send_rooms(msg, msgs[msg])



class Main:
    @classmethod
    def _retrieve_device_id(cls) -> str:
        """Retrieve the device id from the matrix store

        Return the device id from the matrix store, or an empty string if none
        is found, in which case it will be later generated by the server on the
        first connection and stored for subsequent use.
        """
        con = sqlite3.connect(os.path.join(Config.Bot.store_dir, Config.Bot.store_name))
        try:
            device_id = con.execute("SELECT device_id FROM accounts;").fetchone()[0]
        except (TypeError, sqlite3.OperationalError):
            device_id = ""
        finally:
            con.close()
        return device_id

    @classmethod
    async def main(cls):
        print(banner)
        if not os.path.isdir(Config.Bot.store_dir):
            print("+ Creating the store dir: {}".format(Config.Bot.store_dir))
            os.mkdir(Config.Bot.store_dir)
        device_id = cls._retrieve_device_id()
        client_config=nio.ClientConfig(
                store_name=Config.Bot.store_name,
                store_sync_tokens=True)
        client = nio.AsyncClient(
                Config.Matrix.server,
                Config.Matrix.user_id,
                device_id=device_id,
                store_path=Config.Bot.store_dir,
                config=client_config)
        ratstalker = RatStalker(client)

        try:
            await ratstalker.start_stalking()
        except asyncio.CancelledError:
            print("* Terminating active tasks...")
            await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(Main.main())
    except KeyboardInterrupt:
        print("* Shutting down...")
