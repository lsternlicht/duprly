import json
import pandas as pd
from datetime import datetime
import sys

def parse_match_data(json_file_path):
    """Parse the JSON file and extract match data"""
    
    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Extract the matches array (it's the second element in the response)
    matches = data[1]
    
    # Create a list to store flattened match data
    flattened_matches = []
    
    for match in matches:
        match_row = {
            # Match basic info
            'Match ID': match.get('id'),
            'Display ID': match.get('displayIdentity'),
            'Event Date': match.get('eventDate'),
            'Event Name': match.get('eventName'),
            'League': match.get('league'),
            'Tournament': match.get('tournament', ''),
            'Venue': match.get('venue', ''),
            'Location': match.get('location', ''),
            'Event Format': match.get('eventFormat'),
            'Match Source': match.get('matchSource'),
            'Status': match.get('status'),
            'Confirmed': match.get('confirmed'),
            
            # Score format
            'Score Format': match.get('scoreFormat', {}).get('format', ''),
            'Games': match.get('scoreFormat', {}).get('games', ''),
            'Winning Score': match.get('scoreFormat', {}).get('winningScore', ''),
            
            # Team 1 info
            'Team1_Winner': '',
            'Team1_Player1_Name': '',
            'Team1_Player1_DUPR_ID': '',
            'Team1_Player1_Pre_Singles': '',
            'Team1_Player1_Pre_Doubles': '',
            'Team1_Player1_Post_Singles': '',
            'Team1_Player1_Post_Doubles': '',
            'Team1_Player1_Doubles_Impact': '',
            'Team1_Player2_Name': '',
            'Team1_Player2_DUPR_ID': '',
            'Team1_Player2_Pre_Singles': '',
            'Team1_Player2_Pre_Doubles': '',
            'Team1_Player2_Post_Singles': '',
            'Team1_Player2_Post_Doubles': '',
            'Team1_Player2_Doubles_Impact': '',
            
            # Team 2 info
            'Team2_Winner': '',
            'Team2_Player1_Name': '',
            'Team2_Player1_DUPR_ID': '',
            'Team2_Player1_Pre_Singles': '',
            'Team2_Player1_Pre_Doubles': '',
            'Team2_Player1_Post_Singles': '',
            'Team2_Player1_Post_Doubles': '',
            'Team2_Player1_Doubles_Impact': '',
            'Team2_Player2_Name': '',
            'Team2_Player2_DUPR_ID': '',
            'Team2_Player2_Pre_Singles': '',
            'Team2_Player2_Pre_Doubles': '',
            'Team2_Player2_Post_Singles': '',
            'Team2_Player2_Post_Doubles': '',
            'Team2_Player2_Doubles_Impact': '',
            
            # Scores
            'Team1_Game1': '',
            'Team1_Game2': '',
            'Team1_Game3': '',
            'Team2_Game1': '',
            'Team2_Game2': '',
            'Team2_Game3': '',
            
            # Timestamps
            'Created': match.get('created', ''),
            'Modified': match.get('modified', '')
        }
        
        # Process teams
        teams = match.get('teams', [])
        for i, team in enumerate(teams, 1):
            team_prefix = f'Team{i}_'
            
            # Team winner status
            match_row[f'{team_prefix}Winner'] = team.get('winner', False)
            
            # Game scores
            match_row[f'{team_prefix}Game1'] = team.get('game1', '')
            match_row[f'{team_prefix}Game2'] = team.get('game2', '') if team.get('game2', -1) != -1 else ''
            match_row[f'{team_prefix}Game3'] = team.get('game3', '') if team.get('game3', -1) != -1 else ''
            
            # Player 1 info
            player1 = team.get('player1', {})
            if player1:
                match_row[f'{team_prefix}Player1_Name'] = player1.get('fullName', '')
                match_row[f'{team_prefix}Player1_DUPR_ID'] = player1.get('duprId', '')
                match_row[f'{team_prefix}Player1_Post_Singles'] = player1.get('postMatchRating', {}).get('singles', '')
                match_row[f'{team_prefix}Player1_Post_Doubles'] = player1.get('postMatchRating', {}).get('doubles', '')
                
                # Pre-match ratings and impact
                pre_match = team.get('preMatchRatingAndImpact', {})
                match_row[f'{team_prefix}Player1_Pre_Singles'] = pre_match.get('preMatchSingleRatingPlayer1', '')
                match_row[f'{team_prefix}Player1_Pre_Doubles'] = pre_match.get('preMatchDoubleRatingPlayer1', '')
                match_row[f'{team_prefix}Player1_Doubles_Impact'] = pre_match.get('matchDoubleRatingImpactPlayer1', '')
            
            # Player 2 info
            player2 = team.get('player2', {})
            if player2:
                match_row[f'{team_prefix}Player2_Name'] = player2.get('fullName', '')
                match_row[f'{team_prefix}Player2_DUPR_ID'] = player2.get('duprId', '')
                match_row[f'{team_prefix}Player2_Post_Singles'] = player2.get('postMatchRating', {}).get('singles', '')
                match_row[f'{team_prefix}Player2_Post_Doubles'] = player2.get('postMatchRating', {}).get('doubles', '')
                
                # Pre-match ratings and impact
                match_row[f'{team_prefix}Player2_Pre_Singles'] = pre_match.get('preMatchSingleRatingPlayer2', '')
                match_row[f'{team_prefix}Player2_Pre_Doubles'] = pre_match.get('preMatchDoubleRatingPlayer2', '')
                match_row[f'{team_prefix}Player2_Doubles_Impact'] = pre_match.get('matchDoubleRatingImpactPlayer2', '')
        
        flattened_matches.append(match_row)
    
    return flattened_matches

def create_excel_file(flattened_data, output_file='pickleball_matches.xlsx'):
    """Create an Excel file from the flattened data"""
    
    # Create DataFrame
    df = pd.DataFrame(flattened_data)
    
    # Convert date columns to datetime
    date_columns = ['Event Date', 'Created', 'Modified']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Sort by Event Date (most recent first)
    df = df.sort_values('Event Date', ascending=False)
    
    # Create Excel writer with xlsxwriter engine
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Write main sheet
        df.to_excel(writer, sheet_name='All Matches', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['All Matches']
        
        # Auto-adjust column widths
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column) + 1
            worksheet.column_dimensions[chr(64 + col_idx) if col_idx <= 26 else 
                                       chr(64 + (col_idx-1)//26) + chr(65 + (col_idx-1)%26)].width = min(column_length + 2, 50)
    
    # Also create a CSV version
    csv_file = output_file.replace('.xlsx', '.csv')
    df.to_csv(csv_file, index=False)
    
    return df

def create_player_summary(flattened_data, output_file='player_summary.xlsx'):
    """Create a summary sheet for individual players"""
    
    player_stats = {}
    
    for match in flattened_data:
        # Process Team 1 players
        for player_num in ['1', '2']:
            name = match.get(f'Team1_Player{player_num}_Name')
            if name:
                if name not in player_stats:
                    player_stats[name] = {
                        'Name': name,
                        'DUPR_ID': match.get(f'Team1_Player{player_num}_DUPR_ID'),
                        'Matches_Played': 0,
                        'Wins': 0,
                        'Losses': 0,
                        'Latest_Singles_Rating': None,
                        'Latest_Doubles_Rating': None,
                        'Latest_Match_Date': None
                    }
                
                player_stats[name]['Matches_Played'] += 1
                if match.get('Team1_Winner'):
                    player_stats[name]['Wins'] += 1
                else:
                    player_stats[name]['Losses'] += 1
                
                # Update latest ratings
                post_singles = match.get(f'Team1_Player{player_num}_Post_Singles')
                post_doubles = match.get(f'Team1_Player{player_num}_Post_Doubles')
                match_date = match.get('Event Date')
                
                if match_date and (not player_stats[name]['Latest_Match_Date'] or 
                                  match_date > player_stats[name]['Latest_Match_Date']):
                    player_stats[name]['Latest_Match_Date'] = match_date
                    if post_singles:
                        player_stats[name]['Latest_Singles_Rating'] = post_singles
                    if post_doubles:
                        player_stats[name]['Latest_Doubles_Rating'] = post_doubles
        
        # Process Team 2 players (similar logic)
        for player_num in ['1', '2']:
            name = match.get(f'Team2_Player{player_num}_Name')
            if name:
                if name not in player_stats:
                    player_stats[name] = {
                        'Name': name,
                        'DUPR_ID': match.get(f'Team2_Player{player_num}_DUPR_ID'),
                        'Matches_Played': 0,
                        'Wins': 0,
                        'Losses': 0,
                        'Latest_Singles_Rating': None,
                        'Latest_Doubles_Rating': None,
                        'Latest_Match_Date': None
                    }
                
                player_stats[name]['Matches_Played'] += 1
                if match.get('Team2_Winner'):
                    player_stats[name]['Wins'] += 1
                else:
                    player_stats[name]['Losses'] += 1
                
                # Update latest ratings
                post_singles = match.get(f'Team2_Player{player_num}_Post_Singles')
                post_doubles = match.get(f'Team2_Player{player_num}_Post_Doubles')
                match_date = match.get('Event Date')
                
                if match_date and (not player_stats[name]['Latest_Match_Date'] or 
                                  match_date > player_stats[name]['Latest_Match_Date']):
                    player_stats[name]['Latest_Match_Date'] = match_date
                    if post_singles:
                        player_stats[name]['Latest_Singles_Rating'] = post_singles
                    if post_doubles:
                        player_stats[name]['Latest_Doubles_Rating'] = post_doubles
    
    # Convert to DataFrame
    player_df = pd.DataFrame(list(player_stats.values()))
    
    # Calculate win percentage
    player_df['Win_Percentage'] = (player_df['Wins'] / player_df['Matches_Played'] * 100).round(1)
    
    # Sort by matches played
    player_df = player_df.sort_values('Matches_Played', ascending=False)
    
    # Save to Excel
    player_df.to_excel(output_file, index=False)
    
    return player_df

def main():
    # Input and output file paths
    input_file = 'matches-short.json'  # Change this to your JSON file path
    output_excel = 'pickleball_matches.xlsx'
    player_summary_file = 'player_summary.xlsx'
    
    try:
        # Parse the JSON data
        print(f"Reading JSON file: {input_file}")
        flattened_data = parse_match_data(input_file)
        print(f"Successfully parsed {len(flattened_data)} matches")
        
        # Create Excel file
        print(f"Creating Excel file: {output_excel}")
        df = create_excel_file(flattened_data, output_excel)
        print(f"Excel file created successfully with {len(df)} rows")
        
        # Create player summary
        print(f"Creating player summary: {player_summary_file}")
        player_df = create_player_summary(flattened_data, player_summary_file)
        print(f"Player summary created with {len(player_df)} unique players")
        
        # Print summary statistics
        print("\n=== Summary Statistics ===")
        print(f"Total matches: {len(df)}")
        print(f"Date range: {df['Event Date'].min()} to {df['Event Date'].max()}")
        print(f"Unique events: {df['Event Name'].nunique()}")
        print(f"Unique venues: {df['Venue'].nunique()}")
        
        print("\n=== Top 5 Players by Matches Played ===")
        print(player_df[['Name', 'Matches_Played', 'Wins', 'Losses', 'Win_Percentage', 'Latest_Doubles_Rating']].head())
        
    except FileNotFoundError:
        print(f"Error: Could not find the file '{input_file}'")
        print("Please make sure the JSON file is in the same directory as this script")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()