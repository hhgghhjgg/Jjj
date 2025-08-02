# file: database.py
import sqlite3
import json

DB_FILE = "system_rpg.db"

def db_query(query, params=(), fetch_one=False, commit=False):
    # ... (این تابع بدون تغییر باقی می‌ماند)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(query, params)
        if commit:
            conn.commit()
            return None
        result = cursor.fetchone() if fetch_one else cursor.fetchall()
        return result

def init_db():
    # ساخت جدول بازیکنان با تمام آمار جدید
    db_query('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            location_name TEXT,
            coord_x INTEGER,
            coord_y INTEGER,
            hp INTEGER,
            max_hp INTEGER,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            xp_to_next_level INTEGER DEFAULT 100,
            strength INTEGER DEFAULT 5,
            agility INTEGER DEFAULT 5,
            intelligence INTEGER DEFAULT 5,
            stat_points INTEGER DEFAULT 0, -- امتیاز برای تخصیص
            inventory TEXT DEFAULT '[]'
        )
    ''', commit=True)
    
    # ساخت جدول ماموریت‌ها
    db_query('''
        CREATE TABLE IF NOT EXISTS quests (
            quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            quest_name TEXT,
            status TEXT, -- 'active' or 'completed'
            FOREIGN KEY (player_id) REFERENCES players (user_id)
        )
    ''', commit=True)
    print("پایگاه داده سیستمی با موفقیت راه‌اندازی شد.")

def get_player(user_id):
    player_row = db_query("SELECT * FROM players WHERE user_id = ?", (user_id,), fetch_one=True)
    return dict(player_row) if player_row else None

def update_player(user_id, data):
    fields = ', '.join([f"{key} = ?" for key in data.keys()])
    values = list(data.values())
    values.append(user_id)
    db_query(f"UPDATE players SET {fields} WHERE user_id = ?", tuple(values), commit=True)

def create_player(user_id, name, location, x, y, max_hp, xp_to_next_level):
    db_query(
        """INSERT INTO players 
           (user_id, name, location_name, coord_x, coord_y, hp, max_hp, xp_to_next_level) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, location, x, y, max_hp, max_hp, xp_to_next_level),
        commit=True
    )

def get_active_quest(player_id, quest_name):
    quest = db_query(
        "SELECT * FROM quests WHERE player_id = ? AND quest_name = ? AND status = 'active'",
        (player_id, quest_name),
        fetch_one=True
    )
    return dict(quest) if quest else None

def add_quest(player_id, quest_name):
    if not get_active_quest(player_id, quest_name):
        db_query(
            "INSERT INTO quests (player_id, quest_name, status) VALUES (?, ?, 'active')",
            (player_id, quest_name),
            commit=True
        )

def complete_quest(player_id, quest_name):
     db_query(
        "UPDATE quests SET status = 'completed' WHERE player_id = ? AND quest_name = ?",
        (player_id, quest_name),
        commit=True
    )
