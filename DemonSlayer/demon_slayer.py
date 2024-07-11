import discord
from redbot.core import commands, Config
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

class DemonSlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        default_user = {
            "breathing_technique": None,
            "secondary_breathing": None,
            "nichirin_color": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "form_levels": {},
            "last_daily": None,
            "slayer_points": 0,
            "guild": None,
            "companion": None,
            "nichirin_blade_level": 1,
            "materials": {"steel": 0, "wisteria": 0, "scarlet_ore": 0},
            "completed_missions": {"daily": [], "weekly": []},
            "last_hunt": None,
            "active_daily_mission": None,
            "active_weekly_mission": None,
            "last_daily_mission": None,
            "last_weekly_mission": None,
        }
        
        default_guild = {
            "event_channel": None,
            "active_boss_raid": None,
            "seasonal_event": None,
            "guilds": {},
            "active_hashira_trial": None,
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
        
        self.ranks = [
            "Mizunoto", "Mizunoe", "Kanoto", "Kanoe", "Tsuchinoto", "Tsuchinoe",
            "Hinoto", "Hinoe", "Kinoto", "Kinoe", "Hashira"
        ]
        
        self.demons = {
            "Lower Moon Six": {"difficulty": 60, "xp": 100},
            "Lower Moon Five": {"difficulty": 65, "xp": 120},
            "Lower Moon Four": {"difficulty": 70, "xp": 140},
            "Lower Moon Three": {"difficulty": 75, "xp": 160},
            "Lower Moon Two": {"difficulty": 80, "xp": 180},
            "Lower Moon One": {"difficulty": 85, "xp": 200},
            "Upper Moon Six": {"difficulty": 90, "xp": 250},
            "Upper Moon Five": {"difficulty": 92, "xp": 300},
            "Upper Moon Four": {"difficulty": 94, "xp": 350},
            "Upper Moon Three": {"difficulty": 96, "xp": 400},
            "Upper Moon Two": {"difficulty": 98, "xp": 450},
            "Upper Moon One": {"difficulty": 99, "xp": 500}
        }
        
        self.companions = {
            "Kasugai Crow": {"bonus": "communication", "strength": 50},
            "Nichirin Ore Fox": {"bonus": "sensing", "strength": 75},
            "Demon Slayer Cat": {"bonus": "agility", "strength": 100}
        }
        
        self.active_pvp_duels = {}
        self.missions = {
            "daily": [
                "Slay 5 demons",
                "Train for 3 hours",
                "Help 3 civilians",
                "Collect 10 wisteria flowers",
                "Defeat a Lower Moon demon"
            ],
            "weekly": [
                "Slay 50 demons",
                "Complete 10 daily missions",
                "Upgrade your Nichirin Blade",
                "Participate in a boss raid",
                "Reach the next rank"
            ]
        }
        
        self.event_task = None

    async def check_mission_completion(self, ctx, mission_type):
        user_data = await self.config.user(ctx.author).all()
        mission = user_data[f"active_{mission_type}_mission"]
        if not mission:
            return False
    
        completed = False
        if mission == "Slay 5 demons" and user_data["demons_slayed"] >= 5:
            completed = True
        elif mission == "Train for 3 hours":
            # Assuming we track training time, we'd check it here
            pass
        elif mission == "Help 3 civilians":
            # This would require a new tracking mechanism
            pass
        elif mission == "Collect 10 wisteria flowers":
            if user_data["materials"]["wisteria"] >= 10:
                completed = True
        elif mission == "Defeat a Lower Moon demon":
            # This would require tracking specific demon defeats
            pass
        elif mission == "Slay 50 demons" and user_data["demons_slayed"] >= 50:
            completed = True
        elif mission == "Complete 10 daily missions":
            # This would require tracking completed daily missions
            pass
        elif mission == "Upgrade your Nichirin Blade":
            # Check if the blade was upgraded since the mission was given
            pass
        elif mission == "Participate in a boss raid":
            # Check if the user participated in a raid since the mission was given
            pass
        elif mission == "Reach the next rank":
            # Check if the user's rank changed since the mission was given
            pass
    
        if completed:
            await self.complete_mission(ctx, mission_type)
        return completed

    async def complete_mission(self, ctx, mission_type):
        user_data = await self.config.user(ctx.author).all()
        xp_reward = 100 if mission_type == "daily" else 500
        material_reward = {"steel": 5, "wisteria": 3, "scarlet_ore": 2} if mission_type == "daily" else {"steel": 20, "wisteria": 15, "scarlet_ore": 10}
    
        user_data["experience"] += xp_reward
        for material, amount in material_reward.items():
            user_data["materials"][material] += amount
    
        user_data[f"active_{mission_type}_mission"] = None
        user_data[f"last_{mission_type}_mission"] = datetime.now().isoformat()
    
        await self.config.user(ctx.author).set(user_data)
    
        embed = discord.Embed(title=f"{mission_type.capitalize()} Mission Completed!", color=discord.Color.green())
        embed.description = f"You've completed your {mission_type} mission!"
        embed.add_field(name="XP Reward", value=str(xp_reward))
        embed.add_field(name="Material Rewards", value="\n".join(f"{material.capitalize()}: {amount}" for material, amount in material_reward.items()))
        await ctx.send(embed=embed)
    

    def cog_unload(self):
        if self.event_task:
            self.event_task.cancel()

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""
        if ctx.invoked_subcommand is None:
            if ctx.message.content.lower().strip() == f"{ctx.prefix}ds join":
                if self.active_global_event:
                    await self.join_global_event(ctx)
                else:
                    await ctx.send("There's no active global event to join right now.")
            else:
                await ctx.send_help(ctx.command)

    @ds.command(name="start")
    async def start_journey(self, ctx):
        """Begin your journey as a Demon Slayer"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you've already begun your journey!")
            return

        technique = random.choice(list(self.breathing_techniques.keys()))
        color = random.choice(["Red", "Blue", "Green", "Yellow", "Purple", "Black"])
        first_form = self.breathing_techniques[technique][0]
        
        await self.config.user(ctx.author).breathing_technique.set(technique)
        await self.config.user(ctx.author).nichirin_color.set(color)
        await self.config.user(ctx.author).known_forms.set([first_form])
        await self.config.user(ctx.author).form_levels.set({first_form: 1})

        await ctx.send(f"Welcome to the Demon Slayer Corps, {ctx.author.mention}!\n"
                       f"Your Breathing Technique is: {technique}\n"
                       f"Your Nichirin Blade is: {color}\n"
                       f"You've learned your first form: {first_form}")

    @ds.command(name="profile")
    async def show_profile(self, ctx, user: discord.Member = None):
        """Display your Demon Slayer profile"""
        if user is None:
            user = ctx.author
        user_data = await self.config.user(user).all()

        if not user_data["breathing_technique"]:
            await ctx.send(f"{user.mention} hasn't started their Demon Slayer journey yet!")
            return

        embed = discord.Embed(title=f"{user.name}'s Demon Slayer Profile", color=discord.Color.red())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"], inline=False)
        if user_data["secondary_breathing"]:
            embed.add_field(name="Secondary Breathing", value=user_data["secondary_breathing"], inline=False)
        embed.add_field(name="Nichirin Blade", value=f"{user_data['nichirin_color']} (Level {user_data['nichirin_blade_level']})", inline=False)
        embed.add_field(name="Rank", value=user_data["rank"], inline=True)
        embed.add_field(name="Demons Slayed", value=user_data["demons_slayed"], inline=True)
        embed.add_field(name="Experience", value=user_data["experience"], inline=True)
        
        forms = "\n".join([f"{form} (Level {user_data['form_levels'].get(form, 1)})" for form in user_data["known_forms"]])
        embed.add_field(name="Known Forms", value=forms, inline=False)
        
        if user_data["companion"]:
            embed.add_field(name="Companion", value=user_data["companion"], inline=False)
        
        if user_data["guild"]:
            embed.add_field(name="Guild", value=user_data["guild"], inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="train")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def train(self, ctx):
        """Train to improve your skills"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        xp_gained = random.randint(10, 50)
        await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)

        embed = discord.Embed(title="Training Results", color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} trains intensively and gains {xp_gained} experience!"

        # Chance to learn a new form
        if random.random() < 0.2:  # 20% chance to learn a new form
            await self.learn_new_form(ctx, embed)
        
        await ctx.send(embed=embed)
        await self.check_rank_up(ctx)

    @ds.command(name="hunt")
    @commands.cooldown(1, 7200, commands.BucketType.user)  # 2-hour cooldown
    async def personal_hunt(self, ctx):
        """Initiate a personal demon hunt"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        demon_types = ["Lesser Demon", "Stronger Demon", "Lower Moon", "Upper Moon"]
        weights = [0.4, 0.3, 0.2, 0.1]
        demon_type = random.choices(demon_types, weights=weights)[0]

        if demon_type == "Lesser Demon":
            demon = random.choice(["Swamp Demon", "Temple Demon", "Drum Demon"])
            strength = random.randint(100, 300)
        elif demon_type == "Stronger Demon":
            demon = random.choice(["Arrow Demon", "Temari Demon", "Spider Demon"])
            strength = random.randint(300, 600)
        elif demon_type == "Lower Moon":
            demon = f"Lower Moon {random.randint(1, 6)}"
            strength = random.randint(600, 1000)
        else:
            demon = f"Upper Moon {random.randint(1, 6)}"
            strength = random.randint(1000, 2000)

        embed = discord.Embed(title="Personal Demon Hunt", color=discord.Color.dark_red())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} encounters {demon}! The battle begins..."
        embed.add_field(name="Demon Strength", value=strength)
        message = await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating battle time

        user_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10
        if user_data["companion"]:
            user_strength += self.companions[user_data["companion"]]["strength"]
        victory = user_strength > strength

        if victory:
            xp_gained = strength // 2
            await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)
            await self.config.user(ctx.author).demons_slayed.set(user_data["demons_slayed"] + 1)
            embed.color = discord.Color.green()
            embed.description += f"\n\nVictory! You've defeated {demon} and gained {xp_gained} XP!"
            # Add materials
            materials_gained = {"steel": random.randint(1, 5), "wisteria": random.randint(1, 3), "scarlet_ore": random.randint(0, 2)}
            for material, amount in materials_gained.items():
                user_data["materials"][material] += amount
            await self.config.user(ctx.author).materials.set(user_data["materials"])
            embed.add_field(name="Materials Gained", value="\n".join([f"{mat.capitalize()}: {amt}" for mat, amt in materials_gained.items()]))
        else:
            xp_gained = strength // 10
            await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)
            embed.color = discord.Color.red()
            embed.description += f"\n\nDefeat... {demon} was too powerful. You gained {xp_gained} XP from the experience."

        await message.edit(embed=embed)
        await self.check_rank_up(ctx)

    @ds.command(name="train_form")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def train_specific_form(self, ctx, *, form_name: str):
        """Train a specific breathing technique form"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        matching_forms = [f for f in user_data["known_forms"] if form_name.lower() in f.lower()]
        if not matching_forms:
            await ctx.send(f"{ctx.author.mention}, you don't know a form by that name.")
            return
        if len(matching_forms) > 1:
            await ctx.send(f"{ctx.author.mention}, please be more specific. Matching forms: {', '.join(matching_forms)}")
            return

        form = matching_forms[0]
        current_level = user_data["form_levels"].get(form, 1)
        xp_gained = random.randint(10, 30)
        new_level = current_level + 1 if random.random() < 0.3 else current_level  # 30% chance to level up

        async with self.config.user(ctx.author).all() as user_data:
            user_data["experience"] += xp_gained
            user_data["form_levels"][form] = new_level

        embed = discord.Embed(title="Form Training Results", color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} trains {form} and gains {xp_gained} experience!"
        if new_level > current_level:
            embed.description += f"\n\nYour mastery of {form} has increased to level {new_level}!"

        await ctx.send(embed=embed)
        await self.check_rank_up(ctx)

    @ds.command(name="leaderboard")
    async def show_leaderboard(self, ctx, category: str = "experience", scope: str = "global"):
        """Show leaderboard for various achievements"""
        if category not in ["experience", "demons_slayed", "rank"]:
            await ctx.send("Invalid category. Choose from: experience, demons_slayed, rank")
            return
        if scope not in ["global", "server"]:
            await ctx.send("Invalid scope. Choose from: global, server")
            return

        if scope == "global":
            all_users = await self.config.all_users()
        else:
            all_users = {member.id: await self.config.user(member).all() for member in ctx.guild.members}

        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get(category, 0), reverse=True)[:10]

        embed = discord.Embed(title=f"{scope.capitalize()} {category.replace('_', ' ').title()} Leaderboard", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                if category == "rank":
                    value = data.get(category, "Unranked")
                else:
                    value = data.get(category, 0)
                embed.add_field(name=f"{i}. {user.name}", value=f"{value} {category.replace('_', ' ')}", inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="boss_raid")
    @commands.admin()
    async def start_boss_raid(self, ctx, duration: int = 30):
        """Start a boss raid event (Admin only)"""
        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data["active_boss_raid"]:
            await ctx.send("A boss raid is already active!")
            return

        boss = random.choice(["Muzan Kibutsuji", "Kokushibo", "Doma", "Akaza", "Hantengu", "Gyokko"])
        strength = random.randint(5000, 10000)
        guild_data["active_boss_raid"] = {
            "boss": boss,
            "strength": strength,
            "participants": [],
            "total_strength": 0,
            "end_time": (datetime.now() + timedelta(minutes=duration)).isoformat()
        }
        await self.config.guild(ctx.guild).set(guild_data)

        embed = discord.Embed(title="Boss Raid Event", color=discord.Color.dark_red())
        embed.description = f"A powerful demon, {boss}, has appeared! Join forces to defeat it!\n"
        embed.description += f"Use `{ctx.prefix}ds join_raid` to participate.\n"
        embed.description += f"Event ends in {duration} minutes."
        embed.add_field(name="Boss Strength", value=strength)

        await ctx.send(embed=embed)
        await asyncio.sleep(duration * 60)
        await self.end_boss_raid(ctx)

    @ds.command(name="join_raid")
    async def join_boss_raid(self, ctx):
        """Join the active boss raid"""
        guild_data = await self.config.guild(ctx.guild).all()
        if not guild_data["active_boss_raid"]:
            await ctx.send("There's no active boss raid right now.")
            return

        user_data = await self.config.user(ctx.author).all()
        if ctx.author.id not in guild_data["active_boss_raid"]["participants"]:
            guild_data["active_boss_raid"]["participants"].append(ctx.author.id)
            user_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10
            if user_data["companion"]:
                user_strength += self.companions[user_data["companion"]]["strength"]
            guild_data["active_boss_raid"]["total_strength"] += user_strength
            await self.config.guild(ctx.guild).set(guild_data)
            await ctx.send(f"{ctx.author.mention} has joined the raid against {guild_data['active_boss_raid']['boss']}!")
        else:
            await ctx.send("You're already participating in this raid!")

    async def end_boss_raid(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        if not guild_data["active_boss_raid"]:
            return

        victory = guild_data["active_boss_raid"]["total_strength"] > guild_data["active_boss_raid"]["strength"]
        embed = discord.Embed(title="Boss Raid Results", color=discord.Color.green() if victory else discord.Color.red())
        
        if victory:
            embed.description = f"The raid against {guild_data['active_boss_raid']['boss']} was successful!"
            xp_reward = guild_data["active_boss_raid"]["strength"] // len(guild_data["active_boss_raid"]["participants"])
            for participant_id in guild_data["active_boss_raid"]["participants"]:
                user = self.bot.get_user(participant_id)
                if user:
                    user_data = await self.config.user(user).all()
                    user_data["experience"] += xp_reward
                    user_data["demons_slayed"] += 1
                    await self.config.user(user).set(user_data)
            embed.add_field(name="Reward", value=f"Each participant gains {xp_reward} XP and 1 powerful demon slayed!")
        else:
            embed.description = f"The raid against {guild_data['active_boss_raid']['boss']} has failed. The demon escaped."

        await ctx.send(embed=embed)
        guild_data["active_boss_raid"] = None
        await self.config.guild(ctx.guild).set(guild_data)

    @ds.command(name="seasonal_event")
    @commands.admin()
    async def start_seasonal_event(self, ctx, duration: int = 7):
        """Start a seasonal event (Admin only)"""
        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data["seasonal_event"]:
            await ctx.send("A seasonal event is already active!")
            return

        events = [
            {"name": "Blood Moon Festival", "bonus": "double_xp"},
            {"name": "Wisteria Bloom", "bonus": "weaker_demons"},
            {"name": "Demon Slayer Corps Anniversary", "bonus": "increased_rewards"}
        ]
        event = random.choice(events)
        guild_data["seasonal_event"] = {
            "name": event["name"],
            "bonus": event["bonus"],
            "end_time": (datetime.now() + timedelta(days=duration)).isoformat()
        }
        await self.config.guild(ctx.guild).set(guild_data)

        embed = discord.Embed(title=f"Seasonal Event: {event['name']}", color=discord.Color.gold())
        embed.description = f"A special event has started! Enjoy {event['bonus']} for the next {duration} days!"
        await ctx.send(embed=embed)

        # Schedule event end
        await asyncio.sleep(duration * 86400)  # Convert days to seconds
        await self.end_seasonal_event(ctx)

    async def end_seasonal_event(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        if not guild_data["seasonal_event"]:
            return

        embed = discord.Embed(title="Seasonal Event Ended", color=discord.Color.blue())
        embed.description = f"The {guild_data['seasonal_event']['name']} has ended. We hope you enjoyed the {guild_data['seasonal_event']['bonus']}!"
        await ctx.send(embed=embed)
        guild_data["seasonal_event"] = None
        await self.config.guild(ctx.guild).set(guild_data)

    @ds.command(name="fuse_techniques")
    async def fuse_breathing_techniques(self, ctx):
        """Attempt to fuse two breathing techniques"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["rank"] not in ["Kinoe", "Hashira"]:
            await ctx.send("You must be at least Kinoe rank to attempt technique fusion.")
            return

        if user_data["secondary_breathing"]:
            await ctx.send("You have already fused techniques.")
            return

        primary_technique = user_data["breathing_technique"]
        available_techniques = [t for t in self.breathing_techniques.keys() if t != primary_technique]
        secondary_technique = random.choice(available_techniques)

        success_chance = 0.01 if user_data["rank"] == "Kinoe" else 0.05  # 1% for Kinoe, 5% for Hashira

        if random.random() < success_chance:
            user_data["secondary_breathing"] = secondary_technique
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations! You've successfully fused {primary_technique} and {secondary_technique} breathing techniques!")
        else:
            await ctx.send("The fusion attempt failed. Keep training and try again later.")

    @ds.group(name="guild")
    async def guild_commands(self, ctx):
        """Guild-related commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @guild_commands.command(name="create")
    async def create_guild(self, ctx, *, name: str):
        """Create a new Demon Slayer guild"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["guild"]:
            await ctx.send("You are already in a guild.")
            return

        guild_data = await self.config.guild(ctx.guild).all()
        if name in guild_data["guilds"]:
            await ctx.send("A guild with that name already exists.")
            return

        guild_data["guilds"][name] = {"leader": ctx.author.id, "members": [ctx.author.id], "exp": 0}
        await self.config.guild(ctx.guild).set(guild_data)

        user_data["guild"] = name
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"Guild '{name}' has been created with you as the leader!")

    @guild_commands.command(name="join")
    async def join_guild(self, ctx, *, name: str):
        """Join an existing Demon Slayer guild"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["guild"]:
            await ctx.send("You are already in a guild.")
            return

        guild_data = await self.config.guild(ctx.guild).all()
        if name not in guild_data["guilds"]:
            await ctx.send("That guild does not exist.")
            return

        guild_data["guilds"][name]["members"].append(ctx.author.id)
        await self.config.guild(ctx.guild).set(guild_data)

        user_data["guild"] = name
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You have joined the guild '{name}'!")

    @ds.command(name="hashira_trial")
    async def start_hashira_trial(self, ctx):
        """Start the Hashira trial (must be Kinoe rank)"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["rank"] != "Kinoe":
            await ctx.send("You must be Kinoe rank to attempt the Hashira trial.")
            return

        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data["active_hashira_trial"]:
            await ctx.send("A Hashira trial is already in progress.")
            return

        guild_data["active_hashira_trial"] = {
            "participant": ctx.author.id,
            "stage": 1,
            "success": True
        }
        await self.config.guild(ctx.guild).set(guild_data)

        await ctx.send("The Hashira trial has begun! You will face three challenging stages.")
        await self.run_hashira_trial_stage(ctx)

    async def run_hashira_trial_stage(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        stage = guild_data["active_hashira_trial"]["stage"]
        user = self.bot.get_user(guild_data["active_hashira_trial"]["participant"])

        challenges = [
            "Defeat 100 demons in 5 minutes",
            "Survive against a Lower Moon for 10 minutes",
            "Land a hit on a current Hashira"
        ]

        embed = discord.Embed(title=f"Hashira Trial - Stage {stage}", color=discord.Color.gold())
        embed.description = f"Challenge: {challenges[stage-1]}"
        await ctx.send(embed=embed)

        # Simulate the challenge
        await asyncio.sleep(10)  # In a real scenario, this would be more complex

        success_chance = 0.7 / stage  # Gets harder with each stage
        if random.random() < success_chance:
            await ctx.send(f"{user.mention} has passed stage {stage}!")
            if stage < 3:
                guild_data["active_hashira_trial"]["stage"] += 1
                await self.config.guild(ctx.guild).set(guild_data)
                await self.run_hashira_trial_stage(ctx)
            else:
                await self.conclude_hashira_trial(ctx, True)
        else:
            await ctx.send(f"{user.mention} has failed stage {stage}.")
            await self.conclude_hashira_trial(ctx, False)

    async def conclude_hashira_trial(self, ctx, success):
        guild_data = await self.config.guild(ctx.guild).all()
        user = self.bot.get_user(guild_data["active_hashira_trial"]["participant"])
        if success:
            user_data = await self.config.user(user).all()
            user_data["rank"] = "Hashira"
            await self.config.user(user).set(user_data)
            await ctx.send(f"Congratulations, {user.mention}! You have passed the Hashira trial and are now a Hashira!")
        else:
            await ctx.send(f"{user.mention}, you have failed the Hashira trial. Train harder and try again when you're ready.")
        
        guild_data["active_hashira_trial"] = None
        await self.config.guild(ctx.guild).set(guild_data)

    @ds.command(name="duel")
    async def pvp_duel(self, ctx, opponent: discord.Member):
        """Challenge another player to a duel"""
        if ctx.author == opponent:
            await ctx.send("You can't duel yourself!")
            return

        if ctx.author.id in self.active_pvp_duels or opponent.id in self.active_pvp_duels:
            await ctx.send("One of the players is already in a duel.")
            return

        await ctx.send(f"{opponent.mention}, you have been challenged to a duel by {ctx.author.mention}. Do you accept? (yes/no)")

        def check(m):
            return m.author == opponent and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("The duel request has timed out.")
            return

        if msg.content.lower() == 'no':
            await ctx.send("The duel has been declined.")
            return

        self.active_pvp_duels[ctx.author.id] = opponent.id
        self.active_pvp_duels[opponent.id] = ctx.author.id

        await self.run_pvp_duel(ctx, ctx.author, opponent)

    async def run_pvp_duel(self, ctx, player1, player2):
        p1_data = await self.config.user(player1).all()
        p2_data = await self.config.user(player2).all()

        p1_strength = p1_data["experience"] + sum(p1_data["form_levels"].values()) * 10
        p2_strength = p2_data["experience"] + sum(p2_data["form_levels"].values()) * 10

        if p1_data["companion"]:
            p1_strength += self.companions[p1_data["companion"]]["strength"]
        if p2_data["companion"]:
            p2_strength += self.companions[p2_data["companion"]]["strength"]

        total_strength = p1_strength + p2_strength
        p1_win_chance = p1_strength / total_strength

        winner = player1 if random.random() < p1_win_chance else player2
        loser = player2 if winner == player1 else player1

        xp_gain = random.randint(50, 100)
        winner_data = await self.config.user(winner).all()
        winner_data["experience"] += xp_gain
        await self.config.user(winner).set(winner_data)

        embed = discord.Embed(title="Duel Results", color=discord.Color.gold())
        embed.description = f"{winner.mention} has won the duel against {loser.mention}!"
        embed.add_field(name="Reward", value=f"{winner.mention} gains {xp_gain} XP!")

        await ctx.send(embed=embed)

        del self.active_pvp_duels[player1.id]
        del self.active_pvp_duels[player2.id]

    @ds.command(name="daily_mission")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily_mission(self, ctx):
        """Get or check your daily mission"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return
    
        if user_data["active_daily_mission"]:
            completed = await self.check_mission_completion(ctx, "daily")
            if completed:
                return
            else:
                embed = discord.Embed(title="Active Daily Mission", color=discord.Color.blue())
                embed.description = f"Your current daily mission: {user_data['active_daily_mission']}"
                embed.set_footer(text="Complete this mission for bonus XP and rewards!")
                await ctx.send(embed=embed)
                return
    
        mission = random.choice(self.missions["daily"])
        user_data["active_daily_mission"] = mission
        await self.config.user(ctx.author).set(user_data)
    
        embed = discord.Embed(title="New Daily Mission", color=discord.Color.blue())
        embed.description = f"Your daily mission: {mission}"
        embed.set_footer(text="Complete this mission for bonus XP and rewards!")
        await ctx.send(embed=embed)
    
    @ds.command(name="weekly_mission")
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def weekly_mission(self, ctx):
        """Get or check your weekly mission"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return
    
        if user_data["active_weekly_mission"]:
            completed = await self.check_mission_completion(ctx, "weekly")
            if completed:
                return
            else:
                embed = discord.Embed(title="Active Weekly Mission", color=discord.Color.purple())
                embed.description = f"Your current weekly mission: {user_data['active_weekly_mission']}"
                embed.set_footer(text="Complete this mission for significant XP and special rewards!")
                await ctx.send(embed=embed)
                return
    
        mission = random.choice(self.missions["weekly"])
        user_data["active_weekly_mission"] = mission
        await self.config.user(ctx.author).set(user_data)
    
        embed = discord.Embed(title="New Weekly Mission", color=discord.Color.purple())
        embed.description = f"Your weekly mission: {mission}"
        embed.set_footer(text="Complete this mission for significant XP and special rewards!")
        await ctx.send(embed=embed)

    @ds.command(name="companion")
    async def get_companion(self, ctx):
        """Attempt to get a companion"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["companion"]:
            await ctx.send(f"{ctx.author.mention}, you already have a companion: {user_data['companion']}")
            return

        companion = random.choice(list(self.companions.keys()))
        user_data["companion"] = companion
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="New Companion", color=discord.Color.green())
        embed.description = f"Congratulations! You've obtained a {companion}!"
        embed.add_field(name="Bonus", value=f"Your {companion} provides a {self.companions[companion]['bonus']} bonus.")
        embed.add_field(name="Strength", value=f"Combat Strength: {self.companions[companion]['strength']}")
        await ctx.send(embed=embed)

    @ds.command(name="craft")
    async def craft_item(self, ctx, item: str):
        """Craft or upgrade items"""
        user_data = await self.config.user(ctx.author).all()
        if item.lower() == "nichirin blade":
            if user_data["nichirin_blade_level"] >= 10:
                await ctx.send("Your Nichirin Blade is already at maximum level!")
                return
            
            required_materials = {
                "steel": 5 * user_data["nichirin_blade_level"],
                "scarlet_ore": 2 * user_data["nichirin_blade_level"],
                "wisteria": 3 * user_data["nichirin_blade_level"]
            }
            
            for material, amount in required_materials.items():
                if user_data["materials"][material] < amount:
                    await ctx.send(f"You don't have enough {material}. You need {amount}.")
                    return
            
            for material, amount in required_materials.items():
                user_data["materials"][material] -= amount
            
            user_data["nichirin_blade_level"] += 1
            await self.config.user(ctx.author).set(user_data)
            
            await ctx.send(f"You've successfully upgraded your Nichirin Blade to level {user_data['nichirin_blade_level']}!")
        else:
            await ctx.send("Invalid item. You can currently only craft/upgrade your Nichirin Blade.")

    @ds.command(name="materials")
    async def show_materials(self, ctx):
        """Show your crafting materials"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(title=f"{ctx.author.name}'s Crafting Materials", color=discord.Color.blue())
        for material, amount in user_data["materials"].items():
            embed.add_field(name=material.capitalize(), value=amount)
        await ctx.send(embed=embed)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000

        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            user_data["rank"] = new_rank
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")

    async def learn_new_form(self, ctx, embed):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data["breathing_technique"]
        known_forms = user_data["known_forms"]
        all_forms = self.breathing_techniques[technique]

        unknown_forms = [form for form in all_forms if form not in known_forms]
        if unknown_forms:
            new_form = random.choice(unknown_forms)
            known_forms.append(new_form)
            user_data["known_forms"] = known_forms
            user_data["form_levels"][new_form] = 1
            await self.config.user(ctx.author).set(user_data)
            embed.add_field(name="New Form Learned!", value=f"You've learned {new_form}!")
        else:
            embed.add_field(name="Mastery", value="You've mastered all forms of your breathing technique!")

    async def check_active_missions(self, ctx):
        await self.check_mission_completion(ctx, "daily")
        await self.check_mission_completion(ctx, "weekly")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
