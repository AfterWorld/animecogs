import discord
from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import random
import asyncio
from datetime import datetime, timedelta
import logging

class OnePieceBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.spawn_channel_id = None
        self.spawn_task = None
        self.logger = logging.getLogger("red.onepiecebattle")
        self.awakening_chance = 0.05  # 5% chance each turn
        self.awakening_boost = 1.5  # 50% power boost when awakened
        self.combo_chance = 0.15  # 15% chance to perform a combo attack

        default_user = {
            "fighting_style": None,
            "devil_fruit": None,
            "haki": {
                "observation": 0,
                "armament": 0,
                "conquerors": 0
            },
            "doriki": 0,
            "bounty": 0,
            "battles_won": 0,
            "last_train": None,
            "level": 1,
            "experience": 0,
            "stamina": 100,
            "skill_points": 0,
            "strength": 1,
            "speed": 1,
            "defense": 1,
            "learned_techniques": [],
            "equipped_items": [],
            "fatigue": 0,
            "last_rest_time": None,
            "devil_fruit_mastery": 0,
            "unlocked_abilities": [],
            "temporary_effects": [],
            "active_quests": []
        }
        
        default_global = {
            "last_bounty_update": None,
            "top_bounties": [],
            "battle_royale_channel": None,
            "next_battle_royale": None,
            "ongoing_battle_royale": False,
            "world_state": {
                "marine_presence": 50,  # 0-100 scale
                "pirate_influence": 50,  # 0-100 scale
                "world_events": []
            },
            "bounty_rankings": {}  # Add this line
        }
 
        self.battle_royale_task = self.bot.loop.create_task(self.battle_royale_scheduler())
        self.bounty_update_task = self.bot.loop.create_task(self.periodic_bounty_update()) # Start the bounty update loop
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)
        self.max_fatigue = 100
        self.fatigue_per_battle = 10
        self.fatigue_recovery_rate = 5  # Amount of fatigue recovered per hour of rest

        self.awakening_levels = {
            0: {"name": "Novice", "boost": 1.0},
            25: {"name": "Adept", "boost": 1.1},
            50: {"name": "Master", "boost": 1.2},
            75: {"name": "Awakened", "boost": 1.3},
            100: {"name": "Fully Awakened", "boost": 1.5}
        }

        self.gear_system = {
            "Gear Second": {"boost": 1.5, "stamina_cost": 20},
            "Gear Third": {"boost": 2.0, "stamina_cost": 30},
            "Gear Fourth": {"boost": 3.0, "stamina_cost": 50},
            "Gear Fifth": {"boost": 5.0, "stamina_cost": 90}
        }
        
        self.battle_environments = {
            "Calm Belt": "The oppressive silence amplifies every move!",
            "Marineford Plaza": "The echoes of war still resonate in this historic battleground!",
            "Alabasta Desert": "The scorching sand tests the fighters' endurance!",
            "Skypiea": "The thin air at this altitude makes every action more challenging!",
            "Fishman Island": "The underwater pressure adds a unique twist to the battle!",
            "Punk Hazard": "Half-frozen, half-ablaze, this island is a battleground of extremes!"
        }
        
        self.terrain_effects = {
            "Sea": {
                "water": 1.5,
                "fire": 0.7,
                "lightning": 1.3,
                "earth": 0.8,
                "wind": 1.2
            },
            "Island": {
                "water": 0.9,
                "fire": 1.1,
                "lightning": 1.0,
                "earth": 1.3,
                "wind": 1.1
            },
            "City": {
                "water": 1.0,
                "fire": 1.2,
                "lightning": 1.1,
                "earth": 0.9,
                "wind": 1.0
            },
            "Desert": {
                "water": 1.5,
                "fire": 1.3,
                "lightning": 0.8,
                "earth": 1.2,
                "wind": 1.1
            },
            "Sky": {
                "water": 0.8,
                "fire": 0.9,
                "lightning": 1.5,
                "earth": 0.7,
                "wind": 1.4
            },
            "Volcano": {  # Add this new environment
                "water": 0.7,
                "fire": 1.5,
                "lightning": 1.1,
                "earth": 1.2,
                "wind": 0.9
            }
        }
        
        self.devil_fruit_elements = {
            "Mera Mera no Mi": "fire",
            "Hie Hie no Mi": "water",  # Ice is considered water-based
            "Goro Goro no Mi": "lightning",
            "Suna Suna no Mi": "earth",
            "Kaze Kaze no Mi": "wind",  # Hypothetical wind fruit
            # ... add more as needed
        }
        
        self.environments = {
            "Sea": {
                "description": "Surrounded by water, Devil Fruit users are weakened.",
                "df_modifier": 0.8,
                "non_df_modifier": 1.1
            },
            "Island": {
                "description": "A balanced environment for all fighters.",
                "df_modifier": 1.0,
                "non_df_modifier": 1.0
            },
            "City": {
                "description": "Urban terrain provides cover and mobility advantages.",
                "df_modifier": 1.1,
                "non_df_modifier": 1.1
            },
            "Volcano": {
                "description": "Intense heat boosts fire-based abilities but challenges others.",
                "df_modifier": 1.2,
                "non_df_modifier": 0.9
            }
        }
        
        self.battle_hazards = {
            "Sea": [
                {"name": "Sea King Attack", "description": "A massive Sea King emerges!", "effect": self.sea_king_attack},
                {"name": "Whirlpool", "description": "A dangerous whirlpool forms nearby!", "effect": self.whirlpool_effect},
                {"name": "Tidal Wave", "description": "A massive tidal wave approaches!", "effect": self.tidal_wave_effect},
                {"name": "Storm Surge", "description": "A powerful storm surge hits the area!", "effect": self.storm_surge_effect}
            ],
            "Island": [
                {"name": "Volcano Eruption", "description": "The island's volcano begins to erupt!", "effect": self.volcano_eruption_effect},
                {"name": "Jungle Ambush", "description": "Wild animals suddenly attack!", "effect": self.jungle_ambush_effect},
                {"name": "Quicksand", "description": "The ground beneath turns to quicksand!", "effect": self.quicksand_effect},
                {"name": "Earthquake", "description": "The island is hit by a sudden earthquake!", "effect": self.earthquake_effect}
            ],
            "City": [
                {"name": "Falling Debris", "description": "Buildings start to collapse!", "effect": self.falling_debris_effect},
                {"name": "Civilian Panic", "description": "Panicked civilians run through the battlefield!", "effect": self.civilian_panic_effect},
                {"name": "Marine Interference", "description": "A Marine patrol stumbles upon the battle!", "effect": self.marine_interference_effect},
                {"name": "Blackout", "description": "The city's power grid fails, causing a blackout!", "effect": self.blackout_effect}
            ]
        }
        
        self.mythical_zones = {
            "Raftel": {
                "description": "The legendary final island of the Grand Line.",
                "effect": self.raftel_effect,
                "reward": "Ancient Weapon Blueprint",
                "spawn_chance": 0.01  # 1% chance
            },
            "All Blue": {
                "description": "The mystical sea where all four Blues meet.",
                "effect": self.all_blue_effect,
                "reward": "Legendary Fish",
                "spawn_chance": 0.05  # 5% chance
            },
            "Emerald City": {
                "description": "A hidden city of advanced technology.",
                "effect": self.emerald_city_effect,
                "reward": "Advanced Den Den Mushi",
                "spawn_chance": 0.03  # 3% chance
            },
            "God Valley": {
                "description": "An island that disappeared from history.",
                "effect": self.god_valley_effect,
                "reward": "Celestial Dragon Artifact",
                "spawn_chance": 0.02  # 2% chance
            },
            "Laugh Tale": {
                "description": "The island where the One Piece is hidden.",
                "effect": self.laugh_tale_effect,
                "reward": "Poneglyph Rubbing",
                "spawn_chance": 0.005  # 0.5% chance
            }
        }
        
        self.devil_fruits = {
            "Gomu Gomu no Mi": {"ability": "Elasticity", "modifier": 1.2, "type": "Paramecia"},
            "Mera Mera no Mi": {"ability": "Fire Control", "modifier": 1.3, "type": "Logia"},
            "Hie Hie no Mi": {"ability": "Ice Control", "modifier": 1.3, "type": "Logia"},
            "Pika Pika no Mi": {"ability": "Light Manipulation", "modifier": 1.4, "type": "Logia"},
            "Gura Gura no Mi": {"ability": "Earthquake Generation", "modifier": 1.5, "type": "Paramecia"},
            "Yami Yami no Mi": {"ability": "Darkness Manipulation", "modifier": 1.4, "type": "Logia"},
            "Ope Ope no Mi": {"ability": "Operation", "modifier": 1.3, "type": "Paramecia"},
            "Magu Magu no Mi": {"ability": "Magma Control", "modifier": 1.4, "type": "Logia"},
            "Goro Goro no Mi": {"ability": "Lightning Control", "modifier": 1.4, "type": "Logia"},
            "Suna Suna no Mi": {"ability": "Sand Control", "modifier": 1.3, "type": "Logia"},
            "Mochi Mochi no Mi": {"ability": "Mochi Manipulation", "modifier": 1.3, "type": "Special Paramecia"},
            "Bara Bara no Mi": {"ability": "Body Separation", "modifier": 1.2, "type": "Paramecia"},
            "Doku Doku no Mi": {"ability": "Poison Generation", "modifier": 1.3, "type": "Paramecia"},
            "Hana Hana no Mi": {"ability": "Body Replication", "modifier": 1.2, "type": "Paramecia"},
            "Kilo Kilo no Mi": {"ability": "Weight Manipulation", "modifier": 1.2, "type": "Paramecia"}
        }

        self.techniques = {
            "Swordsman": [
                {"name": "Single Sword Style", "level": 1},
                {"name": "Two Sword Style", "level": 5},
                {"name": "Three Sword Style", "level": 10},
                {"name": "Flying Slash Attack", "level": 15},
                {"name": "Lion's Song", "level": 20},
                {"name": "Great Dragon Shock", "level": 25},
                {"name": "Purgatory Onigiri", "level": 30},
                {"name": "Phoenix of the 36 Earthly Desires", "level": 35},
                {"name": "One Sword Style: Great Dragon Shock", "level": 40},
                {"name": "Santoryu Ogi: Rokudo no Tsuji", "level": 50}
            ],
            "Martial Artist": [
                {"name": "Shigan", "level": 1},
                {"name": "Tekkai", "level": 5},
                {"name": "Rankyaku", "level": 10},
                {"name": "Soru", "level": 15},
                {"name": "Geppou", "level": 20},
                {"name": "Kami-e", "level": 25},
                {"name": "Rokuogan", "level": 30},
                {"name": "Life Return", "level": 35},
                {"name": "Seimei Kikan: Kami-e Bushin", "level": 40},
                {"name": "Rokushiki Ogi: Rokuogan", "level": 50}
            ],
            "Sniper": [
                {"name": "Lead Star", "level": 1},
                {"name": "Exploding Star", "level": 5},
                {"name": "Fire Bird Star", "level": 10},
                {"name": "Smoke Star", "level": 15},
                {"name": "Kemuri Boshi", "level": 20},
                {"name": "Platanus Shuriken", "level": 25},
                {"name": "Hissatsu Firebird Star", "level": 30},
                {"name": "Midori Boshi: Devil", "level": 35},
                {"name": "Grow Up: Kuro Kabuto", "level": 40},
                {"name": "Hissatsu: Totsugeki Ryuseigun", "level": 50}
            ],
            "Brawler": [
                {"name": "Gomu Gomu no Pistol", "level": 1},
                {"name": "Gomu Gomu no Bazooka", "level": 5},
                {"name": "Gomu Gomu no Gatling", "level": 10},
                {"name": "Gear Second", "level": 15},
                {"name": "Gomu Gomu no Jet Pistol", "level": 20},
                {"name": "Gear Third", "level": 25},
                {"name": "Gomu Gomu no Elephant Gun", "level": 30},
                {"name": "Gear Fourth", "level": 35},
                {"name": "Gomu Gomu no King Kong Gun", "level": 40},
                {"name": "Gear Fifth", "level": 50}
            ],
            "Tactician": [
                {"name": "Mirage Tempo", "level": 1},
                {"name": "Thunderbolt Tempo", "level": 5},
                {"name": "Cyclone Tempo", "level": 10},
                {"name": "Thunder Lance Tempo", "level": 15},
                {"name": "Clima-Tact: Rain Tempo", "level": 20},
                {"name": "Weather Egg", "level": 25},
                {"name": "Thunder Breed Tempo", "level": 30},
                {"name": "Zeus Breeze Tempo", "level": 35},
                {"name": "Raitei", "level": 40},
                {"name": "Big Mom: Thunderbolt", "level": 50}
            ]
        }
        
        self.elemental_interactions = {
            "Fire": {"strong_against": ["Ice", "Plant"], "weak_against": ["Water", "Earth"]},
            "Water": {"strong_against": ["Fire", "Lightning"], "weak_against": ["Plant", "Ice"]},
            "Earth": {"strong_against": ["Lightning", "Fire"], "weak_against": ["Water", "Plant"]},
            "Ice": {"strong_against": ["Water", "Plant"], "weak_against": ["Fire", "Earth"]},
            "Lightning": {"strong_against": ["Water", "Metal"], "weak_against": ["Earth", "Rubber"]},
            "Plant": {"strong_against": ["Earth", "Water"], "weak_against": ["Fire", "Ice"]},
            "Metal": {"strong_against": ["Ice", "Rock"], "weak_against": ["Lightning", "Fire"]},
            "Rubber": {"strong_against": ["Lightning", "Impact"], "weak_against": ["Fire", "Cutting"]}
        }
        
        self.legendary_weapons = {
            "Yoru": {"type": "Sword", "boost": 50, "ability": "Black Blade", "description": "One of the 12 Supreme Grade Swords"},
            "Murakumogiri": {"type": "Naginata", "boost": 45, "ability": "Weather Manipulation", "description": "One of the 12 Supreme Grade Weapons"},
            "Kabuto": {"type": "Slingshot", "boost": 40, "ability": "Pop Green", "description": "Usopp's ultimate weapon"},
            "Clima-Tact": {"type": "Staff", "boost": 45, "ability": "Weather Control", "description": "Nami's weather-controlling weapon"},
            "Shodai Kitetsu": {"type": "Sword", "boost": 48, "ability": "Cursed Blade", "description": "One of the 21 Great Grade Swords"}
        }

        self.equipment = {
            "Weapons": {
                "Wooden Sword": {"type": "Sword", "rarity": "Common", "strength": 5, "speed": 2},
                "Steel Cutlass": {"type": "Sword", "rarity": "Uncommon", "strength": 15, "speed": 5},
                "Graded Sword: Wado Ichimonji": {"type": "Sword", "rarity": "Rare", "strength": 30, "speed": 10, "special": "Increases critical hit chance"},
                "Supreme Grade Sword: Yoru": {"type": "Sword", "rarity": "Legendary", "strength": 50, "speed": 20, "special": "Chance to unleash devastating slash"},
                
                "Flintlock Pistol": {"type": "Gun", "rarity": "Common", "strength": 8, "speed": 10},
                "Modified Rifle": {"type": "Gun", "rarity": "Uncommon", "strength": 20, "speed": 15},
                "Kabuto": {"type": "Gun", "rarity": "Rare", "strength": 35, "speed": 25, "special": "Versatile ammo types"},
                "Clima-Tact": {"type": "Staff", "rarity": "Legendary", "strength": 40, "speed": 30, "special": "Weather manipulation"}
            },
            "Armor": {
                "Light Vest": {"type": "Chest", "rarity": "Common", "defense": 10},
                "Steel Armor": {"type": "Chest", "rarity": "Uncommon", "defense": 25, "speed": -5},
                "Sea Stone Gauntlets": {"type": "Hands", "rarity": "Rare", "defense": 20, "strength": 15, "special": "Nullifies Devil Fruit powers on contact"},
                "Adam Wood Armor": {"type": "Chest", "rarity": "Legendary", "defense": 50, "special": "Greatly reduces damage from slashing attacks"}
            },
            "Accessories": {
                "Straw Hat": {"type": "Head", "rarity": "Uncommon", "speed": 5, "special": "Increases crew morale"},
                "Log Pose": {"type": "Wrist", "rarity": "Rare", "special": "Improves navigation, chance to avoid ambushes"},
                "Eternal Pose": {"type": "Wrist", "rarity": "Epic", "special": "Always find your way, significant boost to escape chances"},
                "Red Poneglyph Rubbing": {"type": "Pocket", "rarity": "Legendary", "special": "Reveals hidden knowledge, chance for instant victory against history-based encounters"}
            }
        }
        
        self.combo_attacks = {
            "Swordsman": {
                "Gomu Gomu no Mi": "Gum-Gum Sword Whip",
                "Mera Mera no Mi": "Flame-Edged Blade Dance",
                "Hie Hie no Mi": "Frozen Sword Barrage",
                "Pika Pika no Mi": "Light Speed Slash",
                "Gura Gura no Mi": "Tremor Blade Quake",
                "Yami Yami no Mi": "Dark Matter Slash",
                "Ope Ope no Mi": "Precision Surgical Strike",
                "Magu Magu no Mi": "Magma Sword Eruption",
                "Goro Goro no Mi": "Thunder Blade Tempest",
                "Suna Suna no Mi": "Sand Storm Blade",
                "Mochi Mochi no Mi": "Sticky Blade Assault",
                "Bara Bara no Mi": "Separate Sword Dance",
                "Doku Doku no Mi": "Venomous Blade Strike",
                "Hana Hana no Mi": "Blooming Sword Garden",
                "Kilo Kilo no Mi": "Gravity Slash"
            },
            "Martial Artist": {
                "Gomu Gomu no Mi": "Elastic Fist Gatling",
                "Mera Mera no Mi": "Blazing Kick Tempest",
                "Hie Hie no Mi": "Frost-Knuckle Assault",
                "Pika Pika no Mi": "Light Speed Barrage",
                "Gura Gura no Mi": "Seismic Shockwave Punch",
                "Yami Yami no Mi": "Gravity Well Throw",
                "Ope Ope no Mi": "Shambles Combo Strike",
                "Magu Magu no Mi": "Volcanic Eruption Fist",
                "Goro Goro no Mi": "Thunder God's Wrath",
                "Suna Suna no Mi": "Desert Whirlwind Kick",
                "Mochi Mochi no Mi": "Sticky Mochi Beatdown",
                "Bara Bara no Mi": "Chop-Chop Cannon",
                "Doku Doku no Mi": "Toxic Touch Combo",
                "Hana Hana no Mi": "Thousand-Arm Barrage",
                "Kilo Kilo no Mi": "Meteor Punch"
            },
            "Sniper": {
                "Gomu Gomu no Mi": "Rubber Bullet Barrage",
                "Mera Mera no Mi": "Inferno Snipe",
                "Hie Hie no Mi": "Absolute Zero Shot",
                "Pika Pika no Mi": "Photon Beam Precision",
                "Gura Gura no Mi": "Shatterpoint Precision Shot",
                "Yami Yami no Mi": "Black Hole Projectile",
                "Ope Ope no Mi": "Surgical Snipe",
                "Magu Magu no Mi": "Magma Meteor Shower",
                "Goro Goro no Mi": "Lightning Bolt Accuracy",
                "Suna Suna no Mi": "Sandstorm Spread Shot",
                "Mochi Mochi no Mi": "Sticky Trap Shot",
                "Bara Bara no Mi": "Separate Homing Missile",
                "Doku Doku no Mi": "Venom Dart Volley",
                "Hana Hana no Mi": "Bloom-Bloom Crossfire",
                "Kilo Kilo no Mi": "Variable Mass Bullet"
            },
            "Brawler": {
                "Gomu Gomu no Mi": "Gum-Gum Storm",
                "Mera Mera no Mi": "Flame Emperor's Wrath",
                "Hie Hie no Mi": "Absolute Zero Smash",
                "Pika Pika no Mi": "Light Speed Barrage",
                "Gura Gura no Mi": "World Shaker Assault",
                "Yami Yami no Mi": "Black Hole Crush",
                "Ope Ope no Mi": "Operating Room Rampage",
                "Magu Magu no Mi": "Volcanic Devastation",
                "Goro Goro no Mi": "Million Volt Mayhem",
                "Suna Suna no Mi": "Sahara Tempest",
                "Mochi Mochi no Mi": "Mochi Mochi Pummeling",
                "Bara Bara no Mi": "Chop-Chop Festival",
                "Doku Doku no Mi": "Venom Demon Onslaught",
                "Hana Hana no Mi": "Cien Fleur Fury",
                "Kilo Kilo no Mi": "Mass Shift Beatdown"
            },
            "Tactician": {
                "Gomu Gomu no Mi": "Elastic Trap Network",
                "Mera Mera no Mi": "Firewall Strategy",
                "Hie Hie no Mi": "Cryo-Lockdown Maneuver",
                "Pika Pika no Mi": "Lightspeed Tactical Array",
                "Gura Gura no Mi": "Tectonic Battlefield Control",
                "Yami Yami no Mi": "Void Field Tactics",
                "Ope Ope no Mi": "Surgical Strike Plan",
                "Magu Magu no Mi": "Magma Flow Redirect",
                "Goro Goro no Mi": "Thunder Cloud Formation",
                "Suna Suna no Mi": "Sandstorm Cover Op",
                "Mochi Mochi no Mi": "Sticky Situation Setup",
                "Bara Bara no Mi": "Disassembly Maze",
                "Doku Doku no Mi": "Toxic Terrain Advantage",
                "Hana Hana no Mi": "Spy Network Bloom",
                "Kilo Kilo no Mi": "Gravity Well Trap"
            }
        }
        
        self.devil_fruit_abilities = {
            "Gomu Gomu no Mi": [
                {"name": "Gum-Gum Pistol", "mastery_required": 0},
                {"name": "Gum-Gum Bazooka", "mastery_required": 10},
                {"name": "Gum-Gum Gatling", "mastery_required": 20},
                {"name": "Gear Second", "mastery_required": 30},
                {"name": "Gear Third", "mastery_required": 40},
                {"name": "Gear Fourth", "mastery_required": 50}
            ],
            "Mera Mera no Mi": [
                {"name": "Fire Fist", "mastery_required": 0},
                {"name": "Fire Gun", "mastery_required": 10},
                {"name": "Flame Commandment", "mastery_required": 20},
                {"name": "Firefly", "mastery_required": 30},
                {"name": "Great Flame Commandment", "mastery_required": 40},
                {"name": "Flame Emperor", "mastery_required": 50}
            ],
            "Hie Hie no Mi": [
                {"name": "Ice Age", "mastery_required": 0},
                {"name": "Ice Saber", "mastery_required": 10},
                {"name": "Ice Time", "mastery_required": 20},
                {"name": "Ice Block: Pheasant Beak", "mastery_required": 30},
                {"name": "Ice Time Capsule", "mastery_required": 40},
                {"name": "Ice Age: Eternal Freeze", "mastery_required": 50}
            ],
            "Pika Pika no Mi": [
                {"name": "Light Speed Kick", "mastery_required": 0},
                {"name": "Yata no Kagami", "mastery_required": 10},
                {"name": "Ama no Murakumo", "mastery_required": 20},
                {"name": "Yasakani no Magatama", "mastery_required": 30},
                {"name": "Light Logia Transformation", "mastery_required": 40},
                {"name": "Photon Teleportation", "mastery_required": 50}
            ],
            "Gura Gura no Mi": [
                {"name": "Shock Wave", "mastery_required": 0},
                {"name": "Seaquake", "mastery_required": 10},
                {"name": "Island Quake", "mastery_required": 20},
                {"name": "Tilting", "mastery_required": 30},
                {"name": "Tsunami", "mastery_required": 40},
                {"name": "Shattered Space", "mastery_required": 50}
            ],
            "Yami Yami no Mi": [
                {"name": "Black Hole", "mastery_required": 0},
                {"name": "Liberation", "mastery_required": 10},
                {"name": "Kurouzu", "mastery_required": 20},
                {"name": "Blackbeard Whirlpool", "mastery_required": 30},
                {"name": "Black World", "mastery_required": 40},
                {"name": "Dark End", "mastery_required": 50}
            ],
            "Suna Suna no Mi": [
                {"name": "Desert Spada", "mastery_required": 0},
                {"name": "Desert Girasole", "mastery_required": 10},
                {"name": "Sables", "mastery_required": 20},
                {"name": "Ground Secco", "mastery_required": 30},
                {"name": "Desert Encierro", "mastery_required": 40},
                {"name": "Sandstorm", "mastery_required": 50}
            ],
            "Magu Magu no Mi": [
                {"name": "Dai Funka", "mastery_required": 0},
                {"name": "Meigo", "mastery_required": 10},
                {"name": "Bakuretsu Kazan", "mastery_required": 20},
                {"name": "Ryusei Kazan", "mastery_required": 30},
                {"name": "Meteor Volcano", "mastery_required": 40},
                {"name": "Great Eruption", "mastery_required": 50}
            ]
        }

    def get_awakening_level(self, mastery):
        for level, data in sorted(self.awakening_levels.items(), reverse=True):
            if mastery >= level:
                return data
        return self.awakening_levels[0]
    
    def get_attack_element(self, attack_name):
            # This method determines the elemental type of an attack based on its name
        if "Fire" in attack_name or "Flame" in attack_name:
            return "fire"
        elif "Water" in attack_name or "Aqua" in attack_name:
            return "water"
        elif "Thunder" in attack_name or "Lightning" in attack_name:
            return "lightning"
        elif "Earth" in attack_name or "Stone" in attack_name:
            return "earth"
        elif "Wind" in attack_name or "Air" in attack_name:
            return "wind"
        else:
            return "normal"

    def apply_terrain_effect(self, attack_power, attack_name, terrain, devil_fruit):
        attack_element = self.get_attack_element(attack_name)
        
        # If the attack doesn't have a specific element, check if it's a Devil Fruit attack
        if attack_element == "normal" and devil_fruit in self.devil_fruit_elements:
            attack_element = self.devil_fruit_elements[devil_fruit]
        
        terrain_modifier = self.terrain_effects[terrain].get(attack_element, 1.0)
        return attack_power * terrain_modifier
    
    async def sea_king_attack(self, ctx, user_data, opponent_data):
        damage = random.randint(50, 100)
        user_data["hp"] -= damage
        opponent_data["hp"] -= damage
        return f"The Sea King attacks both fighters for {damage} damage!"

    async def whirlpool_effect(self, ctx, user_data, opponent_data):
        if user_data.get("devil_fruit"):
            user_data["hp"] -= 50
            return f"{ctx.author.name} is weakened by the whirlpool and loses 50 HP!"
        elif opponent_data.get("devil_fruit"):
            opponent_data["hp"] -= 50
            return f"{opponent_data['name']} is weakened by the whirlpool and loses 50 HP!"
        return "The whirlpool rages, but both fighters manage to stay clear!"

    async def tidal_wave_effect(self, ctx, user_data, opponent_data):
        user_damage = random.randint(30, 70)
        opp_damage = random.randint(30, 70)
        user_data["hp"] -= user_damage
        opponent_data["hp"] -= opp_damage
        return f"The tidal wave crashes into both fighters! {ctx.author.name} takes {user_damage} damage and {opponent_data['name']} takes {opp_damage} damage!"

    async def storm_surge_effect(self, ctx, user_data, opponent_data):
        speed_penalty = 10
        user_data["speed"] = max(0, user_data["speed"] - speed_penalty)
        opponent_data["speed"] = max(0, opponent_data["speed"] - speed_penalty)
        return f"A storm surge hits! Both fighters' speed is reduced by {speed_penalty}!"

    async def volcano_eruption_effect(self, ctx, user_data, opponent_data):
        damage = random.randint(40, 80)
        user_data["hp"] -= damage
        opponent_data["hp"] -= damage
        return f"The volcano erupts, showering both fighters with hot ash and debris! Both take {damage} damage!"

    async def jungle_ambush_effect(self, ctx, user_data, opponent_data):
        if random.random() < 0.5:
            user_data["hp"] -= 30
            return f"Wild animals ambush {ctx.author.name}, dealing 30 damage!"
        else:
            opponent_data["hp"] -= 30
            return f"Wild animals ambush {opponent_data['name']}, dealing 30 damage!"

    async def quicksand_effect(self, ctx, user_data, opponent_data):
        speed_reduction = 20
        user_data["speed"] = max(0, user_data["speed"] - speed_reduction)
        opponent_data["speed"] = max(0, opponent_data["speed"] - speed_reduction)
        return f"Quicksand appears! Both fighters' speed is reduced by {speed_reduction}!"

    async def earthquake_effect(self, ctx, user_data, opponent_data):
        damage = random.randint(20, 60)
        user_data["hp"] -= damage
        opponent_data["hp"] -= damage
        return f"An earthquake shakes the island! Both fighters take {damage} damage and lose their footing!"

    async def falling_debris_effect(self, ctx, user_data, opponent_data):
        if random.random() < 0.5:
            damage = random.randint(30, 70)
            user_data["hp"] -= damage
            return f"Falling debris hits {ctx.author.name}, dealing {damage} damage!"
        else:
            damage = random.randint(30, 70)
            opponent_data["hp"] -= damage
            return f"Falling debris hits {opponent_data['name']}, dealing {damage} damage!"

    async def civilian_panic_effect(self, ctx, user_data, opponent_data):
        speed_boost = 15
        user_data["speed"] += speed_boost
        opponent_data["speed"] += speed_boost
        return f"Panicked civilians create chaos! Both fighters' speed increases by {speed_boost} as they maneuver through the crowd!"

    async def marine_interference_effect(self, ctx, user_data, opponent_data):
        damage = random.randint(10, 40)
        user_data["hp"] -= damage
        opponent_data["hp"] -= damage
        return f"Marine forces interfere with the battle! Both fighters take {damage} damage from stray attacks!"

    async def blackout_effect(self, ctx, user_data, opponent_data):
        accuracy_penalty = 20
        user_data["accuracy"] = max(0, user_data.get("accuracy", 100) - accuracy_penalty)
        opponent_data["accuracy"] = max(0, opponent_data.get("accuracy", 100) - accuracy_penalty)
        return f"A sudden blackout occurs! Both fighters' accuracy is reduced by {accuracy_penalty}%!"
    
    async def trigger_hazard(self, ctx, environment, user_data, opponent_data):
        if random.random() < 0.2:  # 20% chance of a hazard occurring
            hazard = random.choice(self.battle_hazards[environment])
            await ctx.send(f"**{hazard['name']}**: {hazard['description']}")
            effect_message = await hazard['effect'](ctx, user_data, opponent_data)
            await ctx.send(effect_message)
            return True
        return False
    
    async def check_new_techniques(self, user):
        """Check and grant new techniques based on user's level"""
        user_data = await self.config.user(user).all()
        fighting_style = user_data["fighting_style"]
        current_level = user_data["level"]
        learned_techniques = user_data["learned_techniques"]

        new_techniques = []
        for technique in self.techniques[fighting_style]:
            if technique["level"] <= current_level and technique["name"] not in learned_techniques:
                learned_techniques.append(technique["name"])
                new_techniques.append(technique["name"])

        if new_techniques:
            await self.config.user(user).learned_techniques.set(learned_techniques)
            return new_techniques
        return []

    async def devil_fruit_spawn(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                await asyncio.sleep(random.randint(3600, 7200))  # Random spawn time between 1-2 hours
                channel_id = await self.config.spawn_channel_id()
                if not channel_id:
                    self.logger.warning("No spawn channel set. Skipping spawn.")
                    continue

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    self.logger.error(f"Could not find channel with ID {channel_id}")
                    continue

                devil_fruit = random.choice(list(self.devil_fruits.keys()))
                embed = discord.Embed(
                    title="Devil Fruit Spawn!",
                    description=f"A {devil_fruit} has spawned in this channel! React with 🍎 to claim it!",
                    color=discord.Color.gold()
                )
                message = await channel.send(embed=embed)
                await message.add_reaction("🍎")

                def check(reaction, user):
                    return str(reaction.emoji) == "🍎" and user != self.bot.user and reaction.message.id == message.id

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await message.delete()
                    self.logger.info("Devil Fruit spawn timed out")
                else:
                    user_data = await self.config.user(user).all()
                    if user_data["devil_fruit"]:
                        await channel.send(f"{user.mention}, you already have a Devil Fruit!")
                    else:
                        user_data["devil_fruit"] = devil_fruit
                        await self.config.user(user).set(user_data)
                        await channel.send(f"Congratulations {user.mention}! You have claimed the {devil_fruit}!")
                        self.logger.info(f"User {user.id} claimed the {devil_fruit}")

            except Exception as e:
                self.logger.error(f"Error in devil_fruit_spawn: {str(e)}", exc_info=True)
                await asyncio.sleep(300)  # Wait 5 minutes before trying again

    async def handle_gear_stamina(self, user_data):
        if "active_gear" in user_data:
            gear_data = self.gear_system[user_data["active_gear"]]
            user_data["stamina"] -= gear_data["stamina_cost"] // 2  # Continuous drain
            if user_data["stamina"] <= 0:
                del user_data["active_gear"]
                await self.config.user(user_data["_id"]).set(user_data)
                return "Your Gear has deactivated due to stamina depletion!"
        return None
    
    async def periodic_bounty_update(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.update_top_bounties()
            await asyncio.sleep(3600)  # Update every hour

    async def update_top_bounties(self):
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get('bounty', 0), reverse=True)
        top_50 = sorted_users[:50]

        top_bounties = [
            {"user_id": user_id, "bounty": user_data.get('bounty', 0)}
            for user_id, user_data in top_50
        ]

        await self.config.top_bounties.set(top_bounties)
        await self.config.last_bounty_update.set(datetime.datetime.utcnow().isoformat())
        
    async def raftel_effect(self, ctx, user_data, opponent_data):
        """Double all stats for both fighters"""
        for stat in ['strength', 'speed', 'defense']:
            user_data[stat] *= 2
            opponent_data[stat] *= 2
        return "The power of Raftel doubles all stats for both fighters!"

    async def all_blue_effect(self, ctx, user_data, opponent_data):
        """Heal both fighters and boost water-based attacks"""
        heal_amount = 50
        user_data['hp'] = min(user_data['max_hp'], user_data['hp'] + heal_amount)
        opponent_data['hp'] = min(opponent_data['max_hp'], opponent_data['hp'] + heal_amount)
        return f"The healing waters of All Blue restore {heal_amount} HP to both fighters and boost water-based attacks!"

    async def emerald_city_effect(self, ctx, user_data, opponent_data):
        """Randomly enhance one stat for each fighter"""
        user_stat = random.choice(['strength', 'speed', 'defense'])
        opp_stat = random.choice(['strength', 'speed', 'defense'])
        user_data[user_stat] *= 1.5
        opponent_data[opp_stat] *= 1.5
        return f"The advanced technology of Emerald City enhances {ctx.author.name}'s {user_stat} and {opponent_data['name']}'s {opp_stat}!"

    async def god_valley_effect(self, ctx, user_data, opponent_data):
        """Temporarily unlock advanced Haki for both fighters"""
        haki_boost = 50
        for haki_type in user_data['haki']:
            user_data['haki'][haki_type] += haki_boost
            opponent_data['haki'][haki_type] += haki_boost
        return f"The mysterious power of God Valley unlocks advanced Haki for both fighters, boosting all Haki types by {haki_boost}!"

    async def laugh_tale_effect(self, ctx, user_data, opponent_data):
        """Reveal the 'Voice of All Things' to one random fighter"""
        if random.choice([True, False]):
            user_data['voice_of_all_things'] = True
            return f"{ctx.author.name} hears the Voice of All Things, gaining incredible insight!"
        else:
            opponent_data['voice_of_all_things'] = True
            return f"{opponent_data['name']} hears the Voice of All Things, gaining incredible insight!"
        
    async def update_discovered_zones(self, user, zone):
        async with self.config.user(user).all() as user_data:
            user_data.setdefault('discovered_zones', [])
            if zone not in user_data['discovered_zones']:
                user_data['discovered_zones'].append(zone)
                
    async def battle_royale_scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            all_guilds = await self.config.all_guilds()
            for guild_id, guild_data in all_guilds.items():
                if guild_data["battle_royale_channel"] and not guild_data["ongoing_battle_royale"]:
                    next_battle = guild_data["next_battle_royale"]
                    if next_battle and datetime.now() >= datetime.fromisoformat(next_battle):
                        guild = self.bot.get_guild(guild_id)
                        if guild:
                            await self.start_battle_royale(guild)
            await asyncio.sleep(60)  # Check every minute
    
    def cog_unload(self):
        # Cancel the update task when the cog is unloaded
        if self.bounty_update_task:
            self.bounty_update_task.cancel()

    def cog_unload(self):
        if self.spawn_task:
            self.spawn_task.cancel()
            
    def cog_unload(self):
        if self.battle_royale_task:
            self.battle_royale_task.cancel()
            

    @commands.group()
    async def op(self, ctx):
        pass
    
    @op.command()
    async def begin(self, ctx):
        """Start your One Piece journey"""
        user_data = await self.config.user(ctx.author).all()

        if user_data["fighting_style"]:
            await ctx.send("You've already begun your journey!")
            return

        await ctx.send(f"{ctx.author.mention}, welcome to the world of One Piece! I am Gol D. Roger. Are you ready to start your journey and become the Pirate King? (React with ⚔️ to begin)")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '⚔️'

        try:
            await ctx.message.add_reaction('⚔️')
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, you took too long to decide. Come back when you're ready to start your journey!")
            return

        fighting_styles = ["Swordsman", "Martial Artist", "Sniper", "Brawler", "Tactician"]

        embed = discord.Embed(title="Character Creation", color=discord.Color.gold())
        embed.add_field(name="Fighting Styles", value="\n".join([f"{i+1}. {style}" for i, style in enumerate(fighting_styles)]), inline=False)

        embed.set_footer(text="Type the number of your fighting style choice")

        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, you took too long to decide. Come back when you're ready to start your journey!")
            return

        try:
            style_choice = int(msg.content) - 1
            if not (0 <= style_choice < len(fighting_styles)):
                raise ValueError
        except (ValueError, TypeError):
            await ctx.send(f"{ctx.author.mention}, invalid choice. Please try again and follow the instructions carefully.")
            return

        user_data["fighting_style"] = fighting_styles[style_choice]
        user_data["doriki"] = 500
        user_data["bounty"] = 0
        await self.config.user(ctx.author).set(user_data)

        await ctx.send(f"{ctx.author.mention}, you have begun your journey as a {user_data['fighting_style']}! Your initial Doriki is {user_data['doriki']}. Train hard and make a name for yourself!")
    
    @op.command(name="battle")
    async def battle(self, ctx, opponent: discord.Member = None):
        """Start a battle with another user or a strong AI opponent"""
        user_data = await self.config.user(ctx.author).all()

        if user_data["fatigue"] >= self.max_fatigue:
            await ctx.send(f"{ctx.author.mention}, you're too fatigued to battle! You need to rest first.")
            return

        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return

        if opponent:
            opponent_data = await self.config.user(opponent).all()
            if not opponent_data["fighting_style"]:
                await ctx.send(f"{opponent.mention} has not begun their journey yet!")
                return
            opponent_name = opponent.name
        else:
            ai_names = ["Admiral Akainu", "Yonko Kaido", "Shichibukai Doflamingo", "CP0 Rob Lucci", "Revolutionary Dragon"]
            opponent_name = random.choice(ai_names)
            opponent = ctx.author  # This is just to reuse the existing logic
            opponent_data = self.create_ai_opponent(opponent_name)

        # Determine battle environment
        battle_env = random.choice(list(self.environments.keys()))
        env_effect = self.environments[battle_env]

        # Check for Mythical Zone
        mythical_zone = None
        for zone, data in self.mythical_zones.items():
            if random.random() < data['spawn_chance']:
                mythical_zone = zone
                break

        if mythical_zone:
            battle_env = mythical_zone
            await ctx.send(f"**Mythical Zone Discovered: {mythical_zone}!**\n{self.mythical_zones[mythical_zone]['description']}")
            effect_message = await self.mythical_zones[mythical_zone]['effect'](ctx, user_data, opponent_data)
            await ctx.send(effect_message)
        else:
            await ctx.send(f"The battle takes place in a {battle_env} environment!")

        battle_embed = discord.Embed(
            title=f"⚔️ __**Epic Battle: {ctx.author.name} vs {opponent_name}**__ ⚔️",
            description=f"*{env_effect['description']} The seas tremble as two mighty warriors clash!*",
            color=discord.Color.red()
        )
        battle_message = await ctx.send(embed=battle_embed)

        # Calculate base strength
        user_strength = max(1, user_data["doriki"] + sum(user_data["haki"].values()) + user_data["strength"])
        opp_strength = max(1, opponent_data["doriki"] + sum(opponent_data["haki"].values()) + opponent_data["strength"])

        # Apply Legendary Weapon boost
        user_strength = self.apply_legendary_weapon(user_data, user_strength)
        opp_strength = self.apply_legendary_weapon(opponent_data, opp_strength)

        # Apply Devil Fruit boost (including awakening)
        user_strength = self.apply_devil_fruit_boost(user_data, user_strength)
        opp_strength = self.apply_devil_fruit_boost(opponent_data, opp_strength)

        # Apply Gear boost for Paramecia users
        user_strength = self.apply_gear_boost(user_data, user_strength)
        opp_strength = self.apply_gear_boost(opponent_data, opp_strength)

        # Apply fatigue penalty to user's strength
        fatigue_penalty = 1 - (user_data["fatigue"] / self.max_fatigue) * 0.5  # Max 50% penalty at full fatigue
        user_strength *= fatigue_penalty

        # Apply environment effects
        if user_data["devil_fruit"]:
            user_strength *= env_effect["df_modifier"]
        else:
            user_strength *= env_effect["non_df_modifier"]
        
        if opponent_data["devil_fruit"]:
            opp_strength *= env_effect["df_modifier"]
        else:
            opp_strength *= env_effect["non_df_modifier"]

        user_hp = user_strength * 20
        opp_hp = opp_strength * 20

        # Equipment effects
        for item in user_data["equipped_items"]:
            for stat, value in self.equipment[item].items():
                if stat == "strength":
                    user_strength += value
                elif stat == "speed":
                    user_data["speed"] += value
                elif stat == "defense":
                    user_data["defense"] += value

        for item in opponent_data["equipped_items"]:
            for stat, value in self.equipment[item].items():
                if stat == "strength":
                    opp_strength += value
                elif stat == "speed":
                    opponent_data["speed"] += value
                elif stat == "defense":
                    opponent_data["defense"] += value

        battle_log = []

        def get_health_bar(current_hp, max_hp, bar_length=10):
            fill = int(current_hp / max_hp * bar_length)
            if fill <= bar_length * 0.2:
                color = "🟥"
            elif fill <= bar_length * 0.5:
                color = "🟨"
            else:
                color = "🟩"
            return f"{color * fill}{'⬜' * (bar_length - fill)}"

        async def update_battle_embed():
            battle_embed.description = f"*{env_effect['description']}*\n" + "*" + "\n".join(battle_log[-3:]) + "*"
            user_health = get_health_bar(user_hp, user_strength * 20)
            opp_health = get_health_bar(opp_hp, opp_strength * 20)
            
            user_health_text = f"**{ctx.author.name}**\n{user_health} {user_hp:.0f}/{user_strength * 20:.0f} HP"
            opp_health_text = f"**{opponent_name}**\n{opp_health} {opp_hp:.0f}/{opp_strength * 20:.0f} HP"
            
            battle_embed.set_field_at(0, name="__Health Status__", value=f"{user_health_text}\n\n{opp_health_text}", inline=False)
            
            await battle_message.edit(embed=battle_embed)

        battle_embed.add_field(name="__Health Status__", value="", inline=False)
        battle_embed.add_field(name="__Battle Environment__", value=f"{battle_env}: {env_effect['description']}", inline=False)

        user_awakened = False
        opp_awakened = False

        turn_counter = 0
        while user_hp > 0 and opp_hp > 0:
            turn_counter += 1
            
            # Generate attacks
            user_attack, user_technique = self.generate_attack(ctx.author, user_data, user_strength)
            opp_attack, opp_technique = self.generate_attack(opponent, opponent_data, opp_strength)

            # Apply terrain effects
            user_attack = self.apply_terrain_effect(user_attack, user_technique, battle_env, user_data.get("devil_fruit"))
            opp_attack = self.apply_terrain_effect(opp_attack, opp_technique, battle_env, opponent_data.get("devil_fruit"))

            # Devil Fruit Awakening chance
            if not user_awakened and user_data["devil_fruit"] and random.random() < self.awakening_chance:
                awakening_boost = self.get_awakening_level(user_data.get("devil_fruit_mastery", 0))["boost"]
                user_strength *= awakening_boost
                user_awakened = True
                battle_log.append(f"💥 {ctx.author.name}'s Devil Fruit has temporarily awakened, boosting their power!")

            if not opp_awakened and opponent_data["devil_fruit"] and random.random() < self.awakening_chance:
                awakening_boost = self.get_awakening_level(opponent_data.get("devil_fruit_mastery", 0))["boost"]
                opp_strength *= awakening_boost
                opp_awakened = True
                battle_log.append(f"💥 {opponent_name}'s Devil Fruit has temporarily awakened, boosting their power!")

            # Handle Gear stamina drain
            gear_message = await self.handle_gear_stamina(user_data)
            if gear_message:
                battle_log.append(gear_message)
                user_strength = self.apply_gear_boost(user_data, user_strength)

            # Critical hit chance (10%)
            if random.random() < 0.1:
                user_attack *= 2
                battle_log.append(f"💥 **CRITICAL HIT!** {ctx.author.name}'s attack devastates the opponent!")

            # Dodge chance
            total_speed = max(1, user_data["speed"] + opponent_data["speed"])
            user_dodge_chance = user_data["speed"] / total_speed
            if random.random() < user_dodge_chance:
                opp_attack = 0
                battle_log.append(f"💨 With lightning speed, {ctx.author.name} **DODGES** the attack!")

            # Battle Hazards
            hazard_occurred = await self.trigger_hazard(ctx, battle_env, user_data, opponent_data)
            if hazard_occurred:
                await update_battle_embed()
                await asyncio.sleep(2)

            opp_hp = max(0, opp_hp - user_attack)
            user_hp = max(0, user_hp - opp_attack)

            battle_log.append(f"**Turn {turn_counter}**")
            battle_log.append(f"🌊 {ctx.author.name} unleashes **{user_technique}** with {user_attack:.0f} power!")
            battle_log.append(f"🔥 {opponent_name} retaliates with **{opp_technique}**, dealing {opp_attack:.0f} damage!")

            await update_battle_embed()
            await asyncio.sleep(2)

            if turn_counter >= 30:
                battle_log.append("⏱️ The battle has reached its time limit!")
                break

        # Reset awakening boost after battle
        if user_awakened:
            user_strength /= awakening_boost
        if opp_awakened:
            opp_strength /= awakening_boost

        if user_hp > opp_hp:
            winner = ctx.author
            loser = opponent
            winner_data = user_data
            loser_data = opponent_data
            is_victory = True
        else:
            winner = opponent
            loser = ctx.author
            winner_data = opponent_data
            loser_data = user_data
            is_victory = False

        if is_victory:
            doriki_gain = random.randint(100, 250)
            haki_gain = random.randint(5, 15)
            bounty_gain = loser_data.get("bounty", 0) // 20 if loser_data.get("bounty", 0) > 0 else random.randint(10000000, 50000000)

            user_data["doriki"] += doriki_gain
            user_data["haki"]["observation"] += haki_gain
            user_data["haki"]["armament"] += haki_gain
            user_data["haki"]["conquerors"] += haki_gain // 2
            user_data["bounty"] = user_data.get("bounty", 0) + bounty_gain
            user_data["battles_won"] = user_data.get("battles_won", 0) + 1

            # Increase Devil Fruit mastery
            if user_data["devil_fruit"]:
                mastery_gain = random.randint(1, 5)
                user_data["devil_fruit_mastery"] = min(100, user_data.get("devil_fruit_mastery", 0) + mastery_gain)
                await self.check_new_abilities(ctx, user_data)

            result_embed = discord.Embed(
                title="🏆 __**Battle Conclusion**__ 🏆",
                description=f"***In an epic clash on {battle_env}, {ctx.author.name} emerges victorious against {opponent_name}!***",
                color=discord.Color.gold()
            )
            result_embed.add_field(name="💪 Doriki Gained", value=f"**{doriki_gain}**")
            result_embed.add_field(name="🔮 Haki Improved", value=f"**{haki_gain}**")
            result_embed.add_field(name="💰 Bounty Increased", value=f"**{bounty_gain:,}**")
            if user_data["devil_fruit"]:
                result_embed.add_field(name="🍎 Devil Fruit Mastery", value=f"+{mastery_gain} (Total: {user_data['devil_fruit_mastery']})", inline=True)

            if random.random() < 0.3:
                reward, description = self.generate_post_battle_reward()
                result_embed.add_field(name=f"🎁 Special Reward: {reward}", value=description, inline=False)

            # Mythical Zone reward
            if mythical_zone:
                mythical_reward = self.mythical_zones[mythical_zone]['reward']
                user_data.setdefault('inventory', []).append(mythical_reward)
                result_embed.add_field(name="🏝️ Mythical Zone Reward", value=f"You've obtained: {mythical_reward}!", inline=False)
        else:
            # Penalties for losing
            doriki_loss = random.randint(50, 150)
            bounty_loss = user_data.get("bounty", 0) // 10  # Lose 10% of current bounty
            
            user_data["doriki"] = max(0, user_data["doriki"] - doriki_loss)
            user_data["bounty"] = max(0, user_data["bounty"] - bounty_loss)

            result_embed = discord.Embed(
                title="💀 __**Battle Conclusion**__ 💀",
                description=f"***In a fierce battle on {battle_env}, {opponent_name} has defeated {ctx.author.name}!***",
                color=discord.Color.red()
            )
            result_embed.add_field(name="💪 Doriki Lost", value=f"**{doriki_loss}**")
            result_embed.add_field(name="💰 Bounty Decreased", value=f"**{bounty_loss:,}**")

        # Common operations for both win and loss
        user_data["stamina"] = max(0, user_data.get("stamina", 100) - 20)
        user_data["fatigue"] = min(self.max_fatigue, user_data["fatigue"] + self.fatigue_per_battle)
        result_embed.add_field(name="😓 Fatigue", value=f"{user_data['fatigue']}/{self.max_fatigue}", inline=True)

        # Remove active gear after battle
        if "active_gear" in user_data:
            del user_data["active_gear"]

        # Update user data in the database
        await self.config.user(ctx.author).set(user_data)

        # Update opponent data if it's a real player
        if isinstance(opponent, discord.Member):
            await self.config.user(opponent).set(opponent_data)

        # Add experience
        exp_gain = random.randint(50, 100) if is_victory else random.randint(20, 50)
        user_data["experience"] += exp_gain
        result_embed.add_field(name="📊 Experience Gained", value=f"**{exp_gain}**", inline=True)

        # Check for level up
        level_up_message = await self.check_level_up(ctx.author, user_data)
        if level_up_message:
            result_embed.add_field(name="🎉 Level Up!", value=level_up_message, inline=False)

        # Update bounty rankings
        await self.update_bounty_rankings(ctx.guild, ctx.author, user_data["bounty"])

        # Send the final result embed
        await battle_message.edit(embed=result_embed)

        # If it was a Mythical Zone battle, update the user's discovered zones
        if mythical_zone:
            await self.update_discovered_zones(ctx.author, mythical_zone)

        # Trigger any post-battle events
        await self.trigger_post_battle_events(ctx, is_victory, battle_env)

    async def check_level_up(self, user, user_data):
        exp_needed = user_data["level"] * 100
        if user_data["experience"] >= exp_needed:
            user_data["level"] += 1
            user_data["experience"] -= exp_needed
            user_data["skill_points"] += 3
            await self.config.user(user).set(user_data)
            return f"{user.mention} has reached level {user_data['level']}! You've gained 3 skill points."
        return None

    async def update_bounty_rankings(self, guild, user, bounty):
        async with self.config.bounty_rankings() as rankings:
            rankings[str(user.id)] = bounty
            # Keep only top 100 bounties
            sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:100]
            rankings.clear()
            rankings.update(dict(sorted_rankings))

    async def update_discovered_zones(self, user, zone):
        async with self.config.user(user).discovered_zones() as zones:
            if zone not in zones:
                zones.append(zone)

    async def trigger_post_battle_events(self, ctx, is_victory, battle_env):
        user_data = await self.config.user(ctx.author).all()

    async def apply_temporary_effects(self, ctx, user_data):
        current_time = datetime.now()
        active_effects = []
        for effect in user_data.get("temporary_effects", []):
            if current_time < effect["expiry"]:
                active_effects.append(effect)
                await ctx.send(f"🔮 Active effect: {effect['name']} - {effect['description']}")
                # Apply effect logic here
                if effect["name"] == "Adrenaline Rush":
                    user_data["strength"] *= 1.2
                elif effect["name"] == "Battle Fatigue":
                    user_data["stamina_regen"] *= 0.8
                elif effect["name"] == "Minor Injury":
                    user_data["speed"] *= 0.9
                elif effect["name"] == "Heightened Senses":
                    user_data["haki"]["observation"] *= 1.2
            
        user_data["temporary_effects"] = active_effects
        await self.config.user(ctx.author).set(user_data)
        
    async def trigger_post_battle_events(self, ctx, is_victory, battle_env):
        user_data = await self.config.user(ctx.author).all()

        # Item Discovery Event (15% chance)
        if random.random() < 0.15:
            special_items = [
                "Mystery Map", "Ancient Coin", "Strange Device", "Broken Log Pose",
                "Vivre Card Fragment", "Unidentified Fruit", "Weathered Jolly Roger",
                "Encrypted Message", "Mysterious Key", "Odd Compass"
            ]
            special_item = random.choice(special_items)
            user_data.setdefault("inventory", []).append(special_item)
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"🎁 In the aftermath of the battle, {ctx.author.mention} discovers a {special_item}!")

        # World Event (10% chance)
        if random.random() < 0.10:
            world_events = [
                f"News of the fierce battle in {battle_env} spreads across the world!",
                f"A mysterious figure was spotted watching the battle in {battle_env}...",
                f"The clash in {battle_env} has attracted the attention of a nearby pirate crew!",
                f"Marine headquarters receives a report about unusual activity in {battle_env}.",
                f"A powerful tremor shakes {battle_env} following the intense battle!"
            ]
            event_message = random.choice(world_events)
            await ctx.send(f"📰 **Breaking News**: {event_message}")
            # TODO: Implement logic to affect world state based on these events

        # Character Interaction (20% chance)
        if random.random() < 0.20:
            interactions = [
                f"A local shopkeeper, impressed by your battle, offers you a discount on your next purchase!",
                f"A mysterious old man approaches, sharing cryptic wisdom about your fighting style.",
                f"A group of aspiring pirates asks to join your crew after witnessing your strength!",
                f"A rival pirate crew sends you a message, challenging you to a future confrontation.",
                f"A Marine scout was watching your battle. Your actions have influenced their report."
            ]
            interaction = random.choice(interactions)
            await ctx.send(f"👥 **Interaction**: {interaction}")
            # TODO: Implement effects of these interactions (e.g., temporary buffs, future quests)

        # Temporary Buff/Debuff (25% chance for winners, 15% for losers)
        buff_chance = 0.25 if is_victory else 0.15
        if random.random() < buff_chance:
            buffs = [
                ("Adrenaline Rush", "Your next battle will start with a 20% strength boost!"),
                ("Battle Fatigue", "Your stamina regeneration is reduced for the next hour."),
                ("Inspired Technique", "You've gained insight into a new fighting move!"),
                ("Minor Injury", "Your speed is slightly reduced in your next battle."),
                ("Heightened Senses", "Your observation Haki is temporarily sharpened!")
            ]
            buff, description = random.choice(buffs)
            user_data["temporary_effects"] = user_data.get("temporary_effects", []) + [buff]
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"✨ **Battle Effect**: {buff} - {description}")

        # Rare Event (5% chance)
        if random.random() < 0.05:
            rare_events = [
                f"A Sea King emerges near {battle_env}, curious about the commotion!",
                f"A celestial phenomenon occurs over {battle_env}, said to be an omen of great change.",
                f"The battle has unknowingly unveiled an ancient ruin in {battle_env}!",
                f"A legendary pirate was secretly observing your battle technique.",
                f"Your actions in {battle_env} have slightly altered the local balance of power!"
            ]
            rare_event = random.choice(rare_events)
            await ctx.send(f"🌟 **Rare Occurrence**: {rare_event}")
            # TODO: Implement significant effects for these rare events

        # Experience Bonus (30% chance for winners, 10% for losers)
        exp_chance = 0.30 if is_victory else 0.10
        if random.random() < exp_chance:
            exp_bonus = random.randint(10, 50)
            user_data["experience"] += exp_bonus
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"📊 **Bonus Experience**: You gained an additional {exp_bonus} XP from this battle!")

        # TODO: Implement any necessary world state updates or trigger follow-up events

    async def trigger_post_battle_events(self, ctx, is_victory, battle_env):
        user_data = await self.config.user(ctx.author).all()

        # Item Discovery Event (15% chance)
        if random.random() < 0.15:
            special_items = [
                "Mystery Map", "Ancient Coin", "Strange Device", "Broken Log Pose",
                "Vivre Card Fragment", "Unidentified Fruit", "Weathered Jolly Roger",
                "Encrypted Message", "Mysterious Key", "Odd Compass"
            ]
            special_item = random.choice(special_items)
            user_data.setdefault("inventory", []).append(special_item)
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"🎁 In the aftermath of the battle, {ctx.author.mention} discovers a {special_item}!")

        # World Event (10% chance)
        if random.random() < 0.10:
            await self.trigger_world_event(ctx, battle_env)

        # Character Interaction (20% chance)
        if random.random() < 0.20:
            await self.trigger_character_interaction(ctx)

        # Temporary Buff/Debuff (25% chance for winners, 15% for losers)
        buff_chance = 0.25 if is_victory else 0.15
        if random.random() < buff_chance:
            await self.apply_temporary_buff(ctx, user_data)

        # Rare Event (5% chance)
        if random.random() < 0.05:
            await self.trigger_rare_event(ctx, battle_env)

        # Experience Bonus (30% chance for winners, 10% for losers)
        exp_chance = 0.30 if is_victory else 0.10
        if random.random() < exp_chance:
            exp_bonus = random.randint(10, 50)
            user_data["experience"] += exp_bonus
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"📊 **Bonus Experience**: You gained an additional {exp_bonus} XP from this battle!")

    async def trigger_world_event(self, ctx, battle_env):
        world_events = [
            f"News of the fierce battle in {battle_env} spreads across the world!",
            f"A mysterious figure was spotted watching the battle in {battle_env}...",
            f"The clash in {battle_env} has attracted the attention of a nearby pirate crew!",
            f"Marine headquarters receives a report about unusual activity in {battle_env}.",
            f"A powerful tremor shakes {battle_env} following the intense battle!"
        ]
        event_message = random.choice(world_events)
        await ctx.send(f"📰 **Breaking News**: {event_message}")
        
        async with self.config.world_state() as world_state:
            world_state["world_events"].append(event_message)
            if "pirate" in event_message.lower():
                world_state["pirate_influence"] = min(100, world_state["pirate_influence"] + 5)
            elif "marine" in event_message.lower():
                world_state["marine_presence"] = min(100, world_state["marine_presence"] + 5)

    async def trigger_character_interaction(self, ctx):
        interactions = [
            ("A local shopkeeper, impressed by your battle, offers you a discount on your next purchase!", "discount_coupon"),
            ("A mysterious old man approaches, sharing cryptic wisdom about your fighting style.", "wisdom_boost"),
            ("A group of aspiring pirates asks to join your crew after witnessing your strength!", "crew_request"),
            ("A rival pirate crew sends you a message, challenging you to a future confrontation.", "rival_challenge"),
            ("A Marine scout was watching your battle. Your actions have influenced their report.", "marine_attention")
        ]
        interaction, quest_type = random.choice(interactions)
        await ctx.send(f"👥 **Interaction**: {interaction}")
        
        quest = {
            "type": quest_type,
            "description": interaction,
            "expiry": datetime.now() + timedelta(days=7)
        }
        async with self.config.user(ctx.author).active_quests() as active_quests:
            active_quests.append(quest)

    async def apply_temporary_buff(self, ctx, user_data):
        buffs = [
            ("Adrenaline Rush", "Your next battle will start with a 20% strength boost!", timedelta(hours=2)),
            ("Battle Fatigue", "Your stamina regeneration is reduced for the next hour.", timedelta(hours=1)),
            ("Inspired Technique", "You've gained insight into a new fighting move!", timedelta(days=1)),
            ("Minor Injury", "Your speed is slightly reduced in your next battle.", timedelta(hours=3)),
            ("Heightened Senses", "Your observation Haki is temporarily sharpened!", timedelta(hours=4))
        ]
        buff, description, duration = random.choice(buffs)
        effect = {
            "name": buff,
            "description": description,
            "expiry": datetime.now() + duration
        }
        user_data.setdefault("temporary_effects", []).append(effect)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"✨ **Battle Effect**: {buff} - {description}")

    async def trigger_rare_event(self, ctx, battle_env):
        rare_events = [
            f"A Sea King emerges near {battle_env}, curious about the commotion!",
            f"A celestial phenomenon occurs over {battle_env}, said to be an omen of great change.",
            f"The battle has unknowingly unveiled an ancient ruin in {battle_env}!",
            f"A legendary pirate was secretly observing your battle technique.",
            f"Your actions in {battle_env} have slightly altered the local balance of power!"
        ]
        rare_event = random.choice(rare_events)
        await ctx.send(f"🌟 **Rare Occurrence**: {rare_event}")
        
        # Update world state
        async with self.config.world_state() as world_state:
            world_state["world_events"].append(rare_event)
            world_state["pirate_influence"] = max(0, min(100, world_state["pirate_influence"] + random.randint(-10, 10)))
            world_state["marine_presence"] = max(0, min(100, world_state["marine_presence"] + random.randint(-10, 10)))

    async def check_level_up(self, user, user_data):
        exp_needed = user_data["level"] * 100
        if user_data["experience"] >= exp_needed:
            user_data["level"] += 1
            user_data["experience"] -= exp_needed
            user_data["skill_points"] += 3
            await self.config.user(user).set(user_data)
            return f"{user.mention} has reached level {user_data['level']}! You've gained 3 skill points."
        return None

    async def update_bounty_rankings(self, guild, user, bounty):
        async with self.config.guild(guild).bounty_rankings() as rankings:
            rankings[str(user.id)] = bounty
            # Keep only top 100 bounties
            rankings = dict(sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:100])

    async def update_discovered_zones(self, user, zone):
        async with self.config.user(user).discovered_zones() as zones:
            if zone not in zones:
                zones.append(zone)

    async def trigger_post_battle_events(self, ctx, is_victory, battle_env):
        # Implement any post-battle events here
        # For example, random item discoveries, special announcements, etc.
        if is_victory and random.random() < 0.1:  # 10% chance
            special_item = random.choice(["Mystery Map", "Ancient Coin", "Strange Device"])
            user_data = await self.config.user(ctx.author).all()
            user_data.setdefault("inventory", []).append(special_item)
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"🎁 In the aftermath of the battle, {ctx.author.mention} discovers a {special_item}!")

        # Maybe trigger a random world event based on the battle outcome
        if random.random() < 0.05:  # 5% chance
            event_message = f"News of the fierce battle in {battle_env} spreads across the world!"
            # Implement logic to affect world state or trigger follow-up events
            await ctx.send(f"📰 **Breaking News**: {event_message}")

    async def check_level_up(self, user, user_data):
        exp_needed = user_data["level"] * 100
        if user_data["experience"] >= exp_needed:
            user_data["level"] += 1
            user_data["experience"] -= exp_needed
            user_data["skill_points"] += 3
            await self.config.user(user).set(user_data)
            return f"{user.mention} has reached level {user_data['level']}! You've gained 3 skill points."
        return None

    async def update_bounty_rankings(self, guild, user, bounty):
        async with self.config.guild(guild).bounty_rankings() as rankings:
            rankings[str(user.id)] = bounty
            # Keep only top 100 bounties
            rankings = dict(sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:100])

    async def update_discovered_zones(self, user, zone):
        async with self.config.user(user).discovered_zones() as zones:
            if zone not in zones:
                zones.append(zone)

    async def trigger_post_battle_events(self, ctx, is_victory, battle_env):
        # Implement any post-battle events here
        # For example, random item discoveries, special announcements, etc.
        if is_victory and random.random() < 0.1:  # 10% chance
            special_item = random.choice(["Mystery Map", "Ancient Coin", "Strange Device"])
            user_data = await self.config.user(ctx.author).all()
            user_data.setdefault("inventory", []).append(special_item)
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"🎁 In the aftermath of the battle, {ctx.author.mention} discovers a {special_item}!")

        # Maybe trigger a random world event based on the battle outcome
        if random.random() < 0.05:  # 5% chance
            event_message = f"News of the fierce battle in {battle_env} spreads across the world!"
            # Implement logic to affect world state or trigger follow-up events
            await ctx.send(f"📰 **Breaking News**: {event_message}")
    
        # Common operations for both win and loss
        user_data["stamina"] = max(0, user_data.get("stamina", 100) - 20)
        user_data["fatigue"] = min(self.max_fatigue, user_data["fatigue"] + self.fatigue_per_battle)
        result_embed.add_field(name="😓 Fatigue", value=f"{user_data['fatigue']}/{self.max_fatigue}", inline=True)
    
        # Remove active gear after battle
        if "active_gear" in user_data:
            del user_data["active_gear"]
    
        await self.config.user(ctx.author).set(user_data)
        await battle_message.edit(embed=result_embed)

    async def check_new_abilities(self, ctx, user_data):
        if user_data["devil_fruit"] not in self.devil_fruit_abilities:
            return

        new_abilities = []
        for ability in self.devil_fruit_abilities[user_data["devil_fruit"]]:
            if ability["mastery_required"] <= user_data["devil_fruit_mastery"] and ability["name"] not in user_data["unlocked_abilities"]:
                user_data["unlocked_abilities"].append(ability["name"])
                new_abilities.append(ability["name"])

        if new_abilities:
            await self.config.user(ctx.author).set(user_data)
            abilities_str = ", ".join(new_abilities)
            await ctx.send(f"🎉 Congratulations! You've unlocked new Devil Fruit abilities: {abilities_str}")

    def generate_attack(self, user, user_data, base_strength):
        if random.random() < self.combo_chance and user_data.get("fighting_style") in self.combo_attacks and user_data.get("devil_fruit") in self.combo_attacks.get(user_data.get("fighting_style", {}), {}):
            technique = self.combo_attacks[user_data["fighting_style"]][user_data["devil_fruit"]]
            attack_power = random.randint(int(base_strength * 1.5), int(base_strength * 2))
            return attack_power, technique
        
        if user_data.get("devil_fruit") and user_data.get("unlocked_abilities"):
            technique = random.choice(user_data["unlocked_abilities"])
            attack_power = random.randint(int(base_strength * 1.2), int(base_strength * 1.8))
        elif user_data.get("devil_fruit") and user_data["devil_fruit"] in self.devil_fruit_abilities:
            # If no unlocked abilities, use a random ability from the devil fruit
            technique = random.choice([ability["name"] for ability in self.devil_fruit_abilities[user_data["devil_fruit"]]])
            attack_power = random.randint(int(base_strength * 1.2), int(base_strength * 1.8))
        else:
            technique = random.choice(user_data.get("learned_techniques", [])) if user_data.get("learned_techniques") else "Basic Attack"
            attack_power = random.randint(1, max(1, int(base_strength))) * (1.5 if technique != "Basic Attack" else 1)
        
        return attack_power, technique

    def create_ai_opponent(self, name):
        ai_fighting_style = random.choice(list(self.techniques.keys()))
        ai_devil_fruit = random.choice(list(self.devil_fruits.keys()))
        
        opponent_data = {
            "name": name,
            "fighting_style": ai_fighting_style,
            "devil_fruit": ai_devil_fruit,
            "haki": {
                "observation": random.randint(50, 100),
                "armament": random.randint(50, 100),
                "conquerors": random.randint(30, 80)
            },
            "doriki": random.randint(1000, 2000),
            "strength": random.randint(100, 200),
            "speed": random.randint(100, 200),
            "defense": random.randint(100, 200),
            "learned_techniques": random.sample(self.techniques[ai_fighting_style], min(5, len(self.techniques[ai_fighting_style]))),
            "equipped_items": random.sample(list(self.equipment.keys()), 3),
            "stamina": 150,
            "bounty": random.randint(500000000, 1500000000),
            "unlocked_abilities": [ability["name"] for ability in self.devil_fruit_abilities[ai_devil_fruit] if ability["mastery_required"] <= 50],  # Assuming AI has mastery up to 50
            "devil_fruit_mastery": 50
        }
        return opponent_data

    def trigger_special_event(self, user_name, opponent_name):
        events = [
            f"⚡ A sudden lightning strike energizes {user_name}, boosting their next attack!",
            f"🌊 A massive wave crashes into the battlefield, momentarily stunning {opponent_name}!",
            f"🌋 The ground splits open, forcing both fighters to adapt their strategies!",
            f"🌟 A mysterious power awakens within {user_name}, unlocking a hidden technique!",
            f"🌀 A whirlwind sweeps across the arena, adding chaos to the battle!"
        ]
        return random.choice(events)

    def generate_post_battle_reward(self):
        rewards = [
            ("🗺️ Piece of a Treasure Map", "You found a fragment of a legendary treasure map!"),
            ("💎 Rare Gem", "A sparkling gem caught your eye amidst the battlefield debris!"),
            ("📜 Ancient Scroll", "An old scroll with mysterious techniques was hidden nearby!"),
            ("🔮 Strange Orb", "A glowing orb pulses with unknown power..."),
            ("🏆 Battle Trophy", "Your victory has earned you a magnificent trophy!")
        ]
        return random.choice(rewards)

    # Add this to your battle method
    def apply_legendary_weapon(self, user_data, base_strength):
        if "legendary_weapon" in user_data:
            weapon = self.legendary_weapons.get(user_data["legendary_weapon"])
            if weapon:
                return base_strength + weapon["boost"]
        return base_strength
    
    # You can add this effect to the main battle loop to apply continuous damage
    async def apply_poison_effect(self, ctx, user_data, opponent_data):
        if "poisoned" in user_data:
            user_data["hp"] -= 10
            await ctx.send(f"{ctx.author.name} takes 10 poison damage!")
        if "poisoned" in opponent_data:
            opponent_data["hp"] -= 10
            await ctx.send(f"{opponent_data['name']} takes 10 poison damage!")

    # Modify your battle method to use the awakening boost
    def apply_devil_fruit_boost(self, user_data, base_strength):
        if user_data["devil_fruit"]:
            mastery = user_data.get("devil_fruit_mastery", 0)
            awakening_level = self.get_awakening_level(mastery)
            return base_strength * awakening_level["boost"] * self.devil_fruits[user_data["devil_fruit"]]["modifier"]
        return base_strength

    # Modify your battle method to apply gear boosts
    def apply_gear_boost(self, user_data, base_strength):
        if "active_gear" in user_data:
            gear_data = self.gear_system[user_data["active_gear"]]
            return base_strength * gear_data["boost"]
        return base_strength
    
    @op.command(name="checkq")
    async def check_quests(self, ctx):
        """Check your active quests"""
        active_quests = await self.config.user(ctx.author).active_quests()
        if not active_quests:
            await ctx.send("You don't have any active quests at the moment.")
            return

        embed = discord.Embed(title="Active Quests", color=discord.Color.blue())
        for quest in active_quests:
            embed.add_field(name=quest["type"].replace("_", " ").title(), value=quest["description"], inline=False)
        await ctx.send(embed=embed)

    @op.command(name="world")
    async def world_status(self, ctx):
        """Check the current world status"""
        world_state = await self.config.world_state()
        embed = discord.Embed(title="World Status", color=discord.Color.green())
        embed.add_field(name="Marine Presence", value=f"{world_state['marine_presence']}%", inline=True)
        embed.add_field(name="Pirate Influence", value=f"{world_state['pirate_influence']}%", inline=True)
        recent_events = world_state['world_events'][-5:] if world_state['world_events'] else ["No recent events"]
        embed.add_field(name="Recent Events", value="\n".join(recent_events), inline=False)
        await ctx.send(embed=embed)
    
    @op.command(name="lvlup")
    async def level_up(self, ctx):
        """Simulate leveling up (for testing purposes)"""
        user_data = await self.config.user(ctx.author).all()
        user_data["level"] += 1
        await self.config.user(ctx.author).set(user_data)

        new_techniques = await self.check_new_techniques(ctx.author)
        
        if new_techniques:
            techniques_str = ", ".join(new_techniques)
            await ctx.send(f"Congratulations! You've reached level {user_data['level']} and learned new techniques: {techniques_str}")
        else:
            await ctx.send(f"Congratulations! You've reached level {user_data['level']}.")
            
    @op.command(name="terrain")
    async def terrain_info(self, ctx, terrain: str = None):
        """Display information about terrain effects"""
        if terrain is None or terrain.capitalize() not in self.terrain_effects:
            terrains = ", ".join(self.terrain_effects.keys())
            await ctx.send(f"Please specify a valid terrain: {terrains}")
            return

        terrain = terrain.capitalize()
        embed = discord.Embed(title=f"{terrain} Terrain Effects", color=discord.Color.green())
        for element, modifier in self.terrain_effects[terrain].items():
            effect = "Boosted" if modifier > 1 else "Weakened" if modifier < 1 else "Neutral"
            embed.add_field(name=element.capitalize(), value=f"{effect} ({modifier}x)", inline=True)
        
        await ctx.send(embed=embed)
    
    @op.command(name="rewards")
    async def bounty_rewards(self, ctx):
        """Display information about bounty rewards"""
        embed = discord.Embed(title="Bounty Ranking Rewards", color=discord.Color.gold())
        embed.add_field(name="1st Place", value="1,000,000 Berries and Yonko's Treasure", inline=False)
        embed.add_field(name="2nd Place", value="750,000 Berries and Admiral's Medal", inline=False)
        embed.add_field(name="3rd Place", value="500,000 Berries and Shichibukai Emblem", inline=False)
        embed.add_field(name="4th - 10th Place", value="250,000 Berries", inline=False)
        embed.add_field(name="11th - 50th Place", value="100,000 Berries", inline=False)
        embed.set_footer(text="Rewards are distributed periodically to top-ranked players.")
        await ctx.send(embed=embed)
        
    @op.command(name="zones")
    async def mythical_zones(self, ctx):
        """Display information about Mythical Zones"""
        embed = discord.Embed(title="Mythical Zones", color=discord.Color.purple())
        for zone, data in self.mythical_zones.items():
            embed.add_field(name=zone, value=f"Description: {data['description']}\nReward: {data['reward']}\nSpawn Chance: {data['spawn_chance']*100}%", inline=False)
        embed.set_footer(text="Mythical Zones are rare battle environments with unique effects and rewards!")
        await ctx.send(embed=embed)
    
    @op.command(name="myzones")
    async def my_discoveries(self, ctx):
        """View the Mythical Zones you've discovered"""
        user_data = await self.config.user(ctx.author).all()
        discovered = user_data.get('discovered_zones', [])
        
        if not discovered:
            await ctx.send("You haven't discovered any Mythical Zones yet. Keep exploring!")
            return

        embed = discord.Embed(title=f"{ctx.author.name}'s Discovered Mythical Zones", color=discord.Color.gold())
        for zone in discovered:
            embed.add_field(name=zone, value=self.mythical_zones[zone]['description'], inline=False)
        
        await ctx.send(embed=embed)
        
    @op.command(name="bountytop")
    async def bounty_leaderboard(self, ctx, page: int = 1):
        """Display the bounty leaderboard"""
        top_bounties = await self.config.top_bounties()
        last_update = await self.config.last_bounty_update()

        if not top_bounties:
            await ctx.send("The bounty leaderboard is currently empty.")
            return

        items_per_page = 10
        pages = []

        for i in range(0, len(top_bounties), items_per_page):
            embed = discord.Embed(title="Bounty Leaderboard", color=discord.Color.gold())
            for j, entry in enumerate(top_bounties[i:i+items_per_page], start=i+1):
                user = self.bot.get_user(entry['user_id'])
                user_name = user.name if user else f"User {entry['user_id']}"
                embed.add_field(
                    name=f"{j}. {user_name}",
                    value=f"Bounty: {entry['bounty']:,} Berries",
                    inline=False
                )
            
            if last_update:
                embed.set_footer(text=f"Last updated: {last_update}")
            pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS)

    @op.command(name="rank")
    async def my_rank(self, ctx):
        """Check your current bounty rank"""
        top_bounties = await self.config.top_bounties()
        user_data = await self.config.user(ctx.author).all()
        user_bounty = user_data.get('bounty', 0)

        for i, entry in enumerate(top_bounties, start=1):
            if entry['user_id'] == ctx.author.id:
                await ctx.send(f"Your current bounty rank is #{i} with a bounty of {user_bounty:,} Berries!")
                return

        await ctx.send(f"You are not in the top 50. Your current bounty is {user_bounty:,} Berries.")

    @commands.command(name="rewardtop")
    async def rewardtop(self, ctx):
        """Reward the top bounty holders"""
        top_bounties = await self.config.top_bounties()
        
        rewards = [
            {"rank": 1, "berries": 1000000, "special_item": "Yonko's Treasure"},
            {"rank": 2, "berries": 750000, "special_item": "Admiral's Medal"},
            {"rank": 3, "berries": 500000, "special_item": "Shichibukai Emblem"},
            {"rank": (4, 10), "berries": 250000},
            {"rank": (11, 50), "berries": 100000}
        ]

        for i, entry in enumerate(top_bounties, start=1):
            user = self.bot.get_user(entry['user_id'])
            if not user:
                continue

            for reward in rewards:
                if isinstance(reward['rank'], int) and i == reward['rank'] or \
                isinstance(reward['rank'], tuple) and reward['rank'][0] <= i <= reward['rank'][1]:
                    user_data = await self.config.user(user).all()
                    user_data['berries'] = user_data.get('berries', 0) + reward['berries']
                    if 'special_item' in reward:
                        user_data.setdefault('inventory', []).append(reward['special_item'])
                    await self.config.user(user).set(user_data)

                    # Notify the user
                    try:
                        await user.send(f"Congratulations! You've received a bounty reward for your rank #{i}:\n"
                                        f"{reward['berries']:,} Berries" + 
                                        (f" and a {reward['special_item']}!" if 'special_item' in reward else "!"))
                    except discord.HTTPException:
                        pass  # Unable to send DM to the user
                    break

        await ctx.send("Top bounty holders have been rewarded!")

    @op.command(name="forcebounty")
    @commands.is_owner()
    async def force_bounty_update(self, ctx):
        """Force an update of the bounty leaderboard and distribute rewards"""
        await self.update_top_bounties()
        await self.reward_top_bounties()
        await ctx.send("Bounty leaderboard updated and rewards distributed!")

    @op.command(name="techniques")
    async def my_techniques(self, ctx):
        """Display your learned techniques"""
        user_data = await self.config.user(ctx.author).all()
        learned_techniques = user_data["learned_techniques"]

        if not learned_techniques:
            await ctx.send("You haven't learned any techniques yet!")
        else:
            techniques_str = "\n".join(learned_techniques)
            await ctx.send(f"Your learned techniques:\n{techniques_str}")

    @op.command(name="gears")
    async def activate_gear(self, ctx, gear: str):
        """Activate a gear for Paramecia users"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["devil_fruit"] or self.devil_fruits[user_data["devil_fruit"]]["type"] != "Paramecia":
            await ctx.send("You need a Paramecia-type Devil Fruit to use Gears.")
            return

        if gear not in self.gear_system:
            await ctx.send("Invalid Gear. Choose from: " + ", ".join(self.gear_system.keys()))
            return

        gear_data = self.gear_system[gear]
        if user_data["stamina"] < gear_data["stamina_cost"]:
            await ctx.send("Not enough stamina to activate this Gear.")
            return

        user_data["active_gear"] = gear
        user_data["stamina"] -= gear_data["stamina_cost"]
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"{gear} activated! Your power is boosted, but be careful of the stamina drain.")

    @op.command(name="devilfruit")
    async def devil_fruit_status(self, ctx):
        """Display your Devil Fruit status and awakening progress"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["devil_fruit"]:
            await ctx.send("You don't have a Devil Fruit power.")
            return

        mastery = user_data.get("devil_fruit_mastery", 0)
        awakening_level = self.get_awakening_level(mastery)

        embed = discord.Embed(title=f"{ctx.author.name}'s Devil Fruit Status", color=discord.Color.purple())
        embed.add_field(name="Devil Fruit", value=user_data["devil_fruit"])
        embed.add_field(name="Mastery", value=f"{mastery}/100")
        embed.add_field(name="Awakening Level", value=awakening_level["name"])
        embed.add_field(name="Current Boost", value=f"{awakening_level['boost']}x")
        await ctx.send(embed=embed)

    @op.command(name="weapon")
    async def legendary_weapon_info(self, ctx, weapon_name: str):
        """Display information about a legendary weapon"""
        weapon = self.legendary_weapons.get(weapon_name)
        if not weapon:
            await ctx.send("That legendary weapon doesn't exist.")
            return

        embed = discord.Embed(title=f"Legendary Weapon: {weapon_name}", color=discord.Color.gold())
        embed.add_field(name="Type", value=weapon["type"])
        embed.add_field(name="Boost", value=str(weapon["boost"]))
        embed.add_field(name="Special Ability", value=weapon["ability"])
        embed.add_field(name="Description", value=weapon["description"], inline=False)
        await ctx.send(embed=embed)

    @op.command(name="profile")
    async def op_profile(self, ctx, user: discord.Member = None):
        """View your or another user's profile"""
        target = user or ctx.author
        user_data = await self.config.user(target).all()
        self.logger.info(f"Profile viewed for user {target.id}")

        if not user_data["fighting_style"]:
            await ctx.send(f"{target.mention} has not begun their One Piece journey yet!")
            return

        embed = discord.Embed(title=f"{target.name}'s Pirate Profile", color=0x3498db)  # Use hex color code
        embed.set_thumbnail(url=target.display_avatar.url)  # Use display_avatar for compatibility

        embed.add_field(name="Fighting Style", value=user_data["fighting_style"], inline=True)
        embed.add_field(name="Devil Fruit", value=user_data["devil_fruit"] or "None", inline=True)
        embed.add_field(name="Bounty", value=f"{user_data['bounty']:,} Berries", inline=True)

        haki_info = "\n".join([f"{k.capitalize()}: {v}" for k, v in user_data["haki"].items()])
        embed.add_field(name="Haki", value=haki_info, inline=False)

        embed.add_field(name="Doriki", value=user_data["doriki"], inline=True)
        embed.add_field(name="Level", value=user_data["level"], inline=True)
        embed.add_field(name="Battles Won", value=user_data["battles_won"], inline=True)

        stats = f"Strength: {user_data['strength']}\nSpeed: {user_data['speed']}\nDefense: {user_data['defense']}"
        embed.add_field(name="Stats", value=stats, inline=False)

        techniques = ", ".join(user_data["learned_techniques"]) or "None"
        embed.add_field(name="Learned Techniques", value=techniques, inline=False)

        equipment = ", ".join(user_data["equipped_items"]) or "None"
        embed.add_field(name="Equipped Items", value=equipment, inline=False)

        await ctx.send(embed=embed)

    @op.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)  # Once per hour
    async def train(self, ctx, stat: str):
        """Train a specific stat (strength, speed, defense, or haki)"""
        user_data = await self.config.user(ctx.author).all()

        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return

        valid_stats = ["strength", "speed", "defense", "haki"]
        if stat.lower() not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return

        if user_data["stamina"] < 20:
            await ctx.send("You're too tired to train right now. Rest up and try again later!")
            return

        gain = random.randint(1, 5)
        if stat.lower() == "haki":
            haki_type = random.choice(["observation", "armament", "conquerors"])
            user_data["haki"][haki_type] += gain
            await ctx.send(f"You've trained your {haki_type.capitalize()} Haki and gained {gain} points!")
        else:
            user_data[stat.lower()] += gain
            await ctx.send(f"You've trained your {stat.capitalize()} and gained {gain} points!")

        user_data["stamina"] -= 20
        user_data["experience"] += random.randint(10, 30)

        # Level up check
        if user_data["experience"] >= user_data["level"] * 100:
            user_data["level"] += 1
            user_data["skill_points"] += 3
            await ctx.send(f"Congratulations! You've reached level {user_data['level']}! You've gained 3 skill points.")

        await self.config.user(ctx.author).set(user_data)

    @op.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)  # Once per 30 minutes
    async def rest(self, ctx):
        """Rest to recover from fatigue"""
        user_data = await self.config.user(ctx.author).all()
        current_time = ctx.message.created_at.timestamp()

        if user_data["last_rest_time"] is not None:
            hours_passed = (current_time - user_data["last_rest_time"]) / 3600
            fatigue_recovery = int(hours_passed * self.fatigue_recovery_rate)
            user_data["fatigue"] = max(0, user_data["fatigue"] - fatigue_recovery)

        user_data["last_rest_time"] = current_time
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(
            title="🛌 Rest",
            description=f"{ctx.author.mention} has rested and recovered from fatigue.",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Fatigue", value=f"{user_data['fatigue']}/{self.max_fatigue}")
        await ctx.send(embed=embed)
        
    @op.command()
    async def fatigue(self, ctx):
        """Check your current fatigue level"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(
            title="😓 Fatigue Status",
            description=f"{ctx.author.mention}'s current fatigue level.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Fatigue", value=f"{user_data['fatigue']}/{self.max_fatigue}")
        await ctx.send(embed=embed)

    @op.command(name="leaderboard")
    async def op_leaderboard(self, ctx, category: str = "bounty"):
        """View the leaderboard (categories: bounty, level, battles_won)"""
        valid_categories = ["bounty", "level", "battles_won"]
        if category.lower() not in valid_categories:
            await ctx.send(f"Invalid category. Please choose one of: {', '.join(valid_categories)}")
            return

        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get(category, 0), reverse=True)[:10]

        embed = discord.Embed(title=f"Top 10 Pirates - {category.capitalize()}", color=0xffd700)
        
        for i, (user_id, user_data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                value = user_data.get(category, 0)
                if category == "bounty":
                    value = f"{value:,} Berries"
                embed.add_field(name=f"{i}. {user.name}", value=value, inline=False)

        await ctx.send(embed=embed)
        
    @commands.command()
    @commands.is_owner()
    async def set_devil_fruit_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for Devil Fruit spawns"""
        await self.config.spawn_channel_id.set(channel.id)
        await ctx.send(f"Devil Fruits will now spawn in {channel.mention}")
        
        if self.spawn_task and not self.spawn_task.done():
            self.spawn_task.cancel()
        
        self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn())
        self.logger.info(f"Devil Fruit spawn task started for channel {channel.id}")

    async def initialize(self):
        channel_id = await self.config.spawn_channel_id()
        if channel_id:
            self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn())
            self.logger.info(f"Devil Fruit spawn task started for channel {channel_id}")

    @op.command(name="reset")
    @commands.is_owner()
    async def op_reset(self, ctx, user: discord.Member = None):
        """Reset a user's data (owner only)"""
        if user is None:
            user = ctx.author

        default_user = {
            "fighting_style": None,
            "devil_fruit": None,
            "haki": {
                "observation": 0,
                "armament": 0,
                "conquerors": 0
            },
            "doriki": 0,
            "bounty": 0,
            "battles_won": 0,
            "last_train": None,
            "level": 1,
            "experience": 0,
            "stamina": 100,
            "skill_points": 0,
            "strength": 1,
            "speed": 1,
            "defense": 1,
            "learned_techniques": [],
            "equipped_items": []
        }

        await self.config.user(user).set(default_user)
        self.logger.info(f"Reset data for user {user.id}")
        await ctx.send(f"{user.mention}'s data has been reset to default values.")
        
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def battleroyale(self, ctx):
        """Battle Royale management commands"""
        pass

    @battleroyale.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for Battle Royale announcements"""
        await self.config.guild(ctx.guild).battle_royale_channel.set(channel.id)
        await ctx.send(f"Battle Royale announcements will now be sent to {channel.mention}")

    @battleroyale.command()
    async def schedule(self, ctx, hours: int):
        """Schedule the next Battle Royale"""
        next_battle = datetime.now() + timedelta(hours=hours)
        await self.config.guild(ctx.guild).next_battle_royale.set(next_battle.isoformat())
        await ctx.send(f"Next Battle Royale scheduled for {next_battle.strftime('%Y-%m-%d %H:%M:%S')}")

    async def start_battle_royale(self, guild):
        channel_id = await self.config.guild(guild).battle_royale_channel()
        channel = guild.get_channel(channel_id)
        if not channel:
            return

        await self.config.guild(guild).ongoing_battle_royale.set(True)
        
        # Announce the start of Battle Royale
        announcement = await channel.send("🏴‍☠️ **BATTLE ROYALE STARTING SOON!** 🏴‍☠️\nPlace your bets or join the battle!")
        await announcement.add_reaction("💰")  # For betting
        await announcement.add_reaction("⚔️")  # For joining

        # Wait for bets and participants
        await asyncio.sleep(300)  # 5 minutes waiting period

        # Get bets and participants
        announcement = await channel.fetch_message(announcement.id)
        bets = [user for user in await announcement.reactions[0].users().flatten() if not user.bot]
        participants = [user for user in await announcement.reactions[1].users().flatten() if not user.bot]

        # Generate AI opponents
        ai_opponents = [self.generate_ai_opponent() for _ in range(max(5 - len(participants), 0))]
        all_participants = participants + ai_opponents

        # Run the Battle Royale
        winner = await self.run_battle_royale(channel, all_participants)

        # Distribute rewards
        await self.distribute_battle_royale_rewards(channel, winner, participants, bets)

        await self.config.guild(guild).ongoing_battle_royale.set(False)
        await self.config.guild(guild).next_battle_royale.set((datetime.now() + timedelta(hours=24)).isoformat())

    def generate_ai_opponent(self):
        return {
            "name": f"AI Pirate {random.randint(1, 999)}",
            "strength": random.randint(50, 100),
            "hp": random.randint(500, 1000)
        }

    async def run_battle_royale(self, channel, participants):
        await channel.send("🏴‍☠️ **BATTLE ROYALE BEGINS!** 🏴‍☠️")
        while len(participants) > 1:
            attacker = random.choice(participants)
            defender = random.choice([p for p in participants if p != attacker])
            
            damage = random.randint(50, 150)
            if isinstance(defender, dict):  # AI opponent
                defender["hp"] -= damage
                if defender["hp"] <= 0:
                    participants.remove(defender)
                    await channel.send(f"{attacker.name if isinstance(attacker, discord.Member) else attacker['name']} defeated {defender['name']}!")
            else:  # Player
                user_data = await self.config.user(defender).all()
                user_data["hp"] -= damage
                if user_data["hp"] <= 0:
                    participants.remove(defender)
                    await channel.send(f"{attacker.name if isinstance(attacker, discord.Member) else attacker['name']} defeated {defender.name}!")
                await self.config.user(defender).set(user_data)
            
            await asyncio.sleep(2)  # Pause between attacks

        winner = participants[0]
        await channel.send(f"🏆 **BATTLE ROYALE WINNER: {winner.name if isinstance(winner, discord.Member) else winner['name']}** 🏆")
        return winner

    async def distribute_battle_royale_rewards(self, channel, winner, participants, bets):
        reward_pool = len(bets) * 10000  # 10,000 Berries per bet
        
        if isinstance(winner, discord.Member):
            user_data = await self.config.user(winner).all()
            user_data["berries"] = user_data.get("berries", 0) + reward_pool
            user_data["battle_royale_wins"] = user_data.get("battle_royale_wins", 0) + 1
            await self.config.user(winner).set(user_data)
            await channel.send(f"{winner.mention} wins {reward_pool:,} Berries and a Battle Royale victory!")
        else:
            await channel.send(f"AI opponent {winner['name']} wins, but doesn't claim the prize.")

        # Distribute participation rewards
        for participant in participants:
            if isinstance(participant, discord.Member) and participant != winner:
                user_data = await self.config.user(participant).all()
                participation_reward = 5000  # 5,000 Berries for participating
                user_data["berries"] = user_data.get("berries", 0) + participation_reward
                await self.config.user(participant).set(user_data)
                await channel.send(f"{participant.mention} receives {participation_reward:,} Berries for participating!")

        # Handle bets
        winning_bets = [user for user in bets if user.id == winner.id]
        if winning_bets:
            bet_reward = reward_pool // len(winning_bets)
            for better in winning_bets:
                user_data = await self.config.user(better).all()
                user_data["berries"] = user_data.get("berries", 0) + bet_reward
                await self.config.user(better).set(user_data)
                await channel.send(f"{better.mention} wins {bet_reward:,} Berries from their bet!")

    @commands.command()
    async def battleroyalestats(self, ctx):
        """View your Battle Royale statistics"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(title=f"{ctx.author.name}'s Battle Royale Stats", color=discord.Color.gold())
        embed.add_field(name="Victories", value=user_data.get("battle_royale_wins", 0))
        embed.add_field(name="Berries Won", value=f"{user_data.get('berries', 0):,}")
        await ctx.send(embed=embed)

    @op.command(name="nextbr")
    async def nextbattleroyale(self, ctx):
        """View the time of the next scheduled Battle Royale"""
        next_battle = await self.config.guild(ctx.guild).next_battle_royale()
        if next_battle:
            battle_time = datetime.fromisoformat(next_battle)
            time_until = battle_time - datetime.now()
            await ctx.send(f"The next Battle Royale is scheduled for {battle_time.strftime('%Y-%m-%d %H:%M:%S')} "
                           f"(in {time_until.days} days, {time_until.seconds // 3600} hours, and {(time_until.seconds // 60) % 60} minutes)")
        else:
            await ctx.send("There is no Battle Royale currently scheduled.")    

    @op.command()
    async def allocate(self, ctx, stat: str, points: int):
        """Allocate skill points to a specific stat"""
        user_data = await self.config.user(ctx.author).all()
        valid_stats = ["strength", "speed", "defense", "haki"]
        
        if stat not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return

        if points <= 0 or points > user_data["skill_points"]:
            await ctx.send("Invalid number of points. You don't have enough skill points.")
            return

        user_data[stat] += points
        user_data["skill_points"] -= points
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You have allocated {points} points to {stat}.")

    @op.command()
    async def skill_tree(self, ctx):
        """View your skill tree"""
        user_data = await self.config.user(ctx.author).all()
        
        embed = discord.Embed(title=f"{ctx.author.name}'s Skill Tree", color=discord.Color.green())
        embed.add_field(name="Skill Points", value=user_data["skill_points"], inline=False)
        
        for stat in ["strength", "speed", "defense", "haki"]:
            embed.add_field(name=stat.capitalize(), value=user_data[stat], inline=True)
        
        await ctx.send(embed=embed)

    @op.command()
    async def devil_fruit_info(self, ctx, *, fruit_name: str = None):
        """Display information about a Devil Fruit or your own if no name is provided"""
        user_data = await self.config.user(ctx.author).all()
        
        if fruit_name is None:
            fruit_name = user_data.get("devil_fruit")
            if fruit_name is None:
                await ctx.send("You don't have a Devil Fruit. Specify a fruit name to get information about it.")
                return

        fruit = self.devil_fruits.get(fruit_name)
        if fruit is None:
            await ctx.send(f"No information found for {fruit_name}.")
            return

        embed = discord.Embed(title=f"Devil Fruit: {fruit_name}", color=discord.Color.purple())
        embed.add_field(name="Ability", value=fruit["ability"], inline=False)
        embed.add_field(name="Type", value=fruit["type"], inline=True)
        embed.add_field(name="Power Modifier", value=f"{fruit['modifier']}x", inline=True)

        # Display combo attacks for this fruit
        combo_attacks = []
        for style, attacks in self.combo_attacks.items():
            if fruit_name in attacks:
                combo_attacks.append(f"{style}: {attacks[fruit_name]}")
        
        if combo_attacks:
            embed.add_field(name="Combo Attacks", value="\n".join(combo_attacks), inline=False)

        await ctx.send(embed=embed)
        
    @op.command(name="view_techniques")
    async def op_view_techniques(self, ctx):
        """View available techniques for your fighting style"""
        user_data = await self.config.user(ctx.author).all()
        fighting_style = user_data["fighting_style"]
        
        if not fighting_style:
            await ctx.send("You need to begin your journey first!")
            return
        
        available_techniques = self.techniques.get(fighting_style, [])
        learned_techniques = user_data["learned_techniques"]
        
        embed = discord.Embed(title=f"Techniques for {fighting_style}", color=discord.Color.blue())
        for technique in available_techniques:
            status = "Learned" if technique in learned_techniques else "Not Learned"
            embed.add_field(name=technique, value=status, inline=False)
        
        await ctx.send(embed=embed)

    @op.command(name="view_equipment")
    async def op_view_equipment(self, ctx):
        """View available equipment and their stats"""
        embed = discord.Embed(title="Available Equipment", color=discord.Color.green())
        for item, stats in self.equipment.items():
            stat_string = ", ".join([f"{stat}: {value}" for stat, value in stats.items()])
            embed.add_field(name=item, value=stat_string, inline=False)
        
        await ctx.send(embed=embed)

    @op.command(name="learn_technique")
    async def op_learn_technique(self, ctx, *, technique_name: str):
        """Learn a new technique"""
        user_data = await self.config.user(ctx.author).all()
        fighting_style = user_data["fighting_style"]
        
        if not fighting_style:
            await ctx.send("You need to begin your journey first!")
            return
        
        if technique_name not in self.techniques[fighting_style]:
            await ctx.send(f"That technique is not available for your fighting style.")
            return
        
        if technique_name in user_data["learned_techniques"]:
            await ctx.send("You've already learned this technique.")
            return
        
        user_data["learned_techniques"].append(technique_name)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've learned the {technique_name} technique!")

    @op.command(name="equip")
    async def equip(self, ctx, *, item_name: str):
        """Equip an item from your inventory"""
        user_data = await self.config.user(ctx.author).all()
        
        if item_name not in user_data.get("inventory", []):
            await ctx.send(f"You don't have {item_name} in your inventory.")
            return

        for category, items in self.equipment.items():
            if item_name in items:
                item = items[item_name]
                slot = item["type"]
                
                # Check if the slot is already occupied
                if slot in user_data.get("equipped", {}):
                    old_item = user_data["equipped"][slot]
                    user_data["inventory"].append(old_item)
                    await ctx.send(f"Unequipped {old_item}.")

                user_data.setdefault("equipped", {})[slot] = item_name
                user_data["inventory"].remove(item_name)
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"Successfully equipped {item_name}!")
                return

        await ctx.send(f"Couldn't find equipment named {item_name}.")

    @op.command(name="unequip")
    async def unequip(self, ctx, *, slot: str):
        """Unequip an item from a specific slot"""
        user_data = await self.config.user(ctx.author).all()
        equipped = user_data.get("equipped", {})
        
        if slot not in equipped:
            await ctx.send(f"You don't have anything equipped in the {slot} slot.")
            return

        item = equipped[slot]
        del equipped[slot]
        user_data.setdefault("inventory", []).append(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"Successfully unequipped {item} from {slot} slot.")
    
    @op.command(name="inv")
    async def inventory(self, ctx):
        """Display your inventory and equipped items"""
        user_data = await self.config.user(ctx.author).all()
        inventory = user_data.get("inventory", [])
        equipped = user_data.get("equipped", {})

        embed = discord.Embed(title=f"{ctx.author.name}'s Inventory", color=discord.Color.blue())
        
        if inventory:
            embed.add_field(name="Inventory", value="\n".join(inventory), inline=False)
        else:
            embed.add_field(name="Inventory", value="Your inventory is empty.", inline=False)

        if equipped:
            equipped_str = "\n".join([f"{slot}: {item}" for slot, item in equipped.items()])
            embed.add_field(name="Equipped", value=equipped_str, inline=False)
        else:
            embed.add_field(name="Equipped", value="You have no items equipped.", inline=False)

        await ctx.send(embed=embed)

    @commands.group(name="ophelp")
    async def op_help(self, ctx):
        """Displays the help menu for the One Piece Battle Game"""
        if ctx.invoked_subcommand is None:
            pages = self.get_help_pages()
            await menu(ctx, pages, DEFAULT_CONTROLS)

    def get_help_pages(self):
        pages = []

        # Page 1: Introduction
        intro_embed = discord.Embed(title="One Piece Battle Game - Help", color=discord.Color.blue())
        intro_embed.add_field(name="Welcome", value="Embark on an epic journey in the world of One Piece! Battle fearsome opponents, master Devil Fruits, and become the Pirate King!", inline=False)
        intro_embed.add_field(name="Getting Started", value="Use `.op begin` to start your adventure and choose your fighting style.", inline=False)
        pages.append(intro_embed)

        # Page 2: Core Mechanics
        mechanics_embed = discord.Embed(title="Core Mechanics", color=discord.Color.green())
        mechanics_embed.add_field(name="Fighting Styles", value="Choose from Swordsman, Martial Artist, Sniper, or others. Each has unique techniques.", inline=False)
        mechanics_embed.add_field(name="Devil Fruits", value="Rare abilities that grant immense power. Master them to unlock their true potential!", inline=False)
        mechanics_embed.add_field(name="Haki", value="A mysterious power that can be developed through battle. Enhances your overall strength.", inline=False)
        mechanics_embed.add_field(name="Doriki", value="A measure of your physical strength. Increases as you train and win battles.", inline=False)
        mechanics_embed.add_field(name="Bounty", value="Reflects your notoriety. Higher bounties attract stronger opponents and better rewards.", inline=False)
        pages.append(mechanics_embed)

        # Page 3: Battle System
        battle_embed = discord.Embed(title="Battle System", color=discord.Color.red())
        battle_embed.add_field(name="Initiating Battles", value="Use `.op battle [opponent]` to start a fight. If no opponent is specified, you'll face an AI.", inline=False)
        battle_embed.add_field(name="Battle Mechanics", value="Battles are turn-based. Your strength, techniques, and Devil Fruit abilities determine your power.", inline=False)
        battle_embed.add_field(name="Critical Hits & Dodges", value="Chance for extra damage or avoiding attacks based on your stats.", inline=False)
        battle_embed.add_field(name="Environmental Effects", value="Different battle locations can affect your performance, especially for Devil Fruit users.", inline=False)
        battle_embed.add_field(name="Awakenings", value="Devil Fruits have a chance to temporarily awaken during battle, greatly boosting your power!", inline=False)
        pages.append(battle_embed)

        # Page 4: Progression
        progression_embed = discord.Embed(title="Progression", color=discord.Color.gold())
        progression_embed.add_field(name="Leveling Up", value="Gain experience from battles and training to level up and earn skill points.", inline=False)
        progression_embed.add_field(name="Skill Points", value="Allocate skill points to improve your strength, speed, or defense.", inline=False)
        progression_embed.add_field(name="Devil Fruit Mastery", value="The more you use your Devil Fruit, the stronger it becomes. Unlock new abilities as you master it!", inline=False)
        progression_embed.add_field(name="Haki Development", value="Your Haki improves as you battle tough opponents, unlocking new techniques.", inline=False)
        progression_embed.add_field(name="Equipment", value="Find or earn powerful weapons and items to boost your stats.", inline=False)
        pages.append(progression_embed)

        # Page 5: Commands
        commands_embed = discord.Embed(title="Game Commands", color=discord.Color.purple())
        commands_embed.add_field(name=".op begin", value="Start your journey and choose your fighting style.", inline=False)
        commands_embed.add_field(name=".op profile [user]", value="View your or another user's profile.", inline=False)
        commands_embed.add_field(name=".op battle [opponent]", value="Start a battle with another user or an AI opponent.", inline=False)
        commands_embed.add_field(name=".op train <stat>", value="Train a specific stat (strength, speed, defense, or haki).", inline=False)
        commands_embed.add_field(name=".op rest", value="Recover stamina and reduce fatigue.", inline=False)
        commands_embed.add_field(name=".op leaderboard [category]", value="View the top players in different categories.", inline=False)
        commands_embed.add_field(name=".op devil_fruit_info", value="Check your Devil Fruit status and abilities.", inline=False)
        commands_embed.add_field(name=".op equip <item>", value="Equip a weapon or item.", inline=False)
        commands_embed.add_field(name=".op unequip <item>", value="Unequip a weapon or item.", inline=False)
        commands_embed.add_field(name=".op inventory", value="View your inventory of items and equipment.", inline=False)
        commands_embed.add_field(name=".op shop", value="Browse and purchase items from the shop.", inline=False)
        pages.append(commands_embed)

        # Page 6: Cooldowns and Limitations
        cooldown_embed = discord.Embed(title="Cooldowns and Limitations", color=discord.Color.orange())
        cooldown_embed.add_field(name="Battle Cooldown", value="You can initiate a battle every 5 minutes to prevent spam.", inline=False)
        cooldown_embed.add_field(name="Training Cooldown", value="Training has a 1-hour cooldown to encourage diverse gameplay.", inline=False)
        cooldown_embed.add_field(name="Rest Cooldown", value="You can rest every 30 minutes to recover stamina.", inline=False)
        cooldown_embed.add_field(name="Fatigue System", value="Engaging in too many activities increases fatigue, reducing performance. Rest to recover!", inline=False)
        cooldown_embed.add_field(name="Daily Limits", value="Some actions (e.g., certain quests or rewards) may have daily limits to balance progression.", inline=False)
        pages.append(cooldown_embed)

        # Page 7: Tips and Strategies
        tips_embed = discord.Embed(title="Tips and Strategies", color=discord.Color.teal())
        tips_embed.add_field(name="Balanced Growth", value="Don't focus on just one stat. A well-rounded character performs better in various situations.", inline=False)
        tips_embed.add_field(name="Master Your Devil Fruit", value="Regularly use your Devil Fruit abilities to increase mastery and unlock powerful techniques.", inline=False)
        tips_embed.add_field(name="Strategic Equipment", value="Choose equipment that complements your fighting style and covers your weaknesses.", inline=False)
        tips_embed.add_field(name="Haki Training", value="Don't neglect Haki training. It's crucial for high-level battles, especially against Logia users.", inline=False)
        tips_embed.add_field(name="Rest and Recover", value="Keep an eye on your stamina and fatigue. A well-rested fighter performs much better in battle!", inline=False)
        tips_embed.add_field(name="Explore and Interact", value="Engage with the game's features. You might discover hidden quests or rare items!", inline=False)
        pages.append(tips_embed)

        return pages

    @op_help.command(name="commands")
    async def help_commands(self, ctx):
        """Displays detailed information about game commands"""
        embed = discord.Embed(title="One Piece Battle Game - Commands", color=discord.Color.blue())
        embed.add_field(name=".op begin", value="Start your journey in the world of One Piece. You'll choose your fighting style and receive your initial stats.", inline=False)
        embed.add_field(name=".op profile [user]", value="View your profile or another user's profile. Shows stats, equipment, Devil Fruit, and more.", inline=False)
        embed.add_field(name=".op battle [opponent]", value="Initiate a battle. If no opponent is specified, you'll fight an AI. Battles earn you experience, Doriki, and possibly bounty.", inline=False)
        embed.add_field(name=".op train <stat>", value="Train a specific stat. Options are strength, speed, defense, or haki. Has a 1-hour cooldown.", inline=False)
        embed.add_field(name=".op rest", value="Recover stamina and reduce fatigue. Essential for maintaining peak performance. Has a 30-minute cooldown.", inline=False)
        embed.add_field(name=".op leaderboard [category]", value="View the top players. Categories include bounty, level, and battles won.", inline=False)
        embed.add_field(name=".op devil_fruit_info", value="Check your Devil Fruit's current status, mastery level, and unlocked abilities.", inline=False)
        embed.add_field(name=".op equip <item>", value="Equip a weapon or item from your inventory to boost your stats.", inline=False)
        embed.add_field(name=".op unequip <item>", value="Unequip a currently equipped item, freeing up a slot for something else.", inline=False)
        embed.add_field(name=".op inventory", value="View all items in your possession, including equipment and consumables.", inline=False)
        embed.add_field(name=".op shop", value="Browse available items for purchase. Spend your hard-earned Berries on equipment and supplies!", inline=False)
        await ctx.send(embed=embed)

    @op_help.command(name="mechanics")
    async def help_mechanics(self, ctx):
        """Explains the core game mechanics"""
        embed = discord.Embed(title="One Piece Battle Game - Core Mechanics", color=discord.Color.green())
        embed.add_field(name="Fighting Styles", value="Your chosen style affects your base stats and available techniques. Can be improved through training and battles.", inline=False)
        embed.add_field(name="Devil Fruits", value="Grants unique abilities. Mastery increases through use, unlocking more powerful techniques. Some environments may affect their strength.", inline=False)
        embed.add_field(name="Haki", value="A powerful ability that grows stronger as you battle. Comes in three types: Observation, Armament, and Conqueror's.", inline=False)
        embed.add_field(name="Doriki", value="Represents your overall physical strength. Increases mainly through battles and specific training.", inline=False)
        embed.add_field(name="Bounty", value="Reflects your threat level. Higher bounties attract stronger opponents but also offer better rewards.", inline=False)
        embed.add_field(name="Stamina & Fatigue", value="Stamina is consumed in battles and training. Low stamina and high fatigue negatively affect performance.", inline=False)
        embed.add_field(name="Leveling & Skill Points", value="Gain experience to level up. Each level grants skill points to improve your base stats.", inline=False)
        embed.add_field(name="Equipment", value="Weapons and items that can be equipped to boost various stats. Some may have special effects in battle.", inline=False)
        await ctx.send(embed=embed)

    @op_help.command(name="tips")
    async def help_tips(self, ctx):
        """Provides helpful tips and strategies"""
        embed = discord.Embed(title="One Piece Battle Game - Tips and Strategies", color=discord.Color.gold())
        embed.add_field(name="Balanced Growth", value="While specializing can be good, a balanced character often performs better across various situations.", inline=False)
        embed.add_field(name="Devil Fruit Mastery", value="Use your Devil Fruit abilities frequently to increase mastery. Higher mastery unlocks more powerful techniques.", inline=False)
        embed.add_field(name="Haki Development", value="Don't neglect Haki training. It's crucial for high-level battles, especially against other Devil Fruit users.", inline=False)
        embed.add_field(name="Strategic Equipment", value="Choose equipment that complements your fighting style or covers your weaknesses.", inline=False)
        embed.add_field(name="Stamina Management", value="Keep an eye on your stamina and fatigue levels. Rest when needed to maintain peak performance.", inline=False)
        embed.add_field(name="Environment Awareness", value="Different battle environments can affect your performance. Plan your strategy accordingly.", inline=False)
        embed.add_field(name="Regular Training", value="Engage in regular training sessions to steadily improve your stats, even when you can't battle.", inline=False)
        embed.add_field(name="Explore Game Features", value="Interact with all aspects of the game. You might discover hidden quests, rare items, or useful information!", inline=False)
        await ctx.send(embed=embed)

    @op_help.command(name="cooldowns")
    async def help_cooldowns(self, ctx):
        """Explains the game's cooldown systems"""
        embed = discord.Embed(title="One Piece Battle Game - Cooldowns and Limitations", color=discord.Color.orange())
        embed.add_field(name="Battle Cooldown", value="5 minutes between battles. This prevents spam and encourages strategic play.", inline=False)
        embed.add_field(name="Training Cooldown", value="1 hour between training sessions. Encourages diverse gameplay and prevents rapid stat inflation.", inline=False)
        embed.add_field(name="Rest Cooldown", value="30 minutes between rest periods. Balances the stamina recovery mechanic.", inline=False)
        embed.add_field(name="Fatigue System", value="Accumulates with actions, reducing performance. Decreases slowly over time and with rest.", inline=False)
        embed.add_field(name="Daily Limits", value="Some actions may have daily limits to balance long-term progression.", inline=False)
        embed.add_field(name="Cooldown Reset", value="Cooldowns reset at midnight UTC. Plan your daily activities accordingly!", inline=False)
        embed.add_field(name="Cooldown Display", value="Use `.op cooldowns` to view your current cooldown timers and plan your next moves.", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(OnePieceBattle(bot))
