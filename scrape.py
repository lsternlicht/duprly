import argparse
import os
import json
import csv
import sys
from typing import Dict, List, Optional, Union
import requests
from datetime import datetime

class DUPRMatchFetcher:
    def __init__(self, auth_token: str):
        self.base_url = "https://api.dupr.gg"
        self.headers = {
            "accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {auth_token}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Expires": "0",
            "Host": "api.dupr.gg",
            "Origin": "https://dashboard.dupr.com",
            "Pragma": "no-cache",
            "Referer": "https://dashboard.dupr.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
        }
        
    def _print_request_details(self, method: str, url: str, headers: Dict, payload: Dict = None):
        """Print detailed request information."""
        print("\n=== Request Details ===")
        print(f"Method: {method}")
        print(f"URL: {url}")
        print("\nHeaders:")
        for key, value in headers.items():
            # Truncate long auth tokens for readability
            if key == "Authorization" and len(value) > 50:
                print(f"{key}: {value[:30]}...{value[-20:]}")
            else:
                print(f"{key}: {value}")
        if payload:
            print("\nPayload:")
            print(json.dumps(payload, indent=2))
        print("=====================")

    def _handle_response(self, response: requests.Response, context: str) -> Optional[Dict]:
        """Handle API response with detailed logging."""
        print(f"\n=== Response Details ({context}) ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code != 200:
            print("Error Response Headers:")
            print(json.dumps(dict(response.headers), indent=2))
            print("\nError Response Content:")
            try:
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print(response.text)
            print("================================")
            return None
            
        try:
            data = response.json()
            if data.get('status') != 'SUCCESS':
                print(f"API returned non-success status: {data.get('status')}")
                print(json.dumps(data, indent=2))
                return None
            print("Response Status: SUCCESS")
            print("================================")
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {response.text[:500]}...")
            print("================================")
            return None

    def save_matches(self, matches: List[Dict], output_file: str, format: str = 'json'):
        """
        Save matches to a file in JSON or CSV format.
        
        Args:
            matches (List[Dict]): List of match dictionaries to save
            output_file (str): Path to output file
            format (str): Output format - either 'json' or 'csv'
        """
        if not matches:
            print("\nNo matches to save")
            return
            
        print(f"\nPreparing to save {len(matches)} matches in {format.upper()} format")
        
        try:
            if format == 'json':
                print("Formatting JSON data...")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "metadata": {
                            "total_matches": len(matches),
                            "export_date": datetime.now().isoformat(),
                            "format_version": "1.0"
                        },
                        "matches": matches
                    }, f, indent=2, ensure_ascii=False)
                
            else:  # CSV format
                print("Flattening match data for CSV format...")
                flattened_matches = []
                
                for match in matches:
                    # Base match details
                    flat_match = {
                        'match_id': match.get('matchId'),
                        'event_date': match.get('eventDate'),
                        'venue': match.get('venue'),
                        'format': match.get('eventFormat'),
                        'event_name': match.get('eventName'),
                        'league': match.get('league'),
                        'match_source': match.get('matchSource'),
                        'status': match.get('status'),
                        'created': match.get('created'),
                        'modified': match.get('modified')
                    }
                    
                    # Process teams and scores
                    for team in match.get('teams', []):
                        team_num = team.get('serial')
                        
                        # Team results
                        flat_match[f'team{team_num}_winner'] = team.get('winner', False)
                        
                        # Game scores
                        for game_num in range(1, 6):
                            score = team.get(f'game{game_num}')
                            if score is not None and score != -1:
                                flat_match[f'team{team_num}_game{game_num}'] = score
                        
                        # Player details
                        for player_key in ['player1', 'player2']:
                            if player := team.get(player_key):
                                prefix = f'team{team_num}_{player_key}'
                                flat_match.update({
                                    f'{prefix}_id': player.get('id'),
                                    f'{prefix}_name': player.get('fullName'),
                                    f'{prefix}_dupr_id': player.get('duprId')
                                })
                                
                                # Player ratings
                                ratings = player.get('postMatchRating', {})
                                flat_match.update({
                                    f'{prefix}_singles_rating': ratings.get('singles'),
                                    f'{prefix}_doubles_rating': ratings.get('doubles')
                                })
                                
                                # Rating impacts if available
                                rating_impact = team.get('preMatchRatingAndImpact', {})
                                impact_prefix = f'preMatchSingle{player_key[:-1].title()}Rating'
                                if impact := rating_impact.get(f'{impact_prefix}Player{player_key[-1]}'):
                                    flat_match[f'{prefix}_pre_match_rating'] = impact
                                
                                impact_prefix = f'matchSingle{player_key[:-1].title()}RatingImpact'
                                if impact := rating_impact.get(f'{impact_prefix}Player{player_key[-1]}'):
                                    flat_match[f'{prefix}_rating_impact'] = impact
                    
                    flattened_matches.append(flat_match)
                
                print("Writing CSV file...")
                if flattened_matches:
                    # Get all possible fields across all matches
                    all_fields = set()
                    for match in flattened_matches:
                        all_fields.update(match.keys())
                    
                    fieldnames = sorted(list(all_fields))
                    
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(flattened_matches)
                
            print(f"Successfully saved to {output_file}")
            print(f"File size: {os.path.getsize(output_file):,} bytes")
            
        except IOError as e:
            print(f"\nError saving file: {e}")
            print(f"Attempted to save to: {output_file}")
        except Exception as e:
            print(f"\nUnexpected error while saving: {e}")
            print("Attempting to write to backup file...")
            try:
                backup_file = f"{output_file}.backup.{format}"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(matches, f)
                print(f"Successfully wrote backup to: {backup_file}")
            except Exception as backup_error:
                print(f"Failed to write backup file: {backup_error}")
    def search_player(self, query: str) -> Optional[int]:
        """Search for a player by name and return their ID."""
        url = f"{self.base_url}/player/v1.0/search"
        payload = {
            "limit": 10,
            "offset": 0,
            "query": query,
            "exclude": [],
            "includeUnclaimedPlayers": True,
            "filter": {
                "lat": 40.7127753,
                "lng": -74.0059728,
                "rating": {"maxRating": None, "minRating": None},
                "locationText": ""
            }
        }
        
        print(f"\nSearching for player: '{query}'")
        self._print_request_details("POST", url, self.headers, payload)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            data = self._handle_response(response, "Player Search")
            if not data:
                return None
                
            hits = data.get('result', {}).get('hits', [])
            if not hits:
                print(f"No players found matching '{query}'")
                return None
                
            print(f"\nFound {len(hits)} player(s) matching '{query}':")
            for idx, player in enumerate(hits, 1):
                ratings = player.get('ratings', {})
                print(f"{idx}. {player['fullName']} (ID: {player['id']})")
                print(f"   Location: {player.get('shortAddress', 'No location')}")
                print(f"   Ratings - Singles: {ratings.get('singles', 'NR')}, Doubles: {ratings.get('doubles', 'NR')}")
            
            if len(hits) > 1:
                choice = input(f"\nEnter the number of the player you want to fetch (1-{len(hits)}): ")
                try:
                    return hits[int(choice)-1]['id']
                except (ValueError, IndexError):
                    print(f"Invalid selection: {choice}")
                    return None
            return hits[0]['id']
            
        except requests.exceptions.RequestException as e:
            print(f"Network error during player search: {e}")
            return None

    def _fetch_match_page(self, url: str, offset: int, limit: int) -> Optional[Dict]:
        """Fetch a single page of matches."""
        payload = {
            "filters": {"eventFormat": None},
            "limit": limit,
            "offset": offset,
            "sort": {"order": "DESC", "parameter": "MATCH_DATE"}
        }
        
        self._print_request_details("POST", url, self.headers, payload)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return self._handle_response(response, f"Match Page (offset={offset}, limit={limit})")
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching match page: {e}")
            return None

    def fetch_matches(self, player_id: int) -> List[Dict]:
        """Fetch all matches for a player using pagination."""
        url = f"{self.base_url}/player/v1.0/{player_id}/history"
        matches = []
        offset = 0
        limit = 10
        
        print(f"\nFetching match history for player ID: {player_id}")
        
        initial_response = self._fetch_match_page(url, offset, limit)
        if not initial_response:
            return matches
            
        total_matches = initial_response.get('result', {}).get('total', 0)
        matches.extend(initial_response.get('result', {}).get('hits', []))
        
        print(f"\nFound {total_matches} total matches")
        remaining_pages = (total_matches - limit) // limit + (1 if (total_matches - limit) % limit else 0)
        
        for page in range(1, remaining_pages + 1):
            offset = page * limit
            print(f"\nFetching page {page+1}/{remaining_pages+1} (matches {offset+1}-{min(offset+limit, total_matches)})")
            
            response = self._fetch_match_page(url, offset, limit)
            if response:
                matches.extend(response.get('result', {}).get('hits', []))
            else:
                print(f"Failed to fetch page {page+1}, stopping pagination")
                break
                
        print(f"\nSuccessfully fetched {len(matches)} matches")
        return matches

    # [Rest of the class implementation remains the same...]

def main():
    parser = argparse.ArgumentParser(description='Fetch DUPR player match history')
    parser.add_argument('--token', required=True, help='DUPR API authorization token')
    parser.add_argument('--id', type=int, help='Player ID (if known)')
    parser.add_argument('--query', help='Player name to search')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format (default: json)')
    parser.add_argument('--output', help='Output filename')
    args = parser.parse_args()
    
    if not args.id and not args.query:
        parser.error("Either --id or --query must be provided")
        
    print("\n=== DUPR Match History Fetcher ===")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    fetcher = DUPRMatchFetcher(args.token)
    player_id = args.id
    
    if not player_id and args.query:
        player_id = fetcher.search_player(args.query)
        if not player_id:
            print("\nError: No player found or invalid selection")
            sys.exit(1)
    
    matches = fetcher.fetch_matches(player_id)
    
    output_file = args.output or f"dupr_matches_{player_id}_{datetime.now().strftime('%Y%m%d')}.{args.format}"
    fetcher.save_matches(matches, output_file, args.format)
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("================================")

if __name__ == "__main__":
    main()
