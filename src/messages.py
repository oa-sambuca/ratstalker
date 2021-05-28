from __future__ import annotations
from typing import List, Iterable

import nio
from deps.oaquery.oaquery import ARENA_COLORS, COLOR_RESET, ArenaString

from config import Config
from src import snapshot
from src import exceptions
from src import matrix



class ColorPalette:
    """Base class for color palettes"""
    black = red  = green = yellow = blue = cyan = magenta = white = orange = ""

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
    # universal palette suitable for both light and dark themes (thx treb)
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



class MessageArenaString:
    def __init__(self, string: ArenaString):
        self.string = string

    def get_text(self) -> str:
        return self.string.getstr()

    def get_term(self) -> str:
        return self.string.getstr(True)

    def get_html(self) -> str:
        return self.string.gethtml(HtmlPalette.colormap)



class Message:
    text_template = ""
    term_template = ""
    html_template = ""

    def __init__(self, text: str, term: str = None, html: str = None):
        self.text = text
        self.term = term if term else text
        self.html = html if html else text

    @staticmethod
    def get_comma_separated_string(strings: Iterable[str]) -> str:
        """Return an escaped comma separated string from the input list"""
        return ', '.join([s.replace(',', '\,') for s in strings])

# notifications

class Notification(Message):
    """Base class for notifications"""

class OverThresholdNotification(Notification):
    """Notification for the players over threshold change"""
    text_template = "[+] {server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    term_template = TermPalette.strgreen("●")+" {server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    html_template = HtmlPalette.strgreen("●")+" <b>{server}</b>: {nplayers} player{s} now @ <b>{mapname}</b>/{mode} ({players})"

    def __init__(self, snap: snapshot.ServerSnapshot):
        s = '' if snap.get_num_players() == 1 else 's'

        self.text = self.text_template.format(
                server = snap.get_servername_text(),
                nplayers = snap.get_num_players(),
                s = s,
                mapname = snap.get_map_text(),
                mode = snap.get_game_mode(),
                players = self.get_comma_separated_string(snap.get_players_text()))

        self.term = self.term_template.format(
                server = snap.get_servername_term(),
                nplayers = snap.get_num_players(),
                s = s,
                mapname = snap.get_map_term(),
                mode = snap.get_game_mode(),
                players = self.get_comma_separated_string(snap.get_players_term()))

        self.html = self.html_template.format(
                server = snap.get_servername_html(),
                nplayers = snap.get_num_players(),
                s = s,
                mapname = snap.get_map_html(),
                mode = snap.get_game_mode(),
                players = self.get_comma_separated_string(snap.get_players_html()))

class UnderThresholdNotification(Notification):
    """Notification for the players under threshold change"""
    text_template = "[-] {server}: {nplayers} player{s} now"
    term_template = TermPalette.strred("●")+" {server}: {nplayers} player{s} now"
    html_template = HtmlPalette.strred("●")+" <b>{server}</b>: {nplayers} player{s} now"

    def __init__(self, snap: snapshot.ServerSnapshot):
        s = '' if snap.get_num_players() == 1 else 's'

        self.text = self.text_template.format(
                server = snap.get_servername_text(),
                nplayers = snap.get_num_players(),
                s = s)

        self.term = self.term_template.format(
                server = snap.get_servername_term(),
                nplayers = snap.get_num_players(),
                s = s)

        self.html = self.html_template.format(
                server = snap.get_servername_html(),
                nplayers = snap.get_num_players(),
                s = s)

class DurationNotification(Notification):
    """Notification for the match duration"""
    text_template = "[*] {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    term_template = TermPalette.strcyan("●")+" {server}: {players} {tobe} still having a lot of fun @ {mapname}/{mode}"
    html_template = HtmlPalette.strcyan("●")+" <b>{server}</b>: {players} {tobe} still having a lot of fun @ <b>{mapname}</b>/{mode}"

    def __init__(self, snap: snapshot.ServerSnapshot):
        tobe = 'is' if snap.get_num_players() == 1 else 'are'

        self.text = self.text_template.format(
                players = self.get_comma_separated_string(snap.get_players_text()),
                tobe = tobe,
                mapname = snap.get_map_text(),
                mode = snap.get_game_mode(),
                server = snap.get_servername_text())

        self.term = self.term_template.format(
                players = self.get_comma_separated_string(snap.get_players_term()),
                tobe = tobe,
                mapname = snap.get_map_term(),
                mode = snap.get_game_mode(),
                server = snap.get_servername_term())

        self.html = self.html_template.format(
                players = self.get_comma_separated_string(snap.get_players_html()),
                tobe = tobe,
                mapname = snap.get_map_html(),
                mode = snap.get_game_mode(),
                server = snap.get_servername_html())

class PlayerNotification(Notification):
    def __init__(self, players: List[MessageArenaString], snap: snapshot.ServerSnapshot):

        self.text = self.text_template.format(
                players = self.get_comma_separated_string([player.get_text() for player in players]),
                server = snap.get_servername_text())

        self.term = self.term_template.format(
                players = self.get_comma_separated_string([player.get_term() for player in players]),
                server = snap.get_servername_term())

        self.html = self.html_template.format(
                players = self.get_comma_separated_string([player.get_html() for player in players]),
                server = snap.get_servername_html())

class PlayerEnterNotification(PlayerNotification):
    """Notification of some players entering the server"""
    text_template = "[->] {players} entered {server}"
    term_template = TermPalette.strgreen("→")+" {players} entered {server}"
    html_template = HtmlPalette.strgreen("→")+" {players} entered <b>{server}</b>"

class PlayerLeaveNotification(PlayerNotification):
    """Notification for some players leaving the server"""
    text_template = "[<-] {players} left {server}"
    term_template = TermPalette.strred("←")+" {players} left {server}"
    html_template = HtmlPalette.strred("←")+" {players} left <b>{server}</b>"

# replies

class Reply(Message):
    """Base class for replies to bot commands"""

class CommandFeedbackReply(Reply):
    """Generic feedback to commands"""
    text_template_ok = "Done"
    term_template_ok = TermPalette.strgreen(text_template_ok)
    html_template_ok = HtmlPalette.strgreen(text_template_ok)
    text_template_ko = "Some errors occurred during the execution of the command"
    term_template_ko = TermPalette.strred(text_template_ko)
    html_template_ko = HtmlPalette.strred(text_template_ko)
    def __init__(self, success = bool):
        (self.text, self.term, self.html) = (
                self.text_template_ok, self.term_template_ok, self.html_template_ok) if success else (
                self.term_template_ko, self.term_template_ko, self.html_template_ko)


class QueryReply(Reply):
    """Reply for the query command"""
    text_template = "{server}: {nplayers} player{s} now @ {mapname}/{mode} ({players})"
    term_template = text_template
    html_template = "<b>{server}</b>: {nplayers} player{s} now @ <b>{mapname}</b>/{mode} ({players})"

    def __init__(self, snaps: List[snapshot.ServerSnapshot], by_keywords: bool = True):
        if not snaps:
            self.text = self.term = self.html = (
                    "No match for this search" if by_keywords else
                    "No player currently online")
            return

        self.text = '\n'.join([self.text_template.format(
            server = snap.get_servername_text(),
            nplayers = snap.get_num_players(),
            s = '' if snap.get_num_players() == 1 else 's',
            mapname = snap.get_map_text(),
            mode = snap.get_game_mode(),
            players = self.get_comma_separated_string(snap.get_players_text())
            ) for snap in snaps])

        self.term = self.text

        self.html = '<br>'.join([self.html_template.format(
            server = snap.get_servername_html(),
            nplayers = snap.get_num_players(),
            s = '' if snap.get_num_players() == 1 else 's',
            mapname = snap.get_map_html(),
            mode = snap.get_game_mode(),
            players = self.get_comma_separated_string(snap.get_players_html())
            ) for snap in snaps])

class HuntReply(QueryReply):
    """Reply for the hunt command"""

class StalkReply(Reply):
    """Reply for the stalk command"""
    text_template = "Currently in the stalk list: {players}"
    term_template = html_template = text_template

    def __init__(self, no_echo: bool = False):
        if no_echo:
            self.text = "Done"
        elif not Config.Players.stalk_list:
            self.text = "No player in the stalk list"
        else:
            self.text = self.text_template.format(
                players = self.get_comma_separated_string(Config.Players.stalk_list))
        self.term = self.html = self.text

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

class RoomsReply(Reply):
    """Reply for room commands returning a list of rooms"""
    text_template = "{room}: {members}"
    term_template = text_template
    html_template = "<b>{room}</b>: {members}"

    def __init__(self, rooms: List[matrix.Room], rooms_only: bool = False):
        if rooms_only and rooms:
            self.text = self.term = self.html = ' '.join([room.name for room in rooms])
        elif rooms:
            self.text = self.term = '\n'.join([self.text_template.format(
                room = room.name, 
                members = ', '.join(["{} ({})".format(m.user_id, m.display_name) for m in room.members]))
                for room in rooms])
            self.html = '<br>'.join([self.html_template.format(
                room = room.name, 
                members = ', '.join(["{} ({})".format(m.user_id, m.display_name) for m in room.members]))
                for room in rooms])
        else:
            self.text = self.term = self.html = "No result"

class HelpReply(Reply):
    """Reply for the help command"""
    text_template = (
            "Usage: "                                                   +
            "query[ keyword ...] | "                                    +
            "hunt player[, ...] | "                                     +
            #"stalk list|clear|save|restore|[add|del player[, ...]] | "    +
            #"monitor[ on|off] | "                                         +
            "help")
    term_template = text_template
    html_template = (
            "Usage: "                                                                           +
            HtmlPalette.strcyan("query")+"[ keyword ...] | "                                    +
            HtmlPalette.strcyan("hunt")+" player[, ...] | "                                     +
            #HtmlPalette.strcyan("stalk")+" list|clear|save|restore|[add|del player[, ...]] | "    +
            #HtmlPalette.strcyan("monitor")+"[ on|off] | "                                         +
            HtmlPalette.strcyan("help"))

    def __init__(self):
        self.text = self.text_template.format(botname = Config.Bot.name)
        self.term = self.text
        self.html = self.html_template.format(botname = Config.Bot.name)

class HelpAdminReply(HelpReply):
    """Reply for the help command when issued by admins"""
    text_template = (
            HelpReply.text_template+" | "   +
            "notify 'message' | "           +
            "rooms create userid[ ...] | leave [userid | roomid][ ...] | list[ userid] | anomalies")
    term_template = text_template
    html_template = (
            HelpReply.html_template+" | "                       +
            HtmlPalette.strmagenta("notify")+" 'message' | "    +
            HtmlPalette.strmagenta("rooms")+" create userid[ ...] | leave [userid | roomid][ ...] | list[ userid] | anomalies")

# generic messages

class NotifyMessage(Notification):
    """Message for the notify command"""
    text_template = "[i] {message}"
    term_template = text_template
    html_template = HtmlPalette.strblue("<b>ℹ</b>")+" {message}"

    def __init__(self, message: str):
        self.text = self.text_template.format(message = message)
        self.term = self.text
        self.html = self.html_template.format(message = message)

# message sender

class MessageSender:
    client: nio.AsyncClient = None

    @classmethod
    async def send_rooms(cls, message: Message, rooms: List[str], notice: bool = True) -> bool:
        """Send a message to (some) joined rooms

        message : the message to send
        notice  : whether the message must be sent as notice or regular text
        rooms   : list of rooms to send the message to

        returns a bool representing success/failure in sending all the messages

        raises exceptions.MessageError if the client attribute was not initialized
        """
        res = []
        try:
            for room in rooms:
                res.append(await cls.client.room_send(
                        room,
                        "m.room.message",
                        {
                            "msgtype"           : "m.notice" if notice else "m.text",
                            "body"              : message.text,
                            "formatted_body"    : message.html,
                            "format"            : "org.matrix.custom.html"
                            }
                        ))
        except AttributeError:
            raise exceptions.MessageError("Unable to send message: client attribute is not initialized")
        
        return all([type(r) is nio.RoomSendResponse for r in res])
