"""Commands processed by the bot"""

from typing import List
import asyncio

from deps.oaquery import oaquery

from config import Config
from src import exceptions



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
    """Query all configured OA servers"""
    async def execute(self) -> str:
        infos: List[oaquery.ServerInfo] = oaquery.query_servers(Config.OAQuery.hosts.values())
        resp = {}
        for info in infos:
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
        return str(resp)

class ListServersCommand(Command):
    """List all configured OA servers"""
    async def execute(self) -> str:
        return str(Config.OAQuery.hosts)

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
        return "usage: {} query|listservers|monitor[true|false]|help".format(Config.Bot.trigger)
