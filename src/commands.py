"""Commands processed by the bot"""

from typing import List
import asyncio

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
        return messages.QueryReply(snaps)

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

    syntax: stalk list | add player[, ...] | del player[, ...]
    """
    def __init__(self, args: str = ""):
        super().__init__(args)

    async def execute(self) -> messages.StalkReply:
        try:
            action = self.args.split()[0].lower()
        except IndexError:
            action = "list"

        players = [p.strip() for p in self.args[len(action):].split(',')]
        if action == "add":
            Config.Players.stalk_list.update(players)
        elif action == "del":
            Config.Players.stalk_list.difference_update(players)
        return messages.StalkReply()

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

class HelpCommand(Command):
    """Show help"""
    async def execute(self) -> messages.HelpReply:
        return messages.HelpReply()
