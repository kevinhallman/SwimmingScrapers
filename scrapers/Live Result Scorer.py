from __future__ import print_function

#####Scores a live result

#The URL of the live result's page 
#if the page url ends in something like index.htm delete that bit (anything that ends in .htm)
#so it would go from this (incorrect):
#http://www.mgoblue.com/livestats/m-swim/index.htm
#to this (correct):
#http://www.mgoblue.com/livestats/m-swim/
#!!!!!!!!!!!!!!
#known bugs/oversights: 
#1. three way or higher ties are not scored correctly
#2. if a swimmer scratches out of finals and the prelims results are listed below the finals results, the swimmer who scratched is sometimes listed with their prelims place. If the meet is scored to 16 places and the swimmer who scratched was 16th exactly in prelims, their time will be scored as atie for 16th. same for 24 and 24th. This line:
#	if not data[0]=='--' and int(data[0])<int(lastSwim[0]):
#       in scoreEvent makes sure that anything less than the last place to make it back scratch should be filtered out, but the obvious solution, switching the < to a <= would break all event scoring on a tie in any position. this requires a more complicated solution (what if check for tie for 16th? that shouldn't be possible in a finals system. it does mess up scoring prelims slightly. could be a ignore in prelims kind of thing)


URL="http://sidearmstats.com/acc/swimming/"
URL="http://www.sidearmstats.com/tamu/secsd18/"
URL="http://www.gophersports.com/livestats/c-swim/"
URL="http://sidearmstats.com/acc/swimming/"
URL="http://results.teamunify.com/pnws2/meets/PAC-12W18/"
URL="http://www.sidearmstats.com/ncaa/swimming/"
#URL="http://www.swmeets.com/Realtime/NCAA/2018/"
#URL="http://www.greensboroaquaticcenter.com/sites/default/files/race-results/2018_NCAA_DII/"
#URL="http://www.gophersports.com/livestats/c-swim/"
#URL="http://results.teamunify.com/pnws2/meets/PAC-12M18/"
#URL="http://www.swmeets.com/Realtime/Jr%20PanPacs/2014/"
URL="http://www.sidearmstats.com/unc/swimming/"
URL="https://static.stkatesathletics.com/custompages/MIACswim/"
URL="https://www.sidearmstats.com/ugeorgia/swimming/"
#URL="https://athletics.indiana.edu/livestats/sw/CurrentMeet/"
URL="http://sidearmstats.com/acc/swimming/"
URL="http://swimmeet.christiansburg.org/"
URL="http://results.spire.institute/2019_a10/"
URL="http://sidearmstats.com/bucknell/swimming/"
URL="https://live.sportstiming.com/meets/2019/02-20-NCAA-BigEast/"
URL="http://sidearmstats.com/usd/swimdive/"
URL="http://sidearmstats.com/mountainwest/wswim/"
URL="http://upload.swimcloud.com/104719/"
URL="http://www.sidearmstats.com/uiowa/swim/"
#URL="http://www.atlswim.net/liveresults/naia/"
URL="http://sidearmstats.com/acc/swimming/"
URL="http://results.teamunify.com/pnws2/meets/PAC-12W19/"
URL="http://results.teamunify.com/pnws2/meets/PAC-12M19/"
#URL="http://sidearmstats.com/texas/swim/"
#URL="http://upload.swimcloud.com/118546/"
#URL="http://wac.org/livestats/swim/2019/"
URL="http://www.swmeets.com/Realtime/NCAA/2018/"
URL="http://www.sidearmstats.com/ncaa/swimming/"
URL="http://athletics.indiana.edu/livestats/SW/CurrentMeet/"
URL="https://swimmeetresults.tech/NCAA-Division-I-Men-2023/"

#which session numbers to score (for example 2 days of finals + 3rd day prelims)
#If you want it to score all completed finals events and ignore prelims, use {'all'} ***the 'all' functionality is not implemented yet, planned furture feature****
#ex {2,4,5} would score sessions 2,4, and 5.
#WARNING:
#This counts by actual number in the list NOT BY THE SESSION NUMBER LISTED IN THE LIVE RESULT. THOSE OFTEN DO NOT INCREMENT EVENLY OR ARE NOT NUMBERS
#For example, if the third session in the live result is called "Session BB", to include it, include a 3 in the sessions list.
#If the 4th session listed is labeled "Session 5" put a 4 in the sessions list (this happens more than you would think)
Sessions=[1,3,5,8]
#how many places to score thru. currently it knows 16 and 24 point systems. It will also assume the number of finals heats based on this parameter. (16 is A-B finals, 24 is A-B-C)
Score_Thru=16
#only used when looking up power points for the individualBreakdown
Division=1
#only set this to true if the finals doesn't include the scoring prelims divers that were eliminated. You want to score finals, but the finals dive result includes only the top 8. The lower dive places are only in the prelim. Set this to True. Otherwise set this to false. If youre scoring a prelim session normally, diving should get scored.
Score_Dive_Prelims=False
#only set this to true if you want all prelims ignored. this parameter exists for when there are sessions with both prelims and finals and you're looking for only finals scores
exclude_all_prelims=False
#this solves the "this is a pain in the ass to copy paste into an article problem"; outputs the individual data with html tags so it can be pasted directly into a swimswam article window with the "text" view on
htmlOutput=True

ScoreSession=True
printNumbered=False

#different output options
#UpDown now autmatically detects if there are relays and individuals. If there are both, the total column is split in two with an individual and relay column with the totals for each. If available diving is included in the individual total
#If you are only interested in individual up downs, for now, this is not configurable. Just delete the relay column from the output. There will also be a column for the relay(s) in the event by eent breakdown
UpDown=False
scoreProgression=False
eventScores=False
individualBreakdown=True
returning=True
yearBreakdown=False
placeCount=False
skipExhibition=False

##NOTE:
##If you're using this on non NCAA events, need to comment out the swimulator power points call and uncomment the power="" line
topX=False
topN=5

import requests
from lxml import html
import re
from operator import itemgetter
from lxml.etree import tostring
import os
import operator

def scoreLiveResult(URL="",Sessions={},Score_Thru=16,Division=1,ScoreSession=True,UpDown=False,scoreProgression=False,eventScores=False,yearBreakdown=True,individualBreakdown=False,placeCount=False,Score_Dive_Prelims=False,exclude_all_prelims=False,htmlOutput=False,printNumbered=False,returning=False,skipExhibition=True,topX=False,topN=3):
	Sessions=sorted(Sessions)
	ses = requests.session()
	#get the sidebar
	try:
		r = requests.get(URL+"evtindex.htm")
	except:		
		return 0
	sidebar = html.fromstring(r.content)
	events = sidebar.xpath('//a | //h3/text()[1]')
	eventNames = sidebar.xpath('//a/text()')
	#if there's issues due to color highlighting, try using this one and commenting out the line above
	#eventNames = sidebar.xpath('//a//font/text()')
	eventNames=['']+eventNames
	
	eventURL=[]
	count=0
	sessionBreak=[]
	for event in events:
		if "Session" not in event:
			eventURL.append(URL+event.attrib['href'])
			count=count+1
		else:
			sessionBreak.append(count)
	sessionBreak.append(count)
	#Score the sessions
	if ScoreSession:
		score={}
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("Time",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(prelim and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					score=score_event(parseTimes(eventURL[event]),score,prelim,Score_Thru,Score_Dive_Prelims)
		Scores={}
		for team in score:
			if re.search("Men",team):
				Scores[team[:len(team)-4]]=score[team]
		sortedScoresMen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		Scores={}
		for team in score:
			if re.search("Women",team):
				Scores[team[:len(team)-6]]=score[team]
		sortedScoresWomen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		if not htmlOutput:
			print("Men")
			place=1
			for team in sortedScoresMen:
				if printNumbered:
					print(str(place)+". "+team[0]+": "+str(team[1]))
				else:
					print(team[0]+"|"+str(team[1]))
				place+=1
			print("Women")
			place=1
			for team in sortedScoresWomen:
				if printNumbered:
					print(str(place)+". "+team[0]+": "+str(team[1]))
				else:
					print(team[0]+"|"+str(team[1]))
				place+=1
		else:
			if len(sortedScoresMen)>0:
				if len(sortedScoresWomen)>0:
					print("<h2>Final Scores Men</h2>")
				else:
					print("<h2>Final Scores</h2>")
				place=1
				for team in sortedScoresMen:
					if place==1:
						print("<p>"+str(place)+". "+team[0]+": "+'{0:g}'.format(float(team[1]))+"<br />")
					else:
						print(str(place)+". "+team[0]+": "+'{0:g}'.format(float(team[1]))+"<br />")
					place+=1
			if len(sortedScoresWomen)>0:
				if len(sortedScoresMen)>0:
					print("<h2>Final Scores Women</h2>")
				else:
					print("<h2>Final Scores</h2>")
				place=1
				for team in sortedScoresWomen:
					if place==1:
						print("<p>"+str(place)+". "+team[0]+": "+'{0:g}'.format(float(team[1]))+"<br />")
					else:
						print(str(place)+". "+team[0]+": "+'{0:g}'.format(float(team[1]))+"<br />")
					place+=1
	if yearBreakdown:
		individs={}
		count=0
		teams={}
		eventList=[]
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(prelim and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					individs=yearPoints(parseTimes(eventURL[event]),individs,Score_Thru,eventNames[event],Division,Score_Dive_Prelims,prelim)
		teams=[]
		genders=[]
		for swmmer in individs:
			out=swmmer.split("|")
			if out[0]+"|"+out[2] not in teams:
				teams.append(out[0]+"|"+out[2])
			if out[2] not in genders:
				genders.append(out[2])
		if not htmlOutput:
			print("Men")
			teamOut=""
			returningpts={}
			for team in sortedScoresMen:
				teamOut=teamOut+"|"+team[0]
				returningpts[team]=0
				tmSwimmers=[]
				events=[]
				for individual in individs:
					ind=individual.split("|")
					if ind[0]==team[0] and ind[2]=="Men" and (ind[1]=="FR" or ind[1]=="SO" or ind[1]=="JR" or ind[1]=="FY" or ind[1]==""):
						returningpts[team[0]]=returningpts[team[0]]+individs[individual]
						
			print(teamOut)
			years=["FR","SO","JR","SR","Returning"]
			for year in years:
				lineOut=year
				for team in sortedScoresMen:
					try:
						lineOut=lineOut+"|"+str(individs[team[0]+"|"+year+"|"+"Men"])
					except:
						if year=="FR":
							try:
								lineOut=lineOut+"|"+str(individs[team[0]+"|FY|"+"Men"])
							except:
								lineOut=lineOut+"|0"
						elif year=="Returning":
							try:
								lineOut=lineOut+"|"+str(returningpts[team[0]])
							except:
								lineOut=lineOut+"|0"
						else:
							lineOut=lineOut+"|0"
			print("Women")
			teamOut=""
			returningpts={}
			for team in sortedScoresWomen:
				teamOut=teamOut+"|"+team[0]
				returningpts[team[0]]=0
				tmSwimmers=[]
				events=[]
				for individual in individs:
					ind=individual.split("|")
					if ind[0]==team[0] and ind[2]=="Women" and (ind[1]=="FR" or ind[1]=="SO" or ind[1]=="JR" or ind[1]=="FY" or ind[1]==""):
						returningpts[team[0]]=returningpts[team[0]]+individs[individual]
			print(teamOut)
			years=["FR","SO","JR","SR","Returning"]
			for year in years:
				lineOut=year
				for team in sortedScoresWomen:
					try:
						lineOut=lineOut+"|"+str(individs[team[0][:team[0].find("-")]+"|"+year+"|"+"Women"])
					except:
						if year=="FR":
							try:
								lineOut=lineOut+"|"+str(individs[team[0]+"|FY|"+"Women"])
							except:
								lineOut=lineOut+"|0"
						elif year=="Returning":
							try:
								lineOut=lineOut+"|"+str(returningpts[team[0]])
							except:
								lineOut=lineOut+"|0"
						else:
							lineOut=lineOut+"|0"
				print(lineOut)
		else:
			if len(sortedScoresMen)>0:
				if len(sortedScoresWomen)>0:
					print("<h2>Individual Scores by Year Men</h2>")
				else:
					print("<h2>Individual Scores by Year</h2>")
				print("<table border=\"0\" cellspacing=\"0\">")
				print("<colgroup span=\""+str(len(sortedScoresMen)+1)+'" width="85"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				returningpts={}
				for team in sortedScoresMen:
					print("<td align=\"left\">"+team[0]+"</td>")
					returningpts[team[0]]=0
					tmSwimmers=[]
					events=[]
					for individual in individs:
						ind=individual.split("|")
						if ind[0]==team[0] and ind[2]=="Men" and (ind[1]=="FR" or ind[1]=="SO" or ind[1]=="JR" or ind[1]=="FY" or ind[1]==""):
							returningpts[team[0]]=returningpts[team[0]]+individs[individual]
				print("</tr>")
				years=["FR","SO","JR","SR","Returning"]
				for year in years:
					print("<tr>")
					print("<td align=\"left\" height=\"17\">"+year+"</td>")
					
					for team in sortedScoresMen:
						try:
							lineOut='{0:g}'.format(float(individs[team[0]+"|"+year+"|"+"Men"]))
						except:
							if year=="FR":
								try:
									lineOut='{0:g}'.format(float(individs[team[0]+"|FY|"+"Men"]))
								except:
									lineOut="0"
							elif year=="Returning":
								try:
									lineOut='{0:g}'.format(float(returningpts[team[0]]))
								except:
									lineOut="0"
							else:
								lineOut="0"
						print("<td align'\"left\">"+lineOut+"</td>")
					print("</tr>")
				print("</tbody>")
				print("</table>") 
			if len(sortedScoresWomen)>0:
				if len(sortedScoresMen)>0:
					print("<h2>Individual Scores by Year Women</h2>")
				else:
					print("<h2>Individual Scores by Year</h2>")
				print("<table border=\"0\" cellspacing=\"0\">")
				print("<colgroup span=\""+str(len(sortedScoresWomen)+1)+'" width="85"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				returningpts={}
				for team in sortedScoresWomen:
					print("<td align=\"left\">"+team[0]+"</td>")
					returningpts[team[0]]=0
					tmSwimmers=[]
					events=[]
					for individual in individs:
						ind=individual.split("|")
						if ind[0]==team[0] and ind[2]=="Women" and (ind[1]=="FR" or ind[1]=="SO" or ind[1]=="JR" or ind[1]=="FY" or ind[1]==""):
							returningpts[team[0]]=returningpts[team[0]]+individs[individual]
				print("</tr>")
				years=["FR","SO","JR","SR","Returning"]
				for year in years:
					print("<tr>")
					print("<td align=\"left\" height=\"17\">"+year+"</td>")
					
					for team in sortedScoresWomen:
						try:
							lineOut='{0:g}'.format(float(individs[team[0]+"|"+year+"|"+"Women"]))
						except:
							if year=="FR":
								try:
									lineOut='{0:g}'.format(float(individs[team[0]+"|FY|"+"Women"]))
								except:
									lineOut="0"
							elif year=="Returning":
								try:
									lineOut='{0:g}'.format(float(returningpts[team[0]]))
								except:
									lineOut="0"
							else:
								lineOut="0"
						print("<td align'\"left\">"+lineOut+"</td>")
					print("</tr>")
				print("</tbody>")
				print("</table>") 

	if scoreProgression:
		score={}
		count=0
		teams={}
		eventList=[]
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("Time",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(prelim and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					score=score_event(parseTimes(eventURL[event]),score,re.search("Prelim",eventNames[event]),Score_Thru,Score_Dive_Prelims)
					if Score_Dive_Prelims and re.search("Diving",eventNames[event]):
						for eve in eventNames:
							if re.search(eventNames[event][:-7],eve) and re.search("Prelim",eve):
								score=score_event(parseTimes(eventURL[eventNames.index(eve)]),score,re.search("Prelim",eve),Score_Thru,Score_Dive_Prelims)
					eventList.append(eventNames[event])
					for result in score:
						if count==0:
							teams[result]=[]
						elif result not in teams:
							teams[result]=[0]*count
							
					for team in teams:
						try:
							teams[team].append(score[team])
						except:
							teams[team].append(teams[team][-1])
					count+=1
		#print teams
		Scores={}
		for team in score:
			if re.search("Men",team):
				Scores[team[:len(team)-4]]=score[team]
		sortedScoresMen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		Scores={}
		for team in score:
			if re.search("Women",team):
				Scores[team[:len(team)-6]]=score[team]
		sortedScoresWomen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		if not htmlOutput:
			print("Men")
			teamOut=""
			for team in sortedScoresMen:
				teamOut=teamOut+"|"+team[0]
			print(teamOut)
			count=0
			for event in eventList:
				eve=re.search("Men",event)
				if eve:
					eventOut=event[eve.end()+1:]
					for team in sortedScoresMen:
						eventOut=eventOut+"|"+str(teams[team[0]+" Men"][count])
					print(eventOut)
				count+=1
			print("Women")
			teamOut=""
			for team in sortedScoresWomen:
				teamOut=teamOut+"|"+team[0]
			print(teamOut)
			count=0
			for event in eventList:
				eve=re.search("Women",event)
				if eve:
					eventOut=event[eve.end()+1:]
					for team in sortedScoresWomen:
						eventOut=eventOut+"|"+str(teams[team[0]+" Women"][count])
					print(eventOut)
				count+=1
		else:
			if len(sortedScoresMen)>0:
				if len(sortedScoresWomen)>0:
					print("<h2>Score Progression Men</h2>")
				else:
					print("<h2>Score Progression</h2>")
				print("<p>What the score was after each event</p>")
				print("<table border=\"0\" cellspacing=\"0\">")
				###warning check the width parameter here. just based off big 10 example. answer might be blank. might be something based on number of columns
				print("<colgroup span=\""+str(len(sortedScoresMen)+1)+'" width="85"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				for team in sortedScoresMen:
					print("<td align=\"left\">"+team[0]+"</td>")
				print("</tr>")
				count=0
				for event in eventList:
					eve=re.search("Men",event)
					if eve:
						print("<tr>")
						print("<td align=\"left\" height=\"17\">"+cleanEventName(event)+"</td>")
						for team in sortedScoresMen:
							print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Men"][count]))+"</td>")
						print("</tr>")
					count+=1
				print("</tbody>")
				print("</table>")
			if len(sortedScoresWomen)>0:
				if len(sortedScoresMen)>0:
					print("<h2>Score Progression Women</h2>")
				else:
					print("<h2>Score Progression</h2>")
				print("<p>What the score was after each event</p>")
				print("<table border=\"0\" cellspacing=\"0\">")
				###warning check the width parameter here. just based off big 10 example. answer might be blank. might be something based on number of columns
				print("<colgroup span=\""+str(len(sortedScoresWomen)+1)+'\" width=\"85\"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=""left"" height=\"17\"></td>")
				for team in sortedScoresWomen:
					print("<td align=\"left\">"+team[0]+"</td>")
				print("</tr>")
				count=0
				for event in eventList:
					eve=re.search("Women",event)
					if eve:
						print("<tr>")
						print("<td align=\"left\" height=\"17\">"+cleanEventName(event)+"</td>")
						for team in sortedScoresWomen:
							print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Women"][count]))+"</td>")
						print("</tr>")
					count+=1
				print("</tbody>")
				print("</table>")
			#print individs
	if eventScores:
		score={}
		count=0
		teams={}
		eventList=[]
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(Score_Dive_Prelims and re.search("Prelim",eventNames[event])):
					score=score_event(parseTimes(eventURL[event]),score,re.search("Prelim",eventNames[event]),Score_Thru,Score_Dive_Prelims)
					if Score_Dive_Prelims and re.search("Diving",eventNames[event]):
						for eve in eventNames:
							if re.search(eventNames[event][:-7],eve) and re.search("Prelim",eve):
								score=score_event(parseTimes(eventURL[eventNames.index(eve)]),score,re.search("Prelim",eve),Score_Thru,Score_Dive_Prelims)
					eventList.append(eventNames[event])
					for result in score:
						if count==0:
							teams[result]=[]
						elif result not in teams:
							teams[result]=[0]*count
							
					for team in teams:
						try:
							teams[team].append(score[team])
						except:
							teams[team].append(teams[team][-1])
					count+=1
		#print teams
		Scores={}
		for team in score:
			if re.search("Men",team):
				Scores[team[:len(team)-4]]=score[team]
		sortedScoresMen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		Scores={}
		for team in score:
			if re.search("Women",team):
				Scores[team[:len(team)-6]]=score[team]
		sortedScoresWomen = sorted(Scores.items(), key=operator.itemgetter(1),reverse=True)
		if not htmlOutput:
			print("Men")
			teamOut=""
			for team in sortedScoresMen:
				teamOut=teamOut+"|"+team[0]
			print(teamOut)
			count=0
			for event in eventList:
				eve=re.search("Men",event)
				if eve:
					eventOut=cleanEventName(event)
					for team in sortedScoresMen:
						if count==0:
							eventOut=eventOut+"|"+str(teams[team[0]+" Men"][count])
						else:
							eventOut=eventOut+"|"+str(teams[team[0]+" Men"][count]-teams[team[0]+" Men"][count-1])
					print(eventOut)
				count+=1
			print("Women")
			teamOut=""
			for team in sortedScoresWomen:
				teamOut=teamOut+"|"+team[0]
			print(teamOut)
			count=0
			for event in eventList:
				eve=re.search("Women",event)
				if eve:
					eventOut=cleanEventName(event)
					for team in sortedScoresWomen:
						if count==0:
							eventOut=eventOut+"|"+str(teams[team[0]+" Women"][count])
						else:
							eventOut=eventOut+"|"+str(teams[team[0]+" Women"][count]-teams[team[0]+" Women"][count-1])
					print(eventOut)
				count+=1
		else:
			if len(sortedScoresMen)>0:
				if len(sortedScoresWomen)>0:
					print("<h2>Points in Each Event Men</h2>")
				else:
					print("<h2>Points in Each Event</h2>")
				print("<p>What each team scored in each event</p>")
				print("<table border=\"0\" cellspacing=\"0\">")
				#as above this width thing might need to be fixed
				print("<colgroup span=\""+str(len(sortedScoresMen)+1)+'" width="85"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				for team in sortedScoresMen:
					print("<td align=\"left\">"+team[0]+"</td>")
				print("</tr>")
				count=0
				for event in eventList:
					eve=re.search("Men",event)
					if eve:
						print("<tr>")
						print("<td align=\"left\" height=\"17\">"+cleanEventName(event)+"</td>")
						for team in sortedScoresMen:
							if count==0:
								print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Men"][count]))+"</td>")
							else:
								print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Men"][count]-teams[team[0]+" Men"][count-1]))+"</td>")
						print("</tr>")
					count+=1
				print("</tbody>")
				print("</table>")
			if len(sortedScoresWomen)>0:
				if len(sortedScoresMen)>0:
					print("<h2>Points in Each Event Women</h2>")
				else:
					print("<h2>Points in Each Event</h2>")
				print("<p>What each team scored in each event</p>")
				print("<table border=\"0\" cellspacing=\"0\">")
				#as above this width thing might need to be fixed
				print("<colgroup span=\""+str(len(sortedScoresWomen)+1)+'" width="85"></colgroup>')
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				for team in sortedScoresWomen:
					print("<td align=\"left\">"+team[0]+"</td>")
				print("</tr>")
				count=0
				for event in eventList:
					eve=re.search("Women",event)
					if eve:
						print("<tr>")
						print("<td align=\"left\" height=\"17\">"+cleanEventName(event)+"</td>")
						for team in sortedScoresWomen:
							if count==0:
								print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Women"][count]))+"</td>")
							else:
								print("<td align=\"left\">"+'{0:g}'.format(float(teams[team[0]+" Women"][count]-teams[team[0]+" Women"][count-1]))+"</td>")
						print("</tr>")
					count+=1
				print("</tbody>")
				print("</table>")
	
			#if not htmlOutput:
		#	for gender in genders:
		#		print gender
		#		for team in teams:
		#			if re.search(gender,team):
		#				tm=team.split("|")[0]
		#				tmSwimmers=[]
		#				pts=[]
		#				events=[]
		#				for individual in individs:
		#					ind=individual.split("|")
		#					if ind[0]==tm and ind[2]==gender:
		#						tmSwimmers.append(ind[1].split("|")[0])
		#						pts.append(individs[individual])
		#				print '|'+tm
		#				Years=["FR","SO","JR","SR","","FY"]
		#				for year in Years:
		#					try:
		#						index=tmSwimmers.index(year)
		#						print tmSwimmers[index]+"|"+str(pts[index])
		#					except:
		#						if not (year=="" or year =="FY"):
		#							print year+"|0"
	if placeCount:
		counts={}
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event])or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(re.search("Prelim",eventNames[event]) and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					counts=count_Places(parseTimes(eventURL[event]),counts,Score_Thru,Score_Dive_Prelims,re.search("Prelim",eventNames[event]))
		if not htmlOutput:
			print("Men")
			teams=""
			for team in counts:
				if re.search("Men",team):
					teams=teams+"|"+team[:len(team)-4]
			print(teams)
			for i in range(0,Score_Thru):
				out=str(i+1)
				for team in counts:
					if re.search("Men",team):
						out=out+"|"+str(counts[team][i])
				print(out)
			print("Women")
			teams=""
			for team in counts:
				if re.search("Women",team):
					teams=teams+"|"+team[:len(team)-6]
			print(teams)
			for i in range(0,Score_Thru):
				out=str(i+1)
				for team in counts:
					if re.search("Women",team):
						out=out+"|"+str(counts[team][i])
				print(out)
		else:
			teamsm=""
			for team in counts:
				if re.search("Men",team):
					teamsm=teamsm+"|"+team[:len(team)-4]
			teamsw=""
			for team in counts:
				if re.search("Women",team):
					teamsw=teamsw+"|"+team[:len(team)-4]
			if len(teamsm)>0:
				if len(teamsw)>0:
					print("<h2>Number of Times Each Team Got Each Place (Individual Events) Men</h2>")
				else:
						print("<h2>Number of Times Each Team Got Each Place (Individual Events)</h2>")
				print("<table border=\"0\" cellspacing=\"0\">")
				print("<colgroup span=\""+str(len(sortedScoresMen))+"\" width=\"85\"></colgroup>")
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				for team in counts:
					if re.search("Men",team):
						print("<td align=\"left\">"+team[:len(team)-4]+"</td>")
				print("</tr>")
				for i in range(0,Score_Thru):
					out=str(i+1)
					print("<tr>")
					print("<td align=\"left\" height=\"17\">"+out+"</td>")
					for team in counts:
						if re.search("Men",team):	
							print("<td align=\"left\">"+str(counts[team][i])+"</td>")
					print("</tr>")
				print("</tbody>")
				print("</table>")
			if len(teamsw)>0:
				if len(teamsm)>0:
					print("<h2>Number of Times Each Team Got Each Place (Individual Events) Women</h2>")
				else:
						print("<h2>Number of Times Each Team Got Each Place (Individual Events)</h2>")
				print("<table border=\"0\" cellspacing=\"0\">")
				print("<colgroup span=\""+str(len(sortedScoresWomen))+"\" width=\"85\"></colgroup>")
				print("<tbody>")
				print("<tr>")
				print("<td align=\"left\" height=\"17\"></td>")
				for team in counts:
					if re.search("Women",team):
						print("<td align=\"left\">"+team[:len(team)-6]+"</td>")
				print("</tr>")
				for i in range(0,Score_Thru):
					out=str(i+1)
					print("<tr>")
					print("<td align=\"left\" height=\"17\">"+out+"</td>")
					for team in counts:
						if re.search("Women",team):	
							print("<td align=\"left\">"+str(counts[team][i])+"</td>")
					print("</tr>")
				print("</tbody>")
				print("</table>")
	#do up downs
	if UpDown:
		counts={}
		countsevent=0
		events="|All"
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event])):
					if not re.search(cleanEventName(eventNames[event]),events):
						countsevent=countsevent+1
						events=events+"|"+cleanEventName(eventNames[event])
					counts=count_upDown(parseTimes(eventURL[event]),counts,countsevent,events,Score_Thru)
					if re.search("Relay",eventNames[event]):
						events=events.replace("|All","|Individual\tRelays")

		for teamID in counts:
			cnt=counts[teamID].split("|")
			counter=1
			if re.search("Relay",events) and len(cnt[0].split("\t"))==1:
				countsfixed="|"+cnt[0]+"\t0/0/0|"
			else:
				countsfixed="|"+cnt[0]+"|"
			while counter<=countsevent:
				if len(cnt)<=counter:
					countsfixed=countsfixed+"0/0/0|"
				else:
					countsfixed=countsfixed+cnt[counter]+"|"
				counter=counter+1
			counts[teamID]=countsfixed
		#old depricated version. relies on old count_UpDown. probably can be deleted. This is the men's block only
		#Counts={}
		#for team in counts:
		#	if re.search("Men",team):
		#		Counts[team[:len(team)-4]]=counts[team]
		#sortedCounts = sorted(Counts.items(), key=operator.itemgetter(1),reverse=True)
		#print "Men"
		#print events
		#for team in sortedCounts:
		#	upDown=team[1].split(" ")
		#	if Score_Thru==16:
		#		print team[0]," Up:"+str(upDown[0])+" Down:"+str(upDown[1])
		#	else:
		#		print team[0]," Up:"+str(upDown[0])+" Mid:"+str(upDown[1])+" Down:"+str(upDown[2])
		Counts={}
		for team in counts:
			if re.search("Men",team):
				Counts[team[:len(team)-4]]=counts[team]
		sortedCounts = sorted(Counts.items(), key=operator.itemgetter(1),reverse=True)
		print("Men")
		print(events.replace("\t","|"))
		for team in sortedCounts:
			if Score_Thru==16:
				upDown=team[1].replace("/0|","|").replace("/0\t","\t")
			elif Score_Thru==24:
				upDown=team[1]
			print(team[0]+upDown.replace("\t","|"))
		Counts={}
		for team in counts:
			if re.search("Women",team):
				Counts[team[:len(team)-6]]=counts[team]
		sortedCounts = sorted(Counts.items(), key=operator.itemgetter(1),reverse=True)
		print("Women")
		print(events.replace("\t","|"))
		for team in sortedCounts:
			if Score_Thru==16:
				upDown=team[1].replace("/0|","|").replace("/0\t","\t")
			elif Score_Thru==24:
				upDown=team[1]
				#upDown=team[1].replace("/0|","|")
				#upDown=team[1].replace("/0\t","\t")
			print(team[0]+upDown.replace("\t","|"))

	
	if topX:
		individs={}
		count=0
		teams={}
		eventList=[]
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(prelim and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					individs=individualEvents(parseTimes(eventURL[event]),individs,Score_Thru,eventNames[event],Division,Score_Dive_Prelims,prelim,returning,topN)
		teams=[]
		genders=[]
		for swmmr in individs:
			sw=swmmr.split("|")
			#print individs[swmmr][1]
			events=individs[swmmr][1]
			if len(events)>0:
				print(sw[1]+"|"+sw[0]+"|"+sw[2]+"|"+sw[3]+"|"+events)
	if individualBreakdown:
		individs={}
		count=0
		teams={}
		eventList=[]
		for session in Sessions:
			for event in range(sessionBreak[session-1],sessionBreak[session]):
				prelim=re.search("Prelims",eventNames[event])
				if not(re.search("Trial",eventNames[event]) or re.search("off",eventNames[event]) or re.search("Semi",eventNames[event]) or (prelim and exclude_all_prelims)) and not(prelim and Score_Dive_Prelims and not re.search("Diving",eventNames[event])):
					individs=individualEvents(parseTimes(eventURL[event]),individs,Score_Thru,eventNames[event],Division,Score_Dive_Prelims,prelim,returning)
		teams=[]
		genders=[]
		for swmmer in individs:
			out=swmmer.split("|")
			if out[0]+"|"+out[2] not in teams:
				teams.append(out[0]+"|"+out[2])
			if out[2] not in genders:
				genders.append(out[2])
		for swmmer in individs:
			out=swmmer.split("|")
			inList=False
			for t in sortedScoresWomen:
				if out[0]==t[0] and out[2]=='Women':
					inList=True
			if not inList and out[2]=='Women':
				sortedScoresWomen.append((out[0],0))
			for t in sortedScoresMen:
				if out[0]==t[0] and out[2]=='Men':
					inList=True
			if not inList and out[2]=='Men':
				sortedScoresMen.append((out[0],0))
		#for gender in genders:
		#	print gender
		#	for team in teams:
		#		if re.search(gender,team):
		#			tm=team.split("|")[0]
		#			tmSwimmers=[]
		#			pts=[]
		#			events=[]
		#				for individual in individs:
		#				ind=individual.split("|")
		#				if ind[0]==tm and ind[2]==gender:
		#					tmSwimmers.append(ind[1]+"|"+ind[3])
		#					pts.append(individs[individual][0])
		#					events.append(individs[individual][1])
		#				order=sorted(range(len(pts)), key=lambda k: pts[k])
		#			print team
		#			print "|Year|Points|Event|Place|Time|Power|Event|Place|Time|Power|Event|Place|Time|Power"
		#			for place in reversed(order):
		#				print tmSwimmers[place]+"|"+str(pts[place])+"|"+events[place]
		if not htmlOutput:
			print('Men')
			for team in sortedScoresMen:
				tmSwimmers=[]
				yr=[]
				pts=[]
				events=[]
				adjpts=[]
				for individual in individs:
					ind=individual.split("|")
					if ind[0]==team[0] and ind[2]=='Men':
						tmSwimmers.append(ind[1]+"|"+ind[3])
						yr.append(ind[3])
						pts.append(individs[individual][0])
						events.append(individs[individual][1])
						if returning:
							adjpts.append(individs[individual][2])
					order=sorted(range(len(pts)), key=lambda k: pts[k])
				print(team[0])
				if returning:
					print("|Year|Points|No SR Pts|Event|Place|Time|No SR Place|Event|Place|Time|No SR Place|Event|Place|Time|No SR Place")
				else:
					print("|Year|Points|Event|Place|Time|Power|Event|Place|Time|Power|Event|Place|Time|Power")
				for place in reversed(order):
					if returning:
						if yr[place]!="SR":
							print(tmSwimmers[place]+"|"+str(pts[place])+"|"+str(adjpts[place])+"|"+events[place])
					else:
						print(tmSwimmers[place]+"|"+str(pts[place])+"|"+events[place])
		else:
			if len(sortedScoresMen)>0:
				if len(sortedScoresWomen)>0:
					print("<h2>Individual Breakdown Men</h2>")
				else:
					print("<h2>Individual Breakdown</h2>")
				print("<p>Power are <a href=\"https://swimswam.com/swimulator/\" data-wpel-link=\"internal\">Swimulator</a> power points. Those are a way to quantify time quality independent of what event the time is from. Includes only final times and final dive scores.</p>")
				for team in sortedScoresMen:
					tmSwimmers=[]
					pts=[]
					yr=[]
					events=[]
					adjpts=[]
					for individual in individs:
						ind=individual.split("|")
						if ind[0]==team[0] and ind[2]=='Men':
							tmSwimmers.append(ind[1]+'</td>\n<td align="left">'+ind[3])
							pts.append(individs[individual][0])
							yr.append(ind[3])
							events.append(individs[individual][1].replace("|",'</td>\n<td align="left">'))
							if returning:
								adjpts.append(individs[individual][2])
						order=sorted(range(len(pts)), key=lambda k: pts[k])
					print("<h4>"+team[0]+"</h4>")
					print('<table border="0" cellspacing="0"><colgroup span="15" width="85"></colgroup>\n<tbody>\n<tr>\n<td align="left" height="17"></td>')
					if returning:
						print('<td align="left">Year</td>\n<td align="left">Points</td>\n<td align="left">No SR Points</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n</tr>')
					else:
						print('<td align="left">Year</td>\n<td align="left">Points</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n</tr>')
					#print "|Year|Points|Event|Place|Time|Power|Event|Place|Time|Power|Event|Place|Time|Power"
					for place in reversed(order):
						if returning:
							if yr[place]!="SR":
								print('<tr>')
								print('<td align="left" height="17">'+tmSwimmers[place]+'</td>\n<td align="left">'+'{0:g}'.format(float(pts[place]))+'</td>\n<td align="left">'+'{0:g}'.format(float(adjpts[place]))+'</td>\n<td align="left">'+events[place]+'</td>')
								print('</tr>')
						else:
							print('<tr>')
							print('<td align="left" height="17">'+tmSwimmers[place]+'</td>\n<td align="left">'+'{0:g}'.format(float(pts[place]))+'</td>\n<td align="left">'+events[place]+'</td>')
							print('</tr>')
					print('</tbody>\n</table>')
		if not htmlOutput:
			print('Women')
			for team in sortedScoresWomen:
				tmSwimmers=[]
				yr=[]
				pts=[]
				events=[]
				adjpts=[]
				for individual in individs:
					ind=individual.split("|")
					#print individual
					if ind[0]==team[0] and ind[2]=='Women':
						tmSwimmers.append(ind[1]+"|"+ind[3])
						yr.append(ind[3])
						pts.append(individs[individual][0])
						events.append(individs[individual][1])
						if returning:
							adjpts.append(individs[individual][2])
					order=sorted(range(len(pts)), key=lambda k: pts[k])
				print(team[0])
				if returning:
					print("|Year|Points|No SR Pts|Event|Place|Time|No SR Place|Event|Place|Time|No SR Place|Event|Place|Time|No SR Place")
				else:
					print("|Year|Points|Event|Place|Time|Power|Event|Place|Time|Power|Event|Place|Time|Power")
				for place in reversed(order):
					if returning:
						if yr[place]!="SR" and tmSwimmers[place].split("|")[0]!="Katie Ledecky":
							print(tmSwimmers[place]+"|"+str(pts[place])+"|"+str(adjpts[place])+"|"+events[place])
					else:
						print(tmSwimmers[place]+"|"+str(pts[place])+"|"+events[place])
		else:
			if len(sortedScoresWomen)>0:
				if len(sortedScoresMen)>0:
					print("<h2>Individual Breakdown Women</h2>")
				else:
					print("<h2>Individual Breakdown</h2>")
				print("<p>Power are <a href=\"https://swimswam.com/swimulator/\" data-wpel-link=\"internal\">Swimulator</a> power points. Those are a way to quantify time quality independent of what event the time is from. Includes only final times and final dive scores.</p>")
				for team in sortedScoresWomen:
					tmSwimmers=[]
					pts=[]
					yr=[]
					events=[]
					adjpts=[]
					for individual in individs:
						ind=individual.split("|")
						if ind[0]==team[0] and ind[2]=='Women':
							tmSwimmers.append(ind[1]+'</td>\n<td align="left">'+ind[3])
							pts.append(individs[individual][0])
							yr.append(ind[3])
							events.append(individs[individual][1].replace("|",'</td>\n<td align="left">'))
							if returning:
								adjpts.append(individs[individual][2])
						order=sorted(range(len(pts)), key=lambda k: pts[k])
					print("<h4>"+team[0]+"</h4>")
					print('<table border="0" cellspacing="0"><colgroup span="15" width="85"></colgroup>\n<tbody>\n<tr>\n<td align="left" height="17"></td>')
					if returning:
						print('<td align="left">Year</td>\n<td align="left">Points</td>\n<td align="left">No SR Points</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">No SR Place</td>\n</tr>')
					else:
						print('<td align="left">Year</td>\n<td align="left">Points</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n<td align="left">Event</td>\n<td align="left">Place</td>\n<td align="left">Time</td>\n<td align="left">Power</td>\n</tr>')
					#print "|Year|Points|Event|Place|Time|Power|Event|Place|Time|Power|Event|Place|Time|Power"
					for place in reversed(order):
						if returning:
							if yr[place]!="SR" and tmSwimmers[place][0:13]!="Katie Ledecky":
								print('<tr>')
								print('<td align="left" height="17">'+tmSwimmers[place]+'</td>\n<td align="left">'+'{0:g}'.format(float(pts[place]))+'</td>\n<td align="left">'+'{0:g}'.format(float(adjpts[place]))+'</td>\n<td align="left">'+events[place]+'</td>')
								print('</tr>')
						else:
							print('<tr>')
							print('<td align="left" height="17">'+tmSwimmers[place]+'</td>\n<td align="left">'+'{0:g}'.format(float(pts[place]))+'</td>\n<td align="left">'+events[place]+'</td>')
							print('</tr>')
					print('</tbody>\n</table>')
			
def count_Places(result,counts,score_thru,Score_Dive_Prelims,prelim):
	for swim in result:
		data=swim.split('\t')
		lastSwim=[0,"","","","","","",""]
		#protection against scores at the bottom of the page. 
		if re.search("Relay",data[6]):
			break
		if not data[0]=='--' and int(data[0])<int(lastSwim[0]):
			break
		if not data[0]=='--'and not(Score_Dive_Prelims and int(data[0])<=8 and prelim):
			if int(data[0])<=score_thru:
				heat=(int(data[0])-1)//8
				teamID=data[4]+" "+data[5]
				if teamID not in counts:
					counts[teamID]=[0]*score_thru
				counts[teamID][int(data[0])-1]=counts[teamID][int(data[0])-1]+1
		lastSwim=data
	return counts															

def cleanEventName(eventName):
	if re.search("Platform",eventName):
		return "Platform Diving"
	eventName=re.sub("#\d+ ","",eventName)
	eventName=re.sub("^[^0-9]+","",eventName)
	eventName=re.sub(" Prelims ","",eventName)
	eventName=re.sub(" Finals ","",eventName)
	eventName=re.sub(" Swim-off ","",eventName)
	eventName=re.sub(" Time Trial ","",eventName)
	eventName=re.sub(" Semis ","",eventName)
	return eventName

def strokeToLongName(stroke):
	if stroke=="Free":
		stroke="Freestyle"
	if stroke=="Back":
		stroke="Backstroke"
	if stroke=="Fly":
		stroke="Butterfly"
	if stroke=="Breast":
		stroke="Breastroke"
	if stroke=="IM":
		stroke="Individual+Medley"
	return stroke

def is_a_stroke(stroke):
	if stroke=="Freestyle":
		return True
	if stroke=="Backstroke":
		return True
	if stroke=="Butterfly":
		return True
	if stroke=="Breastroke":
		return True
	if stroke=="Individual+Medley":
		return True
	return False

def yearPoints(result,individs,score_thru,event,division,Score_Dive_Prelims,prelim):
	if score_thru==16:
		individual_points=[0,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0]
	elif score_thru==24:
		individual_points=[0,32,28,27,26,25,24,23,22,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0]
	elif score_thru==18:
		individual_points=[0,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0]
	elif score_thru==27:
		individual_points=[0,35,31,30,29,28,27,26,25,24,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0]		
	elif score_thru==8:
		individual_points=[0,9,7,6,5,4,3,2,1,0]
	elif score_thru==5:
		individual_points=[0,9,4,3,2,1,0]
		relay_points=[0,11,4,2,0,0,0]
	lastSwim=[0,"","","","","","",""]
	if re.search("Men",event):
		gender="Men"
	else:
		gender="Women"
	event=cleanEventName(event)
	distance=event.split(" ")[0]
	stroke=strokeToLongName(event.split(" ")[1])
	for swim in result:
		data=swim.split('\t')
		if re.search("Relay",data[6]):
			break
		if not data[0]=='--' and not(Score_Dive_Prelims and int(data[0])<=8 and prelim):
			ID=data[4]+"|"+data[3]+"|"+data[5]
			if ID not in individs:
				individs[ID]=0
			if int(data[0])<(len(individual_points)-1):
				if lastSwim[0]==data[0]:
						individs[ID]=individs[ID]+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
						individs[lastID]=individs[lastID]-lastPoints+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
						lastPoints=(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
				else:
						individs[ID]=individs[ID]+individual_points[int(data[0])]
						lastPoints=individual_points[int(data[0])]
		lastSwim=data
		lastID=ID
	return individs
	
#maybe fold this function into score event? or not..				
def individualEvents(result,individs,score_thru,event,division,Score_Dive_Prelims,prelim,returning,topN=0):
	if score_thru==16:
		individual_points=[0,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	elif score_thru==24:
		individual_points=[0,32,28,27,26,25,24,23,22,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	elif score_thru==18:
		individual_points=[0,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	elif score_thru==27:
		individual_points=[0,35,31,30,29,28,27,26,25,24,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	elif score_thru==8:
		individual_points=[0,9,7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	elif score_thru==5:
		individual_points=[0,9,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	lastSwim=[0,"","","","","","",""]
	lastSwimR=[0,"","","","","","",""]
	if re.search("Men",event):
		gender="Men"
	else:
		gender="Women"
	event=cleanEventName(event)
	distance=event.split(" ")[0]
	stroke=strokeToLongName(event.split(" ")[1])
	seniors=0
	for swim in result:
		data=swim.split('\t')
		print(data)
		if re.search("Relay",data[6]) or re.search("Diving",data[6]):
			break
		if not data[0]=='--' and not(Score_Dive_Prelims and int(data[0])<=8 and prelim):
			ID=data[4]+"|"+data[2]+"|"+data[5]+"|"+data[3]
			lastID=ID
			lastIDR=ID
			if ID not in individs:
				individs[ID]=[0,"",0]
			if int(data[0])<(len(individual_points)-1):
				if lastSwim[0]==data[0]:
						individs[ID][0]=individs[ID][0]+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
						individs[lastID][0]=individs[lastID][0]-lastPoints+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
						lastPoints=(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
				else:
						individs[ID][0]=individs[ID][0]+individual_points[int(data[0])]
						lastPoints=individual_points[int(data[0])]
				if returning:
					if int(lastSwimR[0])-seniors==(int(data[0])-seniors):
							individs[ID][2]=individs[ID][2]+(individual_points[int((int(data[0])-seniors))]+individual_points[(int((int(data[0])-seniors))+1)])/2.0
							individs[lastIDR][2]=individs[lastID][2]-lastPointsR+(individual_points[int((int(data[0])-seniors))]+individual_points[(int((int(data[0])-seniors))+1)])/2.0
							lastPointsR=(individual_points[int((int(data[0])-seniors))]+individual_points[(int((int(data[0])-seniors))+1)])/2.0
					else:
							individs[ID][2]=individs[ID][2]+individual_points[int((int(data[0])-seniors))]
							lastPointsR=individual_points[int((int(data[0])-seniors))]
			time=float(data[7].rstrip())
			if returning:
				if data[3]=="SR" or data[2]=="Katie Ledecky":
					seniors+=1
				power=(int(data[0])-seniors)
				if is_a_stroke(stroke):
					time=toOutTime(time)
			else:
				if is_a_stroke(stroke) and not(distance=="100" and stroke=="Individual+Medley"):
					url="http://swimulator.herokuapp.com/powerscoreJSON?event="+distance+"+Yard+"+stroke+"&hundredths="+str(int(time*100))+"&gender="+gender+"&division=D"+str(division)
					t=requests.get(url)
					power=str(int(t.json()))
					#power=""
					time=toOutTime(time)
				else:
					power=""
			if topN==0:
				individs[ID][1]=individs[ID][1]+cleanEventName(event)+"|"+data[0]+"|"+str(time)+"|"+str(power)+"|"
			else:
				if int(data[0])<=topN:
					individs[ID][1]=individs[ID][1]+cleanEventName(event)+"|"+data[0]+"|"+str(time)+"|"+str(power)+"|"
		if returning:
			if data[3]!="SR" and data[2]!="Katie Ledecky":
				lastSwimR=data
		lastSwim=data
	return individs

def count_upDown(result,counts,countsevent,event,score_thru):
	
	for swim in result:
		data=swim.split('\t')
		lastSwim=[0,"","","","","","",""]
		#protection against scores at the bottom of the page. 
		#if re.search("Relay",data[6]):
		#	break
		if not data[0]=='--' and int(data[0])<int(lastSwim[0]):
			break
		if not data[0]=='--':
			if int(data[0])<=score_thru:
				heat=(int(data[0])-1)//8
				teamID=data[4]+" "+data[5]
				if teamID not in counts:
					counts[teamID]="0/0/0"
				cnt=re.split("\|",counts[teamID])
				cou=re.split("\t",cnt[0])
				if len(cnt)<=countsevent:
					teamUpDownEvent=[0,0,0]
				else:
					teamUpDownEvent=cnt[countsevent].split("/")
				if not re.search("Relay",data[6]):
					teamUpDown=cou[0].split("/")
				else:
					if len(cou)>1:
						teamUpDown=cou[1].split("/")
					else:
						teamUpDown=[0,0,0]
						
				teamUpDown[heat]=int(teamUpDown[heat])+1
				teamUpDownEvent[heat]=int(teamUpDownEvent[heat])+1
				if len(cou)>1 or re.search("Relay",data[6]):
					if re.search("Relay",data[6]):
						temp=cou[0].split("/")
						counts[teamID]=temp[0]+"/"+temp[1]+"/"+temp[2]+"\t"+str(teamUpDown[0])+"/"+str(teamUpDown[1])+"/"+str(teamUpDown[2])
					else:
						temp=cou[1].split("/")
						counts[teamID]=str(teamUpDown[0])+"/"+str(teamUpDown[1])+"/"+str(teamUpDown[2])+"\t"+temp[0]+"/"+temp[1]+"/"+temp[2]
				else:
					counts[teamID]=str(teamUpDown[0])+"/"+str(teamUpDown[1])+"/"+str(teamUpDown[2])
				coun=1
				while coun<countsevent:
						if len(cnt)<=coun and ((re.search("Women",teamID) and data[5]=="Women") or (re.search("Men",teamID) and data[5]=="Men")):
								counts[teamID]=counts[teamID]+"|"+"0/0/0"
						else:
								counts[teamID]=counts[teamID]+"|"+cnt[coun]
						coun=coun+1
				counts[teamID]=counts[teamID]+"|"+str(teamUpDownEvent[0])+"/"+str(teamUpDownEvent[1])+"/"+str(teamUpDownEvent[2])
		lastSwim=data
	return counts
		
#accounts for ties. Does not check for 3 way and above ties.
def score_event(result,score,prelim,score_thru,Score_Dive_Prelims):
	if score_thru==16:
		individual_points=[0,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0]
		relay_points=[0,40,34,32,30,28,26,24,22,18,14,12,10,8,6,4,2,0]
	elif score_thru==24:
		individual_points=[0,32,28,27,26,25,24,23,22,20,17,16,15,14,13,12,11,9,7,6,5,4,3,2,1,0]
		relay_points=[0,64,56,54,52,50,48,46,44,40,34,32,30,28,26,24,22,18,14,12,10,8,6,4,2,0]
		relay_points=[0,64,56,54,52,50,48,46,44,42,34,32,30,28,26,24,22,18,14,12,10,8,6,4,2,0]
		#special NESCAC Case: double check that this is right for future uses of it. They think they're cute
		#relay_points=relay_points=[0,64,56,54,52,50,48,46,44,42,40,38,26,22,20,18,16,14,12,10,8,6,4,0]
	elif score_thru==18:
		individual_points=[0,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0]
		relay_points=[0,44,38,36,34,32,30,28,26,24,20,16,14,12,10,8,6,4,2,0]
	elif score_thru==27:
		individual_points=[0,35,31,30,29,28,27,26,25,24,22,19,18,17,16,15,14,13,12,10,8,7,6,5,4,3,2,1,0]		
		relay_points=[0,70,62,60,58,56,54,52,50,48,44,38,36,34,32,30,28,26,24,20,16,14,12,10,8,6,4,2,0]
	elif score_thru==8:
		individual_points=[0,9,7,6,5,4,3,2,1,0]
		relay_points=[0,18,14,12,10,8,6,4,2,0]
	elif score_thru==5:
		individual_points=[0,9,4,3,2,1,0,0,0,0,0,0]
		relay_points=[0,11,4,2,0,0,0,0,0,0]
	lastSwim=[0,"","","","","","",""]
	for swim in result:
		data=swim.split('\t')
		#protection against scores at the bottom of the page. 
		if not data[0]=='--' and int(data[0])<int(lastSwim[0]):
			break
		if not data[0]=='--' and not(Score_Dive_Prelims and int(data[0])<=8 and prelim):
			if int(data[0])<(len(individual_points)-1):
				if "-" in data[4]:
					teamID=data[4][:data[4].find("-")]+" "+data[5]
				else:
					teamID=data[4]+" "+data[5]
				if teamID not in score:
					score[teamID]=0.0
				if re.search("Relay",data[6]):
					if lastSwim[0]==data[0]:
						score[teamID]=(score[teamID])+(relay_points[int(data[0])]+relay_points[(int(data[0])+1)])/2.0
						if "-" in lastSwim[4]:
							lastTeamID=lastSwim[4][:lastSwim[4].find("-")]+" "+lastSwim[5]
						else:
							lastTeamID=lastSwim[4]+" "+lastSwim[5]
						score[lastTeamID]=(score[lastTeamID])+(relay_points[int(data[0])]+relay_points[(int(data[0])+1)])/2-relay_points[int(data[0])]
					else:
						score[teamID]=(score[teamID])+relay_points[int(data[0])]
				else:
					if lastSwim[0]==data[0]:
						score[teamID]=(score[teamID])+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0
						if "-" in lastSwim[4]:
							lastTeamID=lastSwim[4][:lastSwim[4].find("-")]+" "+lastSwim[5]
						else:
							lastTeamID=lastSwim[4]+" "+lastSwim[5]
						score[lastTeamID]=(score[lastTeamID])+(individual_points[int(data[0])]+individual_points[(int(data[0])+1)])/2.0-individual_points[int(data[0])]
					else:
						score[teamID]=(score[teamID])+individual_points[int(data[0])]
		#not 100% on this if statement. the goal is to make sure the break above catches the case where someone has a scoring place in prelims that they scratch in finals, bu the lower place is listed below and there was a DQ in the final above
		if not data[0]=='--':
			lastSwim=data
	return score

#convers to a time in seconds
def toTime(time):
	if time[0]=="X" or time[0]=="x":
		time=time[1:]
	if re.match(".*:.*",time) == None:
		return float(time)
	return float(re.split(":",time)[0])*60 +float(re.split(":",time)[1])
#converts time in seconds to MM:SS.SS format
def toOutTime(time):
	if time<60:
		return str(time)
	m=int(divmod(time,60)[0])
	s=time-m*60
	sec=s*100
	if s<10:
		if divmod(sec,10)[0]==sec/10:
			time=str(m)+":0"+str(round(s,2))+"0"
		else:
			time=str(m)+":0"+str(round(s,2))
	else:
		if divmod(sec,10)[0]==sec/10:
			time=str(m)+":"+str(round(s,2))+"0"
		else:
			time=str(m)+":"+str(round(s,2))
	return time

def lineType(line):
	if re.match("Event.*",line):
		return "  Event"
	if re.match("\s*\d\d? \D+.*",line) or re.match("\s*-- \D+.*",line):
		 #if re.search("DQ",line) == None:
		return "Swim"
	if re.match("\s\s?\d\d?\D*\d\:\d\d\.\d\d\s*",line):
		return "Relay"
	if re.match("\s+\d\).*\d\).*",line):
		return "Relay Names"
	if re.match("\s*\Z",line):
		return "Empty"
	if re.match('[\s\d\)\(\.: r\+-]+\Z',line):
		return "Splits"
	if re.match('\d+-Yard .*',line):
		return 'Event'
	if re.match('\d+-Meter .*',line):
		return 'Event'
	if re.match('\d+-Rankings .*',line):
		return 'Scores'
	if re.match('\s*\d+ .*\d+\s*\Z',line):
		return 'Swim'
	else:
		return "Unknown"
		
'''
real parser
'''		
def parseTimes(f):
	swimDatabase=[]
	eventType = ""
	ses = requests.session()
	r = requests.get(f)
	f=r.text
	#make sure it's a completed event
	if "Print Result" not in f:
		return []
	f = re.sub("<.*?>", " ", f)
	f=f.split('\n')
	line = f[0]
	nextLine=False
	count=1
	while not count>=len(f)-1:
		if not nextLine: #makes sure the next line has not already been read
			line = f[count]
			count=count+1
		else:
			nextLine=False
		if lineType(line)=='Space':
			line=f[count]
			count=count+1
			continue
		#Determines the Event
		if re.match("  Event.*",line):
			event = ""
			eventArray = re.split("\s+",line.rstrip())
			#print(eventArray)
			gender = eventArray[3]
			for i in range(3,len(eventArray)):
				event += eventArray[i] + " "
			eventType = eventArray[-1]
			if eventType != "Diving" and eventType != "Relay":
				eventType = "Individual"
		if re.match('\s*Name.*',line) or re.match('\s*School',line) or re.match('\s*Preliminaries\s*',line):
			if re.search('Finals',line):
				finals=True
			else:
				finals=False
			#this might cause issues should probably put in a seperate thing for time trials if they are in the same session as something meaningful
			if re.search('Prelim',line) or re.search('Time Trial',line):
				prelims=True
			else:
				prelims=False
			
		#Finds individual events
		if eventType == "Individual" or eventType == "Diving":
			if re.match("\s*\d\d? \D+.*",line) or (re.match("\s*-- \D+.*",line) and re.search("DQ|NS|SCR",line) == None):
				split=re.split("\s\s+",line)
				while '' in split:
					split.remove('')
				#commented out because I don't know what this does and it's breaking things. seems to work without it. if something mysteriously goes wrong check here first
				#if re.findall(" ?\d?\d?-?-? (\D+ \S+).*",split[0])==[]:
				#	continue
				#name=re.findall(" ?\d?\d?-?-? (\D+ \S+).*",split[0])[0].rstrip()
				name=split[1]
				place=split[0].replace(" ","")
				if re.match("\d+ .*",split[2]):
					(year,team)=re.match("(\d+) (.*)",split[2]).group(1,2)
				elif re.match("FR.*|SO.*|JR.*|SR.*|FY.*",split[2]):
					(year,team)=re.match("(\w\w) (.*)",split[2]).group(1,2)
				else:
					year=''
					team=split[2]
				time=0
				if re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)==[]:
					continue
				if re.findall("x\d?\d?:?\d?\d\d.\d\d|X\d?\d?:?\d?\d\d.\d\d",line)!=[]:
					continue
				else:
					if finals:
						time=toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[-1])
					#else:
						#continue can skip prelims results if desi red
						#continue
					if prelims:
						prelimsTime=toTime(re.findall("x?X?\d?\d?:?\d?\d\d.\d\d",line)[-1])
				#team=adjustTeamName(team)
				#name=fixName(name,team,gender)
				if team==None:
					continue
				team=fixTeamName(team)
				if prelims:
					swimDatabase.append(place+"\t" + "\t" + name + "\t" + year + "\t" + team + "\t" + gender + "\t" + event.strip() + " - Prelims\t" + str(prelimsTime) + "\n")
				else:
					swimDatabase.append(place+"\t" + "\t" + name + "\t" + year + "\t" + team + "\t" + gender + "\t" + event.strip() + "\t" + str(time) + "\n")


		#Relays, team names different
		elif eventType == "Relay":
			if re.match("\s\s?\d\d?\D*\d\:\d\d\.\d\d\s*",line) or re.match("\s*--\D*\d\:\d\d\.\d\d\s*",line) and re.search("DQ|NS",line) == None:
				resultArray = re.split("\s+",line)
				#print(resultArray)
				place=resultArray[1].replace(" ","")
				#print place
				teamName = ""
				index = 2
				while re.match("x?X?\d.*", resultArray[index]) == None:
					teamName += resultArray[index] + " "
					index += 1
				time = re.findall("\d+:\d\d.\d\d",line)[-1]
				#teamName = adjustTeamName(teamName)
				#this checks if there is an A-B-C relay denominator in 'A' format and strips it (this was the case on the original test result)
				#the above can sometimes include a trailing "NT " after the A-B-C delimiter. this is also stripped
				if re.match("\w*\w",teamName):
					if re.search("'",teamName):
						if teamName[len(teamName)-3:]=="NT ":
							teamName=teamName[:-8]
						else:
							###if relay team names start acting funny, change this to a -5
							teamName=teamName[:-5]
					else:
						if teamName[len(teamName)-3:]=="NT ":
							teamName=teamName[:-5]
						else:
							teamName=teamName[:-1]
				if teamName==None:
					continue
				teamName=fixTeamName(teamName)
				swimDatabase.append(place+"\t" + "\t\t\t" + teamName + "\t" + gender + "\t" + event + "\t" + str(toTime(time)) + "\n")
					
	#print(swimDatabase)
	return swimDatabase

def fixTeamName(name):
	teams={"MICH":"Michigan",
	"OSU":"Oregon State",
	"Ind":"Indiana",
	"MINN":"Minnesota",
	"WISC":"Wisconsin",
	"IU":"Indiana",
	"NU":"Northwestern",
	"PUR":"Purdue",
	"IOWA":"Iowa",
	"RUT":"Rutgers",
	"PSU":"Penn State",
	"NEB":"Nebraska",
	"MSU":"Michigan State",
	"ILL":"Illinois",
	"R IOWA":"Iowa",
	"FGCU-FL":"Florida Gulf",
	"U.S. Navy ":"U.S. Navy",
	"Army West Point ":"Army West Point",
	"Bucknell ":"Bucknell",
	"BU Swimming ":"BU Swimming",
	"Loyola (Md) ":"Loyola (Md)",
	"Lehigh ":"Lehigh",
	"American ":"American",
	"LAFA ":"LAFA",
	"Holy Cross ":"Holy Cross",
	"Colgate ":"Colgate",
        "Ohio St":"Ohio State",
        "Penn St":"Penn State",
        "Michigan St":"Michigan State"
	}
	try:
		if "-" in name:
			name=name[:name.find("-")]
		name=teams[name]
		return name
	except:
		if "-" in name:
			return name[:name.find("-")]
		else:
			return name

print(URL)
scoreLiveResult(URL=URL,Sessions=Sessions,Score_Thru=Score_Thru,Division=Division,ScoreSession=ScoreSession,UpDown=UpDown,scoreProgression=scoreProgression,eventScores=eventScores,yearBreakdown=yearBreakdown,individualBreakdown=individualBreakdown,placeCount=placeCount,Score_Dive_Prelims=Score_Dive_Prelims,exclude_all_prelims=exclude_all_prelims,htmlOutput=htmlOutput,printNumbered=printNumbered,returning=returning,topX=topX,topN=topN)	
