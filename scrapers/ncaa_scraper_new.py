import requests, json, re, argparse
from datetime import datetime
from bin.models.clubdb import getdb
from bin.models.swimstaging import Swimstaging
import hashlib

db = getdb()

# converts to apyth time in seconds
def toTime(time):
	m = re.match('x?((\d+):)?(\d+\.\d+)r?', time)
	if not m:
		return m
	if not m.group(2):
		return float(m.group(3))
	min, sec = float(m.group(2)), float(m.group(3))
	return min * 60 + sec

class usaswimming:
	gender_ids = {'Women': 'Female', 'Men': 'Male'}
	gender_ids_out = {v:k for k,v in gender_ids.items()}

	event_ids = {
		"50 Free": "50 FR SCY",
		"100 Free": "100 FR SCY",
		"200 Free": "200 FR SCY",
		"500 Free": "500 FR SCY",
		"1000 Free": "1000 FR SCY",
		"1650 Free": "1650 FR SCY",
		#"2000 FR SCY":7,
		#"3000 FR SCY":8,
		#"4000 FR SCY":9,
		#"5000 FR SCY":10,
		#"50 BK SCY":11,
		"100 Back": "100 BK SCY",
		"200 Back": "200 BK SCY",
		#"50 BR SCY":14,
		"100 Breast": "100 BR SCY",
		"200 Breast": "200 BR SCY",
		#"50 FL SCY":17,
		"100 Fly": "100 FL SCY",
		"200 Fly": "200 FL SCY",
		#"100 IM SCY":20,
		"200 IM": "200 IM SCY",
		"400 IM": "400 IM SCY",
		"200 Free Relay": "200 FR-R SCY",
		"400 Free Relay": "400 FR-R SCY",
		"800 Free Relay": "800 FR-R SCY",
		"200 Medley Relay": "200 MED-R SCY",
		"400 Medley Relay": "400 MED-R SCY"}
	event_ids_out = {v:k for k,v in event_ids.items()}

	division_ids = {'D1': 'NCAA Div I', 'D2': 'NCAA Div II', 'D3': 'NCAA Div III'}
	division_ids_out = {v:k for k,v in division_ids.items()}

	season_ids = {2025: '2024-2025', 2024: '2023-2024', 2023: '2022-2023', 2022: '2021-2022', 2021: '2020-201', 2020: '2019-2020'}
	season_ids_out = {v:k for k,v in season_ids.items()}

	with open('scrapers/conferences.json') as f:
		conferences = json.load(f)
	
	def __init__(self):
		self.deviceId = 3408487800
		self.session = requests.session()
		headers = {'UserAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
		#response = self.session.get('https://data.usaswimming.org/datahub/ncaa/divI/timeseventrank', headers=headers)
		response = self.session.get('https://data.usaswimming.org/datahub/usas/timeseventrank', headers=headers)
		request_id = self.get_security_info()
		self.session_id = request_id * 13  # for security
		self.token = self.get_auth() # 1157000
		
	def get_auth(self):
		request_json = {
			"sessionId": self.session_id,
			"deviceId": self.deviceId,
			"hostId": "MzkzMjE5Mzg5",
			"requestUrl": "/datahub/ncaa/divI/timeseventrank"
		}
		response = self.session.post('https://securityapi.usaswimming.org/security/DataHubAuth/GetSisenseAuthToken', json=request_json)
		#print(response.json())
		return response.json()['accessToken']

	def get_security_info(self):
		request_json = {
			"toxonomies": [
				"TopMenu",
				"Footer",
				"MainMenu"
			],
			"scope": "Project",
			"uIProjectName": "times-microsite-ui",
			"bustCache": False,
			"appName": "Data",
			"deviceId": self.deviceId,
			"hostId": "MzkzMjE5Mzg5"
		}
		response = self.session.post('https://securityapi.usaswimming.org/security/Auth/GetSecurityInfoForToken', json=request_json)
		#print(response.json())
		return int(response.json()['requestId'])

	def get_filter(self, dim, value):
		if dim == '[OrgUnit.Division]':
			filter = {'equals': value}
		else:
			filter = {'members': [value]}
		return {
			"jaql": {
				"title": "TypeName",
				"dim": dim,
				"datatype": "text",
				"filter": filter
			},
			"panel": "scope"
		}

	def get_usaswimming_times(self):
		baseURL = 'https://usaswimming.sisense.com/api/datasources/USA%20Swimming%20Times%20Elasticube/jaql?trc=sdk-ui-1.23.0'

	def c(self, season='2024-2025', div='NCAA Div I', event="100 FR SCY", gender="Male", conf="Pacific 12"):
		print(season, div, gender, event, conf)
		headers = {'Authorization': f'Bearer {self.token}'}
		baseURL = "https://usaswimming.sisense.com/api/datasources/NCAA%20Times/jaql?trc=sdk-ui-1.11.0"

		with open('scrapers/event_rank.json') as f:
			request_json = json.load(f)

		# append filters to base JSON
		request_json['metadata'].append(self.get_filter('[SeasonCalendar.NCAASeason]', season))
		request_json['metadata'].append(self.get_filter('[OrgUnit.Division]', div))
		request_json['metadata'].append(self.get_filter('[SwimEvent.EventCode]', event))
		request_json['metadata'].append(self.get_filter('[EventCompetitionCategory.TypeName]', gender))
		request_json['metadata'].append(self.get_filter('[OrgUnit.ConferenceName]', conf))
		#request_json['metadata'].append(get_filter('[NcaaSwimTime.SeasonBest]', "true"))
		#request_json['metadata'].append(get_filter('[NcaaSwimTime.Ineligible]', "false"))
		#request_json['metadata'].append(get_filter('[StandardType.StandardType]', "ns"))
		
		#print(request_json)

		session = requests.Session()
		response = session.post(d1baseURL, json=request_json, headers=headers)

		division = self.division_ids_out[div]
		genderOut = self.gender_ids_out[gender]
		swims = {}
		date_format = '%Y-%m-%dT%H:%M:%S'
		if 'values' not in response.json():
			return
		for swim in response.json()['values']:
			if 'c' in swim[2]['data']: # toss converted times
				continue
			Name = swim[0]['data']
			Year = swim[1]['data']
			SwimTime = toTime(swim[2]['data'])
			#SwimTimeAdj = swim[3]['data']
			Event = self.event_ids_out[swim[4]['data']]
			Team = swim[5]['data']
			Meet = swim[6]['data']
			SwimDate = datetime.strptime(swim[7]['data'], date_format).date()
			#TimeStandard = swim[8]['data']
			#SwimEventKey = swim[9]['data']
			#EventCompetitionCategoryKey = swim[10]['data']
			NCAASeason = self.season_ids_out[swim[11]['data']]
			#SwimTimeSeconds = swim[12]['data']
			#PersonKey = swim[13]['data']
			Conference = swim[14]['data']
			#Rank = swim[15]['data']

			Relay = False
			if 'Relay' in Event:
				Name = Team + ' Relay'
				Relay = True

			unique_str = Name + Event + str(SwimTime) + str(SwimDate)
			key = int(hashlib.md5(unique_str.encode('utf-8')).hexdigest(), 16) % (10**16)

			#print(Name, Year, SwimTime, Event, Team, Meet, SwimDate, NCAASeason, Conference, key)
			
			if key not in swims:
				swims[key] = {'meet': Meet, 'date': SwimDate, 'season': NCAASeason, 'name': Name,
							'team': Team, 'gender': genderOut, 'event': Event, 'time': SwimTime, 'division': division,
							'relay': Relay, 'year': Year, 'conference': Conference, 'key': key, 'date_loaded': datetime.now()}
		
		print(len(swims))
		Swimstaging.insert_many(swims.values()).on_conflict_ignore().execute()

def parse_conferences():
	with open('conferences_raw.json') as f:
		conf_raw = json.load(f)

	conf_dict = {}
	for conf in conf_raw:
		conf_name = conf[0]["data"]
		division = conf[1]["data"]
		
		if division not in conf_dict:
			conf_dict[division] = []
		conf_dict[division].append(conf_name)
	
	with open('conferences.json', 'w+') as f:
		json.dump(conf_dict, f)

def main(season=2025):
	swim_connection = usaswimming()
	#swim_connection.get_ncaa_times(div='NCAA Div I', gender='Female', event='200 FR SCY', conf='Pacific 12')

	season = usaswimming.season_ids[season]
	for division in usaswimming.division_ids_out:
		for gender in usaswimming.gender_ids_out:
			for event in usaswimming.event_ids_out:
				for conference in usaswimming.conferences[division]:
					swim_connection.get_ncaa_times(season=season, div=division, gender=gender, event=event, conf=conference)
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--season', help='season to use. Default current', type=int, default=2025)
	args = parser.parse_args()
	
	main(season=args.season)

