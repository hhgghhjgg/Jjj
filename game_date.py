# file: game_data.py

# ... (داده‌های نقشه و مناطق مانند قبل باقی می‌مانند)
WORLD_WIDTH = 50
WORLD_HEIGHT = 50
STARTING_COORDS = (25, 25)
DEFAULT_HP = 100

def xp_for_level(level):
    """فرمول محاسبه XP مورد نیاز برای سطح بعدی."""
    return int(100 * (level ** 1.5))

# تعریف ماموریت‌ها
QUESTS = {
    'first_steps': {
        'title': 'اولین قدم‌ها',
        'description': 'برای شروع ماجراجویی، ۱۰ متر در دنیای بازی حرکت کن.',
        'trigger': {'type': 'level', 'value': 1},
        'objective': {'type': 'move', 'count': 10},
        'reward': {'xp': 50, 'stat_points': 1}
    },
    'forest_exploration': {
        'title': 'اکتشاف جنگل',
        'description': 'وارد جنگل تاریک شو و خود را به کلبه متروکه برسان.',
        'trigger': {'type': 'level', 'value': 2},
        'objective': {'type': 'reach_coord', 'coords': (35, 25)},
        'reward': {'xp': 100, 'items': ['معجون سلامتی کوچک']}
    }
}

regions = {
    'دشت‌های آرامش': {
        'bounds': (20, 30, 20, 30),
        'base_description': 'شما در دشت‌های وسیع و آرامش‌بخش قدم می‌زنید.',
        'special_locations': {
            (25, 25): 'نقطه شروع. یک سنگ باستانی در این نقطه قرار دارد.'
        }
    },
    'جنگل تاریک': {
        'bounds': (31, 40, 20, 30),
        'base_description': 'شما وارد جنگلی تاریک و انبوه شده‌اید.',
        'special_locations': {
            (35, 25): 'یک کلبه متروکه. به نظر می‌رسد سال‌هاست کسی اینجا زندگی نکرده.'
        }
    }
}
