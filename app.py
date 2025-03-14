from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from competition_manager import CompetitionManager
import json

app = Flask(__name__)
app.secret_key = 'dev'  # Change this to a secure key in production

# Initialize our competition manager
manager = CompetitionManager()

def player_history(player_name, competition_type):
    """Get a player's rating history for a specific competition type"""
    player = manager.player_manager.players.get(player_name)  # Use players dict directly
    if player and competition_type in player.competition_history:
        return sorted(player.competition_history[competition_type], key=lambda x: x['date'])
    return None

# Register the function with Jinja2
app.jinja_env.globals.update(player_history=player_history)

@app.route('/')
def index():
    """Home page showing competition types and their leaderboards"""
    # Get unique competition types
    competition_types = set()
    for comp in manager.competitions.values():
        competition_types.add(comp.competition_type)
    
    # Get ratings for each competition type
    ratings_by_type = {}
    for comp_type in competition_types:
        ratings_by_type[comp_type] = manager.player_manager.get_rating_list(comp_type)
    
    return render_template('index.html', 
                         ratings_by_type=ratings_by_type,
                         competition_types=sorted(competition_types))

@app.route('/submit', methods=['GET', 'POST'])
def submit_competition():
    """Page for submitting new competition results"""
    if request.method == 'POST':
        try:
            data = request.json
            competition_type = data['competition_type']
            name = data['name']
            date = data['date']
            format_type = data['format_type']
            
            # Create the competition
            competition_id = manager.create_competition(
                name=name,
                date=date,
                competition_type=competition_type,
                format_type=format_type
            )
            
            if format_type == 'leaderboard':
                # Process leaderboard results
                results = []
                for entry in data['results']:
                    player_name = entry['player']
                    rank = entry['rank']
                    score = entry.get('score')  # Score is optional
                    if score:
                        try:
                            score = float(score)
                        except ValueError:
                            score = None
                    results.append((player_name, rank, score))
                
                manager.add_leaderboard_results(competition_id, results)
                manager.process_leaderboard_competition(competition_id)
            
            else:  # direct_matches
                # Process direct matches
                for match in data['matches']:
                    player_a = match['player_a']
                    player_b = match['player_b']
                    result = float(match['result'])
                    manager.add_direct_match(competition_id, player_a, player_b, result)
                manager.process_direct_matches(competition_id)
            
            return jsonify({'success': True, 'message': 'Competition processed successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('submit.html')

@app.route('/competitions')
def view_competitions():
    """Page showing all competition results"""
    competitions = []
    for comp in sorted(manager.competitions.values(), 
                      key=lambda x: x.date, reverse=True):
        result_text = manager.get_competition_results(comp.competition_id)
        competitions.append({
            'id': comp.competition_id,
            'name': comp.name,
            'date': comp.date,
            'type': comp.competition_type,
            'format': comp.format_type,
            'results': result_text
        })
    
    return render_template('competitions.html', competitions=competitions)

@app.route('/api/players/<competition_type>')
def get_players(competition_type):
    """API endpoint to get players for a competition type"""
    players = []
    for player in manager.player_manager.players.values():
        if competition_type in player.ratings:
            players.append({
                'name': player.name,
                'rating': player.get_rating(competition_type)
            })
    return jsonify(players)

@app.route('/reprocess', methods=['POST'])
def reprocess():
    """Reprocess all competitions for a specific type or all types"""
    try:
        data = request.json
        competition_type = data.get('competition_type')  # None means all types
        manager.reprocess_competitions(competition_type)
        return jsonify({'success': True, 'message': 'Competitions reprocessed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
