import discord
from redbot.core import commands, Config, checks
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
from datetime import datetime
import aiohttp
from io import BytesIO

class MHAGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.current_event = None
        self.event_participants = set()
        self.bot.loop.create_task(self.event_loop())
        
        default_user = {
            "name": "",
            "quirk": "",
            "alignment": "",  # "Hero" or "Villain"
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "attack": 10,
            "defense": 5,
            "speed": 5,
            "moves": [],
            "inventory": [],
            "currency": 0,
            "created_at": None,
            "active_quest": None
        }
        
        self.config.register_user(**default_user)
        
        self.moves = {
            # Basic Physical Moves
            "Punch": {"power": 40, "accuracy": 100, "type": "Physical"},
            "Kick": {"power": 60, "accuracy": 90, "type": "Physical"},
            "Tackle": {"power": 50, "accuracy": 95, "type": "Physical"},
            
            # Fire Moves
            "Fire Blast": {"power": 80, "accuracy": 85, "type": "Fire"},
            "Flame Burst": {"power": 70, "accuracy": 90, "type": "Fire", "effect": "burn"},
            "Inferno": {"power": 100, "accuracy": 75, "type": "Fire", "effect": "burn"},
            
            # Water Moves
            "Water Jet": {"power": 75, "accuracy": 90, "type": "Water"},
            "Hydro Pump": {"power": 90, "accuracy": 80, "type": "Water"},
            "Aqua Ring": {"power": 0, "accuracy": 100, "type": "Water", "effect": "heal"},
            
            # Earth Moves
            "Earth Wall": {"power": 0, "accuracy": 100, "type": "Earth", "effect": "defense_up"},
            "Rock Throw": {"power": 65, "accuracy": 90, "type": "Earth"},
            "Earthquake": {"power": 85, "accuracy": 85, "type": "Earth"},
            
            # Air Moves
            "Air Slice": {"power": 70, "accuracy": 95, "type": "Air"},
            "Tornado": {"power": 80, "accuracy": 85, "type": "Air", "effect": "confusion"},
            "Gust": {"power": 55, "accuracy": 100, "type": "Air", "effect": "speed_up"},
            
            # Electric Moves
            "Thunderbolt": {"power": 75, "accuracy": 90, "type": "Electric", "effect": "stun"},
            "Static Shock": {"power": 60, "accuracy": 95, "type": "Electric", "effect": "speed_up"},
            
            # Ice Moves
            "Ice Beam": {"power": 70, "accuracy": 90, "type": "Ice", "effect": "freeze"},
            "Blizzard": {"power": 95, "accuracy": 75, "type": "Ice", "effect": "freeze"},
            
            # Psychic Moves
            "Psychic Blast": {"power": 80, "accuracy": 85, "type": "Psychic", "effect": "confusion"},
            "Mind Control": {"power": 0, "accuracy": 70, "type": "Psychic", "effect": "stun"},
            
            # Dark Moves
            "Shadow Ball": {"power": 75, "accuracy": 90, "type": "Dark"},
            "Dark Pulse": {"power": 85, "accuracy": 85, "type": "Dark", "effect": "confusion"},
            
            # Light Moves
            "Dazzling Gleam": {"power": 70, "accuracy": 95, "type": "Light"},
            "Solar Beam": {"power": 100, "accuracy": 80, "type": "Light"},
            
            # Poison Moves
            "Toxic": {"power": 0, "accuracy": 85, "type": "Poison", "effect": "poison"},
            "Sludge Bomb": {"power": 75, "accuracy": 90, "type": "Poison", "effect": "poison"},
            
            # Special Moves
            "Drain Life": {"power": 60, "accuracy": 90, "type": "Special", "effect": "drain"},
            "Mega Punch": {"power": 90, "accuracy": 80, "type": "Physical"},
            "Hyper Beam": {"power": 120, "accuracy": 70, "type": "Special"},
        }
        
        self.quests = {
            "Patrol the City": {"description": "Patrol the city for any signs of trouble.", "reward": 50, "exp": 20},
            "Rescue Mission": {"description": "Save civilians from a collapsing building.", "reward": 100, "exp": 40},
            "Capture Villain": {"description": "Apprehend a known villain causing havoc.", "reward": 150, "exp": 60},
            "Train New Heroes": {"description": "Help train a group of aspiring heroes.", "reward": 80, "exp": 30},
            "Investigate Mystery": {"description": "Solve a mysterious occurrence in the city.", "reward": 120, "exp": 50}
        }

    async def event_loop(self):
        while True:
            await asyncio.sleep(3600 * 6)  # Check for new event every 6 hours
            if random.random() < 0.3:  # 30% chance of event
                await self.start_event()

    async def start_event(self):
        events = [
            "Sports Festival",
            "Villain Attack",
            "Rescue Mission",
            "Training Camp",
            "Hero Internship",
            "Quirk Research Study",
            "Undercover Operation"
        ]
        self.current_event = random.choice(events)
        self.event_participants.clear()
        channel = self.bot.get_channel(YOUR_ANNOUNCEMENT_CHANNEL_ID)  # Replace with your channel ID
        await channel.send(f"A new event has started: {self.current_event}! Use the `mha join_event` command to participate!")

    async def generate_quirk(self):
        quirk_types = ["Emitter", "Transformation", "Mutant", "Accumulation", "Hybrid"]
        quirk_elements = [
            "Fire", "Water", "Earth", "Air", "Light", "Dark", "Energy", "Gravity", "Time", "Space",
            "Lightning", "Ice", "Magma", "Plant", "Metal", "Sound", "Magnetism", "Acid", "Poison",
            "Illusion", "Telekinesis", "Shapeshifting", "Healing", "Duplication", "Invisibility",
            "Elasticity", "Hardening", "Teleportation", "Mind Control", "Force Field"
        ]
        quirk_effects = [
            "Boost", "Control", "Create", "Absorb", "Negate", "Amplify", "Manipulate", "Transform",
            "Sense", "Project", "Fuse", "Disintegrate", "Regenerate", "Enhance", "Mimic", "Summon",
            "Nullify", "Accelerate", "Decelerate", "Reflect"
        ]
        
        quirk_type = random.choice(quirk_types)
        quirk_element = random.choice(quirk_elements)
        quirk_effect = random.choice(quirk_effects)
        
        quirk_name = f"{quirk_effect} {quirk_element}"
        quirk_description = f"Allows the user to {quirk_effect.lower()} {quirk_element.lower()} through their {random.choice(['body', 'hands', 'eyes', 'mind'])}."
        
        return f"{quirk_name} ({quirk_type}): {quirk_description}"

    @commands.group(name="mha")
    async def mha(self, ctx):
        """My Hero Academia game commands"""
        if ctx.invoked_subcommand is None:
            await self.send_mha_help(ctx)

    async def send_mha_help(self, ctx):
        embed = discord.Embed(title="My Hero Academia Game Help", 
                              description="Here are all the commands for the MHA game:",
                              color=discord.Color.blue())

        commands_info = {
            "begin": {"aliases": ["start"], "desc": "Begin your hero/villain journey. Usage: `.mha begin <name> <hero/villain>`"},
            "profile": {"aliases": ["stats"], "desc": "Display your hero/villain profile"},
            "battle": {"aliases": ["fight"], "desc": "Start a battle against a random enemy"},
            "train": {"aliases": ["workout"], "desc": "Train a specific stat. Usage: `.mha train <stat>`"},
            "quests": {"aliases": ["missions"], "desc": "Display available quests"},
            "accept_quest": {"aliases": ["take_quest"], "desc": "Accept a quest. Usage: `.mha accept_quest <quest_name>`"},
            "complete_quest": {"aliases": ["finish_quest"], "desc": "Complete your active quest"},
            "abandon_quest": {"aliases": ["quit_quest"], "desc": "Abandon your active quest"},
            "join_event": {"aliases": ["enter_event"], "desc": "Join the current event"},
        }

        for cmd, info in commands_info.items():
            aliases = ", ".join(info["aliases"])
            embed.add_field(name=f"{cmd} ({aliases})", value=info["desc"], inline=False)

        await ctx.send(embed=embed)

    @mha.command(name="begin", aliases=["start"])
    async def begin_journey(self, ctx, name: str, alignment: str):
        """Begin your hero/villain journey"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["name"]:
            await ctx.send("You've already begun your journey!")
            return

        if alignment.lower() not in ["hero", "villain"]:
            await ctx.send("Please choose either 'hero' or 'villain' as your alignment.")
            return

        quirk = await self.generate_quirk()
        user_data["name"] = name
        user_data["quirk"] = quirk
        user_data["alignment"] = alignment.capitalize()
        user_data["created_at"] = ctx.message.created_at.isoformat()
        
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"Welcome, {name}! Your journey as a {alignment} begins. Your quirk is: {quirk}")
        
    async def generate_profile_card(self, user_data, user):
        # Open the template image
        img = Image.open("/home/adam/photos/mhaid.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("path/to/your/font.ttf", 24)

        # Add user avatar
        if user.avatar:
            avatar_url = user.avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(str(avatar_url)) as resp:
                    if resp.status == 200:
                        avatar_data = await resp.read()
                        avatar_image = Image.open(BytesIO(avatar_data))
                        
                        # Resize avatar to fit the blue rectangle
                        # Adjust these values to match your template
                        avatar_size = (150, 200)  # Example size, adjust as needed
                        avatar_image = avatar_image.resize(avatar_size, Image.Resampling.LANCZOS)
                        
                        # Paste the avatar onto the profile card
                        # Adjust these coordinates to match your template
                        avatar_position = (50, 50)  # Example position, adjust as needed
                        img.paste(avatar_image, avatar_position)

        # Add text to the image
        draw.text((200, 100), user_data["name"], font=font, fill=(0, 0, 0))
        draw.text((200, 150), user_data["quirk"], font=font, fill=(0, 0, 0))
        draw.text((200, 200), user_data["alignment"], font=font, fill=(0, 0, 0))
        draw.text((200, 250), f"Level: {user_data['level']}", font=font, fill=(0, 0, 0))
        
        created_at = datetime.fromisoformat(user_data["created_at"])
        draw.text((200, 300), f"Joined: {created_at.strftime('%Y-%m-%d')}", font=font, fill=(0, 0, 0))

        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer

    @mha.command(name="profile", aliases=["stats", "info"])
    async def show_profile(self, ctx):
        """Display your hero/villain profile"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        profile_image = await self.generate_profile_card(user_data, ctx.author)
        file = discord.File(profile_image, filename="mhaid.png")
        embed = discord.Embed(title=f"{user_data['name']}'s Profile", color=discord.Color.blue())
        embed.set_image(url="attachment://mhaid.png")
        await ctx.send(file=file, embed=embed)

    async def get_quirk_moves(self, quirk):
        quirk_type = quirk.split('(')[1].split(')')[0].lower()
        return [move for move, data in self.moves.items() if data['type'].lower() == quirk_type]

    async def pve_battle(self, ctx, player, enemy):
        battle_embed = discord.Embed(title="Battle", color=discord.Color.red())
        battle_msg = await ctx.send(embed=battle_embed)

        while player["hp"] > 0 and enemy["hp"] > 0:
            # Player turn
            player_moves = await self.get_quirk_moves(player["quirk"])
            move = await self.get_player_move(ctx, player_moves)
            damage, effect = await self.use_move(player, enemy, move)
            
            battle_embed.add_field(name="Player Attack", value=f"{player['name']} uses {move} and deals {damage} damage!", inline=False)
            if effect:
                battle_embed.add_field(name="Effect", value=effect, inline=False)

            if enemy["hp"] <= 0:
                break

            # Enemy turn
            enemy_move = random.choice(list(self.moves.keys()))
            damage, effect = await self.use_move(enemy, player, enemy_move)
            
            battle_embed.add_field(name="Enemy Attack", value=f"{enemy['name']} uses {enemy_move} and deals {damage} damage!", inline=False)
            if effect:
                battle_embed.add_field(name="Effect", value=effect, inline=False)

            battle_embed.clear_fields()
            battle_embed.add_field(name=player["name"], value=f"HP: {player['hp']}/{player['max_hp']}", inline=True)
            battle_embed.add_field(name=enemy["name"], value=f"HP: {enemy['hp']}/{enemy['max_hp']}", inline=True)
            await battle_msg.edit(embed=battle_embed)
            await asyncio.sleep(2)

        if player["hp"] > 0:
            return player
        else:
            return enemy

    async def use_move(self, attacker, defender, move):
        move_data = self.moves[move]
        if random.randint(1, 100) <= move_data["accuracy"]:
            damage = int((attacker["attack"] * move_data["power"] / 100) - (defender["defense"] / 2))
            damage = max(1, damage)  # Ensure at least 1 damage is dealt
            defender["hp"] -= damage
            
            effect = None
            if "effect" in move_data:
                effect = self.apply_effect(attacker, defender, move_data["effect"])
            
            return damage, effect
        else:
            return 0, "The move missed!"

    async def get_player_move(self, ctx, moves):
        move_list = "\n".join(moves)
        await ctx.send(f"Choose your move:\n{move_list}")
        
        def check(m):
            return m.author == ctx.author and m.content in moves
        
        try:
            move_msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            return move_msg.content
        except asyncio.TimeoutError:
            return random.choice(moves)  # Choose a random move if the player doesn't respond in time

    @mha.command(name="battle", aliases=["fight", "duel"])
    async def start_battle(self, ctx):
        """Start a battle against a random enemy"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        enemy = self.generate_enemy(user_data["level"])
        winner = await self.pve_battle(ctx, user_data, enemy)

        if winner == user_data:
            exp_gain = enemy["level"] * 10
            currency_gain = enemy["level"] * 5
            user_data["exp"] += exp_gain
            user_data["currency"] += currency_gain
            await ctx.send(f"You won! Gained {exp_gain} EXP and {currency_gain} currency.")
            await self.check_level_up(ctx, user_data)
        else:
            await ctx.send("You were defeated. Better luck next time!")

        user_data["hp"] = user_data["max_hp"]  # Restore HP after battle
        await self.config.user(ctx.author).set(user_data)

    @mha.command(name="train", aliases=["workout", "practice"])
    async def train_stat(self, ctx, stat: str):
        """Train a specific stat"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        valid_stats = ["attack", "defense", "speed", "hp"]
        if stat.lower() not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose from: {', '.join(valid_stats)}")
            return

        cost = user_data["level"] * 10
        if user_data["currency"] < cost:
            await ctx.send(f"You need {cost} currency to train. You only have {user_data['currency']}.")
            return

        user_data["currency"] -= cost
        increase = random.randint(1, 3)
        
        if stat.lower() == "hp":
            user_data["max_hp"] += increase
            user_data["hp"] = user_data["max_hp"]
        else:
            user_data[stat.lower()] += increase

        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You spent {cost} currency and trained your {stat}. It increased by {increase} points!")

    @mha.command(name="quests", aliases=["missions", "tasks"])
    async def show_quests(self, ctx):
        """Display available quests"""
        embed = discord.Embed(title="Available Quests", color=discord.Color.green())
        for quest, data in self.quests.items():
            embed.add_field(name=quest, value=f"{data['description']}\nReward: {data['reward']} currency, {data['exp']} EXP", inline=False)
        await ctx.send(embed=embed)

    @mha.command(name="accept_quest", aliases=["take_quest", "start_mission"])
    async def accept_quest(self, ctx, *, quest_name: str):
        """Accept a quest"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        if quest_name not in self.quests:
            await ctx.send("Invalid quest name. Use the `mha quests` command to see available quests.")
            return

        if user_data.get("active_quest"):
            await ctx.send("You already have an active quest. Complete it or use `mha abandon_quest` to start a new one.")
            return

        user_data["active_quest"] = quest_name
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You have accepted the quest: {quest_name}")

    @mha.command(name="complete_quest", aliases=["finish_quest", "end_mission"])
    async def complete_quest(self, ctx):
        """Complete your active quest"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data.get("active_quest"):
            await ctx.send("You don't have an active quest.")
            return

        quest = self.quests[user_data["active_quest"]]
        user_data["currency"] += quest["reward"]
        user_data["exp"] += quest["exp"]
        completed_quest = user_data["active_quest"]
        user_data["active_quest"] = None

        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"Congratulations! You completed the quest: {completed_quest}\nYou earned {quest['reward']} currency and {quest['exp']} EXP.")
        await self.check_level_up(ctx, user_data)

    @mha.command(name="abandon_quest", aliases=["quit_quest", "cancel_mission"])
    async def abandon_quest(self, ctx):
        """Abandon your active quest"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data.get("active_quest"):
            await ctx.send("You don't have an active quest.")
            return

        abandoned_quest = user_data["active_quest"]
        user_data["active_quest"] = None
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You have abandoned the quest: {abandoned_quest}")

    @mha.command(name="join_event", aliases=["enter_event", "participate"])
    async def join_event(self, ctx):
        """Join the current event"""
        if not self.current_event:
            await ctx.send("There is no active event at the moment.")
            return

        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        self.event_participants.add(ctx.author.id)
        await ctx.send(f"You've joined the {self.current_event} event!")

    @mha.command(name="end_event", aliases=["finish_event", "conclude_event"])
    @checks.is_owner()
    async def end_event(self, ctx):
        """End the current event and distribute rewards (Owner only)"""
        if not self.current_event:
            await ctx.send("There is no active event to end.")
            return

        for user_id in self.event_participants:
            user = self.bot.get_user(user_id)
            if user:
                user_data = await self.config.user(user).all()
                reward_exp = random.randint(50, 100)
                reward_currency = random.randint(10, 50)
                user_data["exp"] += reward_exp
                user_data["currency"] += reward_currency
                await self.config.user(user).set(user_data)
                await user.send(f"Thank you for participating in the {self.current_event}! You've been rewarded with {reward_exp} EXP and {reward_currency} currency.")

        await ctx.send(f"The {self.current_event} has ended. Rewards have been distributed to all participants.")
        self.current_event = None
        self.event_participants.clear()

    async def check_level_up(self, ctx, user_data):
        exp_needed = user_data["level"] * 100
        while user_data["exp"] >= exp_needed:
            user_data["level"] += 1
            user_data["exp"] -= exp_needed
            user_data["max_hp"] += 10
            user_data["hp"] = user_data["max_hp"]
            user_data["attack"] += 2
            user_data["defense"] += 2
            user_data["speed"] += 2
            exp_needed = user_data["level"] * 100
            await ctx.send(f"Congratulations! You've leveled up to level {user_data['level']}!")

        await self.config.user(ctx.author).set(user_data)

    def generate_enemy(self, player_level):
        enemy_types = ["Villain", "Rogue Hero", "Wild Beast", "Robot", "Alien"]
        enemy_name = f"Level {player_level} {random.choice(enemy_types)}"
        return {
            "name": enemy_name,
            "level": player_level,
            "hp": player_level * 20,
            "max_hp": player_level * 20,
            "attack": player_level * 3,
            "defense": player_level * 2,
            "speed": player_level * 2
        }

    def apply_effect(self, attacker, defender, effect):
    if effect == "defense_up":
        attacker["defense"] += 2
        return f"{attacker['name']}'s defense increased!"
    elif effect == "speed_up":
        attacker["speed"] += 2
        return f"{attacker['name']}'s speed increased!"
    elif effect == "attack_up":
        attacker["attack"] += 2
        return f"{attacker['name']}'s attack increased!"
    elif effect == "heal":
        heal_amount = min(20, attacker["max_hp"] - attacker["hp"])
        attacker["hp"] += heal_amount
        return f"{attacker['name']} healed for {heal_amount} HP!"
    elif effect == "poison":
        defender["status"] = "poisoned"
        return f"{defender['name']} was poisoned!"
    elif effect == "stun":
        defender["status"] = "stunned"
        return f"{defender['name']} was stunned!"
    elif effect == "burn":
        defender["status"] = "burned"
        return f"{defender['name']} was burned!"
    elif effect == "freeze":
        defender["status"] = "frozen"
        return f"{defender['name']} was frozen!"
    elif effect == "confusion":
        defender["status"] = "confused"
        return f"{defender['name']} became confused!"
    elif effect == "drain":
        drain_amount = min(20, defender["hp"])
        defender["hp"] -= drain_amount
        attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + drain_amount)
        return f"{attacker['name']} drained {drain_amount} HP from {defender['name']}!"
    return ""

    @commands.group(name="mhaadmin")
    @checks.is_owner()
    async def mha_admin(self, ctx):
        """MHA game admin commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @mha_admin.command(name="wipe")
    async def wipe_user_data(self, ctx, user: discord.Member):
        """Wipe a user's MHA game data"""
        await self.config.user(user).clear()
        await ctx.send(f"{user.mention}'s MHA game data has been wiped.")

    @mha_admin.command(name="setchannel")
    async def set_announcement_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for MHA game announcements"""
        await self.config.guild(ctx.guild).announcement_channel.set(channel.id)
        await ctx.send(f"Announcement channel set to {channel.mention}")

    @mha_admin.command(name="givequirk")
    async def give_quirk(self, ctx, user: discord.Member, *, quirk: str):
        """Give a specific quirk to a user"""
        user_data = await self.config.user(user).all()
        if not user_data["name"]:
            await ctx.send(f"{user.mention} hasn't started their journey yet.")
            return

        user_data["quirk"] = quirk
        await self.config.user(user).set(user_data)
        await ctx.send(f"{user.mention}'s quirk has been set to: {quirk}")

    @mha_admin.command(name="setlevel")
    async def set_user_level(self, ctx, user: discord.Member, level: int):
        """Set a user's level"""
        user_data = await self.config.user(user).all()
        if not user_data["name"]:
            await ctx.send(f"{user.mention} hasn't started their journey yet.")
            return

        user_data["level"] = level
        await self.config.user(user).set(user_data)
        await ctx.send(f"{user.mention}'s level has been set to {level}")

def setup(bot):
    bot.add_cog(MHAGame(bot))
