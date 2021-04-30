from typing import List

import nio

from config import Config
from deps.oaquery.oaquery import ArenaString



class ColorPalette:
    # https://www.schemecolor.com/pastel-rainbow.php
    red     = "#ff6663"
    orange  = "#feb144"
    yellow  = "#fdfd97"
    green   = "#9ee09e"
    blue    = "#9ec1cf"
    purple  = "#cc99c9"

class Message:
    def __init__(self, text: str, html: str = None):
        self.text = text
        self.html = html if html else text

class OverThresholdMessage(Message):
    """Message for the players over threshold change"""
    text_template = "{}: {} player{} now ({})"
    html_template = "<b>{}</b>: {} player{} now ({})"

    def __init__(self, servername: ArenaString, nplayers: int, playerlist: List[ArenaString]):
        players = ', '.join([player.getstr() for player in playerlist])
        self.text = self.text_template.format(
                servername.getstr(), nplayers, '' if nplayers == 1 else 's', players)
        players = ', '.join([player.getstr(True) for player in playerlist])
        self.term = self.text_template.format(
                servername.getstr(True), nplayers, '' if nplayers == 1 else 's', players)
        players = ', '.join([player.gethtml() for player in playerlist])
        self.html = self.html_template.format(
                servername.gethtml(), nplayers, '' if nplayers == 1 else 's', players)

class UnderThresholdMessage(Message):
    """Message for the players under threshold change"""
    text_template = "{}: {} player{} now"
    html_template = "<b>{}</b>: {} player{} now"

    def __init__(self, servername: ArenaString, nplayers: int):
        self.text = self.text_template.format(
                servername.getstr(), nplayers, '' if nplayers == 1 else 's')
        self.term = self.text_template.format(
                servername.getstr(True), nplayers, '' if nplayers == 1 else 's')
        self.html = self.html_template.format(
                servername.gethtml(), nplayers, '' if nplayers == 1 else 's')

class DurationMessage(Message):
    """Message for the match duration"""
    text_template = "{} {} still having a lot of fun on {}"
    html_template = "{} {} still having a lot of fun on <b>{}</b>"

    def __init__(self, servername: ArenaString, playerlist: List[ArenaString]):
        players = ', '.join([player.getstr() for player in playerlist])
        self.text = self.text_template.format(
                players, 'is' if len(playerlist) == 1 else 'are', servername.getstr())
        players = ', '.join([player.getstr(True) for player in playerlist])
        self.term = self.text_template.format(
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
