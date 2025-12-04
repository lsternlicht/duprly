#!/usr/bin/env python3
"""
Script to get all player data for a given club using a club name search query.
If multiple clubs match the search, the script will interactively prompt the user to select one.
"""

import json
import sys
import argparse
from dupr_client import DuprClient
from datetime import datetime

def search_and_select_club(dupr: DuprClient, club_query: str):
    """
    Search for clubs matching the query and return the selected club ID.
    If multiple clubs match, interactively prompt the user to select one.
    """
    print(f"\nSearching for clubs matching '{club_query}'...")
    status_code, clubs = dupr.search_clubs(club_query)
    
    if status_code != 200:
        print(f"Error searching for clubs: HTTP {status_code}")
        return None
    
    if not clubs:
        print(f"No clubs found matching '{club_query}'")
        return None
    
    if len(clubs) == 1:
        club = clubs[0]
        print(f"\nFound club: {club.get('clubName', 'Unknown')} (ID: {club.get('clubId')})")
        return club
    
    # Multiple clubs found - interactive selection
    # breakpoint()
    print(f"\nFound {len(clubs)} club(s) matching '{club_query}':")
    for idx, club in enumerate(clubs, 1):
        club_name = club.get('clubName', 'Unknown')
        club_id = club.get('clubId', 'Unknown')
        location = club.get('shortAddress', club.get('address', {}).get('formattedAddress', 'No location'))
        print(f"{idx}. {club_name} (ID: {club_id})")
        if location:
            print(f"   Location: {location}")
    
    while True:
        try:
            choice = input(f"\nEnter the number of the club you want (1-{len(clubs)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(clubs):
                selected_club = clubs[choice_num - 1]
                print(f"\nSelected: {selected_club.get('clubName', 'Unknown')} (ID: {selected_club.get('clubId')})")
                return selected_club
            else:
                print(f"Please enter a number between 1 and {len(clubs)}")
        except ValueError:
            print(f"Invalid input. Please enter a number between 1 and {len(clubs)}")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            return None


def get_club_players(dupr: DuprClient, club_id: str):
    """
    Get all players for a given club ID.
    """
    print(f"\nFetching players for club ID: {club_id}...")
    status_code, players = dupr.get_members_by_club(club_id)
    
    if status_code != 200:
        print(f"Error fetching players: HTTP {status_code}")
        return None
    
    return players


def main():
    parser = argparse.ArgumentParser(
        description='Get all player data for a given club using a club name search query'
    )
    parser.add_argument(
        'club_query',
        nargs='?',
        help='Club name search query (if not provided, will prompt)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file to save player data (JSON format)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Initialize DUPR client
    dupr = DuprClient(verbose=args.verbose)
    
    # Get club query from args or prompt
    club_query = args.club_query
    if not club_query:
        club_query = input("Enter club name to search for: ").strip()
        if not club_query:
            print("Error: Club name query is required")
            sys.exit(1)
    
    # Search and select club
    club = search_and_select_club(dupr, club_query)
    if not club:
        sys.exit(1)
    club_id = club.get('clubId')
    club_name = club.get('clubName')
    if not club_id:
        sys.exit(1)
    
    # Get all players for the club
    players = get_club_players(dupr, club_id)
    breakpoint()
    if players is None:
        sys.exit(1)
    
    # Display results
    print(f"\nFound {len(players)} player(s) in the club:")
    print("-" * 80)
    for idx, player in enumerate(players, 1):
        full_name = player.get('fullName', player.get('name', 'Unknown'))
        player_id = player.get('id', 'Unknown')
        ratings = player.get('ratings', {})
        singles_rating = ratings.get('singles', 'NR')
        doubles_rating = ratings.get('doubles', 'NR')
        
        print(f"{idx}. {full_name} (ID: {player_id})")
        print(f"   Ratings - Singles: {singles_rating}, Doubles: {doubles_rating}")
        if player.get('shortAddress'):
            print(f"   Location: {player.get('shortAddress')}")
    
    # Save to file if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(players, f, indent=2)
            print(f"\nPlayer data saved to: {args.output}")
        except Exception as e:
            print(f"\nError saving to file: {e}")
            sys.exit(1)
    else:
        # Save to default file
        formatted_date = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"club_players_{club_id}__{club_name.replace(' ', '_').lower()}_{formatted_date}.json"
        try:
            with open(default_filename, 'w') as f:
                json.dump(players, f, indent=2)
            print(f"\nPlayer data saved to: {default_filename}")
        except Exception as e:
            print(f"\nWarning: Could not save to default file: {e}")


if __name__ == "__main__":
    main()


