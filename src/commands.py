"""Commands processed by the bot"""

from typing import List
import asyncio

from deps.oaquery import oaquery

from config import Config
from src import exceptions
from src import snapshot



class Command:
    """Base class for commands"""
    def __init__(self, args: List[str] = None):
        if type(self) is Command:
            raise NotImplementedError
        self.args = args

    async def execute(self) -> str:
        """Execute command

        returns a string suitable to be replied back
        raises CommandExecutionError
        """

class QueryCommand(Command):
    """Query all configured OA servers, optionally by keyword"""
    def __init__(self, snapshot: snapshot.GlobalSnapshot, by_servername: bool = True, args: List[str] = None):
        super().__init__(args)
        self.snapshot = snapshot
        self.by_servername = by_servername

    async def execute(self) -> str:
        snaps = (self.snapshot.filter_by_servername(self.args) if self.by_servername else
        self.snapshot.filter_by_players(self.args))

        resp = {}
        for info in [s.info for s in snaps]:
            resp.update({
                    info.name().gethtml() : {
                        "map"       : info.map(),
                        "game"      : info.game(),
                        "nplayers"  : "{}/{}/{}".format(
                            info.num_humans(),
                            info.num_clients(),
                            info.maxclients()),
                        "players"   : [player.name.gethtml() for player in info.likely_human_players()]
                        }
                    })
        return str(resp) if resp else "No match for: {}".format(', '.join(self.args))

class MonitorCommand(Command):
    """Set or get the monitor option"""
    def __init__(self, wakeup_event: asyncio.Event, args: List[str] = None):
        super().__init__(args)
        self.wakeup_event = wakeup_event

    async def execute(self) -> str:
        try:
            state = self.args[0].lower()
        except IndexError:
            pass
        else:
            if state == "true":
                Config.Bot.monitor = True
                # restart the monitor task
                await self.wakeup_event.set()
            elif state == "false":
                Config.Bot.monitor = False
                # stop the monitor task
                await self.wakeup_event.clear()
        finally:
            return "Monitor: {}".format(Config.Bot.monitor)

class HelpCommand(Command):
    """Show help"""
    async def execute(self) -> str:
        return "usage: {} query[ keywords]|stalk players|monitor[ true|false]|help".format(Config.Bot.name)
