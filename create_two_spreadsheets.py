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

def find_common_player(flattened_data):
    """Find the player that appears in every match"""
    player_match_count = {}
    total_matches = len(flattened_data)
    
    for match in flattened_data:
        players_in_match = set()
        # Check all player positions
        for team in ['Team1', 'Team2']:
            for player in ['Player1', 'Player2']:
                name = match.get(f'{team}_{player}_Name')
                if name:
                    players_in_match.add(name)
        
        for player in players_in_match:
            player_match_count[player] = player_match_count.get(player, 0) + 1
    
    # Find player(s) who appear in all matches
    common_players = [player for player, count in player_match_count.items() 
                     if count == total_matches]
    
    return common_players[0] if common_players else None

def create_player_normalized_view(flattened_data, player_name):
    """Create a normalized view for a specific player"""
    player_matches = []
    
    for match in flattened_data:
        # Find which team and position the player is in
        player_team = None
        player_position = None
        partner_name = None
        partner_dupr = None
        
        for team in ['Team1', 'Team2']:
            for position in ['Player1', 'Player2']:
                if match.get(f'{team}_{position}_Name') == player_name:
                    player_team = team
                    player_position = position
                    # Find partner
                    partner_position = 'Player2' if position == 'Player1' else 'Player1'
                    partner_name = match.get(f'{team}_{partner_position}_Name')
                    partner_dupr = match.get(f'{team}_{partner_position}_DUPR_ID')
                    break
            if player_team:
                break
        
        if player_team:
            # Determine opponent team
            opponent_team = 'Team2' if player_team == 'Team1' else 'Team1'
            
            player_row = {
                'Match_ID': match.get('Match ID'),
                'Event_Date': str(match.get('Event Date')),
                'Event_Name': match.get('Event Name'),
                'Venue': match.get('Venue'),
                'Location': match.get('Location'),
                
                # Player info
                'Player_Name': player_name,
                'Player_DUPR_ID': match.get(f'{player_team}_{player_position}_DUPR_ID'),
                'Player_Pre_Doubles': match.get(f'{player_team}_{player_position}_Pre_Doubles'),
                'Player_Post_Doubles': match.get(f'{player_team}_{player_position}_Post_Doubles'),
                'Player_Doubles_Impact': match.get(f'{player_team}_{player_position}_Doubles_Impact'),
                
                # Partner info
                'Partner_Name': partner_name,
                'Partner_DUPR_ID': partner_dupr,
                'Partner_Pre_Doubles': match.get(f'{player_team}_{partner_position}_Pre_Doubles'),
                'Partner_Post_Doubles': match.get(f'{player_team}_{partner_position}_Post_Doubles'),
                
                # Opponent info
                'Opponent1_Name': match.get(f'{opponent_team}_Player1_Name'),
                'Opponent1_DUPR_ID': match.get(f'{opponent_team}_Player1_DUPR_ID'),
                'Opponent1_Pre_Doubles': match.get(f'{opponent_team}_Player1_Pre_Doubles'),
                'Opponent1_Post_Doubles': match.get(f'{opponent_team}_Player1_Post_Doubles'),
                'Opponent2_Name': match.get(f'{opponent_team}_Player2_Name'),
                'Opponent2_DUPR_ID': match.get(f'{opponent_team}_Player2_DUPR_ID'),
                'Opponent2_Pre_Doubles': match.get(f'{opponent_team}_Player2_Pre_Doubles'),
                'Opponent2_Post_Doubles': match.get(f'{opponent_team}_Player2_Post_Doubles'),
                
                # Match result
                'Won_Match': match.get(f'{player_team}_Winner'),
                'Team_Score_Game1': match.get(f'{player_team}_Game1'),
                'Team_Score_Game2': match.get(f'{player_team}_Game2'),
                'Team_Score_Game3': match.get(f'{player_team}_Game3'),
                'Opponent_Score_Game1': match.get(f'{opponent_team}_Game1'),
                'Opponent_Score_Game2': match.get(f'{opponent_team}_Game2'),
                'Opponent_Score_Game3': match.get(f'{opponent_team}_Game3'),
                
                # Timestamps
                'Created': match.get('Created'),
                'Modified': match.get('Modified')
            }
            
            player_matches.append(player_row)
    
    return player_matches

def remove_timezone_from_df(df):
    """Remove timezone from all datetime columns in a dataframe"""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # If column has timezone info, remove it
            if hasattr(df[col], 'dt') and df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
    return df

def create_excel_file(flattened_data, output_file='pickleball_matches.xlsx'):
    """Create an Excel file from the flattened data"""
    
    # Create DataFrame
    df = pd.DataFrame(flattened_data)
    
    # Convert date columns to datetime
    # date_columns = ['Event Date', 'Created', 'Modified']
    # for col in date_columns:
    #     if col in df.columns:
    #         df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
    #         # Remove timezone information
    #         df[col] = df[col].dt.tz_localize(None)
    
    # Sort by Event Date (most recent first)
    # df = df.sort_values('Event Date', ascending=False)
    
    # Ensure no timezone info remains
    # df = remove_timezone_from_df(df)
    
    # Create Excel writer with openpyxl engine
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
    """Create a per-player, per-match sheet (one row per player's match)."""

    rows = []

    for match in flattened_data:
        for team in ['Team1', 'Team2']:
            for position in ['Player1', 'Player2']:
                name = match.get(f'{team}_{position}_Name')
                if not name:
                    continue

                partner_position = 'Player2' if position == 'Player1' else 'Player1'
                partner_name = match.get(f'{team}_{partner_position}_Name')
                partner_dupr = match.get(f'{team}_{partner_position}_DUPR_ID')
                opponent_team = 'Team2' if team == 'Team1' else 'Team1'

                row = {
                    'Match_ID': match.get('Match ID'),
                    'Event_Date': match.get('Event Date'),
                    'Event_Name': match.get('Event Name'),
                    'Venue': match.get('Venue'),
                    'Location': match.get('Location'),
                    'Team': team,
                    'Position': position,

                    'Player_Name': name,
                    'Player_DUPR_ID': match.get(f'{team}_{position}_DUPR_ID'),
                    'Player_Pre_Singles': match.get(f'{team}_{position}_Pre_Singles'),
                    'Player_Pre_Doubles': match.get(f'{team}_{position}_Pre_Doubles'),
                    'Player_Post_Singles': match.get(f'{team}_{position}_Post_Singles'),
                    'Player_Post_Doubles': match.get(f'{team}_{position}_Post_Doubles'),
                    'Player_Doubles_Impact': match.get(f'{team}_{position}_Doubles_Impact'),

                    'Partner_Name': partner_name,
                    'Partner_DUPR_ID': partner_dupr,
                    'Partner_Pre_Doubles': match.get(f'{team}_{partner_position}_Pre_Doubles'),
                    'Partner_Post_Doubles': match.get(f'{team}_{partner_position}_Post_Doubles'),

                    'Opponent1_Name': match.get(f'{opponent_team}_Player1_Name'),
                    'Opponent1_DUPR_ID': match.get(f'{opponent_team}_Player1_DUPR_ID'),
                    'Opponent1_Pre_Doubles': match.get(f'{opponent_team}_Player1_Pre_Doubles'),
                    'Opponent1_Post_Doubles': match.get(f'{opponent_team}_Player1_Post_Doubles'),
                    'Opponent2_Name': match.get(f'{opponent_team}_Player2_Name'),
                    'Opponent2_DUPR_ID': match.get(f'{opponent_team}_Player2_DUPR_ID'),
                    'Opponent2_Pre_Doubles': match.get(f'{opponent_team}_Player2_Pre_Doubles'),
                    'Opponent2_Post_Doubles': match.get(f'{opponent_team}_Player2_Post_Doubles'),

                    'Won_Match': match.get(f'{team}_Winner'),
                    'Team_Score_Game1': match.get(f'{team}_Game1'),
                    'Team_Score_Game2': match.get(f'{team}_Game2'),
                    'Team_Score_Game3': match.get(f'{team}_Game3'),
                    'Opponent_Score_Game1': match.get(f'{opponent_team}_Game1'),
                    'Opponent_Score_Game2': match.get(f'{opponent_team}_Game2'),
                    'Opponent_Score_Game3': match.get(f'{opponent_team}_Game3'),

                    'Created': match.get('Created'),
                    'Modified': match.get('Modified')
                }

                rows.append(row)

    # Convert to DataFrame
    player_df = pd.DataFrame(rows)

    # Convert date columns to datetime and remove timezone
    for col in ['Event_Date', 'Created', 'Modified']:
        if col in player_df.columns:
            player_df[col] = pd.to_datetime(player_df[col], errors='coerce', utc=True)
            player_df[col] = player_df[col].dt.tz_localize(None)

    # Sort for readability
    if 'Event_Date' in player_df.columns:
        player_df = player_df.sort_values(['Player_Name', 'Event_Date'], ascending=[True, False])

    # Ensure no timezone info remains
    player_df = remove_timezone_from_df(player_df)

    # Save to Excel
    player_df.to_excel(output_file, index=False)

    return player_df

def save_player_view(player_matches, player_name, output_file):
    """Save the player-specific view to Excel"""
    
    df = pd.DataFrame(player_matches)
    
    # Convert date columns to datetime
    date_columns = ['Event_Date', 'Created', 'Modified']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            # Remove timezone
            df[col] = df[col].dt.tz_localize(None)
    
    # Sort by date
    df = df.sort_values('Event_Date', ascending=False)
    
    # Calculate running statistics
    df['Cumulative_Wins'] = df['Won_Match'].cumsum()
    df['Match_Number'] = range(len(df), 0, -1)  # Reverse numbering (oldest = 1)
    df['Cumulative_Win_Rate'] = (df['Cumulative_Wins'] / df.index.values[::-1] * 100).round(1)
    
    # Reorder columns for better readability
    column_order = [
        'Match_Number', 'Match_ID', 'Event_Date', 'Event_Name', 'Venue', 'Location',
        'Player_Name', 'Player_DUPR_ID', 'Player_Pre_Doubles', 'Player_Post_Doubles', 'Player_Doubles_Impact',
        'Partner_Name', 'Partner_DUPR_ID', 'Partner_Pre_Doubles', 'Partner_Post_Doubles',
        'Opponent1_Name', 'Opponent1_DUPR_ID', 'Opponent1_Pre_Doubles', 'Opponent1_Post_Doubles',
        'Opponent2_Name', 'Opponent2_DUPR_ID', 'Opponent2_Pre_Doubles', 'Opponent2_Post_Doubles',
        'Won_Match', 'Team_Score_Game1', 'Opponent_Score_Game1',
        'Team_Score_Game2', 'Opponent_Score_Game2',
        'Team_Score_Game3', 'Opponent_Score_Game3',
        'Cumulative_Wins', 'Cumulative_Win_Rate',
        'Created', 'Modified'
    ]
    
    # Reorder columns (only those that exist)
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
    # Ensure no timezone info remains
    df = remove_timezone_from_df(df)
    
    # Save to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{player_name} Matches', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets[f'{player_name} Matches']
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column) + 1
            worksheet.column_dimensions[chr(64 + col_idx) if col_idx <= 26 else 
                                       chr(64 + (col_idx-1)//26) + chr(65 + (col_idx-1)%26)].width = min(column_length + 2, 50)
    
    return df

def main():
    # Input and output file paths
    input_file = 'matches.json'  # Change this to your JSON file path
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
        print(f"Player per-match rows created: {len(player_df)}")
        
        # Find and create normalized view for common player
        common_player = find_common_player(flattened_data)
        if common_player:
            print(f"\nFound player in all matches: {common_player}")
            player_matches = create_player_normalized_view(flattened_data, common_player)
            player_file = f'{common_player.replace(" ", "_")}_matches.xlsx'
            player_match_df = save_player_view(player_matches, common_player, player_file)
            print(f"Created normalized view for {common_player}: {player_file}")
            
            # Print player statistics
            total_matches = len(player_match_df)
            wins = player_match_df['Won_Match'].sum()
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            print(f"\n=== {common_player} Statistics ===")
            print(f"Total Matches: {total_matches}")
            print(f"Wins: {wins}")
            print(f"Losses: {total_matches - wins}")
            print(f"Win Rate: {win_rate:.1f}%")
            
            # Show rating progression
            first_rating = player_match_df.iloc[-1]['Player_Pre_Doubles']
            last_rating = player_match_df.iloc[0]['Player_Post_Doubles']
            print(f"Rating Progression: {first_rating} → {last_rating}")
        
        # Print summary statistics
        print("\n=== Summary Statistics ===")
        print(f"Total matches: {len(df)}")
        # print(f"Date range: {df['Event Date'].min().strftime('%Y-%m-%d') if pd.notna(df['Event Date'].min()) else 'N/A'} to {df['Event Date'].max().strftime('%Y-%m-%d') if pd.notna(df['Event Date'].max()) else 'N/A'}")
        print(f"Unique events: {df['Event Name'].nunique()}")
        print(f"Unique venues: {df['Venue'].nunique()}")
        
        print("\n=== Top 5 Players by Matches Played ===")
        try:
            summary = (
                player_df.groupby('Player_Name')
                .agg(
                    Matches_Played=('Match_ID', 'count'),
                    Wins=('Won_Match', 'sum')
                )
            )
            summary['Losses'] = summary['Matches_Played'] - summary['Wins']
            summary['Win_Percentage'] = (summary['Wins'] / summary['Matches_Played'] * 100).round(1)
            summary = summary.sort_values('Matches_Played', ascending=False)
            print(summary[['Matches_Played', 'Wins', 'Losses', 'Win_Percentage']].head())
        except Exception as e:
            print(f"Could not compute top players summary: {e}")
        
    except FileNotFoundError:
        print(f"Error: Could not find the file '{input_file}'")
        print("Please make sure the JSON file is in the same directory as this script")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()