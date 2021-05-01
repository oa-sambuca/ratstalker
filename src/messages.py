from typing import List

import nio

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

class Message:
    def __init__(self, text: str, term: str = None, html: str = None):
        self.text = text
        self.term = term if term else text
        self.html = html if html else text

class OverThresholdMessage(Message):
    """Message for the players over threshold change"""
    text_template = "[+] {}: {} player{} now ({})"
    term_template = TermPalette.green+"●"+TermPalette.reset+" {}: {} player{} now ({})"
    html_template = "<font color="+HtmlPalette.green+">●</font> <b>{}</b>: {} player{} now ({})"

    def __init__(self, servername: ArenaString, nplayers: int, playerlist: List[ArenaString]):
        players = ', '.join([player.getstr() for player in playerlist])
        self.text = self.text_template.format(
                servername.getstr(), nplayers, '' if nplayers == 1 else 's', players)

        players = ', '.join([player.getstr(True) for player in playerlist])
        self.term = self.term_template.format(
                servername.getstr(True), nplayers, '' if nplayers == 1 else 's', players)

        players = ', '.join([player.gethtml() for player in playerlist])
        self.html = self.html_template.format(
                servername.gethtml(), nplayers, '' if nplayers == 1 else 's', players)

class UnderThresholdMessage(Message):
    """Message for the players under threshold change"""
    text_template = "[-] {}: {} player{} now"
    term_template = TermPalette.red+"●"+TermPalette.reset+" {}: {} player{} now"
    html_template = "<font color="+HtmlPalette.red+">●</font> <b>{}</b>: {} player{} now"

    def __init__(self, servername: ArenaString, nplayers: int):
        self.text = self.text_template.format(
                servername.getstr(), nplayers, '' if nplayers == 1 else 's')

        self.term = self.term_template.format(
                servername.getstr(True), nplayers, '' if nplayers == 1 else 's')

        self.html = self.html_template.format(
                servername.gethtml(), nplayers, '' if nplayers == 1 else 's')

class DurationMessage(Message):
    """Message for the match duration"""
    text_template = "[*] {} {} still having a lot of fun on {}"
    term_template = TermPalette.cyan+"●"+TermPalette.reset+" {} {} still having a lot of fun on {}"
    html_template = "<font color="+HtmlPalette.cyan+">●</font> {} {} still having a lot of fun on <b>{}</b>"

    def __init__(self, servername: ArenaString, playerlist: List[ArenaString]):
        players = ', '.join([player.getstr() for player in playerlist])
        self.text = self.text_template.format(
                players, 'is' if len(playerlist) == 1 else 'are', servername.getstr())

        players = ', '.join([player.getstr(True) for player in playerlist])
        self.term = self.term_template.format(
                players, 'is' if len(playerlist) == 1 else 'are', servername.getstr(True))

        players = ', '.join([player.gethtml() for player in playerlist])
        self.html = self.html_template.format(
                players, 'is' if len(playerlist) == 1 else 'are', servername.gethtml())

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
