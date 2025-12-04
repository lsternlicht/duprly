"""
    A client to access the unofficial DUPR API.
    This API seems to be mostly a backend for front end type of API that
    does not necessarily fit other use.

    There is a automatically generated swagger doc that helps a little
    but check the data return and project readme for more tips to
    use this effectively

    https://api.dupr.gg/swagger-ui/index.html

"""
import os
import requests
from requests import Response
from loguru import logger
import json
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta


class DuprClient(object):

    def __init__(self, api_url: str = None, api_version: str = None, verbose: bool = False, env_path: str = None):

        if env_path:
            self.env_path = env_path
            logger.debug(f"config file: {self.env_path}")
        elif os.path.exists('.env'):
            logger.debug(f"loading .env file")
            load_dotenv()
        else:
            self.env_path = os.path.expanduser('~/.duprly_config')
            # config exists?
            logger.debug(f"config exists: {os.path.exists(self.env_path)}")

        if api_url:
            self.env_url = api_url
        else:
            self.env_url = 'https://api.dupr.gg'
        if api_version:
            self.version = api_version
        else:
            self.version = "v1.0"
        self.access_token = None
        self.refresh_token = None  # from login
        self.failed = False  # Strange way to return error, for now TBD
        self.verbose = verbose
        self.profile = None
        # breakpoint()
        self.load_token()
    

    def load_token(self):
        """ Load access token stored locally if available """
        self.access_token = os.getenv('DUPR_ACCESS_TOKEN', None)
        if self.access_token:
            logger.debug(f"Access token found, skipping login. Token: {self.access_token[:10]}...")
        else:
            logger.debug("No access token found, trying to load from config file")
            try:
                with open(self.env_path, "r") as f:
                    data = json.load(f)
                    self.access_token = data['access_token']
            except FileNotFoundError:
                logger.debug(f"No config file found at {self.env_path}")
                pass
        logger.debug(f"access token: {self.access_token[:10]}...")

    def save_token(self):
        """ Save  access token to disk, in plain json text
        """
        try:
            with open(self.env_path, "w") as f:
                data = {
                    'access_token': self.access_token
                }
                json.dump(data, f)
        except FileNotFoundError:
            logger.debug(f"Cannot save token to {self.env_path}")

    def u(self, parts):
        """ Helper function to construct URL """
        url = f'{self.env_url}{parts}'
        return url

    def ppj(self, data):
        """ Pretty Print Json for debug """
        if self.verbose:
            logger.debug(json.dumps(data, indent=4))

    def save_json_to_file(self, name: str, data: dict):
        """ Save raw json to file for later use """
        with open(f"{name}.json", 'w') as f:
            json.dump(data, f)

    def load_json_from_file(self, name: str) -> dict:
        """
            Load previously saved json from file.
        """
        with open(f"{name}.json", 'r') as f:
            data = json.load(f)
            return data

    def auth_user(self, username: str, password: str) -> int:
        """ This is the external callable auth method.
            It handles a saved access token, no need to re-login, or
            login and save token for next time.

            This API curently just use an access token.
            Not oauth style access/refresh token set.
        """
        if self.access_token:
            logger.debug("Access token found, skipping login")
            return 0
        else:
            rc = self.login_user(username, password)
            return rc

    def login_user(self, username: str, password: str) -> int:
        """ Low level just do login (will need refresh after) """
        body = {
            'email': username,
            "password": password,
        }
        logger.debug(f'login user: {username}')
        r = requests.post(self.u('/auth/v1.0/login/'), json=body)
        logger.debug(f'login user: {r.status_code}')
        logger.debug(f'login user: {r.request.url}')
        if r.status_code == 200:
            data = r.json()
            self.ppj(data)
            self.access_token = data.get('result').get('accessToken')
            logger.debug(f'access token: {self.access_token[:10]}...')
            self.save_token()
        return r.status_code

    def headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}'
        }

    def dupr_get(self, url, name: str = "") -> Response:
        logger.debug(f'GET: {name} : {url}')
        r = requests.get(self.u(url), headers=self.headers())
        logger.debug(f'return: {r.status_code}')
        if r.status_code == 403:
            rc = self.refresh_user()
            if rc == 200:
                logger.debug(f'GET: {url}')
                r = requests.get(self.u(url), headers=self.headers())
                logger.debug(f'return: {r.status_code}')
        self.failed = r.status_code != 200
        return r

    def dupr_post(self, url, json_data=None, name: str = "") -> Response:
        logger.debug(f'POST: {name} : {url}')
        headers = self.headers()
        r = requests.post(self.u(url), headers=headers,  json=json_data)
        logger.debug(f'return: {r.status_code}')
        if r.status_code == 403:
            rc = self.refresh_user()
            if rc == 200:
                logger.debug(f'POST: {url}')
                r = requests.post(self.u(url), headers=self.headers())
                logger.debug(f'return: {r.status_code}')
        self.failed = r.status_code != 200
        return r

    def get_profile(self) -> tuple[int, dict]:
        r = self.dupr_get(f'/user/{self.version}/profile/', "get_profile")
        if r.status_code == 200:
            data = r.json()
            self.profile = data["result"]
            self.ppj(data)
            return r.status_code, data["result"]
        else:
            logger.debug(f"Failed to get profile: {r.status_code}")
        return r.status_code, None

    def get_player(self, player_id: str) -> tuple[int, Optional[dict]]:
        r = self.dupr_get(f'/player/{self.version}/{player_id}', "get_player")
        if r.status_code == 200:
            self.ppj(r.json())
            return r.status_code, r.json()["result"]
        else:
            return r.status_code, None

    def get_club(self, club_id: str):
        r = self.dupr_get(f'/club/{self.version}/{club_id}', "get_club")
        if r.status_code == 200:
            self.ppj(r.json())
        return r.status_code

    def search_clubs(self, query: str, limit: int = 10) -> tuple[int, list]:
        """
        Search for clubs by name.
        Returns status code and list of club hits.
        """
        payload = {
            "limit": limit,
            "offset": 0,
            "query": query,
            "exclude": [],
            "filter": {}
        }
        r = self.dupr_post(f'/club/{self.version}/all', json_data=payload, name="search_clubs")
        if r.status_code == 200:
            data = r.json()
            self.ppj(data)
            hits = data.get("result", {}).get("hits", [])
            return r.status_code, hits
        return r.status_code, []

    def get_member_match_history_p(self, member_id: str, start_date: str, end_date: str) -> tuple[int, list]:
        """
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = start_date or datetime.now().strftime("%Y-%m-%d")
        """
       
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # two years before end date
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365*2)).strftime("%Y-%m-%d")  

        page_data = {
              "filters": {
            "eventDate": {
            "endDate": end_date,
            "startDate": start_date
            },
            "eventFormat": [
            "SINGLES",
            "DOUBLES"
            ],
            "eventName": "",
            "matchStatus": [
            "COMPLETE",
            "PENDING"
            ],
        },
            "sort": {
                "order": "DESC",
                "parameter": "MATCH_DATE",
                },
            "limit": 10,
            "offset": 0
        }
        offset = 0
        hit_data = []
        while offset is not None:
            r = self.dupr_post(f'/player/{self.version}/{member_id}/history',
                               page_data,
                               name="get_member_match_history")
            if r.status_code == 200:
                offset, hits = self.handle_paging(r.json())
                hit_data.extend(hits)
                page_data["offset"] = offset
        self.ppj(page_data)
        return r.status_code, hit_data

    def get_member_match_history(self, member_id: str) -> tuple[int, list]:
        offset = 0
        hit_data = []
        while offset is not None:
            r = self.dupr_get(f'/player/{self.version}/{member_id}/history?limit=100&offset={offset}',
                              name="get_member_match_history")
            if r.status_code == 200:
                offset, hits = self.handle_paging(r.json())
                hit_data.extend(hits)
        self.ppj(hit_data)
        return r.status_code, hit_data

    def handle_paging(self, json_data):
        """
        Handle results that are paged.
        use like this:

            while offset is not None:
                dupr_get
                offset, hits = handle_paging(response.json())

        """
        result = json_data["result"]
        total = result["total"]
        offset = result["offset"]
        limit = result["limit"]
        hits = result["hits"]
        if offset + limit < total:
            # there is more
            return offset + limit, hits
        else:
            return None, hits

    def get_members_by_club(self, club_id: str):
        """
        this call is a post call because it supports query and filter.
        """
        data = {
            "exclude": [],
            "limit": 20,
            "offset": 0,
            "query": "*"
            }
        offset = 0
        pdata = []
        while (offset is not None):
            data["offset"] = offset
            r = self.dupr_post(f'/club/{club_id}/members/v1.0/all', json_data=data, name="get_member_by_club")
            if r.status_code == 200:
                self.ppj(r.json())
                offset, hits = self.handle_paging(r.json())
                pdata.extend(hits)

        return r.status_code, pdata

    def get_members_by_club_ranking(self, club_id: str, limit: int = 20, offset: int = 0, query: str = "*", get_all: bool = False): 
        """
        this call is a post call because it supports query and filter.
        """
        data = {
            "exclude": [],
            "limit": limit,
            "offset": offset,
            "query": query
            }
        r = self.dupr_post(f'/club/{club_id}/v1.0/ranking', json_data=data, name="get_member_by_club")
        if r.status_code == 200:
            total_players = r.json()["result"]["memberRanking"]["total"]
            total_pages = total_players // limit
            players = r.json()["result"]["memberRanking"]["hits"]
            if get_all:
                for page in range(1, total_pages + 1):
                    data["offset"] = page * limit
                    r = self.dupr_post(f'/club/{club_id}/v1.0/ranking', json_data=data, name="get_member_by_club")
                    if r.status_code == 200:
                        _players = r.json()["result"]["memberRanking"]["hits"]
                        players.extend(_players)

            return r.status_code, players
        return r.status_code, []