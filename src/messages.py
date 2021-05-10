from typing import List
import html

import nio

from src import snapshot
from config import Config
from deps.oaquery.oaquery import ArenaString, ARENA_COLORS, COLOR_RESET



class ColorPalette:
    """Base class for color palettes"""
    black   = ""
    red     = ""
    green   = ""
    yellow  = ""
    blue    = ""
    cyan    = ""
    magenta = ""
    white   = ""
    orange  = ""

    @classmethod
    def _colorize(cls, string: str, color: str):
        """return the input string colored with the given color"""
        raise NotImplementedError

    @classmethod
    def strblack(cls, string: str):
        return cls._colorize(string, cls.black)
    @classmethod
    def strred(cls, string: str):
        return cls._colorize(string, cls.red)
    @classmethod
    def strgreen(cls, string: str):
        return cls._colorize(string, cls.green)
    @classmethod
    def stryellow(cls, string: str):
        return cls._colorize(string, cls.yellow)
    @classmethod
    def strblue(cls, string: str):
        return cls._colorize(string, cls.blue)
    @classmethod
    def strcyan(cls, string: str):
        return cls._colorize(string, cls.cyan)
    @classmethod
    def strmagenta(cls, string: str):
        return cls._colorize(string, cls.magenta)
    @classmethod
    def strwhite(cls, string: str):
        return cls._colorize(string, cls.white)
    @classmethod
    def strorange(cls, string: str):
        return cls._colorize(string, cls.orange)

class HtmlPalette(ColorPalette):
    # universal palette suitable for both light and dark themes
    colormap = {
            '0' : '4d4d4d',
            '1' : 'db0000',
            '2' : '00cc00',
            '3' : 'f3de00',
            '4' : '4c4cff',
            '5' : '00d4d4',
            '6' : 'e500e5',
            '7' : 'cecece',
            '8' : 'ff5f02'
            }

    black   = colormap['0']
    red     = colormap['1']
    green   = colormap['2']
    yellow  = colormap['3']
    blue    = colormap['4']
    cyan    = colormap['5']
    magenta = colormap['6']
    white   = colormap['7']
    orange  = colormap['8']

    @classmethod
    def _colorize(cls, string: str, color: str):
        return "<font color=#" + color + ">" + string + "</font>"

class TermPalette(ColorPalette):
    colormap = ARENA_COLORS

    black   = colormap['0']
    red     = colormap['1']
    green   = colormap['2']
    yellow  = colormap['3']
    blue    = colormap['4']
    cyan    = colormap['5']
    magenta = colormap['6']
    white   = colormap['7']
    orange  = colormap['8']

    @classmethod
    def _colorize(cls, string: str, color: str):
        return color + string + COLOR_RESET



class Message:
    text_template = ""
    term_template = ""
    html_template = ""

    def __init__(self, text: str, term: str = None, html: str = None):
        self.text = text
        self.term = term if term else text
        self.html = html if html else text

# notifications

class Notification(Message):
    """Base class for notifications"""

class OverThresholdNotification(Notification):
    """Notification for the players over threshold change"""
    text_template = "[+] {server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    term_template = TermPalette.strgreen("●")+" {server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    html_template = HtmlPalette.strgreen("●")+" <b>{server}</b>: {nplayers} player{s} now @ <b>{mapname}</b>/{mode} ({players})"

    def __init__(self, snap: snapshot.ServerSnapshot):
        players = snap.info.likely_human_players()
        nplayers = snap.info.num_humans()
        server = snap.info.name().strip()
        mapname = snap.info.map()
        mode = snap.info.gametype().name
        s = '' if nplayers == 1 else 's'

        self.text = self.text_template.format(
                server = server.getstr(), nplayers = nplayers, s = s,
                mapname = mapname, mode = mode,
                players = ', '.join([player.name.getstr() for player in players]))

        self.term = self.term_template.format(
                server = server.getstr(True), nplayers = nplayers, s = s,
                mapname = mapname, mode = mode,
                players = ', '.join([player.name.getstr(True) for player in players]))

        self.html = self.html_template.format(
                server = server.gethtml(HtmlPalette.colormap), nplayers = nplayers,
                s = s, mapname = html.escape(mapname), mode = mode,
                players = ', '.join([player.name.gethtml(HtmlPalette.colormap) for player in players]))

class UnderThresholdNotification(Notification):
    """Notification for the players under threshold change"""
    text_template = "[-] {server}: {nplayers} player{s} now"
    term_template = TermPalette.strred("●")+" {server}: {nplayers} player{s} now"
    html_template = HtmlPalette.strred("●")+" <b>{server}</b>: {nplayers} player{s} now"

    def __init__(self, snap: snapshot.ServerSnapshot):
        server = snap.info.name().strip()
        nplayers = snap.info.num_humans()
        s = '' if nplayers == 1 else 's'

        self.text = self.text_template.format(
                server = server.getstr(), nplayers = nplayers, s = s)

        self.term = self.term_template.format(
                server = server.getstr(True), nplayers = nplayers, s = s)

        self.html = self.html_template.format(
                server = server.gethtml(HtmlPalette.colormap), nplayers = nplayers, s = s)

class DurationNotification(Notification):
    """Notification for the match duration"""
    text_template = "[*] {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    term_template = TermPalette.strcyan("●")+" {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    html_template = HtmlPalette.strcyan("●")+" <b>{server}</b>: {players} {tobe} still having a lot of fun @ <b>{mapname}</b>/{mode}"

    def __init__(self, snap: snapshot.ServerSnapshot):
        players = snap.info.likely_human_players()
        server = snap.info.name().strip()
        tobe = 'is' if snap.info.num_humans() == 1 else 'are'
        mapname = snap.info.map()
        mode = snap.info.gametype().name

        self.text = self.text_template.format(
                players = ', '.join([player.name.getstr() for player in players]),
                tobe = tobe, mapname = mapname, mode = mode, server = server.getstr())

        self.term = self.term_template.format(
                players = ', '.join([player.name.getstr(True) for player in players]),
                tobe = tobe, mapname = mapname, mode = mode, server = server.getstr(True))

        self.html = self.html_template.format(
                players = ', '.join([player.name.gethtml(HtmlPalette.colormap) for player in players]),
                tobe = tobe, mapname = html.escape(mapname), mode = mode,
                server = server.gethtml(HtmlPalette.colormap))

# replies

class Reply(Message):
    """Base class for replies to bot commands"""

class QueryReply(Reply):
    """Reply for the query command"""
    text_template = "{server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    term_template = text_template
    html_template = "<b>{server}</b>: {nplayers} player{s} now @ <b>{mapname}</b>/{mode} ({players})"

    def __init__(self, snaps: List[snapshot.ServerSnapshot]):
        if not snaps:
            self.text = self.term = self.html = "No match for this search"
            return

        self.text = '\n'.join([self.text_template.format(
            server = info.name().strip().getstr(),
            nplayers = info.num_humans(),
            s = '' if info.num_humans() == 1 else 's',
            mapname = info.map(),
            mode = info.gametype().name,
            players = ', '.join([player.name.getstr() for player in info.likely_human_players()])
            ) for info in [s.info for s in snaps]])

        self.term = self.text

        self.html = '<br>'.join([self.html_template.format(
            server = info.name().strip().gethtml(HtmlPalette.colormap),
            nplayers = info.num_humans(),
            s = '' if info.num_humans() == 1 else 's',
            mapname = html.escape(info.map()),
            mode = info.gametype().name,
            players = ', '.join([player.name.gethtml(HtmlPalette.colormap) for player in info.likely_human_players()])
            ) for info in [s.info for s in snaps]])

class StalkReply(QueryReply):
    """Reply for the stalk command"""

class MonitorReply(Reply):
    """Reply for the monitor command"""
    text_template = "Monitor: {is_enabled}"
    term_template = text_template
    html_template = "Monitor: <b>{is_enabled}</b>"

    def __init__(self):
        is_enabled = 'on' if Config.Bot.monitor else 'off'

        self.text = self.text_template.format(is_enabled = is_enabled)
        self.term = self.text
        self.html = self.html_template.format(is_enabled = is_enabled)

class HelpReply(Reply):
    """Reply for the help command"""
    text_template = "Usage: {botname} query[ keywords]|stalk players|monitor[ on|off]|help"
    term_template = text_template
    html_template = ("Usage: <b>{botname}</b> " +
    HtmlPalette.strcyan("query")+"[ keywords]|" +
    HtmlPalette.strcyan("stalk")+" players|"    +
    HtmlPalette.strcyan("monitor")+"[ on|off]|" +
    HtmlPalette.strcyan("help"))

    def __init__(self):
        self.text = self.text_template.format(botname = Config.Bot.name)
        self.term = self.text
        self.html = self.html_template.format(botname = Config.Bot.name)

# message sender

class MessageSender:
    def __init__(self, client: nio.AsyncClient):
        self.client = client

    async def send_room(self, message: Message, notice: bool = True):
        await self.client.room_send(
                Config.Matrix.room,
                "m.room.message",
                {
                    "msgtype"           : "m.notice" if notice else "m.text",
                    "body"              : message.text,
                    "formatted_body"    : message.html,
                    "format"            : "org.matrix.custom.html"
                    }
                )
