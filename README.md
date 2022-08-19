[![pipeline status](https://gitlab.com/modding-openmw/modhelpertool/badges/main/pipeline.svg)](https://gitlab.com/modding-openmw/modhelpertool/-/commits/main)
[![coverage report](https://gitlab.com/modding-openmw/modhelpertool/badges/main/coverage.svg)](https://gitlab.com/modding-openmw/modhelpertool/-/commits/main)
[![image](https://img.shields.io/badge/pypi-v0.5.0-blue.svg)](https://pypi.org/project/moht/)
[![License](https://img.shields.io/badge/Licence-MIT-blue.svg)](./LICENSE.md)
[![image](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue.svg)](https://gitlab.com/modding-openmw/modhelpertool)
[![moht](https://snyk.io/advisor/python/moht/badge.svg)](https://snyk.io/advisor/python/moht)  
![mohtlogo](https://i.imgur.com/gJoB1Dv.png)  

## Mod Helper Tool
Simple yet powerful tool to help you manage your mods in several ways.

## Name
MHT and MOTH was already occupied by another projects, so **MO**d **H**elper **T**ool, `MOHT` in short was born. 
Anyway if you not pay attention to details or your english is not fluent (as mine) logo fits like a glove. 

## General
For now, application can only clean your mods, but in future more features will be added.

* Run Linux, Windows and Mac
* Two built-in version `tes3cmd` binary (0.37 and 0.40) - no additional downloads needed
* Allow to select custom `tes3cmd` executable file
* Select location of directory with Mods
* Select location of `Morrowind/Data Files` directory
* Simple report after cleaning

## Requirements
* Python 3.7+ (with tcl/tk support, see [GUI Tk](#gui-tk)) should be fine
* Linux users require install additional [Perl module](#perl-module)
* Optional:
  * `PyQt5` for Qt GUI version, see [GUI Style](#gui-pyqt5)
  * `pip` >= 22.2.1 - use to check new version of Moht

## Installation
1. Any Python version grater the 3.7 with tcl/tk support
2. Package is available on [PyPI](https://pypi.org/project/moht/), open Windows Command Prompt (cmd.exe) or any terminal and type:
   ```shell
   pip install moht
   ```
3. You can drag and drop `moht_tk.exe` to desktop and make shortcut (with custom icon, you can find icon in installation 
directory i.e. C:\Python310\lib\site-packages\moht\img\moht.ico).

## GUI Tk
By default, application use `tkinter` (`tk` for short) Python's built-in library for GUI. Install with:
```shell
pip install moht
```
You can [find](#start) executable called `moht_tk.exe` or script `moht_tk`. However, sometimes `tk` isn't available by default:
  * Windows 10/11, during Python installation please select:  
    * Optional Features:
      * pip
      * tcl/tk and IDLE
      * py launcher
    * Advanced Options:
      * Associate files with Python (requires the py launcher)
      * Add Python to environment variables
      * Customize install location: C:\Python310 or C:\Python
  * Debian
    ```shell
    sudo apt install python3-tk
    ``` 
  * OpenSUSE
    ```shell
    sudo zypper install python3-tk
    ```

## GUI PyQt5
You can choose to install `PyQt5` version of GUI as well. Please note this will require depending on 
platform (~50 MB or ~200 MB) of additional space.
```shell
pip install moht[qt5]
```
You can [find](#start) executable called `moht_qt.exe` or script `moht_qt`.

## Perl module
`perl-Config-IniFiles` is required for `tes3cmd` which Moht use to clean-up mods. Install with
  * Debian
    ```shell
    sudo apt install python3-tk
    ``` 
  * OpenSUSE
    ```shell
    sudo zypper install python3-tk
    ```

## Start
* Windows
  You can find executable(s) with little trick, open Windows Command Prompt (cmd.exe) and type:
  ```shell
  pip uninstall moht
  ```
  Note: answer **No** to question. It will show you, where Moht was installed. Usually pip should install moht into your Python directory: i.e.:
  ``` 
  C:\Python310\lib\site-packages\moht-0.5.0.dist-info\*
  C:\Python310\lib\site-packages\moht\*
  C:\Python310\scripts\moht_qt.exe
  C:\Python310\scripts\moht_tk.exe
  ```
* Linux - simply run `moht_tk` or `moht_qt` from terminal

## Upgrade
To upgrade Moht to the latest version:
```shell
pip install -U moht
```

## Uninstall
```shell
pip install -qy moht
```

## Sponsored by Jetbrains Open Source Support Program
[![logo](https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm.svg)](https://jb.gg/OpenSourceSupport)
[![logo](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)](https://jb.gg/OpenSourceSupport)
