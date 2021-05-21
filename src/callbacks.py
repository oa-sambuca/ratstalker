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
    async def __call__(self, room: nio.MatrixRoom, event: nio.RoomMessageText):
        if (event.body.startswith(Config.Bot.name)):
            try:
                tkns = event.body.split()
                trg, cmd = tkns[0], tkns[1:]
                action = cmd[0].lower()
                args = event.body[len(trg):].strip()[len(action):].lstrip()
            except IndexError:
                action = "help"

            command = commands.HelpCommand()

            if action == "query":
                command = commands.QueryCommand(self.context.last_snapshot, args)
            elif action == "hunt":
                command = commands.HuntCommand(self.context.last_snapshot, args)
            elif action == "stalk":
                #command = commands.StalkCommand(args)
                pass
            elif action == "monitor":
                #command = commands.MonitorCommand(self.context.monitor_wakeup_event, args)
                pass
            elif action == "notify" and event.sender == Config.Bot.admin:
                command = commands.NotifyCommand(self.context.message_sender, args)

            try:
                message = await command.execute()
            except exceptions.CommandExecutionError as e:
                errstring = "Command execution error: {}".format(e)
                print("! {}".format(errstring))
                message = messages.Reply(errstring)
            except Exception as e:
                message = messages.Reply("Unexpected exception")
                raise
            await self.context.message_sender.send_rooms(message, False, [room.room_id])

class RoomInviteCallback(EventCallback):
    """Callback for the InviteEvent"""
    # Automatically accept invites to rooms
    # note: only accept invites from the configured room ids to prevent abuses
    async def __call__(self, room: nio.MatrixRoom, event: nio.InviteEvent):
        if room.room_id in Config.Matrix.rooms:
            print("+ Accepting invite for room {}".format(room.room_id))
            self.context.client.join(room.room_id)
        else:
            print("! Unexpected invite for room: {}".format(room.room_id))
