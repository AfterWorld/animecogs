import discord
from redbot.core import commands, Config, checks
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence
import io
from datetime import datetime
import aiohttp
from io import BytesIO
import textwrap

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
            "quirk_type": None,
            "alignment": "",  # "Hero" or "Villain"
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "attack": 10,
            "defense": 5,
            "speed": 5,
            "learned_moves": ["Punch", "Kick", "Dodge"],  # Start with basic moves
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
            
            # Check for new moves to learn
            await self.check_new_moves(ctx, user_data)

        await self.config.user(ctx.author).set(user_data)

    async def check_new_moves(self, ctx, user_data):
        level = user_data["level"]
        quirk_type = user_data["quirk_type"]
        
        new_moves = []
        
        # Check for level-based moves
        if level == 5:
            new_moves.append("Mega Punch")
        elif level == 10:
            new_moves.append("Hyper Beam")
        
        # Check for quirk-specific moves
        if quirk_type:
            quirk_moves = [move for move, data in self.moves.items() if data["type"].lower() == quirk_type.lower()]
            new_moves.extend(quirk_moves[:min(level // 3, len(quirk_moves))])  # Learn a quirk move every 3 levels
        
        # Add new moves to learned moves
        for move in new_moves:
            if move not in user_data["learned_moves"]:
                user_data["learned_moves"].append(move)
                await ctx.send(f"🎉 You learned a new move: {move}!")
        
        await self.config.user(ctx.author).set(user_data)

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
        channel = self.bot.get_channel(1258644179928748122)  # Replace with your channel ID
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
        quirk_type = quirk.split('(')[1].split(')')[0]  # Extract quirk type
        user_data["name"] = name
        user_data["quirk"] = quirk
        user_data["quirk_type"] = quirk_type
        user_data["alignment"] = alignment.capitalize()
        user_data["created_at"] = ctx.message.created_at.isoformat()
        
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"Welcome, {name}! Your journey as a {alignment} begins. Your quirk is: {quirk}")
        
        # Check for initial quirk-specific moves
        await self.check_new_moves(ctx, user_data)
        
    async def generate_profile_card(self, user_data, user):
        # Open the template image
        img = Image.open("/home/adam/photos/mhaid.png")
        draw = ImageDraw.Draw(img)
        
        try:
            main_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except IOError:
            main_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add user avatar (now supports GIFs)
        if user.avatar:
            avatar_url = user.avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(str(avatar_url)) as resp:
                    if resp.status == 200:
                        avatar_data = await resp.read()
                        avatar_image = Image.open(BytesIO(avatar_data))
                        
                        # Handle GIF avatars
                        if getattr(avatar_image, "is_animated", False):
                            frames = []
                            for frame in ImageSequence.Iterator(avatar_image):
                                frame = frame.copy()
                                frame = frame.resize((350, 400), Image.Resampling.LANCZOS)
                                frame_img = img.copy()
                                frame_img.paste(frame, (50, 200))
                                frames.append(frame_img)
                            img = frames[0]  # Use the first frame for static display
                        else:
                            avatar_image = avatar_image.resize((350, 400), Image.Resampling.LANCZOS)
                            img.paste(avatar_image, (50, 200))

        # Generate random attendance number
        attend_number = random.randint(10000, 99999)

        # Current year
        current_year = datetime.now().year

        # Add text to the image
        draw.text((450, 100), f"Year {current_year}", font=main_font, fill=(0, 0, 0))
        draw.text((450, 220), "Year 1", font=main_font, fill=(0, 0, 0))  # Department (Year 1 by default)
        draw.text((450, 290), f"{attend_number}", font=main_font, fill=(0, 0, 0))  # Attendance number

        draw.text((450, 380), user_data['name'], font=main_font, fill=(0, 0, 0))

        created_at = datetime.fromisoformat(user_data["created_at"])
        draw.text((450, 430), f"{created_at.strftime('%Y-%m-%d')}", font=main_font, fill=(0, 0, 0))

        # Quirk with smaller font and word wrap
        quirk_text = f"{user_data['quirk']}"
        lines = textwrap.wrap(quirk_text, width=50)  # Adjust width as needed
        y_text = 480
        for line in lines:
            draw.text((425, y_text), line, font=small_font, fill=(0, 0, 0))
            y_text += 25  # Adjust line spacing as needed

        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        if isinstance(img, list):  # If it's a GIF
            img[0].save(buffer, format="GIF", save_all=True, append_images=img[1:], loop=0, duration=100)
        else:
            img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer
        
    @mha.command(name="moves", aliases=["techniques"])
    async def show_moves(self, ctx):
        """Show your learned moves"""
        user_data = await self.config.user(ctx.author).all()
        moves = user_data["learned_moves"]
        
        embed = discord.Embed(title=f"{ctx.author.name}'s Moves", color=discord.Color.blue())
        for move in moves:
            move_data = self.moves.get(move, {})
            description = f"Power: {move_data.get('power', 'N/A')}, Accuracy: {move_data.get('accuracy', 'N/A')}%"
            if 'effect' in move_data:
                description += f", Effect: {move_data['effect']}"
            embed.add_field(name=move, value=description, inline=False)
        
        await ctx.send(embed=embed)

    async def get_player_move(self, ctx, moves, move_msg):
        # Use the player's learned moves instead of all moves
        user_data = await self.config.user(ctx.author).all()
        learned_moves = user_data["learned_moves"]
        available_moves = [move for move in learned_moves if move in moves]
        
        move_embed = discord.Embed(title="Choose your move", description="\n".join(available_moves), color=discord.Color.blue())
        await move_msg.edit(embed=move_embed)

        def check(m):
            return m.author == ctx.author and m.content.lower() in [move.lower() for move in available_moves]
        
        try:
            move_choice = await self.bot.wait_for("message", check=check, timeout=30.0)
            await move_choice.delete()
            return move_choice.content
        except asyncio.TimeoutError:
            return random.choice(available_moves)

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
        quirk_moves = [move for move, data in self.moves.items() if data['type'].lower() == quirk_type]
        
        # Always include some default moves
        default_moves = ["Punch", "Kick", "Dodge"]
        return list(set(quirk_moves + default_moves))  # Use set to remove duplicates
    
    async def get_player_move(self, ctx, moves):
        if not moves:
            return "Punch"  # Default move if no moves are available
        
        move_list = "\n".join(moves)
        await ctx.send(f"Choose your move:\n{move_list}")
        
        def check(m):
            return m.author == ctx.author and m.content in moves
        
        try:
            move_msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            return move_msg.content
        except asyncio.TimeoutError:
            return random.choice(moves)  # Choose a random move if the player doesn't respond in time
    
    async def pve_battle(self, ctx, player, enemy):
        # Announce the battle
        await ctx.send(f"🏟️ **Battle Start!**\n{player['name']} vs {enemy['name']}")

        battle_embed = discord.Embed(title="Battle", color=discord.Color.red())
        battle_embed.add_field(name=player['name'], value=f"HP: {player['hp']}/{player['max_hp']}", inline=True)
        battle_embed.add_field(name=enemy['name'], value=f"HP: {enemy['hp']}/{enemy['max_hp']}", inline=True)
        battle_msg = await ctx.send(embed=battle_embed)

        player_moves = player['learned_moves']
        move_embed = discord.Embed(title="Choose your move", description="\n".join(player_moves), color=discord.Color.blue())
        move_msg = await ctx.send(embed=move_embed)

        while player["hp"] > 0 and enemy["hp"] > 0:
            # Player turn
            move = await self.get_player_move(ctx, player_moves, move_msg)
            damage, effect = await self.use_move(player, enemy, move)
            
            battle_embed.clear_fields()
            battle_embed.add_field(name="Player Attack", value=f"{player['name']} uses {move} and deals {damage} damage!", inline=False)
            if effect:
                battle_embed.add_field(name="Effect", value=effect, inline=False)
            battle_embed.add_field(name=player['name'], value=f"HP: {player['hp']}/{player['max_hp']}", inline=True)
            battle_embed.add_field(name=enemy['name'], value=f"HP: {enemy['hp']}/{enemy['max_hp']}", inline=True)
            await battle_msg.edit(embed=battle_embed)
            await asyncio.sleep(2)

            if enemy["hp"] <= 0:
                break

            # Enemy turn
            enemy_move = random.choice(list(self.moves.keys()))
            damage, effect = await self.use_move(enemy, player, enemy_move)
            
            battle_embed.clear_fields()
            battle_embed.add_field(name="Enemy Attack", value=f"{enemy['name']} uses {enemy_move} and deals {damage} damage!", inline=False)
            if effect:
                battle_embed.add_field(name="Effect", value=effect, inline=False)
            battle_embed.add_field(name=player['name'], value=f"HP: {player['hp']}/{player['max_hp']}", inline=True)
            battle_embed.add_field(name=enemy['name'], value=f"HP: {enemy['hp']}/{enemy['max_hp']}", inline=True)
            await battle_msg.edit(embed=battle_embed)
            await asyncio.sleep(2)

        await move_msg.delete()  # Clean up the move selection message

        if player["hp"] > 0:
            await ctx.send(f"🏆 {player['name']} wins the battle!")
            return player
        else:
            await ctx.send(f"☠️ {enemy['name']} wins the battle!")
            return enemy
    
    async def get_player_move(self, ctx, moves, move_msg):
        def check(m):
            return m.author == ctx.author and m.content.lower() in [move.lower() for move in moves]
        
        try:
            move_choice = await self.bot.wait_for("message", check=check, timeout=30.0)
            await move_choice.delete()  # Delete the player's move choice message
            return move_choice.content
        except asyncio.TimeoutError:
            return random.choice(moves)  # Choose a random move if the player doesn't respond in time

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

    async def get_player_move(self, ctx, moves, move_msg):
        move_embed = discord.Embed(title="Choose your move", description="\n".join(moves), color=discord.Color.blue())
        await move_msg.edit(embed=move_embed)

        def check(m):
            return m.author == ctx.author and m.content.lower() in [move.lower() for move in moves]
        
        try:
            move_choice = await self.bot.wait_for("message", check=check, timeout=30.0)
            await move_choice.delete()  # Delete the player's move choice message
            return move_choice.content
        except asyncio.TimeoutError:
            return random.choice(moves)  # Choose a random move if the player doesn't respond in time

    @mha.command(name="battle", aliases=["fight", "duel"])
    async def start_battle(self, ctx):
        """Start a battle against a villain"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        villain = self.generate_villain(user_data["level"])
        winner = await self.conduct_battle(ctx, user_data, villain)

        if winner == user_data:
            exp_gain = villain["level"] * 10
            currency_gain = villain["level"] * 5
            user_data["exp"] += exp_gain
            user_data["currency"] += currency_gain
            await ctx.send(f"You won! Gained {exp_gain} EXP and {currency_gain} currency.")
            await self.check_level_up(ctx, user_data)
        else:
            await ctx.send("You were defeated. Better luck next time!")

        user_data["hp"] = user_data["max_hp"]  # Restore HP after battle
        await self.config.user(ctx.author).set(user_data)
        
    @mha.command(name="pvp", aliases=["fight"])
    async def pvp_battle(self, ctx, opponent: discord.Member):
        """Challenge another player to a PvP battle"""
        if opponent == ctx.author:
            await ctx.send("You can't battle yourself!")
            return

        player_data = await self.config.user(ctx.author).all()
        opponent_data = await self.config.user(opponent).all()

        if not player_data["name"] or not opponent_data["name"]:
            await ctx.send("Both players need to have started their journey to battle!")
            return

        await ctx.send(f"{opponent.mention}, {ctx.author.mention} has challenged you to a battle! Type 'accept' to begin.")

        def check(m):
            return m.author == opponent and m.content.lower() == 'accept'

        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("The challenge was not accepted.")
            return

        winner = await self.conduct_battle(ctx, player_data, opponent_data)

        if winner == player_data:
            await ctx.send(f"{ctx.author.mention} wins the duel!")
        else:
            await ctx.send(f"{opponent.mention} wins the duel!")

    async def conduct_battle(self, ctx, player1, player2):
        await ctx.send(f"🏟️ **Battle Start!**\n{player1['name']} vs {player2['name']}")

        battle_embed = discord.Embed(title="Battle", color=discord.Color.red())
        battle_embed.add_field(name=player1['name'], value=f"HP: {player1['hp']}/{player1['max_hp']}", inline=True)
        battle_embed.add_field(name=player2['name'], value=f"HP: {player2['hp']}/{player2['max_hp']}", inline=True)
        battle_msg = await ctx.send(embed=battle_embed)

        while player1["hp"] > 0 and player2["hp"] > 0:
            for attacker, defender in [(player1, player2), (player2, player1)]:
                if attacker["hp"] <= 0:
                    break

                move_embed = discord.Embed(title=f"{attacker['name']}, choose your move", description="\n".join(attacker['learned_moves']), color=discord.Color.blue())
                move_msg = await ctx.send(embed=move_embed)

                move = await self.get_player_move(ctx, attacker['learned_moves'], move_msg)
                damage, effect = await self.use_move(attacker, defender, move)

                battle_embed.clear_fields()
                battle_embed.add_field(name=f"{attacker['name']}'s Attack", value=f"{attacker['name']} uses {move} and deals {damage} damage!", inline=False)
                if effect:
                    battle_embed.add_field(name="Effect", value=effect, inline=False)
                battle_embed.add_field(name=player1['name'], value=f"HP: {player1['hp']}/{player1['max_hp']}", inline=True)
                battle_embed.add_field(name=player2['name'], value=f"HP: {player2['hp']}/{player2['max_hp']}", inline=True)
                await battle_msg.edit(embed=battle_embed)
                await move_msg.delete()
                await asyncio.sleep(2)

        if player1["hp"] > 0:
            return player1
        else:
            return player2

    def generate_villain(self, level):
        villain_names = ["Shadow Fist", "Vortex", "Inferno", "Frost Giant", "Mind Bender"]
        quirk_types = ["Dark", "Air", "Fire", "Ice", "Psychic"]
        
        name = random.choice(villain_names)
        quirk_type = random.choice(quirk_types)
        quirk = f"Villainous {quirk_type} (Emitter)"
        
        villain = {
            "name": name,
            "quirk": quirk,
            "quirk_type": quirk_type,
            "level": level,
            "hp": level * 20,
            "max_hp": level * 20,
            "attack": level * 3,
            "defense": level * 2,
            "speed": level * 2,
            "learned_moves": self.get_moves_for_quirk(quirk_type, level)
        }
        
        return villain

    def get_moves_for_quirk(self, quirk_type, level):
        quirk_moves = [move for move, data in self.moves.items() if data["type"].lower() == quirk_type.lower()]
        num_moves = min(level // 2, len(quirk_moves))
        return random.sample(quirk_moves, num_moves) + ["Punch", "Kick"]


    @mha.command(name="train", aliases=["practice"])
    async def train_move(self, ctx, *, move_name: str):
        """Train to learn a new move"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use the `mha begin` command to start.")
            return

        move_name = move_name.title()  # Capitalize each word
        if move_name not in self.moves:
            await ctx.send(f"'{move_name}' is not a valid move.")
            return

        if move_name in user_data["learned_moves"]:
            await ctx.send(f"You already know the move '{move_name}'.")
            return

        move_data = self.moves[move_name]
        required_level = move_data.get("required_level", 1)
        
        if user_data["level"] < required_level:
            await ctx.send(f"You need to be at least level {required_level} to learn '{move_name}'.")
            return

        # Check if the move type matches the user's quirk type
        if move_data["type"].lower() != user_data["quirk_type"].lower() and move_data["type"] != "Physical":
            await ctx.send(f"Your quirk type doesn't match the move type. You can't learn '{move_name}'.")
            return

        # Training minigame
        await ctx.send(f"Training to learn '{move_name}'! React with 🎯 when you see it!")
        await asyncio.sleep(random.uniform(2, 5))
        train_msg = await ctx.send("🎯")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '🎯'

        try:
            await self.bot.wait_for('reaction_add', timeout=2.0, check=check)
            user_data["learned_moves"].append(move_name)
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations! You've learned the move '{move_name}'!")
        except asyncio.TimeoutError:
            await ctx.send("Training failed. You weren't quick enough. Try again!")

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
