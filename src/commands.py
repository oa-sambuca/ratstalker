"""Commands processed by the bot"""

from typing import List, Tuple, Dict, Union
import asyncio
import re
import json
import os

import nio
import aiofiles
from deps.oaquery import oaquery

from config import Config
from src import exceptions
from src import snapshot
from src import messages
from src import matrix



class Command:
    """Base class for commands"""
    def __init__(self, args: str = ""):
        if type(self) is Command:
            raise NotImplementedError
        self.args = args

    async def execute(self) -> messages.Reply:
        """Execute command

        returns a reply message
        raises CommandExecutionError
        """

class QueryCommand(Command):
    """Query server snapshots by servername

    syntax: query[ keyword ...]
    """
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: str = ""):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.QueryReply:
        patterns = self.args.split()
        snaps = self.snapshot.filter_by_servername(patterns)
        return messages.QueryReply(snaps, bool(patterns))

class HuntCommand(Command):
    """Query server snapshots by playernames

    syntax: hunt player[, ...]
    """
    def __init__(self, snapshot: snapshot.GlobalSnapshot, args: str = ""):
        super().__init__(args)
        self.snapshot = snapshot

    async def execute(self) -> messages.HuntReply:
        players = [p.strip() for p in self.args.split(',')]
        snaps = self.snapshot.filter_by_players(players)
        return messages.HuntReply(snaps)

class StalkCommand(Command):
    """List/add/delete players from the stalk list

    syntax: stalk list | clear | save | restore | add player[, ...] | del player[, ...]
    """
    def __init__(self, args: str = ""):
        super().__init__(args)

    async def execute(self) -> messages.StalkReply:
        try:
            action = self.args.split()[0].lower()
        except IndexError:
            action = "list"

        # use re.split() to split commas only when they don't follow a backslash
        players = [p.strip().replace('\,',',') for p in re.split(r'(?<!\\),', self.args[len(action):])]
        if action == "add":
            Config.Players.stalk_list.update(players)
        elif action == "del":
            Config.Players.stalk_list.difference_update(players)
        elif action == "clear":
            Config.Players.stalk_list.clear()
        elif action == "save":
            async with aiofiles.open(os.path.join(Config.Bot.store_dir, Config.Players.stalk_list_file), "w") as f:
                await f.write(json.dumps(list(Config.Players.stalk_list)))
        elif action == "restore":
            async with aiofiles.open(os.path.join(Config.Bot.store_dir, Config.Players.stalk_list_file), "r") as f:
                Config.Players.stalk_list = set(json.loads(await f.read()))
        return messages.StalkReply(action == "save")

class MonitorCommand(Command):
    """Set or get the monitor option

    syntax: monitor[ on | off]
    """
    def __init__(self, wakeup_event: asyncio.Event, args: str = ""):
        super().__init__(args)
        self.wakeup_event = wakeup_event

    async def execute(self) -> messages.MonitorReply:
        if self.args.startswith("on"):
            Config.Bot.monitor = True
            # restart the monitor task
            self.wakeup_event.set()
        elif self.args.startswith("off"):
            Config.Bot.monitor = False
            # stop the monitor task
            self.wakeup_event.clear()
        return messages.MonitorReply()

class NotifyCommand(Command):
    """Send a message to all rooms

    [admin]
    syntax: notify "message"
    """
    def __init__(self, client: nio.AsyncClient, args: str):
        super().__init__(args)
        self.client = client

    async def execute(self) -> messages.CommandFeedbackReply:
        message = messages.NotifyMessage(self.args.strip('\'"'))
        success = False
        if self.args:
            joined_rooms = (await self.client.joined_rooms()).rooms
            success = await messages.MessageSender.send_rooms(
                    message,
                    [r for r in joined_rooms if r != Config.Bot.admin_room],
                    False)
        return messages.CommandFeedbackReply(success)

class RoomsCommand(Command):
    """Manage bot rooms

    [admin]
    syntax: rooms create userid[ ...] | leave [userid | roomid][ ...] | list[ userid] | anomalies
    """
    def __init__(self, client: nio.AsyncClient, args: str):
        super().__init__(args)
        self.client = client

    async def execute(self) -> Union[messages.RoomsReply, messages.CommandFeedbackReply]:

        async def retrieve_rooms_from_server() -> List[matrix.Room]:
            rooms_infos = []
            for room in (await self.client.joined_rooms()).rooms:
                res = await self.client.joined_members(room)
                if type(res) is nio.JoinedMembersResponse:
                    rooms_infos.append(matrix.Room(room, res.members))
            return rooms_infos

        async def kick_users_from_room(room: matrix.Room):
            for member in room.members:
                if member.user_id != Config.Matrix.user_id:
                    await self.client.room_kick(
                            room.room_id, member.user_id,
                            "Room deletion requested by bot admins")

        try:
            action = self.args.split()[0].lower()
        except IndexError:
            action = "list"
        ids = self.args.lstrip()[len(action):].split()

        rooms_infos = await retrieve_rooms_from_server()

        success = True
        if action == "create" and ids:
            # create one room per user
            for user in set(ids):
                if not any([room.contains_user(user) for room in rooms_infos]):
                    # only do it if user doesn't already have a room with the bot
                    res = await self.client.room_create(
                            visibility = nio.RoomVisibility.private,
                            name = Config.Bot.name,
                            federate = True,
                            is_direct = False,
                            invite = [user])
                    success = success and type(res) is nio.RoomCreateResponse
                rooms_infos = await retrieve_rooms_from_server()
            msg = messages.CommandFeedbackReply(success)
        elif action == "leave" and ids:
            for unwanted in set(ids):
                if unwanted.startswith('@'):
                    rooms = [room for room in rooms_infos if room.contains_user(unwanted)]
                else:
                    rooms = [room for room in rooms_infos if room.room_id == unwanted]
                for room in rooms:
                    if Config.Bot.bot_owned_rooms:
                        await kick_users_from_room(room)
                    await self.client.room_leave(room.room_id)
                    res = await self.client.room_forget(room.room_id)
                    success = success and type(res) is nio.RoomForgetResponse
                rooms_infos = await retrieve_rooms_from_server()
            msg = messages.CommandFeedbackReply(success)
        elif action == "anomalies":
            rooms = [room for room in rooms_infos if room.has_anomalies()]
            msg = messages.RoomsReply(rooms)
        elif action == "list" and len(ids) == 1:
            rooms = [room for room in rooms_infos if room.contains_user(ids[0])]
            msg = messages.RoomsReply(rooms, True)
        else:
            msg = messages.RoomsReply(rooms_infos)

        return msg

class HelpCommand(Command):
    """Show help"""
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def execute(self) -> messages.HelpReply:
        return messages.HelpReply() if not self.is_admin else messages.HelpAdminReply()
