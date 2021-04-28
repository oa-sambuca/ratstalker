from __future__ import annotations
from typing import Dict, List

from config import Config
from deps.oaquery import oaquery



class GlobalSnapshot:
    """Global snapshot containing the ServerSnapshots of all servers"""
    def __init__(self):
        self.servers_snaps: Dict[str, ServerSnapshot] = {}

    def capture(self) -> GlobalSnapshot:
        """Capture a global snapshot"""
        infos: List[oaquery.ServerInfo] = oaquery.query_servers(Config.OAQuery.hosts.values())
        for info in infos:
            servername = info.name().getstr()
            gametype = info.gametype().name
            # get rid of city asap :)
            if 'city' in servername.lower():
                snapshot = CityServerSnapshot(info)
            elif gametype in ("TOURNAMENT", "MULTITOURNAMENT"):
                snapshot = DuelServerSnapshot(info)
            else:
                snapshot = DefaultServerSnapshot(info)

            self.servers_snaps[servername] = snapshot
        return self



# Server snapshot

class ServerSnapshot:
    """Base class for server snapshots"""
    def __init__(self, info: oaquery.ServerInfo):
        if type(self) is ServerSnapshot:
            raise NotImplementedError
        self.info = info

    def compare(self, prev_snap: ServerSnapshot) -> SnapshotDiff:
        """Compare with a previous snapshot

        Every subclass matches against appropriate relevance rules
        """

class DummyServerSnapshot(ServerSnapshot):
    """Dummy snapshot to be used as first server snapshot"""
    # NOTE: This is useful as fallback snapshot when there is no previous
    # snapshot to compare against for a paticular server (like when the bot
    # starts or when a server has just came up), so we use this empty
    # DummyServerSnapshot with a DummyServerInfo providing some fallback
    # values.
    def __init__(self):
        self.info = DummyServerInfo()

class DummyServerInfo(oaquery.ServerInfo):
    """Dummy infos to be used in a DummyServerSnapshot"""
    # This class must override all of the attributes/methods that the
    # SnapshotDiff class operates with. Override the minimum of ServerInfo
    # class as much as it's necessary to fake a reset state from the
    # SnapshotDiff point of view (i.e. just override the attributes and methods
    # used in the SnapshotDiff initializer)
    def __init__(self):
        pass

    def num_humans(self):
        return 0

class DuelServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.duel
        diff = SnapshotDiff(prev_snap, self)
        diff.attach_rule(UnderThresholdRule(threshold)).attach_rule(OverThresholdRule(threshold))
        return diff.evaluate_rules()

class CityServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.City
        diff = SnapshotDiff(prev_snap, self)
        diff.attach_rule(UnderThresholdRule(threshold)).attach_rule(OverThresholdRule(threshold))
        return diff.evaluate_rules()

class DefaultServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.default
        diff = SnapshotDiff(prev_snap, self)
        diff.attach_rule(UnderThresholdRule(threshold)).attach_rule(OverThresholdRule(threshold))
        return diff.evaluate_rules()



# Relevance rules

class RelevanceRule:
    """Base class for a relevance rule

    Relevance rules represent different rules to check for diff relevance
    """
    def __init__(self, *args):
        if type(self) is RelevanceRule:
            raise NotImplementedError

    def evaluate(self, diff: SnapshotDiff) -> bool:
        """Evaluate the rule on the diff"""

class OverThresholdRule(RelevanceRule):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, diff: SnapshotDiff) -> bool:
        return (diff.prev_players < self.threshold and diff.curr_players >= self.threshold)

class UnderThresholdRule(RelevanceRule):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, diff: SnapshotDiff) -> bool:
        return (diff.prev_players >= self.threshold and diff.curr_players < self.threshold)



# Snapshot diff

class SnapshotDiff:
    """Class representing a diff between two server snapshots"""
    def __init__(self, prev: ServerSnapshot, curr: ServerSnapshot):
        # extract all relevant infos involved in diffing
        # NOTE: remember to stay synced with DummyServerInfo by overriding the
        # attributes and methods accessed by prev in there
        self.prev_players = prev.info.num_humans()

        self.curr_players = curr.info.num_humans()
        self.relevance_rules: List[RelevanceRule] = []

    def attach_rule(self, rule: RelevanceRule) -> SnapshotDiff:
        """Add a relevance rule to be later evaluated for this diff"""
        self.relevance_rules.append(rule)
        return self

    def evaluate_rules(self) -> List[RelevanceRule]:
        """Evaluate all of the relevance rules set for this diff"""
        return [rule for rule in self.relevance_rules if rule.evaluate(self)]
