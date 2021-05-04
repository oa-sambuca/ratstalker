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
            print("+ Got command from {}: {}".format(event.sender, event.body))
            try:
                cmd = event.body.split()[1:]
                action = cmd[0].lower()
                # not applying lower() in case of case-sensitive args...
                args = cmd[1:]
            except IndexError:
                action = "help"

            if action == "query":
                command = commands.QueryCommand(self.context.last_snapshot, args)
            elif action == "stalk":
                command = commands.StalkCommand(self.context.last_snapshot, args)
            elif action == "monitor":
                command = commands.MonitorCommand(self.context.monitor_wakeup_event, args)
            elif action == "help":
                command = commands.HelpCommand()
            else:
                command = commands.HelpCommand()

            try:
                message = await command.execute()
            except exceptions.CommandExecutionError as e:
                errstring = "Command execution error: {}".format(e)
                print("! {}".format(errstring))
                message = messages.Reply(errstring)
            except Exception as e:
                message = messages.Reply("Unexpected exception")
                raise
            await self.context.message_sender.send_room(message)

class RoomInviteCallback(EventCallback):
    """Callback for the InviteEvent"""
    # Automatically accept invites to rooms
    # note: only accept invites from the configured room id to prevent abuses
    async def __call__(self, room: nio.MatrixRoom, event: nio.InviteEvent):
        if room.room_id == Config.Matrix.room:
            print("+ Accepting invite for room {}".format(room.room_id))
            self.context.client.join(room.room_id)
        else:
            print("! Unexpected invite for room: {}".format(room.room_id))
