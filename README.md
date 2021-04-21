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
# libolm library, e.g. for debian-based systems:
apt install libolm-dev
# better using virtual environments
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy [config_template.py](config_template.py) to `config.py` and edit relevant
settings before running the bot. You mostly need to provide the Matrix infos
and specify the OpenArena servers you want to query.

## Execution

Run with:

```bash
source venv/bin/activate
./ratstalker.py
```
