from .. import models
import requests
from . import api


def create_new_player(
        nickname: str,
        gender: int
):
    new_player = models.Player(
        nickname=nickname,
        gender=gender
    )
    return new_player


def create_new_player_from_playtomic(
        nickname: str,
        picture: str,
        level: str,
        playtomic_id: int
):
    new_player_from_playtomic = models.Player(
        nickname=nickname,
        picture=picture,
        level=level,
        playtomic_id=playtomic_id,
        gender=1
    )
    return new_player_from_playtomic


def get_user_from_playtomic(
        name: str,
):
    client = api.PlaytomicAPIClient()
    try:
        data = client.make_request(
            "/v1/social/users",
            method="GET",
            params={
                "name":name,
                "requester_user_id":"me",
                "size":"50",
            }
        )
        return data
    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")


def get_user_by_id_from_playtomic(
        id: int,
):
    client = api.PlaytomicAPIClient()
    try:
        data = client.make_request(
            "/v2/users",
            method="GET",
            params={
                "user_id":id,
            }
        )
        return data
    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")


def get_user_level_from_playtomic(
        id: int,
):
    client = api.PlaytomicAPIClient()
    try:
        data = client.make_request(
            "/v1/levels",
            method="GET",
            params={
                "size":1000,
                "sport_id":"PADEL",
                "status":"CONFIRMED",
                "user_id":id,
                "with_history":"false",
                "with_history_size":0
            }
        )
        return data
    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")
