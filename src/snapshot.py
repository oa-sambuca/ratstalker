from __future__ import annotations
from typing import Dict, List

from config import Config
from deps.oaquery import oaquery



class SnapshotConfig:
    class Thresholds:
        city    = 7
        duel    = 1
        default = 3

class GlobalSnapshot:
    def __init__(self):
        self.servers_snaps: Dict[str, ServerSnapshot] = {}

    def capture(self) -> GlobalSnapshot:
        """Capture a global snapshot, i.e. the snapshot of all the servers"""
        infos: List[oaquery.ServerInfo] = oaquery.query_servers(Config.OAQuery.hosts.values())
        for info in infos:
            servername = info.name().getstr()
            gametype = info.gametype().name
            # get rid of city asap :)
            if 'city' in servername.lower():
                threshold = SnapshotConfig.Thresholds.city
            elif gametype in ("TOURNAMENT", "MULTITOURNAMENT"):
                threshold = SnapshotConfig.Thresholds.duel
            else:
                threshold = SnapshotConfig.Thresholds.default

            snapshot = ServerSnapshot(info, threshold)
            self.servers_snaps[servername] = snapshot
        return self

    def dummyfy(self) -> GlobalSnapshot:
        """Get a dummy snapshot to be used as the first snapshot"""
        # Mhhh, this feels like a dirty workaround... hopefully we find a
        # better implementation
        #
        # This is needed because we may already be over threshold at start, and
        # we would like to know that (also considering that there will be no
        # notification until the threshold is crossed again). Just diffing
        # between the first two regular snapshots would hilight no change, so
        # we use DummyServerInfo to implemet a fake reset state
        #
        # This way we don't have to have to differentiate the code for the
        # first snapshots evaluation and can take advantage of SnapshotDiff as
        # usual

        # still getting a real snapshot in order to not rely too much on the
        # server names in the configs (a slightly different name and they won't
        # compare)
        for ssnap in self.servers_snaps.values():
            # replace actual snapshots with the dummy one
            ssnap.dummyfy()
        return self


class ServerSnapshot:
    def __init__(self, info: oaquery.ServerInfo, threshold: int):
        self.info = info
        self.threshold = threshold

    def compare(self, prev_snap: ServerSnapshot) -> SnapshotDiff:
        """Compare with a previous snapshot"""
        return SnapshotDiff(prev_snap, self)

    def dummyfy(self) -> ServerSnapshot:
        self.info = DummyServerInfo()
        return self

class DummyServerInfo(oaquery.ServerInfo):
    """Dummy infos to be used when dummyfying snapshots"""
    # This class must override all of the attributes/methods that the
    # SnapshotDiff class operates with. Override the minimum of ServerInfo
    # class as much as it's necessary to fake a reset state from the
    # SnapshotDiff point of view
    def __init__(self):
        pass

    def num_humans(self):
        # at start we want to compare against 0 players to check the thresholds
        return 0

class SnapshotDiff:
    """A diff between two server snapshots"""
    def __init__(self, prev: ServerSnapshot, curr: ServerSnapshot):
        # remember to stay synced with DummyServerInfo
        self.curr_players = curr.info.num_humans()
        self.prev_players = prev.info.num_humans()

    def num_players_increased(self) -> bool:
        return (self.curr_players - self.prev_players) > 0

    def num_players_decreased(self) -> bool:
        return (self.curr_players - self.prev_players) < 0

    def players_passed_threshold_up(self, threshold: int) -> bool:
        return (self.prev_players < threshold and self.curr_players >= threshold)

    def players_passed_threshold_down(self, threshold: int) -> bool:
        return (self.prev_players >= threshold and self.curr_players < threshold)

    def players_passed_threshold(self, threshold: int) -> bool:
        return self.players_passed_threshold_up() or self.players_passed_threshold_down()
    
    def players_over_threshold(self, threshold: int) -> bool:
        return self.curr_players >= threshold
    
    def players_under_threshold(self, threshold: int) -> bool:
        return self.curr_players < threshold
