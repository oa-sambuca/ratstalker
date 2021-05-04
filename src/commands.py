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
    def __init__(self, args: List[str] = None):
        if type(self) is Command:
            raise NotImplementedError
        self.args = args

    async def execute(self) -> messages.Reply:
        """Execute command

        returns a reply message
        raises CommandExecutionError
        """

class QueryCommand(Command):
    """Query server snapshots by servername"""
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: List[str] = None):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.QueryReply:
        snaps = self.snapshot.filter_by_servername(self.args)
        return messages.QueryReply(snaps)

class StalkCommand(Command):
    """Query server snapshots by playernames"""
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: List[str] = None):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.StalkReply:
        snaps = self.snapshot.filter_by_players(self.args)
        return messages.StalkReply(snaps)

class MonitorCommand(Command):
    """Set or get the monitor option"""
    def __init__(self, wakeup_event: asyncio.Event, args: List[str] = None):
        super().__init__(args)
        self.wakeup_event = wakeup_event

    async def execute(self) -> messages.MonitorReply:
        try:
            state = self.args[0].lower()
        except IndexError:
            pass
        else:
            if state == "on":
                Config.Bot.monitor = True
                # restart the monitor task
                await self.wakeup_event.set()
            elif state == "off":
                Config.Bot.monitor = False
                # stop the monitor task
                await self.wakeup_event.clear()
        finally:
            return messages.MonitorReply()

class HelpCommand(Command):
    """Show help"""
    async def execute(self) -> messages.HelpReply:
        return messages.HelpReply()
