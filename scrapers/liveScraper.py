import requests
from lxml import html
import re
from numpy import mean, std

'''
Scores a live result

The URL of the live result's page
if the page url ends in something like index.htm delete that bit (anything that ends in .htm)
so it would go from this (incorrect):
http://www.mgoblue.com/livestats/m-swim/index.htm
to this (correct):
http://www.mgoblue.com/livestats/m-swim/
'''

URL = 'http://www.swmeets.com/Realtime/NCAA/2018/'
URL = "http://athletics.indiana.edu/livestats/SW/CurrentMeet/"
URL = "https://www.sidearmstats.com/ncaa/swimming/"
URL = "https://swimmeetresults.tech/NCAA-Division-I-Men-2023/"
URL = "https://swimmeetresults.tech/NCAA-Division-I-Women-2023/"

'''
#which session numbers to score (for example 2 days of finals + 3rd day prelims)
#If you want it to score all completed finals events and ignore prelims, use {'all'} ***the 'all' functionality is not implemented yet****
ex {2,4,5} would score sessions 2,4, and 5
'''
Sessions = [1,2,3,4,5,6,7,8]

#reminder to code in a parameter for scoring system. currently it knows how to score thru 16 and 24 places. any other values here break it
Score_Thru = 16

def scoreLiveResult(URL="", Sessions={}, Score_Thru=16):
	ses = requests.session()
	# get the sidebar
	try:
		r = requests.get(URL+"evtindex.htm")
	except:
		return 0

	sidebar = html.fromstring(r.content)
	events = sidebar.xpath('//a | //h3/text()[1]')
	eventNames = sidebar.xpath('//a/text()')
	eventNames = [''] + eventNames
	eventURL = []
	count = 0
	sessionBreak = []
	for event in events:
		if "Session" not in event:
			eventURL.append(URL + event.attrib['href'])
			count += 1
		else:
			sessionBreak.append(count)
	sessionBreak.append(count)
	score = {}
	
	#print(eventURL, sessionBreak[0])
	for session in Sessions:
		for event in range(sessionBreak[session - 1], sessionBreak[session]):
			#if 'Swim-off' in eventN:
			#	continue
			score = score_event(parseTimes(eventURL[event]), score, Score_Thru)
	for team in sorted(score, key=score.get):
		pass
		#print(team + ": " + str(score[team]))


def score_event(result, score, score_thru):
	if score_thru==16:
		individual_points = [0,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1]
		relay_points = [0,40,34,32,30,28,26,24,22,18,14,12,10,8,6,4,2]
	elif score_thru==24:
		individual_points = [0,32,28,27,26,25,24,23,22,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1]
		relay_points = [0,64,56,54,52,50,48,46,44,40,34,32,30,28,26,24,22,18,14,12,10,8,6,4,2]
	else:
		return
	for swim in result:
		data = swim.split('\t')
		if int(data[0]) < len(individual_points):
			teamID = data[4] + " " + data[5]
			if teamID not in score:
				score[teamID] = 0
			if re.search("Relay", data[6]):
				score[teamID] = int(score[teamID]) + relay_points[int(data[0])]
			else:
				score[teamID] = int(score[teamID]) + individual_points[int(data[0])]
	return score


#convers to a time in seconds
def toTime(time):
	if time[0]=="X" or time[0]=="x":
		time = time[1:]
	if re.match(".*:.*",time) == None:
		return float(time)
	return float(re.split(":", time)[0]) * 60 + float(re.split(":", time)[1])


def lineType(line):
	if re.match("Event.*", line):
		return "  Event"
	if re.match("\s*\d\d? \D+.*", line) or re.match("\s*-- \D+.*", line):
		# if re.search("DQ",line) == None:
		return "Swim"
	if re.match("\s\s?\d\d?\D*\d\:\d\d\.\d\d\s*", line):
		return "Relay"
	if re.match("\s+\d\).*\d\).*", line):
		return "Relay Names"
	if re.match("\s*\Z",line):
		return "Empty"
	if re.match('[\s\d\)\(\.: r\+-]+\Z', line):
		return "Splits"
	if re.match('\d+-Yard .*', line):
		return 'Event'
	if re.match('\s*\d+ .*\d+\s*\Z', line):
		return 'Swim'
	else:
		return "Unknown"


'''
real parser
'''
def parseTimes(f):
	swimDatabase = []
	eventType = ""
	ses = requests.session()
	r = requests.get(f)
	f = r.text
	# make sure it's a completed event
	if "#CCCCCC" in f:
		return []
	f = re.sub("<.*?>", " ", f)
	f = f.split('\n')
	line = f[0]
	nextLine = False
	count = 1
	while not count >= len(f) - 1:
		if not nextLine:  # makes sure the next line has not already been read
			line = f[count]
			count += 1
		else:
			nextLine = False
		if lineType(line)=='Space':
			line = f[count]
			count += 1
			continue

		# Determines the Event
		if re.match("  Event.*", line):
			event = ""
			eventArray = re.split("\s+", line.rstrip())
			gender = eventArray[3]
			for i in range(3, len(eventArray)):
				event += eventArray[i] + " "
			eventType = eventArray[-1]
			if eventType != "Diving" and eventType != "Relay":
				eventType = "Individual"
		if re.match('\s*Name.*', line) or re.match('\s*School', line) or re.match('\s*Prelim.*', line):
			if re.search('Finals', line):
				finals = True
			else:
				finals = False
			# this might cause issues should probably put in a separate thing for time trials if they are in the same
			# session as something meaningful
			if re.search('Prelim', line) or re.search('Time Trial', line):
				prelims = True
			else:
				prelims = False

		# Finds individual events
		if eventType == "Individual": # or eventType == "Diving":
			if re.match("\s*\d\d? \D+.*",line) or (re.match("\s*-- \D+.*",line) and re.search("DQ|NS|SCR|DFS",line) == None):
				split = re.split("\s\s+",line)
				while '' in split:
					split.remove('')
				# commented out because I don't know what this does and it's breaking things. seems to work without
				# it. if something goes wrong check here first
				# if re.findall(" ?\d?\d?-?-? (\D+ \S+).*",split[0])==[]:
				#	continue
				# name=re.findall(" ?\d?\d?-?-? (\D+ \S+).*",split[0])[0].rstrip()
				name = split[1]
				place = split[0].replace(" ","")
				if re.match("\d+ .*", split[2]):
					(year, team) = re.match("(\d+) (.*)", split[2]).group(1, 2)
				elif re.match("FR.*|SO.*|JR.*|SR.*",split[2]):
					(year, team)=re.match("(\w\w) (.*)", split[2]).group(1, 2)
				else:
					year=''
					team=split[2]
				time = 0
				if re.findall("x?X?\d?\d?:?\d?\d\d.\d\d", line) == []:
					continue
				else:
					if finals:
						time = toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[-1])
						prelimsTime = toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[0])
						#print prelimsTime, time
					#else:
						#continue can skip prelims results if desired
						#continue
					elif prelims:
						#print(line)
						prelimsTime = toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[-1])
						if eventType != "Diving":
							seedTime = toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[0])
							#print('seed', 'prelims')
							#print(seedTime, prelimsTime)

							drop = (prelimsTime - seedTime) / ((seedTime + prelimsTime) / 2)
							#print(drop)
							drops.append(drop)
							if team not in teamDrops:
								teamDrops[team] = []
							teamDrops[team].append(drop)

				# team=adjustTeamName(team)
				# name=fixName(name,team,gender)
				if not team:
					continue
				if prelims:
					swimDatabase.append(place+"\t" + "\t" + name + "\t" + year + "\t" + team + "\t" + gender + "\t" + event.strip() + " - Prelims\t" + str(prelimsTime) + "\n")
				else:
					swimDatabase.append(place+"\t" + "\t" + name + "\t" + year + "\t" + team + "\t" + gender + "\t" + event.strip() + "\t" + str(time) + "\n")

		# Relays, team names different
		elif eventType == "Relay":
			if re.match("\s\s?\d\d?\D*\d\:\d\d\.\d\d\s*", line) or re.match("\s*--\D*\d\:\d\d\.\d\d\s*", line) and \
							not re.search("DQ|NS|DFS", line):
				resultArray = re.split("\s+", line)
				place = resultArray[1].replace(" ", "")
				teamName = ""
				index = 2
				while not re.match("x?X?\d.*", resultArray[index]):
					teamName += resultArray[index] + " "
					index += 1
				time = re.findall("\d+:\d\d.\d\d", line)[-1]
				seedTime = toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[0])
				#print seedTime, time
				# teamName = adjustTeamName(teamName)
				# this checks if there is an A-B-C relay denominator in 'A' format and strips it (this was the case
				# on the original test result)
				#if re.match("\w*[A-Z]", teamName):
				#	teamName = teamName[:-5]
				teamName = teamName.strip()
				if not teamName:
					continue
				swimDatabase.append(place+"\t" + "\t\t\t" + teamName + "\t" + gender + "\t" + event + "\t" + str(toTime(time)) + "\n")

	return swimDatabase

drops = []
teamDrops = {}
scoreLiveResult(URL=URL, Sessions=Sessions, Score_Thru=Score_Thru)

#for team in teamDrops:
#	print(team, teamDrops[team])

normDrops = []
for team in teamDrops:
	if len(teamDrops[team]) > 1:
		mu = mean(teamDrops[team])
		#for swim in teamDrops[team]:
		normDrops.append(mu)
		#print(team, mu, len(teamDrops[team]))
	for drop in teamDrops[team]:
		print(f'{team},"Women",{drop}')

#print(mean(drops), std(drops), len(drops))
#print(mean(normDrops), std(normDrops), len(normDrops))