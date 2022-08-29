# v0.7.0
* make `tes3cmd-v0.40` default version (it not require `perl-Config-IniFiles`)
* QtGUI:
  * nice report in separate tab
  * remove Report button from main window
  * move close and update button to common area 

# v0.6.2
* Fix missing internal field for TkGui
* Fix double content verification of tes3cmd line edit field
* Internal:
  * format long lists in logger entries

# v0.6.1
* Hotfix - fix starting script

# v0.6.0
* Make GUI responsive - separate thread for plugin cleaning
* Add progress bar for cleaning process
* Make some log entries more clear
* Be more verbose with problem during checking new version

# v0.5.0
* Fix removing not empty cache directory when cleaning failed
* List of dirty plugins has required esm files to clean successfully
* Locate, copy and remove (after cleaning) required (for cleaning) esm files
* Log critical error when starting GUI
* Show correct data in Report when plugin missing more than one esm files
* Fix no popup on TkGui when missing perl InitFiles package
* Fix to many popups on QtGui when missing perl InitFiles package
* Internal:
  * extract functionality to be share between Qt and Tk GUIs
  * add unit tests

# v0.4.1
* Hotfix - fix dependencies for Tk and Qt5 GUI versions

# v0.4.0
* Add option to select built-in or custom `tes3cmd` executable file (Tk and Qt versions)
* Check updates menu item/push button (QtGui) and button (TkGui)
* Add verbose and quiet parameters when starting form CLI

# v0.3.1
* Hotfix - add missing UI for PyQt5 GUI

# v0.3.0
* Optional PyQt5 GUI

# v0.2.1
* change button's text
* change default location for `Mods` and `Data Files`
* move images to img directory
* move `tex3cmd` executable files to resources directory

# v0.2.0
* Checking for updates during start-up
* Better cleaning report
  * use more user-friendly format, instead of Python dict
  * note missing esm files
* allow custom `tes3cmd` executable
* Improve checkbox description
* Add Windows icon
* Basic documentation in Readme file

# v0.1.0
* Simple support for Windows
* Add icon to GUI

# v0.0.1
* Only Linux supports with simple Tk GUI
* Basic cleaning of mods - select root directory with mods
* Mods are clean one by one in sequence - slow
* Draft of job report
