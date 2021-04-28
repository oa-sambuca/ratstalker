import nio

from config import Config



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
    text_template = "{}: {} player{} now"
    html_template = "<b>{}</b>: <span data-mx-color="+ColorPalette.green+">{} player{}</span> now"

    def __init__(self, servername: str, nplayers: int):
        self.text = self.text_template.format(
                servername, nplayers, '' if nplayers == 1 else 's')
        self.html = self.html_template.format(
                servername, nplayers, '' if nplayers == 1 else 's')

class UnderThresholdMessage(Message):
    """Message for the players under threshold change"""
    text_template = "{}: {} player{} now"
    html_template = "<b>{}</b>: <span data-mx-color="+ColorPalette.red+">{} player{}</span> now"

    def __init__(self, servername: str, nplayers: int):
        self.text = self.text_template.format(
                servername, nplayers, '' if nplayers == 1 else 's')
        self.html = self.html_template.format(
                servername, nplayers, '' if nplayers == 1 else 's')

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
