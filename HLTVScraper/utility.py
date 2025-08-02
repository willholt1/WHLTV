def util_JoinTeamRankings(hltv_teams, valve_teams):
       
    valve_dict = {name: (points, rank) for (name, points, rank) in valve_teams}

    combined = []
    for name, hltv_points, hltv_rank in hltv_teams:
        if name in valve_dict:
            valve_points, valve_rank = valve_dict[name]
            combined.append((name, hltv_points, hltv_rank, valve_points, valve_rank))

    return combined
