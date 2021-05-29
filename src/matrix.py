"""Matrix abstractions over nio"""

from typing import List

import nio

from config import Config



class Room:
    def __init__(self, room_id: str, members: List[nio.RoomMember]):
        self.room_id = room_id
        self.members = members

    def contains_user(self, user: str) -> bool:
        return (user in [member.user_id for member in self.members])

    def has_anomalies(self) -> bool:
        return (
            self.room_id != Config.Bot.admin_room and
            len(self.members) != 2
            # TODO more anomalies:
            # rooms that should be bot(user)-owned but are user(bot)-owned
            # user is in multiple rooms
            )
