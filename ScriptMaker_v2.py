from datetime import datetime

global outputScript
outputScript = ""

def createScript(user_input, sampleStart, temperature):
	#creates temperatureScript
	if temperature == "yes":
		temperatureScript = "temperature_module.set_temperature(4)"
	else:
		temperatureScript = ""

	#sets sample starting location
	if sampleStart == "96 well plate":
		sample = "biorad_96_wellplate_200ul_pcr"
	elif sampleStart == "1.5mL Tubes":
		sample = "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"
	else:
		sample = ""

	#calculated total water amount needed and sets water starting location
	waterTotal = calculateTotalWater(user_input)
	if waterTotal > 15000:
		waterTube = ""
	elif waterTotal > 1400:
		waterTube = "opentrons_15_tuberack_nest_15ml_conical"
	elif sample == "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap":
		waterTube = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
	else:
		waterTube = "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"

	#generates dilution plate script+
	totalNumberOfDilutions = sum(map(int, user_input[2]))
	if totalNumberOfDilutions > 0:
		dilutionPlateScript = dilutionScript(totalNumberOfDilutions)
	else:
		dilutionPlateScript = ""
	
	#generates script for distribution water
	waterDistributionScript, heightFunction = waterDistributionFunction(waterTube, dilutionPlateScript)

	#generates scripts for distributing samples
	if len(user_input[1]) > 0:
		if len(user_input[2]) > 0:
			if sampleStart == "1.5mL Tubes":
				sampleDistributionScript = sampleDistributionOption1()
			elif sampleStart == "96 well plate":
				sampleDistributionScript = sampleDistributionOption2()
			else:
				sampleDistributionScript = ""
		else:
			if sampleStart == "1.5mL Tubes":
				sampleDistributionScript = sampleDistributionOption3()
			elif sampleStart == "96 well plate":
				sampleDistributionScript = sampleDistributionOption4()
			else:
				sampleDistributionScript = ""
	else:
		sampleDistributionScript = ""

	outputScript = createScriptHead(user_input) + f'''\nimport math

metadata = {{'protocolName': 'output.py', 'author': 'David Cowan <dcowan2@emory.edu>', 'apiLevel': '2.6'}}
tiprack_slots = ['5', '6', '9']

def run(protocol):
	#set pip_size and tips pos 5, 6, & 8
	tip_name = 'opentrons_96_tiprack_20ul'
	tipracks = [protocol.load_labware(tip_name, slot) for slot in tiprack_slots]
	pipette = protocol.load_instrument("p20_single_gen2", "left", tip_racks=tipracks)

	waterAmount = {waterTotal}
	protocol.comment("Water need = {{:.2f}}mL".format(waterAmount))

	#temp module with plate at pos 10
	temperature_module = protocol.load_module('temperature module gen2', 10)
	finish_plate = temperature_module.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul', 'finish plate')
	{temperatureScript}

	#water rack in 1.5mL tubes at pos 11
	waterrack = protocol.load_labware('{waterTube}', '11')
	water = waterrack.wells()[0]
	{waterDistributionScript}
	{sampleDistributionScript}
	protocol.home()
	protocol.pause(msg="Protocol Complete, remove plate from temperature module")
	temperature_module.deactivate()\n
	{heightFunction}\n'''

	with open('/Users/gencore/Desktop/output.py', 'w') as outputFile:
		outputFile.write(outputScript)

def createScriptHead(user_input):
	#starts scriptHead and initialized stuff
	scriptHead = ""
	currentTime = datetime.now()
	timeString = currentTime.strftime("%m/%d/%Y %I:%M:%S %p")
	scriptHead = "#File created: " + timeString

	if len(user_input) == 0:
			scriptHead += "\n#no user input added"
	elif len(user_input[0]) > 0:
			scriptHead += "\nwater_volumes = ["
			for i in user_input[0]:
					scriptHead += str(i) + ","
			scriptHead = scriptHead[:-1] + "]\n"
	if len(user_input[1]) > 0:
			scriptHead += "sample_volumes = ["
			for i in user_input[1]:
					scriptHead += str(i) + ","
			scriptHead = scriptHead[:-1] + "]\n"
	if len(user_input[2]) > 0:
			scriptHead += "numberOfDilutions= ["
			for i in user_input[2]:
				scriptHead += str(i) + ","
			scriptHead = scriptHead[:-1] + "]\n"
	return scriptHead

def calculateTotalWater(user_input):
	waterTotal = 0
	for i in range(len(user_input[0])):
			waterTotal += float(user_input[0][i])
	if len(user_input[2]) > 0:
		for i in range(len(user_input[2])):
			waterTotal += float(user_input[2][i])*9
	waterTotal = round(waterTotal *1.1/1000 + .05, 1)
	return waterTotal

def waterDistributionFunction(waterTube, dilutionScript):
	if waterTube == "opentrons_15_tuberack_nest_15ml_conical":
		waterDistributionScript = f"""
	amountRemaining = waterAmount*1000
	height = calculateNewHeight(amountRemaining)
	#distributes water to plate
	pipette.pick_up_tip()
	for num, data in enumerate(water_volumes):
		while data > 0:
			if data > 20:
				pipette.transfer(20, water.bottom(z=height), finish_plate.wells()[num], new_tip="never")
				data = data - 20
				amountRemaining -= 20
			else:
				pipette.transfer(data, water.bottom(z=height), finish_plate.wells()[num], new_tip="never")
				amountRemaining -= data
				data = 0
		height = calculateNewHeight(amountRemaining)
{dilutionScript}\tpipette.drop_tip()\n"""
		heightFunction = """\ndef calculateNewHeight(amountLeft):
	if amountLeft < 1500:
		return 0.1
	else:
		height = round(22 + (amountLeft - 1500) / 150 - 10)
		return height"""
	
	elif waterTube == "opentrons_24_aluminumblock_nest_1.5ml_snapcap" or waterTube == "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap":
		waterDistributionScript = f"""
	pipette.pick_up_tip()
	for num, data in enumerate(water_volumes):
		while data > 0:
			if data > 20:
				pipette.transfer(20, water.bottom(), finish_plate.wells()[num], new_tip="never")
				data = data - 20
			else:
				pipette.transfer(data, water.bottom(), finish_plate.wells()[num], new_tip="never")
				data = 0
{dilutionScript}\tpipette.drop_tip()\n"""
		heightFunction = ""
	else:
		waterDistributionScript = ""
		heightFunction = ""
	return waterDistributionScript, heightFunction	
	
#has dilutions and 1.5mL Tubes	
def sampleDistributionOption1():
	sampleDistribution = """
	#distributes sample from 1.5mL tubes into 96 well plate
	startRack = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '4', 'start position')
	dilutionCount, currentTube = 0,0
	for num, volume in enumerate(sample_volumes):
		if volume == 0:
			currentTube += 1
			if currentTube > 23:
				currentTube = 0
				protocol.pause(msg="Change tubes in position 4")
			continue
		pipette.pick_up_tip()
		if numberOfDilutions[num] > 0:
			for i in range(numberOfDilutions[num]):
				if i == 0:
					pipette.transfer(1, startRack.wells()[num], dilution_plate.wells()[dilutionCount], new_tip='never', mix_after=(5,5))
				else:
					pipette.transfer(1, dilution_plate.wells()[dilutionCount-1], dilution_plate.wells()[dilutionCount], new_tip='never', mix_after=(5,5))
				dilutionCount += 1
			pipette.transfer(volume, dilution_plate.wells()[dilutionCount-1], finish_plate.wells()[num], new_tip='never')
		else:
			pipette.transfer(volume, startRack.wells()[num], finish_plate.wells()[num], new_tip='never')
		pipette.drop_tip()
		currentTube += 1
		if currentTube > 23:
			currentTube = 0
			protocol.pause(msg="Changes tubes in position 4")
	#x"""
	return sampleDistribution

#has dilutions and 96 well plate
def sampleDistributionOption2():
	sampleDistribution = """
	#transfers sample into dilution plate (as needed) and then into finish plate
	start_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '4', 'start plate')
	
	dilutionCount = 0
	for num, volume in enumerate(sample_volumes):
		if volume == 0:
			continue
		pipette.pick_up_tip()
		if numberOfDilutions[num] > 0:
			for i in range(numberOfDilutions[num]):
				if i == 0:
					pipette.transfer(1, start_plate.wells()[num], dilution_plate.wells()[dilutionCount], new_tip='never', mix_after = (5,5))
				else:
					pipette.transfer(1, dilution_plate.wells()[dilutionCount-1], dilution_plate.wells()[dilutionCount], new_tip='never', mix_after = (5,5))
				dilutionCount += 1
			pipette.transfer(volume, dilution_plate.wells()[dilutionCount-1], finish_plate.wells()[num], new_tip='never')
		else:
			pipette.transfer(volume, start_plate.wells()[num], finish_plate.wells()[num], new_tip='never')
		pipette.drop_tip()
		#xx"""
	return sampleDistribution

#no dilutions and 1.5mL tubes
def sampleDistributionOption3():
	sampleDistribution = """	
	#distributes sample from 1.5mL tubes into 96 well plate
	startRack = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '4', 'start position')
	currentTube = 0
	for num, volume in enumerate(sample_volumes):
		if volume != 0:
			pipette.transfer(volume, startRack.wells()[currentTube], finish_plate.wells()[num])
		currentTube += 1
		if currentTube > 23:
			currentTube = 0
			protocol.pause(msg="Changes tubes in position 4")
	#xxx"""
	return sampleDistribution

#no dilution and 96 well plate
def sampleDistributionOption4():
	sampleDistribution =  """\t#adds start plate as 96 eppendorf and distributes to finish plate
	start_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '4', 'start plate')
	for num, volume in enumerate(sample_volumes):
		if volume == 0:
			continue
		pipette.transfer(volume, start_plate.wells()[num], finish_plate.wells()[num])
	#xxxx"""
	return sampleDistribution

def dilutionScript(total):
	#dilutions = list(map(user_input[2], int))
	if total < 97:
		dilutionScript = """\t#distrbutes water to dilution plate
	#if len(numberOfDilutions) > 0:
	dilution_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '7', 'dilution plate') 
	pipette.transfer(9, water, dilution_plate.wells()[:sum(numberOfDilutions)], new_tip = "never")\n"""
	else:
		dilutionScript = """#distrbutes water to dilution plate
	#if len(dilution_positions) > 0:
	dilution_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '7', 'dilution plate')
	dilution_plate2 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '8', 'dilution plate2')
	for i in range(97): 
 		pipette.transfer(9, water, dilution_plate.wells()[i], new_tip = "never")
	for i in range(97, sum(numberOfDilutions)):
		pipette.transfer(9, water, dilution_plate2.wells()[i - 96], new_tip = "never")\n"""
	return dilutionScript


"""test_input = [[2,3,4], [4,3,2], [0,1,2]]
testStart = "1.5mL Tubes"
#testStart = "96 well plate"
testTemp = "yes"
createScript(test_input, testStart, testTemp)
print("check output.py")"""