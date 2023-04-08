import streamlit as st
import pandas as pd
import numpy as np
import re

from itertools import product
import pickle

from odds_helper import odds_to_prob, prob_to_odds
from xfl_data import urls, divs

wk = 7 # Change this next week
sims = 500

df_results = pd.read_csv(f"results-week{wk}.csv")

def process_url(url):
    s = re.search("\-(?P<away_team>[A-Z]*)\-at\-(?P<home_team>[A-Z]*)", url)
    return {"away_team": s["away_team"], "home_team": s["home_team"]}

unplayed = []
for w in range(wk+1, 11):
    for url in urls[w]:
        dct = {"week": w}
        dct.update(process_url(url))
        unplayed.append(dct)
unplayed_df = pd.DataFrame(unplayed)

north_teams = {t: "North" for t in divs["North"]}
south_teams = {t: "South" for t in divs["South"]}
team_divs = north_teams.copy()
team_divs.update(south_teams)

teams = sorted(north_teams.keys()) + sorted(south_teams.keys())

df_spread_prob = pd.read_csv("spread_probs.csv")
ser_prob = df_spread_prob.set_index("Spread", drop=True)

def spread_to_prob(s):
    if isinstance(s, str):
        s = float(s)
    i = np.argmin(np.abs(ser_prob.index - s))
    return ser_prob.iloc[i].item()

rng = np.random.default_rng()

blank = {
    "wins": 0,
    "losses": 0,
    "div": None,
    "points_scored": 0,
    "points_allowed": 0,
    "div_wins": 0,
    "div_losses": 0,
}

def make_standings(df):
    standings = pd.DataFrame({t: blank.copy() for t in teams}).T
    
    for c in ["wins", "losses", "points_scored", "points_allowed", "div_wins", "div_losses"]:
        standings[c] = standings[c].astype(int)

    for k in divs.keys():
        standings.loc[divs[k], "div"] = k

    standings["teams_beaten"] = [[] for _ in range(8)]

    for _, row in df.iterrows():
        h = row["home_team"]
        a = row["away_team"]
        if row["home_wins"]:
            winner, loser = h, a
        else:
            winner, loser = a, h
        standings.loc[winner, "wins"] += 1
        standings.loc[loser, "losses"] += 1
        standings.loc[winner, "teams_beaten"].append(loser)
        if row["div_game"]:
            standings.loc[winner, "div_wins"] += 1
            standings.loc[loser, "div_losses"] += 1
        standings.loc[h, "points_scored"] += row["home_score"]
        standings.loc[h, "points_allowed"] += row["away_score"]
        standings.loc[a, "points_scored"] += row["away_score"]
        standings.loc[a, "points_allowed"] += row["home_score"]

    standings["pct"] = standings["wins"]/(standings["wins"]+standings["losses"])
    standings["div_pct"] = standings["div_wins"]/(standings["div_wins"]+standings["div_losses"])
    standings = standings.sort_values(["div", "pct", "div_pct"], ascending=[True, False, False])
    return standings[(standings.wins > 0) | (standings.losses > 0)].copy()

st.title('XFL Championship Simulator')


st.header("Power ratings")

st.markdown(
"""Enter your power rating for each team and your homefield advantage for each team.  Use a positive number to indicate a stronger team or a better home field advantage.    Use a negative number to indicate a weaker team or a home field disadvantage.""")

def make_pr(team):
    return st.text_input(f"{team} power rating:")

def make_hfa(team):
    return st.text_input(f"{team} home-field advantage:", value=1)

col1, _, col2, _2 = st.columns([5,2, 5, 3])

pr_dict = {}
hfa_dict = {}

with col1:
    for team in teams:
        res = make_pr(team)
        try:
            pr_dict[team] = float(res)
        except ValueError:
            pass

with col2:
    for team in teams:
        res = make_hfa(team)
        try:
            hfa_dict[team] = float(res)
        except ValueError:
            pass

st.header("Simulate the rest of the season")

def sim_game(home, away, neutral=False):
    if neutral:
        hfa = 0
    else:
        hfa = hfa_dict[home]
    spread = pr_dict[home] + hfa - pr_dict[away]
    prob = spread_to_prob(spread)
    r = rng.random()
    if r < prob:
        return {"home_score": 22, "away_score": 18}
    else:
        return {"home_score": 18, "away_score": 22}
    
def get_winner(teams, scores):
    if scores["home_score"] > scores["away_score"]:
        return teams[0]
    else:
        return teams[1]

def sim_season(unplayed_df):
    results = []
    for _, row in unplayed_df.iterrows():
        week = row["week"]
        home = row["home_team"]
        away = row["away_team"]
        res_dict = {"week": week, "home_team": home, "away_team": away}
        res = sim_game(home, away)
        res_dict.update(res)
        results.append(res_dict)
    
    sim_df = pd.DataFrame(results)
    df_full = pd.concat([df_results, sim_df], axis=0)
    df_full["home_wins"] = df_full["away_score"] < df_full["home_score"]
    df_full["home_div"] = df_full["home_team"].map(team_divs)
    df_full["away_div"] = df_full["away_team"].map(team_divs)
    df_full["div_game"] = (df_full["home_div"] == df_full["away_div"])
    st.session_state["full"] = df_full

    df_stand = make_standings(df_full)
    st.session_state["stand"] = df_stand

    winners = []
    for div in ["North", "South"]:
        top2 = div_playoff_teams(df_stand, div)
        score_dict = sim_game(*top2)
        winners.append(get_winner(top2, score_dict))
    champ_score = sim_game(*winners, neutral=True)
    champion = get_winner(winners, champ_score)
    return champion

def sim_seasons(unplayed_df):
    champions = {t: 0 for t in teams}
    for i in range(sims):
        champ = sim_season(unplayed_df)
        champions[champ] += 1
    st.session_state["champions"] = champions

def head_games(team_list, df):
    df_sub = df[df.home_team.isin(team_list) & df.away_team.isin(team_list)].copy()
    return df_sub

def break_ties_2way(df):
    team_list = df.index.tolist()
    df_full = st.session_state["full"]
    sub_stand = make_standings(head_games(team_list, df_full))
    if not np.all(sub_stand.iloc[0].loc[["wins", "losses"]].values == sub_stand.iloc[1].loc[["wins", "losses"]].values):
        return [sub_stand.iloc[0].name, sub_stand.iloc[1].name]
    return team_list[:2]

def break_ties_3plus(df):
    team_list = df.index.tolist()
    df_full = st.session_state["full"]
    sub_stand = make_standings(head_games(team_list, df_full))
    tied12 = np.all(sub_stand.iloc[0].loc[["wins", "losses"]].values == sub_stand.iloc[1].loc[["wins", "losses"]].values)
    tied23 = np.all(sub_stand.iloc[1].loc[["wins", "losses"]].values == sub_stand.iloc[2].loc[["wins", "losses"]].values)
    if (not tied12) and (not tied23):
        return [sub_stand.iloc[0].name, sub_stand.iloc[1].name]
    elif tied12 and (not tied23):
        return break_ties_2way(df.loc[sub_stand.iloc[:2].index])
    # After head-to-head, the next tiebreaker is division percentage
    return team_list[:2]

def break_ties(df):
    if len(df) == 2:
        return break_ties_2way(df)
    else:
        return break_ties_3plus(df)

def div_playoff_teams(df, div):
    df_div = df[df["div"] == div]
    wins = df_div["wins"].values
    top = df_div[wins == wins[0]]
    if len(top) > 1:
        return break_ties(top)[:2]
    top_team = top.iloc[0].name
    second = df_div[wins == wins[1]]
    if len(second) > 1:
        return [top_team, break_ties(second)[0]]
    else:
        second_team = second.iloc[0].name
    return [top_team, second_team]

st.button("Simulate", on_click=sim_seasons, kwargs={"unplayed_df": unplayed_df})

st.subheader("Champions")

if "champions" in st.session_state:
    champions = st.session_state["champions"]
    df_champs = pd.DataFrame({"Team": list(champions.keys()), "Championships": list(champions.values())})
    df_champs["pct"] = (df_champs["Championships"] / sims)
    df_champs["Fair odds"] = df_champs["pct"].map(prob_to_odds)
    st.dataframe(df_champs.sort_values("pct", ascending=False).set_index("Team", drop=True))


# def display_matchups(week, df_spreads, spread_dict):
#     df_sub = df_spreads[df_spreads["Week"] == week]
#     for _, row in df_sub.iterrows():
#         res = make_matchup(row)
#         spread_dict[(row["Team1"], row["Team2"])] = res

# df_spreads = pd.read_csv("spreads-Jan22.csv")

# conf_rd = df_spreads[df_spreads["Week"] == 2]
# sb_rd = df_spreads[df_spreads["Week"] == 3]

# teams = list(set([t for t in df_spreads["Team1"]] +[t for t in df_spreads["Team2"]]))

# def get_favorite(team1, team2):
#     return df_spreads[df_spreads["Team1"].isin([team1, team2]) &
#         df_spreads["Team2"].isin([team1, team2])]["Favorite"].item()

# spread_dict = {}

# col1, _, col2, _2 = st.columns([5,2, 5, 3])

# with col1:
#     st.subheader("Conference championship round")
#     display_matchups(2, df_spreads, spread_dict)

# with col2:
#     st.subheader("Super Bowl")
#     display_matchups(3, df_spreads, spread_dict)

# def get_spread(team1, team2):
#     try:
#         return spread_dict[(team1, team2)]
#     except KeyError:
#         return spread_dict[(team2, team1)]

# df_spread_prob = pd.read_csv("spread_probs.csv")
# ser_prob = df_spread_prob.set_index("Spread", drop=True)

# def spread_to_prob(s):
#     if isinstance(s, str):
#         s = float(s)
#     i = np.argmin(np.abs(ser_prob.index - s))
#     return ser_prob.iloc[i].item()

# # b bool for whether favorite wins
# def process_row(row, b):
#     team1, team2 = row[["Team1", "Team2"]]
#     fav = get_favorite(team1, team2)
#     und = team1 if fav == team2 else team2
#     fav_spread = get_spread(team1, team2)
#     winner = fav if b else und
#     try:
#         fav_spread = float(fav_spread)
#         spread = fav_spread if b else -fav_spread
#         prob = spread_to_prob(spread)
#     except:
#         raise ValueError(f"Check the spread for {team1} vs {team2}")
#     return {"winner": winner, "prob": prob}


# def process_rd(df, tup):
#     if len(df) != len(tup):
#         raise ValueError("Wrong df and tup")
#     return pd.DataFrame(
#             [process_row(df.loc[i], b) for i, b in zip(df.index, tup)]
#         )


# def run_sim(tup):
#     conf_matchups = conf_rd
#     conf_outcome = process_rd(conf_matchups, tup[:2])
#     conf_winners = conf_outcome["winner"].values
#     sb_matchup = sb_rd[sb_rd["Team1"].isin(conf_winners) & sb_rd["Team2"].isin(conf_winners)]
#     sb_outcome = process_rd(sb_matchup, tup[2:])
#     df_outcome = pd.concat([conf_outcome, sb_outcome], axis=0).reset_index(drop=True)
#     prob = np.prod(df_outcome["prob"])
#     return (df_outcome["winner"], prob)

# sb_name = "SUPER BOWL - Odds to Win"
# fin_name = "SUPER BOWL - Exact Finalists"
# res_name = "SUPER BOWL - Exact Result"
# lose_name = "SUPER BOWL - Losing Team"

# markets = [sb_name, fin_name, res_name, lose_name]

# results = {}
# for name in markets:
#     results[name] = {}


# def replace(match, sep):
#     return f" {sep} ".join([get_abbr(x) for x in match.split(f" {sep} ")])


# def update_prob(dct, k, p):
#     dct[k] = dct.get(k,0) + p


# try:
#     for outcome in product([True, False], repeat=3):
#         ser_outcome, p = run_sim(outcome)
#         # st.write(ser_outcome)
#         sb_winner = ser_outcome.iloc[-1]
#         update_prob(results[sb_name], sb_winner, p)
#         # AFC team always written first
#         afc_champ = ser_outcome.iloc[-3]
#         nfc_champ = ser_outcome.iloc[-2]
#         sb_loser = next(t for t in (afc_champ, nfc_champ) if t != sb_winner)
#         update_prob(results[fin_name], f"{afc_champ} vs {nfc_champ}", p)
#         update_prob(results[res_name], f"{sb_winner} to beat {sb_loser}", p)
#         update_prob(results[lose_name], sb_loser, p)
# except ValueError:
#     st.write("Enter all spreads above to see the results")
    

# def display_results(name):
#     st.header(name)

#     probs = results[name]
#     sorted_keys = sorted(probs.keys(), key=lambda k: probs[k], reverse=True)

#     for k in sorted_keys:
#         st.markdown(f"**{k}**. Computed fair odds {prob_to_odds(probs[k])}")

# for name in markets:
#     display_results(name)


# st.header("AFC Championship")

# df = pd.read_csv("2023-div-rd.csv")
# df = df.set_index("Team")
# seeds = df["Seed"]



# def get_higher_seed(team1, team2):
#     return team1 if seeds[team1] < seeds[team2] else team2

# placeholder = st.empty()

# use_prob = st.checkbox('Use probabilities instead of spreads')

# if use_prob:
#     placeholder.markdown(
# """Enter the probability (as a decimal between 0 and 1) of the higher seed winning. For example, if you enter 0.8 for KC vs BUF, that means 80% chance KC wins.""")
# else:
#     placeholder.markdown(
# """Enter the spread, with a **positive number meaning the higher seed is favored**. For example, if you enter -2 for KC vs BUF, that means you project Buffalo to be favored by 2, and if you enter 2.5, then you project KC to be favored by 2.5.""")

# col1, col2, buff = st.columns([5,5,5])

# def make_matchup(team1, team2):
#     hteam = get_higher_seed(team1, team2)
#     ateam = team1 if hteam == team2 else team2
#     return st.text_input(f"{hteam} vs {ateam}")

# div_pairs = [("KC", "JAX"), ("BUF", "CIN")]
# teams = [team for pair in div_pairs for team in pair]

# conf_pairs = list(product(*div_pairs))

# val_dict = {}

# with col1:
#     st.write(f"Enter your predicted {'probability' if use_prob else 'spread'}.")
#     st.subheader("Divisional round")
#     for pair in div_pairs:
#         res = make_matchup(*pair)
#         val_dict[pair] = res
#     if res != "":
#         hteam = get_higher_seed(*pair)
#         ateam = pair[0] if hteam == pair[1] else pair[1]
#         p = float(res) if use_prob else spread_to_prob(res)
#         st.write(f"Example: We estimate {hteam} has a {p:.0%} chance of beating {ateam} in the divisional round.")

# with col2:
#     st.subheader("Conference championship")
#     for pair in conf_pairs:
#         val_dict[pair] = make_matchup(*pair)



# def get_team_prob(team, prob_dict):
#     orig = next(pair for pair in div_pairs if team in pair)
#     if get_higher_seed(*orig) == team:
#         prob = prob_dict[orig]
#     else:
#         prob = 1 - prob_dict[orig]
#     opp_pair = next(pair for pair in div_pairs if team not in pair)
    
#     next_prob = 0
#     for pair in conf_pairs:
#         if team not in pair:
#             continue
#         if team == get_higher_seed(*pair):
#             temp_prob = prob_dict[pair]
#         else:
#             temp_prob = 1-prob_dict[pair]
#         opp = next(t for t in pair if t != team)
#         if opp == get_higher_seed(*opp_pair):
#             opp_prob = prob_dict[opp_pair]
#         else:
#             opp_prob = 1-prob_dict[opp_pair]
#         next_prob += opp_prob*temp_prob
    
#     return prob*next_prob


# st.subheader("Estimated fair prices to be AFC Champion:")

# if (len(val_dict) == 6) and all(v != "" for v in val_dict.values()):
#     if use_prob:
#         prob_dict = {k:float(v) for k,v in val_dict.items()}
#     else:
#         prob_dict = {k:spread_to_prob(v) for k,v in val_dict.items()}
#     for team in teams:
#         prob = get_team_prob(team, prob_dict)
#         st.write(f"{team}: {prob_to_odds(prob)} (probability: {prob:.3f})")
# else:
#     st.write("(Be sure to enter all six values.)")
    
# st.header("NFC Championship")

# placeholder = st.empty()

# use_prob_nfc = st.checkbox('Use probabilities instead of spreads', key="prob_checkbox")

# col1, col2, buff = st.columns([5,5,5])

# def make_matchup(team1, team2):
#     hteam = get_higher_seed(team1, team2)
#     ateam = team1 if hteam == team2 else team2
#     return st.text_input(f"{hteam} vs {ateam}")

# wc_pair = ("TB", "DAL")
# div_pairs = [("PHI", "NYG"), ("SF", "TB"), ("SF", "DAL")]
# teams = list({team for pair in div_pairs for team in pair})

# conf_pairs = list(product(("PHI", "NYG"), ("SF", "TB", "DAL")))

# val_dict = {}

# with col1:
#     st.write(f"Enter your predicted {'probability' if use_prob_nfc else 'spread'}.")
#     st.subheader("Wild-card round")
#     res = make_matchup(*wc_pair)
#     val_dict[wc_pair] = res
#     st.subheader("Divisional round")
#     for pair in div_pairs:
#         res = make_matchup(*pair)
#         val_dict[pair] = res
#     if res != "":
#         hteam = get_higher_seed(*pair)
#         ateam = pair[0] if hteam == pair[1] else pair[1]
#         p = float(res) if use_prob_nfc else spread_to_prob(res)
#         st.write(f"Example: We estimate {hteam} has a {p:.0%} chance of beating {ateam} in the divisional round.")

# with col2:
#     st.subheader("Conference championship")
#     for pair in conf_pairs:
#         val_dict[pair] = make_matchup(*pair)


# def get_team_prob(team, prob_dict):
#     output_prob = 0

#     # Assume wc_team wins the wild card round
#     for wc_team in wc_pair:
#         if (team in wc_pair) and (team != wc_team):
#             continue
#         scale = get_pair_prob(wc_team, wc_pair)
#         hyp_div = [("PHI", "NYG"), ("SF", wc_team)]
#         hyp_teams = [t for pair in hyp_div for t in pair]

#         orig = next(pair for pair in hyp_div if team in pair)
#         prob = get_pair_prob(team, orig)
#         opp_pair = next(pair for pair in hyp_div if team not in pair)

#         conf_pairs = product(*hyp_div)
        
#         next_prob = 0
#         for pair in conf_pairs:
#             if team not in pair:
#                 continue
#             temp_prob = get_pair_prob(team, pair)
#             opp = next(t for t in pair if t != team)
#             opp_prob = get_pair_prob(opp, opp_pair)
#             next_prob += opp_prob*temp_prob
        
#         output_prob += scale*prob*next_prob
    
#     return output_prob

# def get_pair_prob(team, pair):
#     p = prob_dict[pair]
#     if get_higher_seed(*pair) == team:
#         return p
#     else:
#         return 1-p

# st.subheader("Estimated fair prices to be NFC Champion:")

# `all_probs = {}

# if (len(val_dict) == 10) and all(v != "" for v in val_dict.values()):
#     if use_prob_nfc:
#         prob_dict = {k:float(v) for k,v in val_dict.items()}
#     else:
#         prob_dict = {k:spread_to_prob(v) for k,v in val_dict.items()}

#     for team in teams:
#         prob = get_team_prob(team, prob_dict)
#         all_probs[team] = prob

#     sorted_keys = sorted(all_probs.keys(), key=lambda k: all_probs[k], reverse=True)
#     for team in sorted_keys:
#         prob = all_probs[team]
#         st.write(f"{team}: {prob_to_odds(prob)} (probability: {prob:.3f})")
# else:
#     st.write("(Be sure to enter all ten values.)")
