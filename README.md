# OpentronsHelper
App that creates script for Opentrons Robot

Upload 1/7/21-v2.0
	user input: a csv (with volumes of water, sample, and number of 1:10 dilutions), select container for sample to start in (1.5mL tubes or 96 well plate), and if to turn cold 				block on to 4C
	takes user input to create script called output.py that is saved to the desktop
	this protocol requires a OT single gen 2 20uL pipette, and OT thermoblock
	OpentronsHelper.py creates the gui for users and send input to ScriptMaker with creates output
