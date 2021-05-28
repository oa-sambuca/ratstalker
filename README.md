# ratstalker

**RatStalker**: a Matrix bot that stalks rats

## Overview

RatStalker is a [Matrix][] bot that can be queried and/or notify rooms about
[OpenArena][] servers status, so that you always know when it's time to jump in
for some frags.

If you are wondering why the _rat_ theme is so recurrent, give a look at
[Ratmod][], our favourite OpenArena mod!

[Matrix]:       https://matrix.org/
[OpenArena]:    http://www.openarena.ws/
[Ratmod]:       https://ratmod.github.io/

## Dependencies

Main dependencies:
- [matrix-nio][]: the Matrix library. Using _matrix-nio[e2e]_ to enable e2ee
  (not implemented) and persistent client storage support
- [libolm][]: required to build _matrix-nio[e2e]_
- [oaquery][]: to query OpenArena servers. Included as submodule

[matrix-nio]:   https://matrix.org/docs/projects/sdk/matrix-nio
[libolm]:       https://gitlab.matrix.org/matrix-org/olm
[oaquery]:      https://github.com/rdntcntrl/oaquery

## Installation

Install with:

```bash
# dev libraries, e.g. for debian-based systems:
apt install python3-dev libolm-dev
# better using virtual environments
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install -r requirements.txt
```

Some more dev libraries needed to build the requirements may be missing. Just
install them accordingly in your system's package manager.

## Configuration

Copy [misc/config_template.py](misc/config_template.py) to `config.py` and edit
relevant settings before running the bot. You mostly need to provide the Matrix
infos and specify the OpenArena servers you want to query.

## Execution

Run with:

```bash
source venv/bin/activate
./ratstalker.py
```

The bot will discard all the events arrived while it was offline, to prevent
the processing of old user queries which are probably no longer relevant.

### Rooms ownership models

The bot is intended to be used in a 1-to-1 room, one per user, thus everyone
is free to interact with it without affecting others. Hence the bot can operate
following one of two room ownership models:

- using **user-owned** rooms: better when automation is required
    - users create rooms and invite the bot
    - the bot automatically joins the room
- using **bot-owned** rooms: better when greater control over allowed users is required
    - the bot creates the rooms and invites users (upon admin request)

In both modes, an admin room created by an admin is strongly suggested, if not
mandatory, and the bot will always try to join one. After the admin invites the
bot, it will join this room, from which privileged commands are available in
addition to the regular ones (e.g. managing rooms).
