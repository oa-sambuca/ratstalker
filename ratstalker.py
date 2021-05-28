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
    
    async def _load_stalk_list(self):
        stalk_list_file = os.path.join(Config.Bot.store_dir, Config.Players.stalk_list_file)
        try:
            async with aiofiles.open(stalk_list_file, "r") as f:
                Config.Players.stalk_list = set(json.loads(await f.read()))
        except FileNotFoundError:
            print("+ Creating stalk list file: {}".format(stalk_list_file))
            async with aiofiles.open(stalk_list_file, 'w') as f:
                await f.write(json.dumps(list()))
        except json.JSONDecodeError:
            print("! Malformed stalk list file")

    async def start_stalking(self):
        """Start stalking!"""
        await self.context.client.login(Config.Matrix.passwd)
        await self.context.client.set_displayname(Config.Bot.name)
        Config.Matrix.rooms = (await self.context.client.joined_rooms()).rooms
        if Config.Bot.admin_room not in Config.Matrix.rooms:
            # make sure we join the admin room if not already
            res = await self.context.client.join(Config.Bot.admin_room)
            if type(res) is nio.JoinResponse:
                Config.Matrix.rooms.append(Config.Bot.admin_room)
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
        await self._load_stalk_list()
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
            for rule in matched_rules:
                ruletype = type(rule)
                if ruletype is snapshot.OverThresholdRule:
                    message = messages.OverThresholdNotification(ssnap)
                elif ruletype is snapshot.UnderThresholdRule:
                    message = messages.UnderThresholdNotification(ssnap)
                elif ruletype is snapshot.DurationRule:
                    message = messages.DurationNotification(ssnap)
                elif ruletype is snapshot.PlayerEnterRule:
                    message = messages.PlayerEnterNotification(rule.players, ssnap)
                elif ruletype is snapshot.PlayerLeaveRule:
                    message = messages.PlayerLeaveNotification(rule.players, ssnap)
                else:
                    print("! Unable to handle rule: {}".format(ruletype))
                    continue
                print(message.term)
                await messages.MessageSender.send_rooms(message, Config.Matrix.rooms)



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
                Config.Matrix.user,
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
