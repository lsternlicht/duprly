import json
from dupr_client import DuprClient

dupr = DuprClient()

dupr.get_profile()
profile_id = dupr.profile["id"]
matches = dupr.get_member_match_history_p(profile_id, "2022-08-01", "2025-08-19")
print(matches)

# save matches to json file
with open("matches.json", "w") as f:
    json.dump(matches, f)