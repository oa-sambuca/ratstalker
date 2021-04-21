"""Commands processed by the bot"""

from typing import List
import json

import deps.oaquery.oaquery as oaquery

from config import Config
import exceptions



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
                    info.name().getstr() : {
                        "map"       : info.map(),
                        "game"      : info.game(),
                        "nplayers"  : "{}/{}/{}".format(
                            info.num_humans(),
                            info.num_clients(),
                            info.maxclients()),
                        "players"   : [player.name.getstr() for player in info.likely_human_players()]
                        }
                    })
        return json.dumps(resp, indent=2)

class ListServersCommand(Command):
    """List all configured OA servers"""
    async def execute(self) -> str:
        return json.dumps(Config.OAQuery.hosts, indent=2)

class MonitorCommand(Command):
    """Set or get the monitor option"""
    async def execute(self) -> str:
        try:
            state = self.args[0].lower()
        except IndexError:
            pass
        else:
            if state == "true":
                Config.Bot.monitor = True
            elif state == "false":
                Config.Bot.monitor = False
        finally:
            return "Monitor: {}".format(Config.Bot.monitor)

class HelpCommand(Command):
    """Show help"""
    async def execute(self) -> str:
        return "usage: {} <query|listservers|monitor[true|false]|help>".format(Config.Bot.trigger)
