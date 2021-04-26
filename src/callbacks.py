"""Callbacks for Matrix events"""

import asyncio

import nio

from config import Config
from src import commands
from src import exceptions
from src import messages


 
class CallbackContext:
    """Additional context to pass to the callbacks"""
    def __init__(self,
            client: nio.AsyncClient,
            sender: messages.MessageSender,
            monitor_wakeup_event: asyncio.Event):
        self.client = client
        self.sender = sender
        self.monitor_wakeup_event = monitor_wakeup_event

class EventCallback:
    """Base class for callbacks"""
    def __init__(self, context: CallbackContext):
        if type(self) is EventCallback:
            raise NotImplementedError()
        self.context = context

class RoomMessageCallback(EventCallback):
    """Callback for the RoomMessageText event"""
    async def __call__(self, room: nio.MatrixRoom, event: nio.RoomMessageText):
        if (event.body.startswith(Config.Bot.trigger)):
            print("+ Got command from {}: {}".format(event.sender, event.body))
            try:
                cmd = event.body.split()[1:]
                action = cmd[0].lower()
                # not applying lower() in case of case-sensitive args...
                args = cmd[1:]
            except IndexError:
                action = "help"

            if action == "query":
                command = commands.QueryCommand()
            elif action == "listservers":
                command = commands.ListServersCommand()
            elif action == "monitor":
                command = commands.MonitorCommand(self.context.monitor_wakeup_event, args)
            elif action == "help":
                command = commands.HelpCommand()
            else:
                command = commands.HelpCommand()

            try:
                reply = await command.execute()
            except exceptions.CommandExecutionError as e:
                errstring = "Command execution error: {}".format(e)
                print("! {}".format(errstring))
                reply = errstring
            except Exception as e:
                reply = "Unexpected exception"
                raise
            await self.context.sender.send_room(messages.Message(reply))

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
