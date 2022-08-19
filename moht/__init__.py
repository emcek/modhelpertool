VERSION = '0.5.0'
PLUGINS2CLEAN = {
    "Abandoned_Flatv2_0.esp": ['Morrowind.esm'],
    "Almalexia_Voicev1.esp": ['Morrowind.esm', 'Tribunal.esm'],
    "FLG - Balmora's Underworld V1.1.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "BitterAndBlighted.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Building Up Uvirith's Legacy1.1.ESP": ['Morrowind.esm'],
    "Caldera.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'OAAB_Data.esm'],
    "DD_Caldera_Expansion.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Radiant Gem.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],  # no mode available
    "Dwemer and Ebony Service Refusal.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "OAAB - Foyada Mamaea.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'OAAB_Data.esm'],
    "Graphic Herbalism.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Graphic Herbalism - No Glow.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Graphic Herbalism Extra.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Hla Oad.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "CultSheog.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],  # already clean
    "CultSheog-TR1807.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'Tamriel_Data.esm'],  # already clean
    "Kilcunda's Balmora.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "MD_Azurian Isles.esm": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'OAAB_Data.esm'],  # already clean
    "Magical Missions.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Mannequins for Sale.esp": ['Morrowind.esm', 'Bloodmoon.esm'],
    "Xenn's Marksman Overhaul.ESP": ['Morrowind.esm'],
    "Meteorite Ministry Palace - Higher.ESP": ['Morrowind.esm'],
    "MW Containers Animated.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],  # already clean
    "Go To Jail.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "MRM.esm": ['Morrowind.esm'],
    "NX9_Guards_Complete.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "OAAB - The Ashen Divide.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'OAAB_Data.esm'],
    "On the Move.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Ports Of Vvardenfell V1.6.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Quill of Feyfolken 2.0.esp": ['Morrowind.esm'],
    "Library of Vivec Overhaul - Full.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'OAAB_Data.esm', 'Tamriel_Data.esm'],
    "sadrith mora expanded TR.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm', 'Tamriel_Data.esm', 'TR_Mainland.esm'],
    "DA_Sobitur_Facility_Clean.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "DA_Sobitur_Quest_Part_1 Clean.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "DA_Sobitur_Repurposed_1.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Stav_gnisis_minaret.ESP": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "OTR_Coast_Variety.esp": ['Morrowind.esm'],
    "TheForgottenShields - Artifacts_NG.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "SG-toughersixth.esp": ['Morrowind.esm', 'Tribunal.esm'],
    "Ttooth's Missing NPCs - No Nolus.ESP": ['Morrowind.esm'],
    "True_Lights_And_Darkness_1.1.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "UCNature.esm": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],  # no plugin available
    "UFR_v3dot2_noRobe.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],
    "Vurt's BC Tree Replacer II.ESP": ['Morrowind.esm'],
    "Windows Glow - Bloodmoon Eng.esp": ['Morrowind.esm', 'Bloodmoon.esm'],
    "Windows Glow - Raven Rock Eng.esp": ['Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'],  # no plugin available
    "Windows Glow - Tribunal Eng.esp": ['Morrowind.esm', 'Tribunal.esm'],
    "Windows Glow.esp": ['Morrowind.esm'],
}
TES3CMD = {
    'win32': {'0_37': 'tes3cmd-0.37v.exe',
              '0_40': 'tes3cmd-0.40-pre_rel2.exe'},
    'linux': {'0_37': 'tes3cmd-0.37w',
              '0_40': 'tes3cmd-0.40-pre_rel2'},
    'darwin': {'0_37': 'tes3cmd-0.37w',
               '0_40': 'tes3cmd-0.40-pre_rel2'},
}
