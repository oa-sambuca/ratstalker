#!/usr/bin/env python3

"""RatStalker: a Matrix bot that stalks rats"""

import asyncio
import os
import sys

import nio

from config import Config
from src import callbacks
from src import exceptions



class RatStalker:
    """RatStalker bot class"""
    def __init__(self, client: nio.AsyncClient):
        self.client = client

    def _init_callbacks(self):
        context = callbacks.CallbackContext(self.client)
        self.client.add_event_callback(
                callbacks.RoomMessageCallback(context),
                nio.RoomMessageText)
        self.client.add_event_callback(
                callbacks.RoomInviteCallback(context),
                nio.InviteEvent)

    async def start_stalking(self):
        """Start stalking!"""
        self._init_callbacks()

        await self.client.login(Config.Matrix.passwd)
        await self.client.set_displayname(Config.Bot.name)
        joinresp = await self.client.join(Config.Matrix.room)
        if type(joinresp) is nio.responses.JoinError:
            print("- Could not join room {}: {}".format(
                        Config.Matrix.room,
                        joinresp.message)
                    )
        # enter the sync loop anyways and wait for an invite
        await self.client.sync_forever(None, full_state=False)



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
            await asyncio.gather(ratstalker.start_stalking())
        except asyncio.CancelledError:
            print("* Terminating active tasks...")
            await client.close()

if __name__ == "__main__":
    main = Main()
    try:
        asyncio.run(main.main())
    except KeyboardInterrupt:
        print("* Shutting down...")

# FIXME: Syncing should be configured in a way that we only reply to events
# while we are online, i.e. only events since the login time are considered, so
# we don't get flooded by old messages we already received, nor by the ones
# arrived during offline time.
# Sync tokens oth only solve half of the problem, since we still receive the
# messages arrived while we were offline (which we don't care about anymore)
#
# btw it looks like full_state=False alone is not enough to discard old
# messages (whether already synced or not) when we start syncing after login
#
# So, assuming we *must* use sync tokens, current cnfiguration is:
# - set store_sync_tokens=True in ClientConfig()
#   otherwise this is not automatically done
# - set device_id in AsyncClient()
#   otherwise a new device will be created everytime
# - full_state=False in sync_forever()
#   so that we discard events fired while we were offline (doesn't seem to be
#   the case...)
#
# which in the end doesn't seem to work either...
