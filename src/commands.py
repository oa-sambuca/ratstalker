"""Commands processed by the bot"""

from typing import List
import asyncio
import re
import json
import os

import aiofiles
from deps.oaquery import oaquery

from config import Config
from src import exceptions
from src import snapshot
from src import messages



class Command:
    """Base class for commands"""
    def __init__(self, args: str = ""):
        if type(self) is Command:
            raise NotImplementedError
        self.args = args

    async def execute(self) -> messages.Reply:
        """Execute command

        returns a reply message
        raises CommandExecutionError
        """

class QueryCommand(Command):
    """Query server snapshots by servername

    syntax: query[ keyword ...]
    """
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: str = ""):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.QueryReply:
        patterns = self.args.split()
        snaps = self.snapshot.filter_by_servername(patterns)
        return messages.QueryReply(snaps, bool(patterns))

class HuntCommand(Command):
    """Query server snapshots by playernames

    syntax: hunt player[, ...]
    """
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: str = ""):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.HuntReply:
        players = [p.strip() for p in self.args.split(',')]
        snaps = self.snapshot.filter_by_players(players)
        return messages.HuntReply(snaps)

class StalkCommand(Command):
    """List/add/delete players from the stalk list

    syntax: stalk list | clear | save | restore | add player[, ...] | del player[, ...]
    """
    def __init__(self, args: str = ""):
        super().__init__(args)

    async def execute(self) -> messages.StalkReply:
        try:
            action = self.args.split()[0].lower()
        except IndexError:
            action = "list"

        # use re.split() to split commas only when they don't follow a backslash
        players = [p.strip().replace('\,',',') for p in re.split(r'(?<!\\),', self.args[len(action):])]
        if action == "add":
            Config.Players.stalk_list.update(players)
        elif action == "del":
            Config.Players.stalk_list.difference_update(players)
        elif action == "clear":
            Config.Players.stalk_list.clear()
        elif action == "save":
            async with aiofiles.open(os.path.join(Config.Bot.store_dir, Config.Players.stalk_list_file), "w") as f:
                await f.write(json.dumps(list(Config.Players.stalk_list)))
        elif action == "restore":
            async with aiofiles.open(os.path.join(Config.Bot.store_dir, Config.Players.stalk_list_file), "r") as f:
                Config.Players.stalk_list = set(json.loads(await f.read()))
        return messages.StalkReply(action == "save")

class MonitorCommand(Command):
    """Set or get the monitor option

    syntax: monitor[ on | off]
    """
    def __init__(self, wakeup_event: asyncio.Event, args: str = ""):
        super().__init__(args)
        self.wakeup_event = wakeup_event

    async def execute(self) -> messages.MonitorReply:
        if self.args.startswith("on"):
            Config.Bot.monitor = True
            # restart the monitor task
            self.wakeup_event.set()
        elif self.args.startswith("off"):
            Config.Bot.monitor = False
            # stop the monitor task
            self.wakeup_event.clear()
        return messages.MonitorReply()

class NotifyCommand(Command):
    """Send a message to all rooms

    [admin]
    syntax: notify "message"
    """
    def __init__(self, args: str):
        super().__init__(args)

    async def execute(self) -> messages.NotifyReply:
        message = messages.NotifyMessage(self.args.strip('\'"'))
        print(self.args)
        if self.args:
            await messages.MessageSender.send_rooms(
                    message, False,
                    [r for r in Config.Matrix.rooms if r != Config.Bot.admin_room])
        return messages.NotifyReply(bool(self.args))

class HelpCommand(Command):
    """Show help"""
    async def execute(self) -> messages.HelpReply:
        return messages.HelpReply()
