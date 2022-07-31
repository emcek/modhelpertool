[![pipeline status](https://gitlab.com/modding-openmw/modhelpertool/badges/main/pipeline.svg)](https://gitlab.com/modding-openmw/modhelpertool/-/commits/main)
[![coverage report](https://gitlab.com/modding-openmw/modhelpertool/badges/main/coverage.svg)](https://gitlab.com/modding-openmw/modhelpertool/-/commits/main)
[![image](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/moht/)
[![License](https://img.shields.io/badge/Licence-MIT-blue.svg)](./LICENSE.md)
[![image](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue.svg)](https://gitlab.com/modding-openmw/modhelpertool)
[![moht](https://snyk.io/advisor/python/moht/badge.svg)](https://snyk.io/advisor/python/moht)  
![mohtlogo](https://i.imgur.com/gJoB1Dv.png)  

## Mod Helper Tool
Simple yet powerful tool to help you manage your mods in several ways.

## Name
MHT or MOTH was already occupied by another projects, so **MO**d **H**elper **T**ool, `MOHT` in short was born. 
Anyway if you not pay attention to details or your english is not fluent (as mine) logo fits like a glove. 

## General
For now, application can only clean your mods, but in future more features will be added.

* Run Linux, Windows and Mac
* Built-in `tes3cmd` binary - no additional downloads
* Select location of directory with Mods
* Select location of `Morrowind/Data Files` directory

## Requirements
* Python 3.7+ (with tcl/tk support, see installation) should be fine

## Installation
1. Any Python version grater the 3.7 with tcl/tk support
2. For Windows, during Python installation please select:
  * Optional Features:
    * pip
    * tcl/tk and IDLE
    * py launcher
  * Advanced Options:
    * Associate files with Python (requires the py launcher)
    * Add Python to environment variables
    * Customize install location: C:\Python310 or C:\Python
3. Package is available on [PyPI](https://pypi.org/project/moht/), open Windows Command Prompt (cmd.exe) or any terminal and type:
```shell
pip install moht
```

## Upgrade
To upgrade Moht to the latest version:
```shell
pip install -U moht
```

## Uninstall
```shell
pip install -qy moht
```
