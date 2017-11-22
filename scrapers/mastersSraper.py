import requests
import re
import time as Time
import os
from bs4 import BeautifulSoup

#convers to a time in seconds
def toTime(time):
	if '*' in time:
		time = re.split('\*', time)[0].strip()
	if time[0]=="X" or time[0]=="x":
		time=time[1:]
	if re.match(".*:.*",time) == None:
		return float(time)
	return float(re.split(":",time)[0])*60 +float(re.split(":",time)[1])


def getTopTimes(File, season=2017, sex='M', stroke='FR', distance=100, lowage=18, highage=24, num=500, course='SCY'):
	URL = 'http://www.usms.org/comp/meets/eventrank.php'
	if course == 'SCY':
		courseID = 1
	elif course == 'LCM':
		courseID = 2
	elif course == 'SCM':
		courseID = 3
	else:
		return

	if stroke=='FR':
		strokeOut = 'Freestyle'
		strokeID = 1
	elif stroke=='FL':
		strokeOut = 'Butterfly'
		strokeID = 2
	elif stroke=='BR':
		strokeOut = 'Breastroke'
		strokeID = 3
	elif stroke=='BK':
		strokeOut = 'Backstroke'
		strokeID = 4
	elif stroke=='IM':
		strokeOut='Individual Medley'
		strokeID = 5
	else:
		return
	payload = {'Season': season,
		'Sex': sex,
		'StrokeID': strokeID,
		'Distance': distance,
		'lowage': lowage,
		'highage': highage,
		'How_Many': num,
		'CourseID': courseID
	}
	print payload

	#headers = {}
	'''
	<tr valign="top" align="left">
	<td align="right">&nbsp;100&nbsp;</td>
	<td>&nbsp;Kuno, Rafi </td>
	<td align="center">20</td>
	<td align="right">&nbsp;<a href="swim.php?s=3070698">1:24.29</a>&nbsp;</td>
	<td align="center"><a title="Navy Masters">NAVY</a></td>
	<td>&nbsp;<a href="meet.php?MeetID=20160807JASNESL">Jason Nessel Memorial Invitational</a></td>
	</tr>
	'''
	r = requests.post(URL, data=payload)
	#r = r.text

	soup = BeautifulSoup(r.text)
	for tag in soup.find_all('td'):
		if hasattr(tag, 'a'):
			if tag.a:
				print tag.a.contents
		else:
			print tag.contents
	#print(soup.prettify())


def topTimesLoop():
	genders = ['F', 'M']
	distances = {}
	distances['FL'] = [100, 200]
	distances['BK'] = [100, 200]
	distances['BR'] = [100, 200]
	distances['IM'] = [200, 400]
	distances['FR'] = [50, 100, 200, 500, 1000, 1650]
	courses = ['SCY', 'SCM', 'LCM']
	years = [2017]
	ages = [(25, 29),
			(30, 34),
			(35, 39),
			(40, 44),
			(45, 49),
			(50, 54),
			(55, 59),
			(60, 64),
			(65, 69),
			(70, 74),
			(75, 79),
			(80, 84)]

	directory = 'data/masters'
	for year in years:
		for course in courses:
			for gender in genders:
				for loage, hiage in ages:
					filePath = directory + '/' + course + str(year) + gender + str(loage)

					with open(filePath, 'w+') as meetFile:
						for stroke in distances:
							for distance in distances[stroke]:
								print year, gender, distance, stroke, loage

								# now find the times and load them into the new file if they aren't in the old
								print getTopTimes(meetFile, season=year, sex=gender, stroke=stroke, distance=distance,
												  lowage=loage, highage=hiage, num=500, course=course)
								break

if __name__ == "__main__":
	topTimesLoop()
