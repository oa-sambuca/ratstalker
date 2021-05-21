"""Bot configuration"""
# Do not edit this template. Copy it to config.py and modify that one
# instead... that's what the bot is looking for.

class Config:
    class Matrix:
        """Configurations for Matrix"""
        # homeserver
        server  : str   = ""
        # username
        user    : str   = ""
        # password
        passwd  : str   = ""
        # list of rooms to join
        rooms   : list  = [
                ]

    class Bot:
        """Configurations for the bot"""
        # public name for the bot
        name            : str   = "RatStalker"
        # monitor the hosts and periodically notify the room
        monitor         : bool  = True
        # minutes between host queries in monitor mode
        monitor_time    : int   = 1
        # time between two syncs with the homeserver (miliseconds or None)
        # decrease for higher responsiveness, increase for lower resources usage
        sync_time       : int   = 500
        # path to the bot store
        store_dir       : str   = "nio_store/"
        # name of the store inside the store_dir
        store_name      : str   = "{}.db".format(name)
        # user allowed to send privileged commands
        admin           : str   = ""

    class Thresholds:
        """Number of players on a server that are considered meaningful"""
        # City
        City            : int   = 8
        # duel
        duel            : int   = 1
        # FFA
        FFA             : int   = 6
        # default
        default         : int   = 4
        # minutes after which a duration notification can be sent
        duration_time   : int   = 30

    class Players:
        """Configurations related to players"""
        # players to stalk for entering/leaving servers
        # loaded at run-time from persistent storage
        stalk_list      : set   = set()
        # file used to save/load the stalk list, saved in the Bot.store_dir
        stalk_list_file : str   = "stalk_list"

    class OAQuery:
        """Configurations for oaquery library"""
        # hosts monitored by this bot
        # [("address", port),...]
        hosts       : list  = [
                ("96.126.107.177",  27969),     # ciggarat - no ratassness
                ("96.126.107.177",  27200),     # /N/ALLMODES
                ("96.126.107.177",  27978),     # /N/Deathmatch
                ("96.126.107.177",  27965),     # /N/Duel
                ("96.126.107.177",  27967),     # /N/silly
                ("96.126.107.177",  27981),     # /N/Treasures
                ("96.126.107.177",  27973),     # /N/try hard
                ("96.126.107.177",  27201),     # /N/CA|CA
                ("151.236.222.109", 27966),     # /N/City UK
                ("151.236.222.109", 27961),     # /N/ALLMODES UK|FFA
                ("151.236.222.109", 27963),     # /N/Duel UK
                ("151.236.222.109", 27960),     # /N/Deathmatch UK
                ("151.236.222.109", 27962),     # /N/try hard UK|CTF
                ("151.236.222.109", 27965),     # /N/INSTA CTF UK
                ("151.236.222.109", 27964),     # /N/CTF UK
                ("151.236.222.109", 27968)      # /N/CA UK|CA
                ]
        # show server if empty
        showempty   : bool  = False
        # show colors
        showcolors  : bool  = True
        # show bots
        showbots    : bool  = True
        # sort results
        showsorted  : bool  = True
        # timeout for server queries
        timeout     : float = 1.0
        # retries for server queries
        retries     : int   = 3
