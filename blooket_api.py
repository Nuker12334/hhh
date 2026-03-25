import requests
import json

GRAPHQL_URL = "https://graphql.blooket.com/graphql"

def graphql_request(query, variables=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    # Bypass any system proxies
    proxies = {"http": None, "https": None}
    resp = requests.post(GRAPHQL_URL, json=payload, headers=headers, proxies=proxies, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"GraphQL error {resp.status_code}: {resp.text[:200]}")
    return resp.json()

def join_game(code, name):
    query = """
    mutation joinGame($code: String!, $name: String!) {
        joinGame(code: $code, name: $name) {
            playerId
            gameId
        }
    }
    """
    variables = {"code": code, "name": name}
    result = graphql_request(query, variables)
    return result["data"]["joinGame"]

def get_question(game_id, player_id):
    query = """
    query getQuestion($gameId: ID!, $playerId: ID!) {
        game(id: $gameId) {
            question(playerId: $playerId) {
                id
                text
                answers
            }
        }
    }
    """
    variables = {"gameId": game_id, "playerId": player_id}
    result = graphql_request(query, variables)
    return result["data"]["game"]["question"]

def answer_question(game_id, player_id, question_id, answer_index):
    query = """
    mutation answerQuestion($gameId: ID!, $playerId: ID!, $questionId: ID!, $answerIndex: Int!) {
        answerQuestion(gameId: $gameId, playerId: $playerId, questionId: $questionId, answerIndex: $answerIndex) {
            correct
        }
    }
    """
    variables = {
        "gameId": game_id,
        "playerId": player_id,
        "questionId": question_id,
        "answerIndex": answer_index
    }
    result = graphql_request(query, variables)
    return result["data"]["answerQuestion"]["correct"]
