import statsapi
import argparse
import csv
import constants

def build_analysis(args):
	finalObj = {
		"players": {},
		"homeRuns": {},
		"triples": {},
		"attendance": {},
		"gameTimes": {}
	}

	with open(args.file) as csvfile:
		reader = csv.reader(csvfile)
		games = 0
		for row in reader:
			games += 1
			gameId = get_game_id(row)
			add_game(gameId, finalObj)
		process_final(finalObj, games)

def get_game_id(row):
	home_team = row[0]
	date = row[1]
	team_code = constants.teamCodes[home_team]
	games = statsapi.schedule(date=date, team=team_code)
	if len(games) == 1:
		return games[0]["game_id"]
	else:
		if len(row) > 2:
			gameNum = row[2]
			for game in games:
				if game["game_num"] == gameNum:
					return game["game_id"]
		else:
			raise Exception("Doubleheaders must have a third column specifying which game was attended")
	raise Exception(f"No game found for {team_code} on {date}")

def add_game(gameId, finalObj):
	boxscore = statsapi.boxscore_data(gameId)
	for player in boxscore["home"]["players"]:
		playerObj = boxscore["home"]["players"][player]
		process_player(playerObj, finalObj)
	for player in boxscore["away"]["players"]:
		playerObj = boxscore["away"]["players"][player]
		process_player(playerObj, finalObj)
	finalObj["attendance"][gameId] = int(get_field(boxscore, "Att").replace(",", ""))
	time = get_field(boxscore, "T").split(":")
	finalObj["gameTimes"][gameId] = 60 * int(time[0]) + int(time[1])
	

def process_player(playerObj, finalObj):
	id = playerObj["person"]["id"]
	played = playerObj["stats"]["batting"] != {} or playerObj["stats"]["pitching"]
	homeRuns = playerObj["stats"]["batting"]["homeRuns"] if "homeRuns" in playerObj["stats"]["batting"] else 0
	triples = playerObj["stats"]["batting"]["triples"] if "triples" in playerObj["stats"]["batting"] else 0
	
	if played:
		if id in finalObj["players"]:
			finalObj["players"][id] += 1
		else:
			finalObj["players"][id] = 1

	if homeRuns > 0:
		if id in finalObj["homeRuns"]:
			finalObj["homeRuns"][id] += homeRuns
		else:
			finalObj["homeRuns"][id] = homeRuns

	if triples > 0:
		if id in finalObj["triples"]:
			finalObj["triples"][id] += triples
		else:
			finalObj["triples"][id] = triples

def get_field(boxscore, field):
	for item in boxscore["gameBoxInfo"]:
		if item["label"] == field:
			return item["value"][:-1]
	return ""

def process_final(finalObj, games):
	print("SUMMARY:\n--------------------------------------\n")
	print(f'Total players seen: {len(finalObj["players"])}')
	process_stat(finalObj, "players", "Most seen players: ", get_player_name)
	print(f'\nYou\'ve seen {len(finalObj["homeRuns"])} players hit {sum(finalObj["homeRuns"].values())} home runs')
	process_stat(finalObj, "homeRuns", "Biggest power hitters: ", get_player_name)
	print(f'\nYou\'ve seen {len(finalObj["triples"])} players hit {sum(finalObj["triples"].values())} triples')
	process_stat(finalObj, "triples", "Fastest around the basepaths: ", get_player_name)

	print(f'\nYou\'ve seen {games} games over the years!')
	process_stat(finalObj, "attendance", "Most attended games: ", get_game_info)
	process_stat(finalObj, "attendance", "Least attended games: ", get_game_info, False)
	process_stat(finalObj, "gameTimes", "Longest games attended: ", get_game_info)
	process_stat(finalObj, "gameTimes", "Shortest games attended: ", get_game_info, False)
	

def process_stat(finalObj, stat, label, process_item, most=True):
	top = sorted(finalObj[stat].items(), reverse=most)
	final_freq = top[4][1] if len(top) >= 5 else 0
	print(label)
	for item in top:
		if item[1] < final_freq:
			break
		process_item(item, stat == "gameTimes")

def get_player_name(player, _):
	playerObj = statsapi.player_stat_data(player[0])
	print(f"{playerObj['first_name']} {playerObj['last_name']}: {player[1]}")

def get_game_info(game, isTime):
	boxscore = statsapi.boxscore_data(game[0])
	dateString = boxscore["gameBoxInfo"][-1]["label"]
	away = boxscore["teamInfo"]["away"]["abbreviation"]
	home = boxscore["teamInfo"]["home"]["abbreviation"]
	value = game[1]
	if isTime:
		hour = int(game[1]/60)
		minute = game[1] - 60 * hour
		value = f"{hour}:{minute}"
	print(f"{dateString} {away} vs. {home}: {value}")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="MLB Analyzer")
	parser.add_argument('-f', '--file', help="CSV of Attendance Data", required=True)
	parser.add_argument('-y', '--year', nargs='+', default=[], help="Years Highlight (not yet implemented)")
	args = parser.parse_args()
	build_analysis(args)