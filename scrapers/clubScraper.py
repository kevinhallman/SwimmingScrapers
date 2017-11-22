'''
scrapes club swimming times from USASwimming using selenium. Results written to text files
'''

import time
import re
import os
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import datetime

eventsSCY = ['1650 Free', '500 Free', '200 Free', '100 Free', '50 Free',
				'50 Fly', '100 Fly', '200 Fly',
				'50 Back', '100 Back', '200 Back',
				'50 Breast', '100 Breast', '200 Breast',
				'100 IM', '200 IM', '400 IM']

eventsSCM = ['1500 Free', '400 Free', '200 Free', '100 Free', '50 Free',
				'50 Fly', '100 Fly', '200 Fly',
				'50 Back', '100 Back', '200 Back',
				'50 Breast', '100 Breast', '200 Breast',
				'100 IM', '200 IM', '400 IM']

eventsLCM = ['1500 Free', '400 Free', '200 Free', '100 Free', '50 Free',
				'50 Fly', '100 Fly', '200 Fly',
				'50 Back', '100 Back', '200 Back',
				'50 Breast', '100 Breast', '200 Breast',
				'200 IM', '400 IM']

def init_driver():
	driver = webdriver.Chrome()
	driver.wait = WebDriverWait(driver, 5)
	return driver


# converts to a time in seconds
def toTime(time):
	if time[0]=='X' or time[0]=='x':
		time=time[1:]
	if time[len(time)-1]=='r' or time[len(time)-1]=='R':
		time=time[0:len(time)-1]
	if re.match('.*:.*',time) == None:
		return time
	return float(re.split(':',time)[0])*60 +float(re.split(':', time)[1])


def lookup(driver, gender='Men', event='50 Free', course='LCM', bestAll='Best', nTimes='4500', year='2016',
		   filePath='test', minAge='All', maxAge='All', zone='All'):
	#skip age/event combos that don't exist
	if event in ['1500 Free', '1650 Free', '400 IM'] and int(maxAge) < 11:
		return

	# translate to USA swimming values
	distance = event[0:event.find(' ')]
	stroke = event[event.find(' ') + 1:]
	strokeDict = {'Free': 1, 'Back': 2, 'Breast': 3, 'Fly': 4, 'IM': 5}
	strokeId = strokeDict[stroke]
	courseDict = {'SCY': 1, 'SCM': 2, 'LCM': 3}
	courseId = courseDict[course]
	bestAllDict = {'All': 'radAllTimesForSwimmer', 'Best': 'radBestTimeOnly'}
	bestAll = bestAllDict[bestAll]
	yearDict = {'1996': '1', '1997': '2', '1998': '3', '1999': '4', '2000': '5', '2001': '6', '2002': '7', '2003': '8',
				'2004': '9', '2005': '10', '2006': '11', '2007': '12', '2008': '13', '2009': '14',
				'2010': '15', '2011': '16', '2012': '17', '2013': '18', '2014': '19', '2015': '20', '2016': '21',
				'2017': '22'}
	yearId = yearDict[year]
	zoneDict = {'All': 0, 'Central': 1, 'Eastern': 2, 'Southern': 3, 'Western': 4}
	zoneId = zoneDict[zone]

	''' for reference, here is how USA swimming looks up the page info in their JS
		data: { divId: 'Times_EventRankSearch_Index_Div_1',
			SelectedDateType: ($(theDiv).find('#' + 'Times_EventRankSearch_Index_Div_1' + 'ddlDateRanges').val() !== "0") ? 'CompletionPeriod' : "DateRange",
			StartDate: $(theDiv).find('#' + divId + 'StartDate').val(),
			EndDate: $(theDiv).find('#' + divId + 'EndDate').val(),
			DateRangeID: $(theDiv).find('#' + divId + 'ddlDateRanges').val(),
			SelectedGender: $(theDiv).find("input[name='SelectedGender']:checked").val(),
			DSC: { DistanceID: $(theDiv).find('#' + divId + 'cboDistance').val(),
			StrokeID: $(theDiv).find('#' + divId + 'cboStroke').val(),
			CourseID: $(theDiv).find('#' + divId + 'cboCourse').val() },
			StandardID: $(theDiv).find('#' + divId + 'ddlStandards').val(),
			LSCs: lscList,
			ZoneID: $(theDiv).find('#' + divId + 'ddlZones').val(),
			AgeRangeStart: $(theDiv).find('#' + divId + 'ddlStartAge').val(),
			AgeRangeEnd: $(theDiv).find('#' + divId + 'ddlEndAge').val(),
			SelectedTimesToInclude: $(theDiv).find('#' + divId + 'ddlIncludedTimes').val(),
			SelectedMembersToInclude: $(theDiv).find('#' + divId + 'ddlIncludedMembers').val(),
			MaxResults: $(theDiv).find('#MaxResults').val(),
			OrderBy: orderBy,var orderBy = $(theDiv).find('#' + divId + 'SortBy1').val();
                if ($(theDiv).find('#' + divId + 'SortBy2').val() != '')
                    orderBy = orderBy + ', ' + $(theDiv).find('#' + divId + 'SortBy2').val();
                if ($(theDiv).find('#' + divId + 'SortBy3').val() != '')
                    orderBy = orderBy + ', ' + $(theDiv).find('#' + divId + 'SortBy3').val();
			clubId: $(theDiv).find("#hidClubId").val(),
			TimeType: $(theDiv).find("input[name='TimeType']:checked").val() }
	'''

	# modify elements on the pave to match selections
	divId = 'Times_EventRankSearch_Index_Div_1'
	element = driver.find_element_by_id(divId + 'ddlDateRanges')
	driver.execute_script('arguments[0].value =' + yearId, element)

	element = driver.find_element_by_id(divId + 'cboDistance')
	driver.execute_script('arguments[0].value =' + str(distance), element)

	element = driver.find_element_by_id(divId + 'cboStroke')
	driver.execute_script('arguments[0].value =' + str(strokeId), element)

	element = driver.find_element_by_id(divId + 'cboCourse')
	driver.execute_script('arguments[0].value =' + str(courseId), element)

	if minAge != 'All':
		element = driver.find_element_by_id(divId + 'ddlStartAge')
		driver.execute_script('arguments[0].value =' + str(minAge), element)
	if maxAge != 'All':
		element = driver.find_element_by_id(divId + 'ddlEndAge')
		driver.execute_script('arguments[0].value =' + str(maxAge), element)

	if gender=='Women':
		driver.find_element_by_css_selector('label[for=SelectedGender_Female').click()
	elif gender=='Men':
		driver.find_element_by_css_selector('label[for=SelectedGender_Male').click()
	else:
		driver.find_element_by_css_selector('label[for=SelectedGender_Mixed').click()

	element = driver.find_element_by_id(divId + 'ddlZones')
	driver.execute_script('arguments[0].value =' + str(zoneId), element)

	element = driver.find_element_by_id('MaxResults')
	driver.execute_script('arguments[0].value =' + str(nTimes), element)

	driver.execute_script("$('#saveButton').click()")

	# grab the data from the script to place it in
	time.sleep(5)
	try:
		element = driver.find_element_by_xpath("//div[@id='Times_EventRankSearch_Index_Div_1-Results']/script[2]")
	except:  # wait another three seconds if nothing
		time.sleep(3)
		try:
			element = driver.find_element_by_xpath("//div[@id='Times_EventRankSearch_Index_Div_1-Results']/script[2]")
		except:
			print 'no results'
			return

	datascript = element.get_attribute('innerHTML')
	start = datascript.find('data: ')
	end = datascript.find('}]', start)

	dataraw = datascript[start + 6: end + 2].strip().encode('ascii', 'ignore')
	data = json.loads(dataraw)

	# parse the data, example format
	'''{u'EventID': 3, u'TeamName': u'King Marlin Swim Club', u'LSC': u'OK', u'SwimTime': u'2:15.64',
	u'EventSortOrder': 30, u'FullName': u'Rice, Keaton', u'Rank': 250, u'Foreign': u'',
	u'SwimDate': u'/Date(1452841200000)/', u'MeetID': 121828, u'PersonClusteredID': u'2095794',
	u'MeetName': u'2016 OK 65th Annual Phillips 66 Meet ', u'AltAdjSwimTime': u'2:15.64', u'AthletesPdf': None,
	u'SponsorWebsite': u'', u'Age': 10, u'EventDesc': u'200 FR SCY', u'Athletes': None, u'PowerPoints': 687,
	u'StandardName': u'"AAA"', u'SponsorImage': u''}'''

	with open(filePath, 'w+') as outFile:
		for line in data:
			jsondate = int(line['SwimDate'][6:-2])
			date = datetime.date.fromtimestamp(jsondate/1000.0)
			name = line['FullName'].encode('ascii', 'ignore')
			outFile.write(line['EventDesc']+'\t'+line['TeamName']+'\t'+line['SwimTime']+'\t'+str(date)+'\t'+ \
				line['MeetName']+'\t'+name+'\t'+gender+'\t'+str(line['Age'])+'\t'+line['StandardName']+'\n')


if __name__ == "__main__":
	basedirectory = 'data/club'
	years = range(2015, 2018)
	genders = ['Women', 'Men']
	course = 'SCY'
	if course=='SCY':
		events = eventsSCY
	elif course=='SCM':
		events = eventsSCM
	else:
		events = eventsLCM

	#events = ['100 Free']
	zones = {'Central', 'Eastern', 'Southern', 'Western'}
	#zones = ['All']
	ages = range(17, 18)

	#load page once and re-use
	driver = init_driver()
	driver.get('https://www.usaswimming.org/times/event-rank-search')

	for gender in genders:
		for event in events:
			for yearInt in years:
				for age in ages:
					for zone in zones:
						year = str(yearInt)
						directory = basedirectory + '/' + year + '/' + str(age)
						if not os.path.exists(directory):
							os.makedirs(directory)

						# skip some data for smaller results sets
						if age == 20:
							minAge = 20
							maxAge = 40
						else:
							maxAge = str(age)
							minAge= str(age)

						if age > 17:  # over age 17 the results won't be capped in a full pull
							if zone == 'Central':
								zone = 'All'
							else:
								continue

						filename = 'Club_' + year + '_' + course + '_' + gender + '_' + event + '_Age_' + str(age) + \
								   '_' + zone
						print filename
						filepath = directory + '/' + filename

						# load old times to prevent dups
						oldTimes = set()
						if os.path.exists(filepath):
							with open(filepath, 'r') as oldMeetFile:
								for line in oldMeetFile:
									oldTimes.add(line)

						lookup(driver, event=event, course=course, gender=gender, year=year, filePath=filepath,
						   		minAge=minAge, maxAge=maxAge, zone=zone)
	driver.quit()