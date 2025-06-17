import pandas as pd

data = pd.read_csv('./data/listHeroFix.csv')
df = pd.read_csv('./data/fix.csv')

index_to_lane = {
        0: 'Jungler',
        1: 'Mid Laner',
        2: 'Gold Laner',
        3: 'Exp Lane',
        4: 'Roam'
    }

def getHeroData(hero_name):
    heroData = data[data['Hero Name'].str.lower() == hero_name.lower()]
    if not heroData.empty:
        return heroData.iloc[0]
    else:
        return None

def matchingHeroLane(dataHero, idx):
    unmatchedLane = 0

    if isinstance(dataHero, dict):
        dataHero = pd.Series(dataHero)

    heroName = dataHero['Hero Name']

    if heroName is not None:
        # Ambil Recommended Lane dan Second Lane dari df
        hero_row = df[df['Hero Name'] == heroName]
        if not hero_row.empty:
            recLane = hero_row['Recommended Lane'].iloc[0]
            secLane = hero_row['Second Lane'].iloc[0]
            # Ambil lane yang sesuai dengan idx
            target_lane = index_to_lane.get(idx)
            
            # Periksa apakah lane sesuai
            if recLane != target_lane and (pd.isna(secLane) or secLane != target_lane):
                unmatchedLane = 1
        else:
            print(f"Hero {heroName} tidak ditemukan di df.")
            unmatchedLane = 1  # Anggap tidak cocok jika hero tidak ditemukan
    else:
        print("dataHero is empty")
        unmatchedLane = 1

    return unmatchedLane

def calculateTeamStrength(team):
    totalStrength = 0
    hero_data = {}
    
    for i, hero in enumerate(team):
        data = getHeroData(hero)
        
        unmatchedLane = matchingHeroLane(data, i)

        if data is not None:
            totalStrength += data['Strength Rating (%)']
            hero_data[hero] = data  
        else:
            print(f"Hero {hero} tidak ditemukan dalam dataset.")

    return totalStrength, hero_data, unmatchedLane

def calculateWinPercentage(team1, team2):
    team1Strength, team1_data, unmatchedLane1 = calculateTeamStrength(team1)
    team2Strength, team2_data, unmatchedLane2 = calculateTeamStrength(team2)
    
    totalStrength = team1Strength + team2Strength
    if totalStrength == 0:  # Hindari pembagian dengan nol
        return 50.0, 50.0, team1_data, team2_data

    team1Base = (team1Strength / totalStrength) * 100
    team2Base = (team2Strength / totalStrength) * 100
    
    # Terapkan penalti dari lane yang tidak cocok (anggap 5% per mismatch)
    penalty_per_unmatched = 5
    team1Penalty = unmatchedLane1 * penalty_per_unmatched
    team2Penalty = unmatchedLane2 * penalty_per_unmatched

    team1WinPercentage = max(team1Base - team1Penalty, 0)
    team2WinPercentage = max(team2Base - team2Penalty, 0)

    # Normalisasi ulang agar total tetap 100%
    total = team1WinPercentage + team2WinPercentage
    if total > 0:
        team1WinPercentage = (team1WinPercentage / total) * 100
        team2WinPercentage = (team2WinPercentage / total) * 100
    else:
        team1WinPercentage = 50.0
        team2WinPercentage = 50.0

    return team1WinPercentage, team2WinPercentage, team1_data, team2_data

def generateMatchData(team1, team2, team1_data, team2_data):
    team1WinPercentage, team2WinPercentage, _, _ = calculateWinPercentage(team1, team2)
    
    # Fitur numerik yang akan dihitung rata-ratanya per tim
    numeric_features = [
        'Win Rate (%)', 'Popularity (%)', 'Pick rate (%)', 'Ban Rate (%)', 'Scaling Rating', 'Cooldown Rating',
        'Item Dependency Rating', 'Mobility Rating', 'Crowd Control Rating',
        'Base Stats Growth Rating', 'Ultimate Impact Rating_All Game Phases',
        'Ultimate Impact Rating_Early Game', 'Ultimate Impact Rating_Late Game',
        'Ultimate Impact Rating_Mid Game', 'Ultimate Impact Rating_Support',
        'Strength Rating (%)'
    ]
    
    def calculate_team_average(team_data, team):
        df_team = pd.DataFrame([team_data[hero] for hero in team])
        avg_features = df_team[numeric_features].mean().to_dict()
        avg_features = {f'{team_prefix}_{k}': v for k, v in avg_features.items()}
        return avg_features

    team_prefix = "team1"
    team1_avg_features = calculate_team_average(team1_data, team1)
    
    team_prefix = "team2"
    team2_avg_features = calculate_team_average(team2_data, team2)

    match_data = {
        **team1_avg_features,
        **team2_avg_features,
        'Persentase_Kemenangan_Tim_1': team1WinPercentage,
        'Persentase_Kemenangan_Tim_2': team2WinPercentage
    }
    
    return match_data