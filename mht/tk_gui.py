import tkinter as tk
from logging import getLogger
from os import path, removedirs, chdir, walk, remove
from pprint import pprint
from shlex import split
from shutil import move, copy2
from subprocess import Popen, PIPE
from tkinter import filedialog

from mht.utils import parse_cleaning

__version__ = '0.0.1'
LOG = getLogger(__name__)


class MhtTkGui(tk.Frame):
    def __init__(self, master: tk.Tk,) -> None:
        """
        Create basic GUI for MHT application.

        :param master: Top level widget
        """
        super().__init__(master)
        self.master = master
        self.master.title('MHT')
        self.status_txt = tk.StringVar()
        self.mod_dir = tk.StringVar()
        self.morr_dir = tk.StringVar()
        self.chk_backup = tk.BooleanVar()
        self._init_widgets()
        self.status_txt.set(f'ver. {__version__}')
        # self.mod_dir.set('/home/emc/.local/share/openmw/data')
        self.mod_dir.set('/home/emc/CitiesTowns/')
        self.morr_dir.set('/home/emc/.wine/drive_c/Morrowind/Data Files/')
        self.chk_backup.set(True)

    def _init_widgets(self) -> None:
        self.master.columnconfigure(index=0, weight=10)
        self.master.columnconfigure(index=1, weight=1)
        self.master.rowconfigure(index=0, weight=10)
        self.master.rowconfigure(index=1, weight=1)
        self.master.rowconfigure(index=2, weight=1)
        self.master.rowconfigure(index=3, weight=1)
        self.master.rowconfigure(index=4, weight=1)

        dir_entry = tk.Entry(master=self.master, textvariable=self.mod_dir)
        morr_dir = tk.Entry(master=self.master, textvariable=self.morr_dir)

        browse = tk.Button(master=self.master, text='Mod Dir', width=7, command=self.select_dir)
        data_dir = tk.Button(master=self.master, text='Morr Dir', width=7, command=self.select_dir)
        clean = tk.Button(master=self.master, text='Clean', width=7, command=self.start_clean)
        close = tk.Button(master=self.master, text='Close', width=7, command=self.master.destroy)
        status = tk.Label(master=self.master, textvariable=self.status_txt)

        check_backup = tk.Checkbutton(master=self.master, text='Remove backup', variable=self.chk_backup)

        dir_entry.grid(row=0, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        morr_dir.grid(row=1, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        check_backup.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        browse.grid(row=0, column=1, padx=2, pady=2)
        data_dir.grid(row=1, column=1, padx=2, pady=2)
        clean.grid(row=3, column=1, padx=2, pady=2)
        close.grid(row=4, column=1, padx=2, pady=2)
        status.grid(row=5, column=0, columnspan=3, sticky=tk.W)

    def select_dir(self) -> None:
        """Select directory location."""
        self.status_txt.set('You can close GUI')
        directory = filedialog.askdirectory(initialdir='/home/emc/', title='Select directory')
        LOG.debug(f'Directory: {directory}')
        self.mod_dir.set(f'{directory}')

    def start_clean(self) -> None:
        """Start cleaning process."""
        # add check for tes3cmd exaple of error when per initconfig not instaled
        # Can't locate Config/IniFiles.pm in @INC (you may need to install the Config::IniFiles module) (@INC contains: /usr/lib/perl5/5.36/site_perl
        # /usr/share/perl5/site_perl /usr/lib/perl5/5.36/vendor_perl /usr/share/perl5/vendor_perl /usr/lib/perl5/5.36/core_perl /usr/share/perl5/core_perl)
        # at /home/emc/tes3cmd-0.37w line 107.
        # BEGIN failed--compilation aborted at /home/emc/tes3cmd-0.37w line 107.

        plugins = ["Abandoned_Flatv2_0.esp", "Almalexia_Voicev1.esp", "FLG - Balmora's Underworld V1.1.esp", "BitterAndBlighted.ESP",
                   "Building Up Uvirith's Legacy1.1.ESP", "Caldera.esp", "DD_Caldera_Expansion.esp", "NX9_Guards_Complete.ESP", "Radiant Gem.esp",
                   "Dwemer and Ebony Service Refusal.ESP", "Foyada Mamaea Overhaul.ESP", "Graphic Herbalism.esp", "Graphic Herbalism - No Glow.esp",
                   "Graphic Herbalism Extra.esp", "Hla Oad.esp", "CultSheog-1.02.ESP", "CultSheog-TR1807.esp", "Kilcunda's Balmora.ESP",
                   "MD_Azurian Isles.esm", "Magical Missions.ESP", "Mannequins for Sale.esp", "Xenn's Marksman Overhaul.ESP",
                   "Meteorite Ministry Palace - Higher.ESP", "MW Containers Animated.esp", "Go To Jail.esp", "Go To Jail (Mournhold + Solshteim).ESP",
                   "MRM.esm", "NX9_Guards_Complete.ESP", "OAAB - The Ashen Divide.ESP", "On the Move.esp", "Ports Of Vvardenfell V1.6.ESP",
                   "Quill of Feyfolken 2.0.esp", "Library of Vivec Overhaul - Full.esp", "SadrithMoraExpandedTR.esp", "Sanctus Shrine.esp",
                   "DA_Sobitur_Facility_Clean.ESP", "DA_Sobitur_Quest_Part_1 Clean.esp", "DA_Sobitur_Quest_Part_2 Clean.esp", "DA_Sobitur_Repurposed_1.ESP",
                   "DA_Sobitur_TRIngred_Compat.ESP", "Stav_gnisis_minaret.ESP", "OTR_Coast_Variety.esp", "TheForgottenShields - Artifacts_NG.esp",
                   "SG-toughersixth.esp", "Ttooth's Missing NPCs - No Nolus.ESP", "True_Lights_And_Darkness_1.1.esp", "UCNature.esm", "UFR_v3dot2_noRobe.esp",
                   "Vurt's BC Tree Replacer II.ESP", "Windows Glow - Bloodmoon Eng.esp", "Windows Glow - Raven Rock Eng.esp",
                   "Windows Glow - Tribunal Eng.esp", "Windows Glow.esp"]

        all_plugins = [path.join(root, f) for root, _, files in walk(self.mod_dir.get()) for f in files if f.lower().endswith('.esp') or f.lower().endswith('.esm')]
        pprint(all_plugins, width=200)
        plugins_to_clean = [f for f in all_plugins if f.split('/')[-1] in plugins]
        print('----------------------------------------------------')
        pprint(plugins_to_clean, width=200)
        print(len(all_plugins))
        print(len(plugins_to_clean))
        chdir(self.morr_dir.get())
        here = path.abspath(path.dirname(__file__))
        print('----------------------------------------------------')
        for plug in plugins_to_clean:
            print(plug)
            print('Copy:', plug, self.morr_dir.get())
            copy2(plug, self.morr_dir.get())
            mod_filename = plug.split('/')[-1]
            stdout, stderr = Popen(split(f'{path.join(here, "tes3cmd-0.37w")} clean --output-dir --overwrite "{mod_filename}"'), stdout=PIPE, stderr=PIPE).communicate()
            out, err = stdout.decode('utf-8'), stderr.decode('utf-8')
            result, reason = parse_cleaning(out, err, mod_filename)
            print(out)
            print(err)
            print(result, reason)
            print('----------------------------------------------------')
            if result:
                print(f'Move: {self.morr_dir.get()}1/{mod_filename}', plug)
                move(f'{self.morr_dir.get()}1/{mod_filename}', plug)  # detect success
            if self.chk_backup.get():
                print(f'Remove: {self.morr_dir.get()}{mod_filename}')
                remove(f'{self.morr_dir.get()}{mod_filename}')
                print('----------------------------------------------------')
        removedirs(f'{self.morr_dir.get()}1')
        self.status_txt.set('Cleaning done')
