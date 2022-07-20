import os
import re
import tkinter as tk
from pprint import pprint
from tkinter import filedialog
from functools import partial
from logging import getLogger
from threading import Thread, Event


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
        self.tes3cmd = tk.StringVar()
        self.morr_dir = tk.StringVar()
        self.event = Event()
        self._init_widgets()
        self.status_txt.set(f'ver. {__version__}')
        # self.mod_dir.set('/home/emc/.local/share/openmw/data')
        self.mod_dir.set('/home/emc/CitiesTowns/')
        self.tes3cmd.set('/home/emc/tes3cmd-0.37w')
        self.morr_dir.set('/home/emc/.wine/drive_c/Morrowind/Data\ Files/')

    def _init_widgets(self) -> None:
        self.master.columnconfigure(index=0, weight=10)
        self.master.columnconfigure(index=1, weight=1)
        self.master.rowconfigure(index=0, weight=10)
        self.master.rowconfigure(index=1, weight=1)
        self.master.rowconfigure(index=2, weight=1)
        self.master.rowconfigure(index=3, weight=1)
        self.master.rowconfigure(index=4, weight=1)

        dir_entry = tk.Entry(master=self.master, textvariable=self.mod_dir)
        clean_bin = tk.Entry(master=self.master, textvariable=self.tes3cmd)
        morr_dir = tk.Entry(master=self.master, textvariable=self.morr_dir)

        browse = tk.Button(master=self.master, text='Mod Dir', width=7, command=self.select_dir)
        set_bin = tk.Button(master=self.master, text='tes3cmd', width=7, command=self.select_file)
        data_dir = tk.Button(master=self.master, text='Morr Dir', width=7, command=self.select_dir)
        clean = tk.Button(master=self.master, text='Clean', width=7, command=self.start_clean)
        close = tk.Button(master=self.master, text='Close', width=7, command=self.master.destroy)
        status = tk.Label(master=self.master, textvariable=self.status_txt)

        dir_entry.grid(row=0, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        clean_bin.grid(row=1, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')
        morr_dir.grid(row=2, column=0, padx=2, pady=2, sticky=f'{tk.W}{tk.E}')

        browse.grid(row=0, column=1, padx=2, pady=2)
        set_bin.grid(row=1, column=1, padx=2, pady=2)
        data_dir.grid(row=2, column=1, padx=2, pady=2)
        clean.grid(row=3, column=1, padx=2, pady=2)
        close.grid(row=4, column=1, padx=2, pady=2)
        status.grid(row=5, column=0, columnspan=3, sticky=tk.W)

    def select_dir(self) -> None:
        self.event = Event()
        self.status_txt.set('You can close GUI')
        directory = filedialog.askdirectory(initialdir='/home/emc/', title='Select directory')
        LOG.debug(f'Directory: {directory}')
        self.mod_dir.set(f'{directory}')

    def select_file(self) -> None:
        self.event = Event()
        self.status_txt.set('You can close GUI')
        tes3cmd_file = filedialog.askopenfilename(initialdir='/home/emc/.local/share/openmw/data', title='Select tes3cmd')
        LOG.debug(f'Directory: {tes3cmd_file}')
        self.tes3cmd.set(f'{tes3cmd_file}')

    def start_clean(self) -> None:
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

        l = [os.path.join(root, f) for root, _, files in os.walk(self.mod_dir.get()) for f in files if f.lower().endswith('.esp') or f.lower().endswith('.esm')]
        pprint(l, width=200)
        c = [f for f in l if f.split('/')[-1] in plugins]
        print('----------------------------------------------------')
        pprint(c, width=200)
        print(len(l))
        print(len(c))
