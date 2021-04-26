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
    def __init__(self, text: str, text_formatted: str = None):
        self.text = text
        self.text_formatted = text_formatted if text_formatted else text

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
                    "formatted_body"    : message.text_formatted,
                    "format"            : "org.matrix.custom.html"
                    }
                )
