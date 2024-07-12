import discord
from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import random
import asyncio
import datetime
import logging

class OnePieceBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.spawn_channel_id = None
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
            "unlocked_abilities": []
        }
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
        
        self.devil_fruits = {
            "Gomu Gomu no Mi": {"ability": "Elasticity", "modifier": 1.2, "type": "Paramecia"},
            "Mera Mera no Mi": {"ability": "Fire Control", "modifier": 1.3, "type": "Logia"},
            "Hie Hie no Mi": {"ability": "Ice Control", "modifier": 1.3, "type": "Logia"},
            "Pika Pika no Mi": {"ability": "Light Manipulation", "modifier": 1.4, "type": "Logia"},
            "Gura Gura no Mi": {"ability": "Earthquake Generation", "modifier": 1.5, "type": "Paramecia"},
            "Yami Yami no Mi": {"ability": "Darkness Manipulation", "modifier": 1.4, "type": "Logia"},
            "Suna Suna no Mi": {"ability": "Sand Control", "modifier": 1.3, "type": "Logia"},
            "Magu Magu no Mi": {"ability": "Magma Control", "modifier": 1.4, "type": "Logia"},
            "Ope Ope no Mi": {"ability": "Operation", "modifier": 1.3, "type": "Paramecia"},
            "Goro Goro no Mi": {"ability": "Lightning Control", "modifier": 1.4, "type": "Logia"},
            "Mochi Mochi no Mi": {"ability": "Mochi Manipulation", "modifier": 1.3, "type": "Special Paramecia"},
            "Bara Bara no Mi": {"ability": "Body Separation", "modifier": 1.2, "type": "Paramecia"},
            "Zoan Fruits": {"ability": "Animal Transformation", "modifier": 1.3, "type": "Zoan"}
        }

        self.techniques = {
            "Swordsman": ["Three Sword Style", "Flying Slash Attack", "Lion's Song"],
            "Martial Artist": ["Shigan", "Tekkai", "Rankyaku"],
            "Sniper": ["Exploding Star", "Lead Star", "Fire Bird Star"],
            "Brawler": ["Gomu Gomu no Pistol", "Gomu Gomu no Bazooka", "Gear Second"],
            "Tactician": ["Mirage Tempo", "Thunderbolt Tempo", "Weather Egg"]
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
            "Sword": {"strength": 20, "speed": 10},
            "Gun": {"strength": 15, "speed": 15},
            "Armor": {"defense": 30},
            "Boots": {"speed": 20},
            "Gloves": {"strength": 10, "speed": 10}
        }
        
        self.combo_attacks = {
            "Swordsman": {
                "Gomu Gomu no Mi": "Gum-Gum Sword Whip",
                "Mera Mera no Mi": "Flame-Edged Blade Dance",
                "Hie Hie no Mi": "Frozen Sword Barrage",
                "Yami Yami no Mi": "Dark Matter Slash",
                "Gura Gura no Mi": "Tremor Blade Quake"
            },
            "Martial Artist": {
                "Gomu Gomu no Mi": "Elastic Fist Gatling",
                "Mera Mera no Mi": "Blazing Kick Tempest",
                "Hie Hie no Mi": "Frost-Knuckle Assault",
                "Yami Yami no Mi": "Gravity Well Throw",
                "Gura Gura no Mi": "Seismic Shockwave Punch"
            },
            "Sniper": {
                "Gomu Gomu no Mi": "Rubber Bullet Barrage",
                "Mera Mera no Mi": "Inferno Snipe",
                "Hie Hie no Mi": "Absolute Zero Shot",
                "Yami Yami no Mi": "Black Hole Projectile",
                "Gura Gura no Mi": "Shatterpoint Precision Shot"
            },
            "Tactician": {
                "Gomu Gomu no Mi": "Elastic Trap Network",
                "Mera Mera no Mi": "Firewall Strategy",
                "Hie Hie no Mi": "Cryo-Lockdown Maneuver",
                "Yami Yami no Mi": "Void Field Tactics",
                "Gura Gura no Mi": "Tectonic Battlefield Control"
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

        self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn(self.spawn_channel_id))

    def cog_unload(self):
        self.spawn_task.cancel()

    def get_awakening_level(self, mastery):
        for level, data in sorted(self.awakening_levels.items(), reverse=True):
            if mastery >= level:
                return data
        return self.awakening_levels[0]

    async def devil_fruit_spawn(self, channel_id):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(3600, 7200))  # Random spawn time between 1-2 hours
            channel = self.bot.get_channel(channel_id)
            if channel:
                devil_fruit = random.choice(list(self.devil_fruits.keys()))
                embed = discord.Embed(
                    title="Devil Fruit Spawn!",
                    description=f"A {devil_fruit} has spawned in this channel! React with 🍎 to claim it!",
                    color=discord.Color.gold()
                )
                message = await channel.send(embed=embed)
                await message.add_reaction("🍎")

                def check(reaction, user):
                    return str(reaction.emoji) == "🍎" and user != self.bot.user

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await message.delete()
                else:
                    user_data = await self.config.user(user).all()
                    if user_data["devil_fruit"]:
                        await channel.send(f"{user.mention}, you already have a Devil Fruit!")
                    else:
                        user_data["devil_fruit"] = devil_fruit
                        await self.config.user(user).set(user_data)
                        await channel.send(f"Congratulations {user.mention}! You have claimed the {devil_fruit}!")

    async def handle_gear_stamina(self, user_data):
        if "active_gear" in user_data:
            gear_data = self.gear_system[user_data["active_gear"]]
            user_data["stamina"] -= gear_data["stamina_cost"] // 2  # Continuous drain
            if user_data["stamina"] <= 0:
                del user_data["active_gear"]
                await self.config.user(user_data["_id"]).set(user_data)
                return "Your Gear has deactivated due to stamina depletion!"
        return None

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
    
        battle_env = random.choice(list(self.environments.keys()))
        env_effect = self.environments[battle_env]
    
        battle_embed = discord.Embed(
            title=f"⚔️ __**Epic Battle: {ctx.author.name} vs {opponent_name}**__ ⚔️",
            description=f"*{env_effect['description']} The seas tremble as two mighty warriors clash!*",
            color=discord.Color.red()
        )
    
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
        battle_message = await ctx.send(embed=battle_embed)
    
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
                # Recalculate user_strength if gear deactivated
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
    
            # Chance to find a Legendary Weapon
            if random.random() < 0.05:  # 5% chance
                new_weapon = random.choice(list(self.legendary_weapons.keys()))
                user_data["legendary_weapon"] = new_weapon
                battle_log.append(f"🏆 {ctx.author.name} found the legendary weapon: {new_weapon}!")
    
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
        self.spawn_channel_id = channel.id
        await ctx.send(f"Devil Fruits will now spawn in {channel.mention}")
        if self.spawn_task:
            self.spawn_task.cancel()
        self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn(self.spawn_channel_id))

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
    async def devil_fruit_info(self, ctx):
        """Display information about your Devil Fruit and mastery"""
        user_data = await self.config.user(ctx.author).all()

        if not user_data["devil_fruit"]:
            await ctx.send("You don't have a Devil Fruit power yet!")
            return

        embed = discord.Embed(
            title=f"🍎 Devil Fruit: {user_data['devil_fruit']}",
            description=f"Mastery Level: {user_data['devil_fruit_mastery']}",
            color=discord.Color.orange()
        )

        unlocked = user_data["unlocked_abilities"]
        all_abilities = self.devil_fruit_abilities.get(user_data["devil_fruit"], [])

        for ability in all_abilities:
            status = "✅ Unlocked" if ability["name"] in unlocked else f"🔒 Locked (Requires Mastery {ability['mastery_required']})"
            embed.add_field(name=ability["name"], value=status, inline=False)

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
    async def op_equip(self, ctx, *, item: str):
        """Equip an item"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        if item not in self.equipment:
            await ctx.send("That item doesn't exist.")
            return
        
        if len(user_data["equipped_items"]) >= 3:
            await ctx.send("You can't equip more than 3 items. Unequip something first.")
            return
        
        user_data["equipped_items"].append(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've equipped the {item}!")

    @op.command(name="unequip")
    async def op_unequip(self, ctx, *, item: str):
        """Unequip an item"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        if item not in user_data["equipped_items"]:
            await ctx.send("You don't have that item equipped.")
            return
        
        user_data["equipped_items"].remove(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've unequipped the {item}.")

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
