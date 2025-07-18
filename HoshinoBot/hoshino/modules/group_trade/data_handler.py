import os
import json
from datetime import datetime
from pathlib import Path

DATA_PATH = Path('data/friend_trade')

def _get_user_path(gid):
    return DATA_PATH / str(gid) / 'users.json'

def _load_users(gid):
    path = _get_user_path(gid)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}', encoding='utf8')
    return json.loads(path.read_text(encoding='utf8'))

def _save_users(gid, data):
    path = _get_user_path(gid)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')

def get_user_data(gid, uid):
    users = _load_users(gid)
    if str(uid) not in users:
        users[str(uid)] = {
            "coin": 500,
            "price": 100,
            "owner": None,
            "owned": [],
            "sign_date": "",
            "dispatch": {},
            "trade_count": 0
        }
        _save_users(gid, users)
    return users[str(uid)]

def update_user_data(gid, uid, key, value):
    users = _load_users(gid)
    uid = str(uid)
    users[uid][key] = value
    _save_users(gid, users)

def add_user_coin(gid, uid, amount):
    users = _load_users(gid)
    uid = str(uid)
    users[uid]["coin"] += amount
    _save_users(gid, users)
    return users[uid]["coin"]

def set_today_signed(gid, uid):
    today = datetime.now().strftime('%Y-%m-%d')
    update_user_data(gid, uid, "sign_date", today)

def has_signed_today(gid, uid):
    user = get_user_data(gid, uid)
    today = datetime.now().strftime('%Y-%m-%d')
    return user["sign_date"] == today