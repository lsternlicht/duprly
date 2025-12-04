from dupr_client import DuprClient
import os
import sys
import json
from loguru import logger
import argparse 

def main():
    parser = argparse.ArgumentParser(
        description='Get the rankings for a given club ID.'
    )
    parser.add_argument('club_id', type=str, help='The ID of the club to get the rankings for')
    args = parser.parse_args()
    dupr = DuprClient()
    status_code, rankings = dupr.get_members_by_club_ranking(args.club_id, get_all=True)
    if status_code != 200:
        logger.error(f"Error fetching rankings: HTTP {status_code}")
        sys.exit(1)
    with open(f"rankings-{args.club_id}.json", "w") as f:
        json.dump(rankings, f)
    logger.info(f"Rankings saved to rankings-{args.club_id}.json")
    
if __name__ == "__main__":
    main()