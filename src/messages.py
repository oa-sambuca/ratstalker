from typing import List

import nio

from src import snapshot
from config import Config
from deps.oaquery.oaquery import ArenaString, ARENA_HTML_COLORS, ARENA_COLORS, COLOR_RESET



class HtmlPalette:
    black   = '#'+ARENA_HTML_COLORS['0']
    red     = '#'+ARENA_HTML_COLORS['1']
    green   = '#'+ARENA_HTML_COLORS['2']
    yellow  = '#'+ARENA_HTML_COLORS['3']
    blue    = '#'+ARENA_HTML_COLORS['4']
    cyan    = '#'+ARENA_HTML_COLORS['5']
    magenta = '#'+ARENA_HTML_COLORS['6']
    white   = '#'+ARENA_HTML_COLORS['7']
    orange  = '#'+ARENA_HTML_COLORS['8']

    @classmethod
    def strblack(cls, string: str):
        return "<font color=" + cls.black + ">" + string + "</font>"
    @classmethod
    def strred(cls, string: str):
        return "<font color=" + cls.red + ">" + string + "</font>"
    @classmethod
    def strgreen(cls, string: str):
        return "<font color=" + cls.green + ">" + string + "</font>"
    @classmethod
    def stryellow(cls, string: str):
        return "<font color=" + cls.yellow + ">" + string + "</font>"
    @classmethod
    def strblue(cls, string: str):
        return "<font color=" + cls.blue + ">" + string + "</font>"
    @classmethod
    def strcyan(cls, string: str):
        return "<font color=" + cls.cyan + ">" + string + "</font>"
    @classmethod
    def strmagenta(cls, string: str):
        return "<font color=" + cls.magenta + ">" + string + "</font>"
    @classmethod
    def strwhite(cls, string: str):
        return "<font color=" + cls.white + ">" + string + "</font>"
    @classmethod
    def strorange(cls, string: str):
        return "<font color=" + cls.orange + ">" + string + "</font>"

class TermPalette:
    black   = ARENA_COLORS['0']
    red     = ARENA_COLORS['1']
    green   = ARENA_COLORS['2']
    yellow  = ARENA_COLORS['3']
    blue    = ARENA_COLORS['4']
    cyan    = ARENA_COLORS['5']
    magenta = ARENA_COLORS['6']
    white   = ARENA_COLORS['7']
    orange  = ARENA_COLORS['8']
    reset   = COLOR_RESET

    @classmethod
    def strblack(cls, string: str):
        return TermPalette.black + string + TermPalette.reset
    @classmethod
    def strred(cls, string: str):
        return TermPalette.red + string + TermPalette.reset
    @classmethod
    def strgreen(cls, string: str):
        return TermPalette.green + string + TermPalette.reset
    @classmethod
    def stryellow(cls, string: str):
        return TermPalette.yellow + string + TermPalette.reset
    @classmethod
    def strblue(cls, string: str):
        return TermPalette.blue + string + TermPalette.reset
    @classmethod
    def strcyan(cls, string: str):
        return TermPalette.cyan + string + TermPalette.reset
    @classmethod
    def strmagenta(cls, string: str):
        return TermPalette.magenta + string + TermPalette.reset
    @classmethod
    def strwhite(cls, string: str):
        return TermPalette.white + string + TermPalette.reset
    @classmethod
    def strorange(cls, string: str):
        return TermPalette.orange + string + TermPalette.reset



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
        name = snap.info.name().strip()
        mapname = snap.info.map()
        mode = snap.info.gametype().name
        s = '' if nplayers == 1 else 's'

        self.text = self.text_template.format(
                server = name.getstr(), nplayers = nplayers, s = s,
                mapname = mapname, mode = mode,
                players = ', '.join([player.name.getstr() for player in players]))

        self.term = self.term_template.format(
                server = name.getstr(True), nplayers = nplayers, s = s,
                mapname = mapname, mode = mode,
                players = ', '.join([player.name.getstr(True) for player in players]))

        self.html = self.html_template.format(
                server = name.gethtml(), nplayers = nplayers, s = s,
                mapname = mapname, mode = mode,
                players = ', '.join([player.name.gethtml() for player in players]))

class UnderThresholdNotification(Notification):
    """Notification for the players under threshold change"""
    text_template = "[-] {server}: {nplayers} player{s} now"
    term_template = TermPalette.strred("●")+" {server}: {nplayers} player{s} now"
    html_template = HtmlPalette.strred("●")+" <b>{server}</b>: {nplayers} player{s} now"

    def __init__(self, snap: snapshot.ServerSnapshot):
        name = snap.info.name().strip()
        nplayers = snap.info.num_humans()
        s = '' if nplayers == 1 else 's'

        self.text = self.text_template.format(
                server = name.getstr(), nplayers = nplayers, s = s)

        self.term = self.term_template.format(
                server = name.getstr(True), nplayers = nplayers, s = s)

        self.html = self.html_template.format(
                server = name.gethtml(), nplayers = nplayers, s = s)

class DurationNotification(Notification):
    """Notification for the match duration"""
    text_template = "[*] {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    term_template = TermPalette.strcyan("●")+" {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    html_template = HtmlPalette.strcyan("●")+" <b>{server}</b>: {players} {tobe} still having a lot of fun @ <b>{mapname}</b>/{mode}"

    def __init__(self, snap: snapshot.ServerSnapshot):
        players = snap.info.likely_human_players()
        name = snap.info.name().strip()
        tobe = 'is' if snap.info.num_humans() == 1 else 'are'
        mapname = snap.info.map()
        mode = snap.info.gametype().name

        self.text = self.text_template.format(
                players = ', '.join([player.name.getstr() for player in players]),
                tobe = tobe, mapname = mapname, mode = mode, server = name.getstr())

        self.term = self.term_template.format(
                players = ', '.join([player.name.getstr(True) for player in players]),
                tobe = tobe, mapname = mapname, mode = mode, server = name.getstr(True))

        self.html = self.html_template.format(
                players = ', '.join([player.name.gethtml() for player in players]),
                tobe = tobe, mapname = mapname, mode = mode, server = name.gethtml())

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
            server = info.name().strip().gethtml(),
            nplayers = info.num_humans(),
            s = '' if info.num_humans() == 1 else 's',
            mapname = info.map(),
            mode = info.gametype().name,
            players = ', '.join([player.name.gethtml() for player in info.likely_human_players()])
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
