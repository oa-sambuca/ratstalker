"""Callbacks for Matrix events"""

import asyncio

import nio

from config import Config
from src import commands
from src import exceptions
from src import messages
from ratstalker import BotContext


 
class EventCallback:
    """Base class for callbacks"""
    def __init__(self, context: BotContext):
        if type(self) is EventCallback:
            raise NotImplementedError()
        self.context = context

class RoomMessageCallback(EventCallback):
    """Callback for the RoomMessageText event"""
    requests_count = {}

    async def __call__(self, room: nio.MatrixRoom, event: nio.RoomMessageText):
        if room.user_name(event.sender) != Config.Bot.name:
            if room.room_id != Config.Bot.admin_room:
                try:
                    self.requests_count[room.room_id] += 1
                except KeyError:
                    self.requests_count[room.room_id] = 1
            else:
                self.requests_count[room.room_id] = 1

            if self.requests_count[room.room_id] <= Config.Bot.requests_limit:
                cmd = event.body.split()[0].lower()
                args = event.body.lstrip()[len(cmd):].strip()

                command = commands.HelpCommand(room.room_id == Config.Bot.admin_room)

                if cmd == "query":
                    command = commands.QueryCommand(self.context.last_snapshot, args)
                elif cmd == "hunt":
                    command = commands.HuntCommand(self.context.last_snapshot, args)
                elif cmd == "stalk":
                    #command = commands.StalkCommand(args)
                    pass
                elif cmd == "monitor":
                    #command = commands.MonitorCommand(self.context.monitor_wakeup_event, args)
                    pass
                # [admin]
                elif cmd == "notify" and room.room_id == Config.Bot.admin_room:
                    command = commands.NotifyCommand(args)
                elif cmd == "rooms" and room.room_id == Config.Bot.admin_room:
                    command = commands.RoomsCommand(self.context.client, args)

                await self.context.client.room_typing(room.room_id, True)
                try:
                    message = await command.execute()
                except exceptions.CommandError as e:
                    errstring = "Command execution error: {}".format(e)
                    print("! {}".format(errstring))
                    message = messages.Reply(errstring)
                except Exception as e:
                    message = messages.Reply("Unexpected exception")
                    raise
                finally:
                    await self.context.client.room_typing(room.room_id, False)

            elif self.requests_count[room.room_id] == Config.Bot.requests_limit + 1:
                message = messages.RequestsExceededReply()
            else:
                # just discard
                return
            await messages.MessageSender.send_rooms(message, [room.room_id], False)

    @classmethod
    def reset_requests_count(cls):
        cls.requests_count.clear()

class RoomInviteCallback(EventCallback):
    """Callback for the InviteEvent"""
    # Automatically accept invites to rooms
    async def __call__(self, room: nio.MatrixRoom, event: nio.InviteEvent):
        print("+ Accepting invite for room {}".format(room.room_id))
        res = await self.context.client.join(room.room_id)
        if type(res) is nio.JoinResponse:
            Config.Matrix.rooms.append(room.room_id)
        else:
            print("- Unable to join room {} ({})".format(room.room_id, res.message))
