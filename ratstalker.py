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



class RatStalker:
    """RatStalker bot class"""
    def __init__(self, client: nio.AsyncClient):
        self.client = client
        self.sender = messages.MessageSender(client)
        self.monitor_wakeup_event = asyncio.Event()
        self.last_snapshot = None

    def _init_callbacks(self):
        context = callbacks.CallbackContext(
                self.client,
                self.sender,
                self.monitor_wakeup_event)
        self.client.add_event_callback(
                callbacks.RoomMessageCallback(context),
                nio.RoomMessageText)
        self.client.add_event_callback(
                callbacks.RoomInviteCallback(context),
                nio.InviteEvent)

    async def start_stalking(self):
        """Start stalking!"""
        await self.client.login(Config.Matrix.passwd)
        await self.client.set_displayname(Config.Bot.name)
        joinresp = await self.client.join(Config.Matrix.room)
        if type(joinresp) is nio.responses.JoinError:
            print("- Could not join room {}: {}".format(
                        Config.Matrix.room,
                        joinresp.message)
                    )
        # dummy sync to consume events arrived while offline
        await self.client.sync(full_state=True)
        self._init_callbacks()
        try:
            await asyncio.gather(
                    self.client.sync_forever(None, full_state=True),
                    self._monitor_servers())
        except asyncio.CancelledError:
            # cleaning local stuff
            raise

    async def _monitor_servers(self):
        if Config.Bot.monitor:
            self.monitor_wakeup_event.set()
        while await self.monitor_wakeup_event.wait():
            try:
                snap = snapshot.GlobalSnapshot().capture()
                await self._process_snapshot(snap)
                self.last_snapshot = snap
            except Exception:
                raise
            await asyncio.sleep(Config.Bot.monitor_time)

    async def _process_snapshot(self, snap: snapshot.GlobalSnapshot):
        for sname, ssnap in snap.servers_snaps.items():
            try:
                matched_rules = ssnap.compare(self.last_snapshot.servers_snaps[sname])
            except (AttributeError, KeyError):
                # first snapshot is None or no snapshot named sname in last_snapshot
                # => compare against a DummyServerSnapshot
                matched_rules = ssnap.compare(snapshot.DummyServerSnapshot())
            for rule in matched_rules:
                ruletype = type(rule)
                if ruletype is snapshot.OverThresholdRule:
                    message = messages.OverThresholdMessage(sname, ssnap.info.num_humans())
                elif ruletype is snapshot.UnderThresholdRule:
                    message = messages.UnderThresholdMessage(sname, ssnap.info.num_humans())
                else:
                    print("! Unable to handle rule: {}".format(ruletype))
                    continue
                print("* {}".format(message.text))
                await self.sender.send_room(message)



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
