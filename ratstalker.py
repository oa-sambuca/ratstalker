#!/usr/bin/env python3

"""RatStalker: a Matrix bot that stalks rats"""

import asyncio
import os
import sys

import nio

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
        self.message_sender = messages.MessageSender(client)

class RatStalker:
    """RatStalker bot class"""
    def __init__(self, client: nio.AsyncClient):
        self.context = BotContext(
                client,
                snapshot.GlobalSnapshot(),
                asyncio.Event())

    def _init_callbacks(self):
        self.context.client.add_event_callback(
                callbacks.RoomMessageCallback(self.context),
                nio.RoomMessageText)
        self.context.client.add_event_callback(
                callbacks.RoomInviteCallback(self.context),
                nio.InviteEvent)

    async def start_stalking(self):
        """Start stalking!"""
        await self.context.client.login(Config.Matrix.passwd)
        await self.context.client.set_displayname(Config.Bot.name)
        joinresp = await self.context.client.join(Config.Matrix.room)
        if type(joinresp) is nio.responses.JoinError:
            print("- Could not join room {}: {}".format(
                        Config.Matrix.room,
                        joinresp.message)
                    )
        else:
            print("+ Joined room: {}".format(Config.Matrix.room))
        # dummy sync to consume events arrived while offline
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
                await self._process_snapshot(snap)
                self.context.last_snapshot = snap
            except Exception:
                raise
            await asyncio.sleep(Config.Bot.monitor_time * 60)

    async def _process_snapshot(self, snap: snapshot.GlobalSnapshot):
        for ssnap in snap.servers_snaps.values():
            sname = ssnap.info.name()
            try:
                matched_rules = ssnap.compare(self.context.last_snapshot.servers_snaps[sname.getstr()])
            except KeyError:
                # No snapshot named sname in last_snapshot (e.g. at start)
                # => compare against a DummyServerSnapshot
                matched_rules = ssnap.compare(snapshot.DummyServerSnapshot(ssnap.timestamp))
            for rule in matched_rules:
                ruletype = type(rule)
                if ruletype is snapshot.OverThresholdRule:
                    players =  [player.name for player in ssnap.info.likely_human_players()]
                    message = messages.OverThresholdMessage(sname, ssnap.info.num_humans(), players)
                elif ruletype is snapshot.UnderThresholdRule:
                    message = messages.UnderThresholdMessage(sname, ssnap.info.num_humans())
                elif ruletype is snapshot.DurationRule:
                    players =  [player.name for player in ssnap.info.likely_human_players()]
                    message = messages.DurationMessage(sname, players)
                else:
                    print("! Unable to handle rule: {}".format(ruletype))
                    continue
                print("{}".format(message.term))
                await self.context.message_sender.send_room(message)



class Main:
    def __init__(self):
        self.device_id = self._compute_device_id()

    def _compute_device_id(self) -> str:
        # mix of fixed platform infos... should be enough for us
        sysinfo = os.uname()
        return "{}@{}({})".format(
                sysinfo.nodename,
                sysinfo.sysname,
                sysinfo.machine)

    async def main(self):
        print(banner)
        if not os.path.isdir(Config.Bot.store_dir):
            os.mkdir(Config.Bot.store_dir)
        client_config=nio.ClientConfig(
                store_name=Config.Bot.store_name,
                store_sync_tokens=True)
        client = nio.AsyncClient(
                Config.Matrix.server,
                Config.Matrix.user,
                device_id=self.device_id,
                store_path=Config.Bot.store_dir,
                config=client_config)
        ratstalker = RatStalker(client)

        try:
            await ratstalker.start_stalking()
        except asyncio.CancelledError:
            print("* Terminating active tasks...")
            await client.close()

if __name__ == "__main__":
    main = Main()
    try:
        asyncio.run(main.main())
    except KeyboardInterrupt:
        print("* Shutting down...")
