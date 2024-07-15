import discord
from redbot.core import commands, Config
import random
import asyncio
from datetime import datetime, timedelta
import json
from redbot.core.utils.predicates import MessagePredicate

def safe_json_loads(self, data, default=None):
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}

class DemonSlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.event_task = self.bot.loop.create_task(self.random_event_loop())
        self.current_event = None

        default_user = {
            "has_passed_exam": False,
            "exam_cooldown": None,
            "breathing_technique": None,
            "breathing_mastery": "{}",  # JSON string
            "nichirin_blade_color": None,
            "nichirin_blade_level": 0,
            "material_scarlet_iron_sand": 0,
            "material_scarlet_ore": 0,
            "material_spirit_wood": 0,
            "demons_slayed": 0,
            "rank": None,
            "experience": 0,
            "companion": None,
            "last_hunt": None,
            "upper_moon_defeated": False,
            "is_demon": False,
            "demon_rank": None,
            "blood_demon_art": None,
            "demons_consumed": 0,
            "story_progress": 0,
        }
        
        default_guild = {
            "active_hashira_training": None,  # Will be set as JSON string when active
            "event_channel": None,
        }
        
        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)
        
        self.breathing_techniques = {
            "Water": ["Water Surface Slash", "Water Wheel", "Flowing Dance", "Striking Tide", "Blessed Rain"],
            "Thunder": ["Thunderclap and Flash", "Rice Spirit", "Thunder Swarm", "Distant Thunder", "Heat Lightning"],
            "Flame": ["Unknowing Fire", "Rising Scorching Sun", "Blazing Universe", "Blooming Flame", "Flame Tiger"],
            "Wind": ["Dust Whirlwind Cutter", "Claws-Purifying Wind", "Clean Storm Wind", "Rising Dust Storm", "Purgatory Windmill"],
            "Stone": ["Serpentine Bipedal", "Upper Smash", "Stone Skin", "Volcanic Rock", "Arcs of Justice"]
        }

        self.story_quests = [
            {
                "title": "First Mission",
                "description": "You've completed your training and are ready for your first mission. A nearby village has reported strange disappearances.",
                "options": ["Investigate the village", "Train more before leaving", "Ask a senior slayer for advice"],
                "outcomes": [
                    "You discover a demon hiding in the village and manage to defeat it!",
                    "Your extra training pays off when you face your first demon.",
                    "The senior slayer's advice proves invaluable in your first encounter."
                ]
            },
            {
                "title": "The Wisteria House",
                "description": "You've been assigned to guard a Wisteria House, a safe haven for demon slayers. Suddenly, you hear screams from inside.",
                "options": ["Rush in immediately", "Assess the situation from outside", "Call for backup"],
                "outcomes": [
                    "Your quick action saves lives, but you're injured in the process.",
                    "Your caution reveals a trap set by demons, which you manage to disarm.",
                    "Backup arrives just in time to help you fend off a powerful demon attack."
                ]
            },
            {
                "title": "Mountain Trial",
                "description": "Your next mission takes you to a remote mountain where several slayers have gone missing.",
                "options": ["Climb the treacherous path", "Search for a hidden route", "Set up a base camp first"],
                "outcomes": [
                    "The difficult climb strengthens your resolve, preparing you for the challenges ahead.",
                    "You discover a network of caves that leads you to the demon's lair.",
                    "Your well-prepared base camp becomes crucial for surviving the lengthy mission."
                ]
            },
            {
                "title": "Demon Moon Encounter",
                "description": "During a routine patrol, you encounter a Lower Moon demon. This is your first time facing such a powerful foe.",
                "options": ["Engage in direct combat", "Use the environment to your advantage", "Attempt to flee and report"],
                "outcomes": [
                    "Your bravery impresses the Hashira, earning you recognition despite the tough battle.",
                    "Your clever use of the terrain allows you to hold your ground until help arrives.",
                    "Your report leads to a coordinated effort to take down the Lower Moon."
                ]
            },
            {
                "title": "The Swordsmith Village",
                "description": "You're tasked with escorting a young swordsmith to their village. On the way, you're ambushed by demons.",
                "options": ["Protect the swordsmith at all costs", "Fight aggressively to end the battle quickly", "Try to lose the demons in the forest"],
                "outcomes": [
                    "Your unwavering protection impresses the swordsmith, who later crafts you a superior blade.",
                    "Your aggressive strategy catches the demons off guard, leading to a swift victory.",
                    "Your knowledge of the forest helps you escape, and you learn valuable evasion techniques."
                ]
            }
        ]
        
        self.ranks = [
            "Mizunoto", "Mizunoe", "Kanoto", "Kanoe", "Tsuchinoto", "Tsuchinoe",
            "Hinoto", "Hinoe", "Kinoto", "Kinoe", "Hashira"
        ]

        self.demon_ranks = ["Newly Turned", "Lower Rank 6", "Lower Rank 5", "Lower Rank 4", "Lower Rank 3", "Lower Rank 2", "Lower Rank 1", 
                            "Upper Rank 6", "Upper Rank 5", "Upper Rank 4", "Upper Rank 3", "Upper Rank 2", "Upper Rank 1"]
        
        self.blood_demon_arts = [
            "Blood Manipulation",
            "Shadow Control",
            "Flesh Manipulation",
            "Illusion Creation",
            "Poison Generation",
            "Sound Manipulation",
            "Time Distortion",
            "Elemental Affinity",
            "Mind Control",
            "Regeneration",
            "Dimensional Manipulation",
            "Emotion Amplification",
            "Gravity Control",
            "Dream Infiltration",
            "Metamorphosis"
        ]
        
        self.companions = ["Kasugai Crow", "Nichirin Ore Fox", "Demon Slayer Cat"]

    def cog_unload(self):
        if self.event_task:
            self.event_task.cancel()

    async def random_event_loop(self):
        while True:
            await asyncio.sleep(600)  # 10 minutes
            await self.trigger_random_event()

    async def trigger_random_event(self):
        events = [
            self.demon_invasion,
            self.rare_material_discovery,
            self.hashira_challenge,
            self.blood_moon,
            self.wisteria_bloom
        ]
        self.current_event = random.choice(events)
        await self.current_event()
        

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def dsset(self, ctx):
        """Demon Slayer settings"""
        pass

    @dsset.command(name="eventchannel")
    async def set_event_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for Demon Slayer events"""
        await self.config.guild(ctx.guild).event_channel.set(channel.id)
        await ctx.send(f"Demon Slayer events will now be announced in {channel.mention}")

    async def get_event_channel(self, guild):
        channel_id = await self.config.guild(guild).event_channel()
        return self.bot.get_channel(channel_id) if channel_id else None

    async def trigger_random_event(self):
        events = [
            self.demon_invasion,
            self.rare_material_discovery,
            self.hashira_challenge,
            self.blood_moon,
            self.wisteria_bloom
        ]
        self.current_event = random.choice(events)
        for guild in self.bot.guilds:
            event_channel = await self.get_event_channel(guild)
            if event_channel:
                await self.current_event(event_channel)

    @ds.command(name="joinevent")
    async def join_event(self, ctx):
        """Join the current active event"""
        if self.current_event is None:
            await ctx.send("There is no active event right now.")
            return
        
        user_data = await self.config.user(ctx.author).all()
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the Demon Slayer exam before participating in events!")
            return

        event_name = self.current_event.__name__
        await ctx.send(f"You've joined the current event: {event_name}")
        
        if event_name == "demon_invasion":
            await self.participate_demon_invasion(ctx, user_data)
        elif event_name == "rare_material_discovery":
            await self.participate_rare_material_discovery(ctx, user_data)
        elif event_name == "hashira_challenge":
            await self.participate_hashira_challenge(ctx, user_data)
        elif event_name == "blood_moon":
            await self.participate_blood_moon(ctx, user_data)
        elif event_name == "wisteria_bloom":
            await self.participate_wisteria_bloom(ctx, user_data)

    async def demon_invasion(self):
        await self.bot.get_channel(self.config.guild(self.bot.guilds[0]).event_channel()).send(
            "🚨 A demon invasion has begun! Use `[p]ds join_event` to defend the village!"
        )
        self.current_event = self.demon_invasion
        await asyncio.sleep(600)  # Event lasts for 10 minutes
        self.current_event = None

    async def participate_demon_invasion(self, ctx, user_data):
        demons_defeated = random.randint(1, 5)
        xp_gained = demons_defeated * 50
        user_data["demons_slayed"] += demons_defeated
        user_data["experience"] += xp_gained
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've defeated {demons_defeated} demons and gained {xp_gained} XP!")

    async def rare_material_discovery(self):
        await self.bot.get_channel(self.config.guild(self.bot.guilds[0]).event_channel()).send(
            "💎 Rare materials have been discovered! Use `[p]ds join_event` to gather them!"
        )
        self.current_event = self.rare_material_discovery
        await asyncio.sleep(600)  # Event lasts for 10 minutes
        self.current_event = None

    async def participate_rare_material_discovery(self, ctx, user_data):
        materials = ["scarlet_iron_sand", "scarlet_ore", "spirit_wood"]
        gathered_material = random.choice(materials)
        amount = random.randint(5, 15)
        user_data[f"material_{gathered_material}"] += amount
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've gathered {amount} {gathered_material.replace('_', ' ')}!")

    async def hashira_challenge(self):
        await self.bot.get_channel(self.config.guild(self.bot.guilds[0]).event_channel()).send(
            "⚔️ A Hashira has issued a challenge! Use `[p]ds join_event` to test your skills!"
        )
        self.current_event = self.hashira_challenge
        await asyncio.sleep(600)  # Event lasts for 10 minutes
        self.current_event = None

    async def participate_hashira_challenge(self, ctx, user_data):
        if self.ranks.index(user_data["rank"]) < self.ranks.index("Kinoe"):
            await ctx.send("You must be at least Kinoe rank to challenge a Hashira!")
            return

        hashira = random.choice(["Water", "Flame", "Wind", "Stone", "Love"])
        success = random.random() < 0.3  # 30% chance of success
        if success:
            xp_gained = random.randint(500, 1000)
            user_data["experience"] += xp_gained
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"You've successfully completed the {hashira} Hashira's challenge and gained {xp_gained} XP!")
        else:
            await ctx.send(f"You were defeated by the {hashira} Hashira. Keep training and try again next time!")

    async def blood_moon(self):
        await self.bot.get_channel(self.config.guild(self.bot.guilds[0]).event_channel()).send(
            "🔴 The Blood Moon has risen! Demons are stronger, but rewards are greater. Use `[p]ds join_event` to hunt!"
        )
        self.current_event = self.blood_moon
        await asyncio.sleep(600)  # Event lasts for 10 minutes
        self.current_event = None

    async def participate_blood_moon(self, ctx, user_data):
        demon_strength = random.randint(100, 500)
        user_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10
        if user_strength > demon_strength:
            xp_gained = demon_strength * 2  # Double XP during Blood Moon
            user_data["experience"] += xp_gained
            user_data["demons_slayed"] += 1
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"You've defeated a powerful demon under the Blood Moon and gained {xp_gained} XP!")
        else:
            await ctx.send("The demon was too strong! You managed to escape, but gained no rewards.")

    async def wisteria_bloom(self):
        await self.bot.get_channel(self.config.guild(self.bot.guilds[0]).event_channel()).send(
            "🌸 Wisteria flowers are in bloom! Use `[p]ds join_event` to receive their blessing!"
        )
        self.current_event = self.wisteria_bloom
        await asyncio.sleep(600)  # Event lasts for 10 minutes
        self.current_event = None

    async def participate_wisteria_bloom(self, ctx, user_data):
        healing = random.randint(50, 200)
        protection_duration = random.randint(1, 3)
        user_data["experience"] += healing
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"The Wisteria bloom has healed you for {healing} HP and granted you {protection_duration} hours of demon protection!")

    @ds.command(name="story")
    async def story_quest(self, ctx):
        """Progress through the Demon Slayer story"""
        user_data = await self.config.user(ctx.author).all()
        
        if user_data["is_demon"]:
            await ctx.send("As a demon, you cannot participate in Demon Slayer story quests.")
            return
        
        if user_data["story_progress"] >= len(self.story_quests):
            await ctx.send("Congratulations! You have completed all available story quests. Stay tuned for more adventures!")
            return
        
        quest = self.story_quests[user_data["story_progress"]]
        
        embed = discord.Embed(title=quest["title"], description=quest["description"], color=discord.Color.blue())
        for i, option in enumerate(quest["options"], 1):
            embed.add_field(name=f"Option {i}", value=option, inline=False)
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(quest["options"])
        
        try:
            choice = await self.bot.wait_for('message', check=check, timeout=30.0)
            choice = int(choice.content) - 1
            
            outcome = quest["outcomes"][choice]
            await ctx.send(f"Outcome: {outcome}")
            
            user_data["story_progress"] += 1
            user_data["experience"] += 100  # Reward for completing a story quest
            await self.config.user(ctx.author).set(user_data)
            
            if user_data["story_progress"] < len(self.story_quests):
                await ctx.send(f"You've completed this quest! Use the command again to start the next one.")
            else:
                await ctx.send("Congratulations! You've completed all available story quests. Stay tuned for more adventures!")
            
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The quest has been cancelled.")
    
    @ds.command(name="demon")
    async def become_demon(self, ctx):
        """Choose to become a demon"""
        user_data = await self.config.user(ctx.author).all()
            
        if user_data["is_demon"]:
            await ctx.send("You are already a demon!")
            return
            
        await ctx.send("Are you sure you want to abandon your humanity and become a demon? This action is irreversible. (yes/no)")
            
        def check(m):
            return m.author == ctx.author and m.content.lower() in ['yes', 'no']
            
        try:
            choice = await self.bot.wait_for('message', check=check, timeout=30.0)
                
            if choice.content.lower() == 'yes':
                user_data["is_demon"] = True
                user_data["demon_rank"] = "Newly Turned"
                user_data["blood_demon_art"] = random.choice(self.blood_demon_arts)
                user_data["breathing_technique"] = None  # Demons don't use breathing techniques
                    
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"You have become a demon! Your Blood Demon Art is: {user_data['blood_demon_art']}")
            else:
                await ctx.send("You have chosen to remain human.")
                    
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The transformation has been cancelled.")

    @ds.command(name="dbattle")
    async def demon_battle(self, ctx, opponent: discord.Member):
        """Challenge another demon to a blood battle"""
        user_data = await self.config.user(ctx.author).all()
        opponent_data = await self.config.user(opponent).all()
        
        if not user_data["is_demon"] or not opponent_data["is_demon"]:
            await ctx.send("Both participants must be demons to engage in a blood battle!")
            return
        
        user_strength = self.calculate_demon_strength(user_data)
        opponent_strength = self.calculate_demon_strength(opponent_data)
        
        await ctx.send(f"{ctx.author.mention} has challenged {opponent.mention} to a blood battle!")
        await asyncio.sleep(3)
        
        if user_strength > opponent_strength:
            winner, loser = ctx.author, opponent
            winner_data, loser_data = user_data, opponent_data
        else:
            winner, loser = opponent, ctx.author
            winner_data, loser_data = opponent_data, user_data
        
        await ctx.send(f"{winner.mention} has emerged victorious in the blood battle!")
        
        # Winner consumes the loser
        winner_data["demons_consumed"] += 1
        self.upgrade_demon_rank(winner_data)
        
        # Reset loser to human
        loser_data["is_demon"] = False
        loser_data["demon_rank"] = None
        loser_data["blood_demon_art"] = None
        
        await self.config.user(winner).set(winner_data)
        await self.config.user(loser).set(loser_data)
        
        await ctx.send(f"{winner.mention} has consumed {loser.mention} and grown stronger!")
        await ctx.send(f"{loser.mention} has been turned back into a human.")

    def calculate_demon_strength(self, user_data):
        rank_index = self.demon_ranks.index(user_data["demon_rank"])
        return (rank_index + 1) * 100 + user_data["demons_consumed"] * 50

    def upgrade_demon_rank(self, user_data):
        current_rank_index = self.demon_ranks.index(user_data["demon_rank"])
        if current_rank_index < len(self.demon_ranks) - 1:
            user_data["demon_rank"] = self.demon_ranks[current_rank_index + 1]

    @ds.command(name="dprofile")
    async def demon_profile(self, ctx, user: discord.Member = None):
        """Display your demon profile"""
        if user is None:
            user = ctx.author
        
        user_data = await self.config.user(user).all()
        
        if not user_data["is_demon"]:
            await ctx.send("This user is not a demon!")
            return
        
        embed = discord.Embed(title=f"{user.name}'s Demon Profile", color=discord.Color.dark_red())
        embed.add_field(name="Rank", value=user_data["demon_rank"])
        embed.add_field(name="Blood Demon Art", value=user_data["blood_demon_art"])
        embed.add_field(name="Demons Consumed", value=str(user_data["demons_consumed"]))
        
        await ctx.send(embed=embed)

    @ds.command(name="exam")
    async def take_exam(self, ctx):
        """Take the Demon Slayer Corps Entrance Exam"""
        user_data = await self.config.user(ctx.author).all()
        
        if user_data["has_passed_exam"]:
            await ctx.send("You've already passed the exam and joined the Demon Slayer Corps!")
            return
        
        if user_data["exam_cooldown"] and user_data["exam_cooldown"] > datetime.now().timestamp():
            cooldown = datetime.fromtimestamp(user_data["exam_cooldown"]) - datetime.now()
            await ctx.send(f"You must wait {cooldown.seconds // 60} minutes before retaking the exam.")
            return
        
        questions = [
            ("What is the primary weakness of demons?", "Sunlight"),
            ("What material are Nichirin Blades made from?", "Scarlet Ore"),
            ("How many forms are there in Water Breathing?", "11"),
            ("Who is the current leader of the Demon Slayer Corps?", "Kagaya Ubuyashiki"),
            ("What is the name of the demon who turns humans into demons?", "Muzan Kibutsuji")
        ]
        
        score = 0
        for i, (question, answer) in enumerate(questions, 1):
            embed = discord.Embed(title=f"Entrance Exam - Question {i}", description=question, color=discord.Color.blue())
            await ctx.send(embed=embed)
            
            try:
                user_answer = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send("Time's up! Moving to the next question.")
                continue
            
            if user_answer.content.lower() == answer.lower():
                score += 1
                await ctx.send("Correct!")
            else:
                await ctx.send(f"Incorrect. The correct answer is: {answer}")
        
        if score >= 3:
            user_data["has_passed_exam"] = True
            user_data["rank"] = "Mizunoto"
            user_data["breathing_technique"] = random.choice(list(self.breathing_techniques.keys()))
            user_data["companion"] = random.choice(self.companions)
            user_data["nichirin_blade_color"] = random.choice(["Red", "Blue", "Green", "Yellow", "Purple", "Black"])
            user_data["breathing_mastery"] = json.dumps({})  # Initialize as empty JSON object
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations! You've passed the exam with a score of {score}/5. Welcome to the Demon Slayer Corps!")
            await ctx.send(f"Your assigned Breathing Technique is: {user_data['breathing_technique']}")
            await ctx.send(f"Your companion is: {user_data['companion']}")
            await ctx.send(f"Your Nichirin Blade color is: {user_data['nichirin_blade_color']}")
        else:
            user_data["exam_cooldown"] = (datetime.now() + timedelta(minutes=5)).timestamp()
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"You've failed the exam with a score of {score}/5. You can retake it in 5 minutes.")

    @commands.is_owner()
    @ds.command(name="wipe_data")
    async def wipe_all_data(self, ctx):
        """Wipe all Demon Slayer data (Owner only)"""
        await ctx.send("⚠️ **WARNING**: This will delete ALL Demon Slayer data for all users and guilds. "
                       "This action is irreversible. Are you sure you want to proceed? (yes/no)")

        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("No response received. Data wipe cancelled.")
            return

        if pred.result is True:
            # Wipe all user data
            await self.config.clear_all_users()
            
            # Wipe all guild data
            await self.config.clear_all_guilds()
            
            await ctx.send("All Demon Slayer data has been wiped.")
        else:
            await ctx.send("Data wipe cancelled.")

    @ds.command(name="hunt")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def hunt(self, ctx):
        """Hunt for demons or humans"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can hunt!")
            return
        
        if user_data["is_demon"]:
            prey = "human"
            prey_types = ["Civilian", "Demon Slayer Trainee", "Lower Rank Demon Slayer", "Higher Rank Demon Slayer"]
        else:
            prey = "demon"
            prey_types = ["Lesser Demon", "Strong Demon", "Lower Moon", "Upper Moon"]
        
        weights = [0.6, 0.3, 0.09, 0.01]
        target = random.choices(prey_types, weights=weights)[0]
        
        embed = discord.Embed(title=f"{prey.capitalize()} Hunt", color=discord.Color.red())
        embed.add_field(name=f"{prey.capitalize()} Type", value=target)
        
        if target in ["Upper Moon", "Higher Rank Demon Slayer"]:
            embed.add_field(name="WARNING", value=f"You've encountered a powerful {prey}! This will be an extremely difficult battle!")
        
        await ctx.send(embed=embed)
        
        # Simulate battle
        await asyncio.sleep(3)
        
        success_chance = {
            "Civilian": 0.9, "Demon Slayer Trainee": 0.7, "Lower Rank Demon Slayer": 0.5, "Higher Rank Demon Slayer": 0.2,
            "Lesser Demon": 0.8, "Strong Demon": 0.6, "Lower Moon": 0.3, "Upper Moon": 0.05
        }
        
        if random.random() < success_chance[target]:
            xp_gain = {
                "Civilian": random.randint(10, 30), "Demon Slayer Trainee": random.randint(30, 70),
                "Lower Rank Demon Slayer": random.randint(70, 150), "Higher Rank Demon Slayer": random.randint(150, 300),
                "Lesser Demon": random.randint(10, 50), "Strong Demon": random.randint(50, 100),
                "Lower Moon": random.randint(100, 500), "Upper Moon": random.randint(500, 1000)
            }[target]
            
            user_data["experience"] += xp_gain
            if not user_data["is_demon"]:
                user_data["demons_slayed"] += 1
            else:
                user_data["humans_consumed"] = user_data.get("humans_consumed", 0) + 1
            
            result_embed = discord.Embed(title="Hunt Result", color=discord.Color.green())
            result_embed.add_field(name="Outcome", value="Victory!")
            result_embed.add_field(name="XP Gained", value=str(xp_gain))
            
            if not user_data["is_demon"]:
                material_gain = {
                    "scarlet_iron_sand": random.randint(1, 5),
                    "scarlet_ore": random.randint(0, 2),
                    "spirit_wood": random.randint(1, 3)
                }
                for material, amount in material_gain.items():
                    user_data[f"material_{material}"] += amount
                result_embed.add_field(name="Materials Gained", value="\n".join([f"{mat.replace('_', ' ').title()}: {amt}" for mat, amt in material_gain.items()]))
            
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(embed=result_embed)
            await self.check_rank_up(ctx)
        else:
            await ctx.send(f"You were defeated by the {target} and had to retreat. Better luck next time!")

    @ds.command(name="upgrade")
    async def upgrade_blade(self, ctx):
        """Upgrade your Nichirin Blade"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can upgrade your blade!")
            return
        
        current_level = user_data["nichirin_blade_level"]
        cost = {
            "scarlet_iron_sand": (current_level + 1) * 5,
            "scarlet_ore": (current_level + 1) * 2,
            "spirit_wood": (current_level + 1) * 3
        }
        
        embed = discord.Embed(title="Nichirin Blade Upgrade", color=discord.Color.gold())
        embed.add_field(name="Current Level", value=f"+{current_level}")
        embed.add_field(name="Upgrade Cost", value="\n".join([f"{mat.replace('_', ' ').title()}: {amt}" for mat, amt in cost.items()]))
        
        if all(user_data[f"material_{mat}"] >= amt for mat, amt in cost.items()):
            embed.add_field(name="Upgrade Possible", value="Yes", inline=False)
            embed.add_field(name="Instructions", value="React with ✅ to upgrade or ❌ to cancel.", inline=False)
            message = await ctx.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Upgrade cancelled due to timeout.")
                return
            
            if str(reaction.emoji) == "✅":
                for mat, amt in cost.items():
                    user_data[f"material_{mat}"] -= amt
                user_data["nichirin_blade_level"] += 1
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"Your Nichirin Blade has been upgraded to +{user_data['nichirin_blade_level']}!")
            else:
                await ctx.send("Upgrade cancelled.")
        else:
            embed.add_field(name="Upgrade Possible", value="No", inline=False)
            embed.add_field(name="Reason", value="Insufficient materials", inline=False)
            await ctx.send(embed=embed)

    @ds.command(name="train")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def train_breathing(self, ctx):
        """Train to improve your skills"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can train!")
            return
        
        if user_data["is_demon"]:
            # Demon training
            blood_art = user_data["blood_demon_art"]
            mastery_gain = random.randint(1, 10)
            
            if "blood_demon_art_mastery" not in user_data:
                user_data["blood_demon_art_mastery"] = {}
            
            if isinstance(user_data["blood_demon_art_mastery"], str):
                user_data["blood_demon_art_mastery"] = {}
            
            if blood_art not in user_data["blood_demon_art_mastery"]:
                user_data["blood_demon_art_mastery"][blood_art] = 0
            
            user_data["blood_demon_art_mastery"][blood_art] += mastery_gain
            
            embed = discord.Embed(title="Demon Training", color=discord.Color.dark_red())
            embed.add_field(name="Blood Demon Art", value=blood_art)
            embed.add_field(name="Mastery Gained", value=str(mastery_gain))
            embed.add_field(name="Current Mastery", value=str(user_data["blood_demon_art_mastery"][blood_art]))
        else:
            # Human training
            technique = user_data["breathing_technique"]
            if not technique:
                await ctx.send("You don't have a breathing technique yet. Please contact an admin to assign you one.")
                return
            
            forms = self.breathing_techniques[technique]
            
            breathing_mastery = user_data.get("breathing_mastery", {})
            if isinstance(breathing_mastery, str):
                try:
                    breathing_mastery = json.loads(breathing_mastery)
                except json.JSONDecodeError:
                    breathing_mastery = {}
            
            if technique not in breathing_mastery:
                breathing_mastery[technique] = {}
            
            form_to_train = random.choice(forms)
            mastery_gain = random.randint(1, 10)
            
            if form_to_train not in breathing_mastery[technique]:
                breathing_mastery[technique][form_to_train] = 0
            
            breathing_mastery[technique][form_to_train] += mastery_gain
            user_data["breathing_mastery"] = breathing_mastery
            
            embed = discord.Embed(title="Breathing Technique Training", color=discord.Color.blue())
            embed.add_field(name="Technique", value=technique)
            embed.add_field(name="Form Trained", value=form_to_train)
            embed.add_field(name="Mastery Gained", value=str(mastery_gain))
            embed.add_field(name="Current Mastery", value=str(breathing_mastery[technique][form_to_train]))
        
        # Common for both demons and humans
        xp_gained = random.randint(10, 50)
        user_data["experience"] += xp_gained
        embed.add_field(name="XP Gained", value=str(xp_gained))
        
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(embed=embed)
        await self.check_rank_up(ctx)

    @ds.command(name="profile")
    async def show_profile(self, ctx, user: discord.Member = None):
        """Display your Demon Slayer profile"""
        if user is None:
            user = ctx.author
        
        user_data = await self.config.user(user).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("This user hasn't passed the Demon Slayer Corps entrance exam yet!")
            return
        
        embed = discord.Embed(title=f"{user.name}'s Demon Slayer Profile", color=discord.Color.blue())
        embed.add_field(name="Rank", value=user_data["rank"])
        embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"])
        embed.add_field(name="Demons Slayed", value=str(user_data["demons_slayed"]))
        embed.add_field(name="Experience", value=str(user_data["experience"]))
        embed.add_field(name="Companion", value=user_data["companion"])
        embed.add_field(name="Nichirin Blade", value=f"{user_data['nichirin_blade_color']} (+{user_data['nichirin_blade_level']})")
        
        breathing_mastery = safe_json_loads(user_data["breathing_mastery"])
        mastery_text = "\n".join([f"{form}: {mastery}" for form, mastery in breathing_mastery.get(user_data["breathing_technique"], {}).items()])
        embed.add_field(name="Breathing Mastery", value=mastery_text or "No forms mastered yet", inline=False)
        
        materials_text = "\n".join([f"{mat.replace('material_', '').replace('_', ' ').title()}: {amt}" for mat, amt in user_data.items() if mat.startswith('material_')])
        embed.add_field(name="Materials", value=materials_text, inline=False)
        
        await ctx.send(embed=embed)

    @commands.is_owner()
    @ds.command(name="starth")
    async def start_hashira_training(self, ctx):
        """Start a Hashira training event (Owner only)"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        if guild_data["active_hashira_training"]:
            await ctx.send("A Hashira training event is already active!")
            return
        
        hashira_training = {
            "hashira": random.choice(["Water", "Flame", "Wind", "Stone", "Love"]),
            "difficulty": random.randint(1, 5),
            "participants": []
        }
        await self.config.guild(ctx.guild).active_hashira_training.set(json.dumps(hashira_training))
        
        embed = discord.Embed(title="Hashira Training Event", color=discord.Color.purple())
        embed.add_field(name="Hashira", value=hashira_training["hashira"])
        embed.add_field(name="Difficulty", value="⭐" * hashira_training["difficulty"])
        embed.add_field(name="How to Join", value="Use the command `[p]ds join_hashira_training` to participate!", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="joinh")
    async def join_hashira_training(self, ctx):
        """Join the active Hashira training event"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_data = await self.config.user(ctx.author).all()
        
        if not guild_data["active_hashira_training"]:
            await ctx.send("There is no active Hashira training event!")
            return
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can participate in Hashira training!")
            return
        
        hashira_training = json.loads(guild_data["active_hashira_training"])
        
        if ctx.author.id in hashira_training["participants"]:
            await ctx.send("You're already participating in this Hashira training event!")
            return
        
        # Check if the user has defeated an Upper Moon demon
        if user_data["upper_moon_defeated"] or self.ranks.index(user_data["rank"]) >= self.ranks.index("Kinoe"):
            hashira_training["participants"].append(ctx.author.id)
            await self.config.guild(ctx.guild).active_hashira_training.set(json.dumps(hashira_training))
            await ctx.send(f"{ctx.author.mention} has joined the Hashira training event!")
        else:
            await ctx.send("You need to have defeated an Upper Moon demon or be at least Kinoe rank to participate in Hashira training!")

    @commands.is_owner()
    @ds.command(name="endh")
    async def end_hashira_training(self, ctx):
        """End the current Hashira training event and distribute rewards"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        if not guild_data["active_hashira_training"]:
            await ctx.send("There is no active Hashira training event!")
            return
        
        hashira_training = json.loads(guild_data["active_hashira_training"])
        
        embed = discord.Embed(title="Hashira Training Results", color=discord.Color.gold())
        embed.add_field(name="Hashira", value=hashira_training["hashira"])
        embed.add_field(name="Difficulty", value="⭐" * hashira_training["difficulty"])
        
        for participant_id in hashira_training["participants"]:
            user = self.bot.get_user(participant_id)
            if user:
                user_data = await self.config.user(user).all()
                xp_gain = random.randint(100, 500) * hashira_training["difficulty"]
                user_data["experience"] += xp_gain
                
                # Chance to learn a new form
                if random.random() < 0.1 * hashira_training["difficulty"]:
                    new_form = random.choice(self.breathing_techniques[hashira_training["hashira"]])
                    breathing_mastery = json.loads(user_data["breathing_mastery"])
                    if hashira_training["hashira"] not in breathing_mastery:
                        breathing_mastery[hashira_training["hashira"]] = {}
                    breathing_mastery[hashira_training["hashira"]][new_form] = 1
                    user_data["breathing_mastery"] = json.dumps(breathing_mastery)
                    embed.add_field(name=f"{user.name} Learned New Form", value=f"{new_form} ({hashira_training['hashira']} Breathing)", inline=False)
                
                await self.config.user(user).set(user_data)
                embed.add_field(name=f"{user.name} Rewards", value=f"XP Gained: {xp_gain}", inline=False)
        
        await ctx.send(embed=embed)
        await self.config.guild(ctx.guild).active_hashira_training.set(None)

    @ds.command(name="leaderboard")
    async def show_leaderboard(self, ctx):
        """Display the Demon Slayer leaderboard"""
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]["experience"], reverse=True)[:10]
        
        embed = discord.Embed(title="Demon Slayer Leaderboard", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"Rank: {data['rank']}\nXP: {data['experience']}\nDemons Slayed: {data['demons_slayed']}", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="stats")
    async def show_stats(self, ctx):
        """Display global Demon Slayer stats"""
        all_users = await self.config.all_users()
        total_demons_slayed = sum(user_data["demons_slayed"] for user_data in all_users.values())
        total_slayers = sum(1 for user_data in all_users.values() if user_data["has_passed_exam"])
        
        embed = discord.Embed(title="Demon Slayer Global Stats", color=discord.Color.blue())
        embed.add_field(name="Total Demons Slayed", value=str(total_demons_slayed))
        embed.add_field(name="Total Demon Slayers", value=str(total_slayers))
        
        # Count of each rank
        rank_counts = {rank: sum(1 for user_data in all_users.values() if user_data["rank"] == rank) for rank in self.ranks}
        rank_stats = "\n".join([f"{rank}: {count}" for rank, count in rank_counts.items() if count > 0])
        embed.add_field(name="Ranks", value=rank_stats, inline=False)
        
        await ctx.send(embed=embed)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        user_data = self.safe_json_loads(user_data, default={})
        
        if user_data.get("is_demon", False):
            current_rank_index = self.demon_ranks.index(user_data.get("demon_rank", "Newly Turned"))
            xp_threshold = (current_rank_index + 1) * 1500  # Demons need more XP to rank up
            
            if user_data.get("experience", 0) >= xp_threshold and current_rank_index < len(self.demon_ranks) - 1:
                new_rank = self.demon_ranks[current_rank_index + 1]
                user_data["demon_rank"] = new_rank
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"Congratulations, {ctx.author.mention}! You've ascended to {new_rank}!")
        else:
            current_rank_index = self.ranks.index(user_data.get("rank", "Mizunoto"))
            xp_threshold = (current_rank_index + 1) * 1000
            
            if user_data.get("experience", 0) >= xp_threshold and current_rank_index < len(self.ranks) - 1:
                new_rank = self.ranks[current_rank_index + 1]
                user_data["rank"] = new_rank
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")
            
def setup(bot):
    bot.add_cog(DemonSlayer(bot))
