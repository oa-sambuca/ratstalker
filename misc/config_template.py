"""Bot configuration"""
# Do not edit this template. Copy it to config.py and modify that one
# instead...  that's what the bot is looking for.

class Config:
    class Matrix:
        """Configurations for Matrix"""
        # homeserver
        server  : str   = ""
        # username
        user    : str   = ""
        # password
        passwd  : str   = ""
        # room to join
        room    : str   = ""

    class Bot:
        """Configurations for the bot"""
        # public name for the bot
        name            : str   = "RatStalker"
        # bot trigger string
        trigger         : str   = "!stalk"
        # monitor the hosts and periodically notify the room
        monitor         : bool  = True
        # seconds between host queries in monitor mode
        monitor_time    : int   = 60
        # path to the bot store
        store_dir       : str   = "nio_store/"
        # name of the store inside the store_dir
        store_name      : str   = "{}.db".format(name)

    class OAQuery:
        """Configurations for oaquery library"""
        # hosts monitored by this bot
        # {"server_name" : ("address", port),...}
        hosts       : dict  = {
                "/N/City UK"            : ("151.236.222.109", 27966),
                "/N/ALLMODES UK|FFA"    : ("151.236.222.109", 27961),
                "/N/Duel UK"            : ("151.236.222.109", 27963)
                }
        # show server if empty
        showempty   : bool  = True
        # show colors
        showcolors  : bool  = True
        # show bots
        showbots    : bool  = True
        # sort results
        showsorted  : bool  = True
        # timeout for server queries
        timeout     : int   = None
        # retries for server queries
        retries     : int   = None
