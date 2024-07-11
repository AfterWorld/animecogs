import discord
from redbot.core import commands, Config
import random
import asyncio
from datetime import datetime, timedelta

class DemonSlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        default_user = {
            "breathing_technique": None,
            "evolved_breathing": False,
            "nichirin_color": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "form_levels": {},
            "last_daily": None,
            "slayer_points": 0,
            "companion": None,
            "companion_level": 1,
            "nichirin_blade_level": 1,
            "nichirin_blade_ability": None,
            "materials": {"steel": 0, "wisteria": 0, "scarlet_ore": 0},
            "is_demon": False,
            "demon_stage": 0,
            "blood_demon_art": None,
            "demon_slayer_mark": False,
            "breathing_mastery": 0,
            "special_abilities": [],
            "active_daily_mission": None,
            "active_weekly_mission": None,
            "completed_missions": {"daily": [], "weekly": []},
            "last_hunt": None,
            "guild": None,
            "secondary_breathing": None,
        }
        
        default_guild = {
            "blood_moon_active": False,
            "blood_moon_end": None,
            "active_boss_raid": None,
            "seasonal_event": None,
            "active_hashira_trial": None,
            "active_tournament": None,
            "event_channel": None,
            "active_global_event": None,
        }
        
        self.config.register_user(**default_user)
        self.config.init_custom("guild", 2)
        self.config.register_custom("guild", **default_guild)
        
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
        
        self.demon_stages = [
            "Newly Turned", "Lesser Demon", "Evolved Demon", "Upper Moon Candidate", "Lower Moon", "Upper Moon"
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
        
        self.corps_divisions = {
            "Kakushi": {"bonus": "stealth", "requirement": "Kanoto"},
            "Cultivator": {"bonus": "herbs", "requirement": "Kanoe"},
            "Shinobi": {"bonus": "information", "requirement": "Tsuchinoto"},
            "Tracker": {"bonus": "hunting", "requirement": "Tsuchinoe"},
            "Slayer": {"bonus": "combat", "requirement": "Hinoto"}
        }
        
        self.blood_demon_arts = [
            "Blood Manipulation", "Shadow Control", "Flesh Modification",
            "Poison Generation", "Illusion Creation", "Regeneration"
        ]
        
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
                

    def cog_unload(self):
        if self.event_task:
            self.event_task.cancel()

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""

    @ds.command(name="start")
    async def start_journey(self, ctx):
        """Begin your journey as a Demon Slayer"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data:
            # Initialize user data if it doesn't exist
            await self.config.user(ctx.author).set(self.config.user.defaults)
            user_data = await self.config.user(ctx.author).all()

        if user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you've already begun your journey!")
            return

        technique = random.choice(list(self.breathing_techniques.keys()))
        color = random.choice(["Red", "Blue", "Green", "Yellow", "Purple", "Black"])
        first_form = self.breathing_techniques[technique][0]
        
        user_data["breathing_technique"] = technique
        user_data["nichirin_color"] = color
        user_data["known_forms"] = [first_form]
        user_data["form_levels"] = {first_form: 1}
        
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="Journey Begins", color=discord.Color.gold())
        embed.description = f"Welcome to the Demon Slayer Corps, {ctx.author.mention}!"
        embed.add_field(name="Breathing Technique", value=technique, inline=False)
        embed.add_field(name="Nichirin Blade Color", value=color, inline=False)
        embed.add_field(name="First Form", value=first_form, inline=False)
        await ctx.send(embed=embed)


    @ds.command(name="profile")
    async def show_profile(self, ctx, user: discord.Member = None):
        """Display your Demon Slayer profile"""
        if user is None:
            user = ctx.author
        user_data = await self.config.user(user).all()

        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{user.mention} hasn't started their journey yet!")
            return

        embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.red())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        if user_data["is_demon"]:
            embed.add_field(name="Type", value="Demon", inline=False)
            embed.add_field(name="Demon Rank", value=self.demon_stages[user_data["demon_stage"]], inline=True)
            embed.add_field(name="Blood Demon Art", value=user_data["blood_demon_art"], inline=True)
        else:
            embed.add_field(name="Type", value="Demon Slayer", inline=False)
            embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"], inline=True)
            embed.add_field(name="Rank", value=user_data["rank"], inline=True)
            embed.add_field(name="Corps Division", value=user_data["corps_division"] or "None", inline=True)
            embed.add_field(name="Nichirin Blade", value=f"{user_data['nichirin_color']} (Level {user_data['nichirin_blade_level']})", inline=False)
            embed.add_field(name="Blade Appearance", value=user_data["nichirin_blade_appearance"], inline=True)
            embed.add_field(name="Blade Ability", value=user_data["nichirin_blade_ability"] or "None", inline=True)

        embed.add_field(name="Experience", value=user_data["experience"], inline=True)
        embed.add_field(name="Demons Slayed", value=user_data["demons_slayed"], inline=True)
        
        forms = "\n".join([f"{form} (Level {user_data['form_levels'].get(form, 1)})" for form in user_data["known_forms"]])
        embed.add_field(name="Known Forms", value=forms or "None", inline=False)
        
        if user_data["companion"]:
            embed.add_field(name="Companion", value=f"{user_data['companion']} (Level {user_data['companion_level']})", inline=False)
        
        if user_data["special_abilities"]:
            embed.add_field(name="Special Abilities", value=", ".join(user_data["special_abilities"]), inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="train")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def train(self, ctx):
        """Train to improve your skills"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        xp_gained = random.randint(10, 50)
        user_data["experience"] += xp_gained

        embed = discord.Embed(title="Training Results", color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} trains intensively and gains {xp_gained} experience!"

        if not user_data["is_demon"]:
            # Chance to learn a new form
            if random.random() < 0.2:  # 20% chance to learn a new form
                await self.learn_new_form(ctx, user_data, embed)
            
            # Increase breathing mastery
            mastery_gain = random.randint(1, 5)
            user_data["breathing_mastery"] += mastery_gain
            embed.add_field(name="Breathing Mastery", value=f"+{mastery_gain} (Total: {user_data['breathing_mastery']})", inline=False)
            
            # Check for new special abilities
            await self.check_special_abilities(ctx, user_data, embed)
        else:
            # Demon-specific training results
            blood_art_mastery = random.randint(1, 5)
            embed.add_field(name="Blood Demon Art Mastery", value=f"+{blood_art_mastery}", inline=False)

        await self.config.user(ctx.author).set(user_data)
        await ctx.send(embed=embed)
        await self.check_rank_up(ctx)

    async def learn_new_form(self, ctx, user_data, embed):
        technique = user_data["breathing_technique"]
        known_forms = user_data["known_forms"]
        all_forms = self.breathing_techniques[technique]

        unknown_forms = [form for form in all_forms if form not in known_forms]
        if unknown_forms:
            new_form = random.choice(unknown_forms)
            known_forms.append(new_form)
            user_data["known_forms"] = known_forms
            user_data["form_levels"][new_form] = 1
            embed.add_field(name="New Form Learned!", value=f"You've learned {new_form}!")
        else:
            embed.add_field(name="Mastery", value="You've mastered all forms of your breathing technique!")

    async def check_special_abilities(self, ctx, user_data, embed):
        if user_data["breathing_mastery"] >= 100 and "Enhanced Speed" not in user_data["special_abilities"]:
            user_data["special_abilities"].append("Enhanced Speed")
            embed.add_field(name="New Ability Unlocked!", value="Enhanced Speed", inline=False)
        elif user_data["breathing_mastery"] >= 250 and "Heightened Senses" not in user_data["special_abilities"]:
            user_data["special_abilities"].append("Heightened Senses")
            embed.add_field(name="New Ability Unlocked!", value="Heightened Senses", inline=False)
        elif user_data["breathing_mastery"] >= 500 and "Total Concentration: Constant" not in user_data["special_abilities"]:
            user_data["special_abilities"].append("Total Concentration: Constant")
            embed.add_field(name="New Ability Unlocked!", value="Total Concentration: Constant", inline=False)

    @ds.command(name="hunt")
    @commands.cooldown(1, 1800, commands.BucketType.user)  # 2-hour cooldown
    async def hunt(self, ctx):
        """Hunt for demons"""
        user_data = await self.config.user(ctx.author).all()
        print(f"User data: {user_data}")  # Debug logging statement

        if user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, as a demon, you cannot hunt other demons!")
            return

        guild_data = await self.config.custom("guild", ctx.guild.id).all()
        print(f"Guild data: {guild_data}")  # Debug logging statement
    
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

        embed = discord.Embed(title="Demon Hunt", color=discord.Color.dark_red())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} encounters {demon}! The battle begins..."
        embed.add_field(name="Demon Strength", value=strength)
        message = await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating battle time

        user_strength = self.calculate_strength(user_data)

        # Apply Blood Moon effects
        if guild_data.get("blood_moon_active", False):  # Check if key exists
            strength *= 1.5  # Demons are 50% stronger
            xp_multiplier = 2  # Double XP
        else:
            xp_multiplier = 1

        victory = user_strength > strength

        if victory:
            xp_gained = int((strength // 2) * xp_multiplier)
            user_data["experience"] += xp_gained
            user_data["demons_slayed"] += 1
            embed.color = discord.Color.green()
            embed.description += f"\n\nVictory! You've defeated {demon} and gained {xp_gained} XP!"
            # Add materials
            materials_gained = {"steel": random.randint(1, 5), "wisteria": random.randint(1, 3), "scarlet_ore": random.randint(0, 2)}
            for material, amount in materials_gained.items():
                user_data["materials"][material] += amount
            embed.add_field(name="Materials Gained", value="\n".join([f"{mat.capitalize()}: {amt}" for mat, amt in materials_gained.items()]))

            # Chance to become a demon
            if random.random() < 0.01:  # 1% chance
                embed.add_field(name="Unexpected Turn!", value="You've been severely wounded and offered demon blood. Use `[p]ds transform` to accept or deny.", inline=False)
                user_data["demon_transformation_pending"] = True
        else:
            xp_gained = strength // 10
            user_data["experience"] += xp_gained
            embed.color = discord.Color.red()
            embed.description += f"\n\nDefeat... {demon} was too powerful. You gained {xp_gained} XP from the experience."

        await self.config.user(ctx.author).set(user_data)
        await message.edit(embed=embed)
        await self.check_rank_up(ctx)

    def calculate_strength(self, user_data):
        base_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10

        if user_data["is_demon"]:
            base_strength *= (1 + (user_data["demon_stage"] * 0.2))  # Each demon stage increases strength by 20%
        else:
            if user_data["evolved_breathing"]:
                base_strength *= 1.5
            if user_data["demon_slayer_mark"]:
                base_strength *= 2

        if "Enhanced Speed" in user_data["special_abilities"]:
            base_strength *= 1.1
        if "Total Concentration: Constant" in user_data["special_abilities"]:
            base_strength *= 1.2

        if user_data["companion"]:
            base_strength += self.companions[user_data["companion"]]["strength"] * user_data["companion_level"]

        return base_strength

    @ds.command(name="transform")
    async def demon_transform(self, ctx):
        """Transform into a demon or advance demon stage"""
        user_data = await self.config.user(ctx.author).all()

        if not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, are you sure you want to abandon your humanity and become a demon? This action is irreversible. React with 👹 to confirm.")
            msg = await ctx.send("Awaiting confirmation...")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '👹' and reaction.message.id == msg.id

            try:
                await msg.add_reaction('👹')
                await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Transformation cancelled.")
                return

            user_data["is_demon"] = True
            user_data["demon_stage"] = 0
            user_data["blood_demon_art"] = random.choice(self.blood_demon_arts)
            user_data["breathing_technique"] = None  # Lose breathing technique when becoming a demon
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"You have transformed into a demon! Your Blood Demon Art is {user_data['blood_demon_art']}.")
        else:
            if user_data["demon_stage"] < len(self.demon_stages) - 1:
                xp_needed = (user_data["demon_stage"] + 1) * 5000
                if user_data["experience"] >= xp_needed:
                    user_data["demon_stage"] += 1
                    user_data["experience"] -= xp_needed
                    await self.config.user(ctx.author).set(user_data)
                    await ctx.send(f"You have advanced to the next demon stage: {self.demon_stages[user_data['demon_stage']]}!")
                else:
                    await ctx.send(f"You need {xp_needed - user_data['experience']} more XP to advance to the next demon stage.")
            else:
                await ctx.send("You have reached the highest demon stage!")

    @ds.command(name="duel")
    async def initiate_duel(self, ctx, opponent: discord.Member):
        """Challenge another player to a duel"""
        if opponent == ctx.author:
            await ctx.send("You can't duel yourself!")
            return

        challenger_data = await self.config.user(ctx.author).all()
        opponent_data = await self.config.user(opponent).all()

        if challenger_data["is_demon"] != opponent_data["is_demon"]:
            await ctx.send("Demons and Demon Slayers cannot duel each other!")
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

        await self.run_duel(ctx, ctx.author, opponent)

    async def run_duel(self, ctx, player1, player2):
        p1_data = await self.config.user(player1).all()
        p2_data = await self.config.user(player2).all()

        p1_strength = self.calculate_strength(p1_data)
        p2_strength = self.calculate_strength(p2_data)

        embed = discord.Embed(title="Duel", color=discord.Color.red())
        embed.add_field(name=player1.name, value=f"Strength: {p1_strength:.2f}", inline=True)
        embed.add_field(name=player2.name, value=f"Strength: {p2_strength:.2f}", inline=True)
        await ctx.send(embed=embed)

        await asyncio.sleep(3)  # Build suspense

        if p1_strength > p2_strength:
            winner, loser = player1, player2
            win_chance = 0.7
        elif p2_strength > p1_strength:
            winner, loser = player2, player1
            win_chance = 0.7
        else:
            winner, loser = random.choice([(player1, player2), (player2, player1)])
            win_chance = 0.5

        if random.random() < win_chance:
            xp_gain = abs(int(p1_strength - p2_strength)) + 50
            winner_data = await self.config.user(winner).all()
            winner_data["experience"] += xp_gain
            await self.config.user(winner).set(winner_data)
            await ctx.send(f"{winner.mention} has won the duel and gained {xp_gain} XP!")
        else:
            await ctx.send(f"In a surprising turn of events, {loser.mention} managed to overcome the odds and win the duel!")

    @ds.command(name="evolve_breathing")
    async def evolve_breathing(self, ctx):
        """Attempt to evolve your breathing style"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons can't use breathing techniques!")
            return

        if user_data["breathing_mastery"] < 1000:
            await ctx.send("Your breathing mastery is not high enough to evolve your technique. Keep training!")
            return

        if user_data["evolved_breathing"]:
            await ctx.send("You've already evolved your breathing technique to its maximum level!")
            return

        success_chance = min(user_data["breathing_mastery"] / 2000, 0.5)  # Max 50% chance

        if random.random() < success_chance:
            user_data["evolved_breathing"] = True
            new_form = f"Evolved {user_data['breathing_technique']}: Ultimate Form"
            user_data["known_forms"].append(new_form)
            user_data["form_levels"][new_form] = 1
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations! You've evolved your {user_data['breathing_technique']} Breathing! You've learned the new form: {new_form}")
        else:
            await ctx.send("Your attempt to evolve your breathing technique has failed. Keep training and try again!")

    @ds.command(name="blood_moon")
    @commands.is_owner()
    async def trigger_blood_moon(self, ctx, duration: int = 60):
        """Trigger a Blood Moon event (Owner only)"""
        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data["blood_moon_active"]:
            await ctx.send("A Blood Moon event is already active!")
            return

        guild_data["blood_moon_active"] = True
        guild_data["blood_moon_end"] = (datetime.now() + timedelta(minutes=duration)).isoformat()
        await self.config.guild(ctx.guild).set(guild_data)

        await ctx.send(f"🔴 A Blood Moon has risen! Demons are stronger, but rewards for slaying them have increased! This event will last for {duration} minutes.")

        # Schedule end of Blood Moon
        await asyncio.sleep(duration * 60)
        await self.end_blood_moon(ctx)

    async def end_blood_moon(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        guild_data["blood_moon_active"] = False
        guild_data["blood_moon_end"] = None
        await self.config.guild(ctx.guild).set(guild_data)
        await ctx.send("The Blood Moon has passed. Demon strength and rewards have returned to normal.")

    @ds.command(name="status")
    async def check_status(self, ctx):
        """Check your current status and progress"""
        user_data = await self.config.user(ctx.author).all()
        guild_data = await self.config.guild(ctx.guild).all()

        embed = discord.Embed(title=f"{ctx.author.name}'s Status", color=discord.Color.blue())
        
        if user_data["is_demon"]:
            embed.add_field(name="Type", value="Demon", inline=True)
            embed.add_field(name="Stage", value=self.demon_stages[user_data["demon_stage"]], inline=True)
            embed.add_field(name="Blood Demon Art", value=user_data["blood_demon_art"], inline=True)
        else:
            embed.add_field(name="Type", value="Demon Slayer", inline=True)
            embed.add_field(name="Rank", value=user_data["rank"], inline=True)
            embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"], inline=True)
            if user_data["evolved_breathing"]:
                embed.add_field(name="Evolved Breathing", value="Yes", inline=True)
            if user_data["demon_slayer_mark"]:
                embed.add_field(name="Demon Slayer Mark", value="Awakened", inline=True)

        embed.add_field(name="Experience", value=user_data["experience"], inline=True)
        embed.add_field(name="Demons Slayed", value=user_data["demons_slayed"], inline=True)

        if user_data["companion"]:
            embed.add_field(name="Companion", value=f"{user_data['companion']} (Level {user_data['companion_level']})", inline=True)

        if not user_data["is_demon"]:
            embed.add_field(name="Nichirin Blade", value=f"{user_data['nichirin_color']} (Level {user_data['nichirin_blade_level']})", inline=True)
            if user_data["nichirin_blade_ability"]:
                embed.add_field(name="Blade Ability", value=user_data["nichirin_blade_ability"], inline=True)

        materials = ", ".join([f"{k}: {v}" for k, v in user_data["materials"].items()])
        embed.add_field(name="Materials", value=materials, inline=False)

        if guild_data["blood_moon_active"]:
            blood_moon_end = datetime.fromisoformat(guild_data["blood_moon_end"])
            time_left = blood_moon_end - datetime.now()
            embed.add_field(name="Blood Moon", value=f"Active for {time_left.seconds // 60} more minutes", inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="leaderboard")
    async def show_leaderboard(self, ctx, category: str = "experience"):
        """Show the leaderboard for a specific category"""
        valid_categories = ["experience", "demons_slayed", "demon_stage"]
        if category not in valid_categories:
            await ctx.send(f"Invalid category. Please choose from: {', '.join(valid_categories)}")
            return

        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get(category, 0), reverse=True)[:10]

        embed = discord.Embed(title=f"Demon Slayer Leaderboard - {category.capitalize()}", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, start=1):
            user = self.bot.get_user(user_id)
            if user:
                value = data.get(category, 0)
                if category == "demon_stage":
                    value = self.demon_stages[value] if data["is_demon"] else "N/A"
                embed.add_field(name=f"{i}. {user.name}", value=f"{value}", inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily_reward(self, ctx):
        """Claim your daily reward"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        last_daily = user_data["last_daily"]
        now = datetime.now()
        if last_daily and datetime.fromisoformat(last_daily) + timedelta(days=1) > now:
            time_left = datetime.fromisoformat(last_daily) + timedelta(days=1) - now
            await ctx.send(f"{ctx.author.mention}, you can claim your next daily reward in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")
            return

        reward = random.randint(50, 100)
        user_data["experience"] += reward
        user_data["last_daily"] = now.isoformat()
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"{ctx.author.mention}, you've claimed your daily reward of {reward} XP!")
        await self.check_rank_up(ctx)

    @ds.command(name="craft")
    async def craft_item(self, ctx, item: str):
        """Craft or upgrade items using materials"""
        user_data = await self.config.user(ctx.author).all()

        if user_data["is_demon"]:
            await ctx.send("Demons cannot craft items.")
            return

        if item.lower() == "nichirin blade":
            if user_data["nichirin_blade_level"] >= 10:
                await ctx.send("Your Nichirin Blade is already at maximum level!")
                return
            
            cost = {
                "steel": 5 * user_data["nichirin_blade_level"],
                "scarlet_ore": 2 * user_data["nichirin_blade_level"],
                "wisteria": 3 * user_data["nichirin_blade_level"]
            }
            
            if all(user_data["materials"][material] >= amount for material, amount in cost.items()):
                for material, amount in cost.items():
                    user_data["materials"][material] -= amount
                
                user_data["nichirin_blade_level"] += 1
                await self.config.user(ctx.author).set(user_data)
                
                await ctx.send(f"You've successfully upgraded your Nichirin Blade to level {user_data['nichirin_blade_level']}!")
            else:
                await ctx.send("You don't have enough materials to upgrade your Nichirin Blade.")
        else:
            await ctx.send("Invalid item. You can currently only craft/upgrade your Nichirin Blade.")

    @ds.command(name="train_companion")
    @commands.cooldown(1, 14400, commands.BucketType.user)  # 4-hour cooldown
    async def train_companion(self, ctx):
        """Train your companion to increase its level and unlock new abilities"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["companion"]:
            await ctx.send("You don't have a companion yet! Use `[p]ds get_companion` to obtain one.")
            return

        xp_gained = random.randint(10, 50)
        user_data["experience"] += xp_gained

        companion_xp = random.randint(5, 25)
        level_up = False

        if user_data["companion_level"] < 10:  # Max level is 10
            user_data["companion_level"] += companion_xp // 100
            level_up = user_data["companion_level"] > user_data["companion_level"] - (companion_xp // 100)

        embed = discord.Embed(title="Companion Training", color=discord.Color.green())
        embed.description = f"You trained with your {user_data['companion']} and gained {xp_gained} XP!"
        embed.add_field(name="Companion XP Gained", value=companion_xp)

        if level_up:
            embed.add_field(name="Level Up!", value=f"Your companion is now level {user_data['companion_level']}!")
            if user_data["companion_level"] in [3, 5, 7, 10]:
                new_ability = self.get_companion_ability(user_data["companion"], user_data["companion_level"])
                user_data["special_abilities"].append(new_ability)
                embed.add_field(name="New Ability Unlocked!", value=new_ability, inline=False)

        await self.config.user(ctx.author).set(user_data)
        await ctx.send(embed=embed)

    def get_companion_ability(self, companion, level):
        abilities = {
            "Kasugai Crow": ["Enhanced Scouting", "Telepathic Link", "Danger Sense", "Crow Clone"],
            "Nichirin Ore Fox": ["Ore Detection", "Stealth Field", "Nichirin Reinforcement", "Spectral Fox"],
            "Demon Slayer Cat": ["Night Vision", "Agility Boost", "Feline Instinct", "Nine Lives"]
        }
        return abilities[companion][level // 3 - 1]

    @ds.command(name="hashira_training")
    @commands.cooldown(1, 604800, commands.BucketType.user)  # Weekly cooldown
    async def hashira_training(self, ctx):
        """Participate in a special Hashira training arc"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons can't participate in Hashira training!")
            return

        if user_data["rank"] not in ["Kinoe", "Hashira"]:
            await ctx.send("You must be at least Kinoe rank to participate in Hashira training!")
            return

        hashira = random.choice(["Water", "Flame", "Wind", "Stone", "Love", "Mist", "Sound", "Serpent", "Insect"])
        training_difficulty = random.randint(1, 5)

        embed = discord.Embed(title="Hashira Training Arc", color=discord.Color.purple())
        embed.description = f"You begin an intense training arc under the {hashira} Hashira!"
        embed.add_field(name="Difficulty", value="⭐" * training_difficulty)
        message = await ctx.send(embed=embed)

        for i in range(1, 6):
            await asyncio.sleep(5)  # Simulating training time
            success = random.random() > (training_difficulty * 0.1)
            if success:
                embed.add_field(name=f"Stage {i}", value="Success!", inline=False)
            else:
                embed.add_field(name=f"Stage {i}", value="Failure", inline=False)
                break
            await message.edit(embed=embed)

        xp_gained = 1000 * i * training_difficulty
        user_data["experience"] += xp_gained

        if i == 5:  # Completed all stages
            new_technique = f"{hashira} Breathing: {random.choice(self.breathing_techniques[user_data['breathing_technique']])}"
            user_data["known_forms"].append(new_technique)
            user_data["form_levels"][new_technique] = 1
            embed.add_field(name="Training Complete!", value=f"You've learned a new technique: {new_technique}", inline=False)
        else:
            embed.add_field(name="Training Incomplete", value="You've gained valuable experience, but couldn't complete the full training.", inline=False)

        embed.add_field(name="XP Gained", value=xp_gained)
        await self.config.user(ctx.author).set(user_data)
        await message.edit(embed=embed)

    @ds.command(name="join_division")
    async def join_corps_division(self, ctx, division: str):
        """Join a Demon Slayer Corps division"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons can't join Demon Slayer Corps divisions!")
            return

        if division not in self.corps_divisions:
            await ctx.send(f"Invalid division. Choose from: {', '.join(self.corps_divisions.keys())}")
            return

        required_rank = self.corps_divisions[division]["requirement"]
        if self.ranks.index(user_data["rank"]) < self.ranks.index(required_rank):
            await ctx.send(f"You must be at least {required_rank} rank to join the {division} division!")
            return

        user_data["corps_division"] = division
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="Division Joined", color=discord.Color.blue())
        embed.description = f"You have joined the {division} division of the Demon Slayer Corps!"
        embed.add_field(name="Bonus", value=f"You now have a {self.corps_divisions[division]['bonus']} bonus!")
        await ctx.send(embed=embed)

    @ds.command(name="info")
    async def show_info(self, ctx, *, subject: str):
        """Get information about various aspects of the game"""
        subject = subject.lower()
        if subject in self.breathing_techniques:
            embed = discord.Embed(title=f"{subject.capitalize()} Breathing", color=discord.Color.blue())
            embed.description = "A breathing technique used by Demon Slayers."
            for i, form in enumerate(self.breathing_techniques[subject], start=1):
                embed.add_field(name=f"Form {i}", value=form, inline=False)
        elif subject == "demon stages":
            embed = discord.Embed(title="Demon Stages", color=discord.Color.dark_red())
            for i, stage in enumerate(self.demon_stages):
                embed.add_field(name=f"Stage {i}", value=stage, inline=False)
        elif subject == "ranks":
            embed = discord.Embed(title="Demon Slayer Ranks", color=discord.Color.gold())
            for rank in self.ranks:
                embed.add_field(name=rank, value="‎", inline=True)
        elif subject == "corps divisions":
            embed = discord.Embed(title="Demon Slayer Corps Divisions", color=discord.Color.green())
            for division, info in self.corps_divisions.items():
                embed.add_field(name=division, value=f"Bonus: {info['bonus']}\nRequirement: {info['requirement']}", inline=False)
        else:
            await ctx.send("Subject not found. Try breathing techniques, demon stages, ranks, or corps divisions.")
            return
        await ctx.send(embed=embed)

    @ds.command(name="help")
    async def demon_slayer_help(self, ctx):
        """Show help for Demon Slayer commands"""
        embed = discord.Embed(title="Demon Slayer Help", color=discord.Color.blue())
        embed.description = "Here are the available Demon Slayer commands:"

        commands = [
            ("start", "Begin your journey as a Demon Slayer"),
            ("profile", "View your Demon Slayer profile"),
            ("train", "Train to improve your skills"),
            ("hunt", "Hunt for demons"),
            ("duel", "Challenge another player to a duel"),
            ("evolve_breathing", "Attempt to evolve your breathing technique"),
            ("transform", "Transform into a demon or advance demon stage"),
            ("daily", "Claim your daily reward"),
            ("craft", "Craft or upgrade items"),
            ("train_companion", "Train your companion"),
            ("hashira_training", "Participate in Hashira training"),
            ("join_division", "Join a Demon Slayer Corps division"),
            ("status", "Check your current status"),
            ("leaderboard", "View the leaderboard"),
            ("info", "Get information about game aspects")
        ]

        for name, description in commands:
            embed.add_field(name=f"[p]ds {name}", value=description, inline=False)

        embed.set_footer(text="Replace [p] with your server's command prefix.")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            if hours == 0 and minutes == 0:
                await ctx.send(f"This command is on cooldown. Please try again in {seconds:.1f} seconds.")
            elif hours == 0:
                await ctx.send(f"This command is on cooldown. Please try again in {minutes:.0f} minutes and {seconds:.1f} seconds.")
            else:
                await ctx.send(f"This command is on cooldown. Please try again in {hours:.0f} hours, {minutes:.0f} minutes and {seconds:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument provided: {error}")
        else:
            await ctx.send(f"An error occurred: {error}")

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000

        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            user_data["rank"] = new_rank
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")

            # Check for Demon Slayer Mark awakening
            if new_rank in ["Kinoe", "Hashira"] and random.random() < 0.1:  # 10% chance
                user_data["demon_slayer_mark"] = True
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"🌟 The Demon Slayer Mark has awakened within you, {ctx.author.mention}! Your strength has greatly increased!")

    @ds.command(name="fuse_breathing")
    @commands.cooldown(1, 604800, commands.BucketType.user)  # Weekly cooldown
    async def fuse_breathing_techniques(self, ctx):
        """Attempt to fuse two breathing techniques (very difficult)"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons can't use breathing techniques!")
            return

        if user_data["rank"] not in ["Kinoe", "Hashira"]:
            await ctx.send("You must be at least Kinoe rank to attempt breathing fusion!")
            return

        if user_data["secondary_breathing"]:
            await ctx.send("You've already fused breathing techniques!")
            return

        available_techniques = [t for t in self.breathing_techniques.keys() if t != user_data["breathing_technique"]]
        secondary_technique = random.choice(available_techniques)

        success_chance = 0.01 if user_data["rank"] == "Kinoe" else 0.05  # 1% for Kinoe, 5% for Hashira
        if user_data["breathing_mastery"] >= 1000:
            success_chance *= 2  # Double chance if breathing mastery is high

        if random.random() < success_chance:
            user_data["secondary_breathing"] = secondary_technique
            new_form = f"{user_data['breathing_technique']}-{secondary_technique} Fusion: {random.choice(self.breathing_techniques[user_data['breathing_technique']])} {random.choice(self.breathing_techniques[secondary_technique])}"
            user_data["known_forms"].append(new_form)
            user_data["form_levels"][new_form] = 1
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Incredible! You've successfully fused {user_data['breathing_technique']} and {secondary_technique} breathing techniques! You've learned a new form: {new_form}")
        else:
            await ctx.send("The fusion attempt failed. The techniques are too difficult to combine. Keep training and try again next week!")

    @ds.command(name="boss_raid")
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    async def start_boss_raid(self, ctx, duration: int = 30):
        """Start a boss raid event"""
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
        embed.description += f"Use `[p]ds join_raid` to participate.\n"
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
        if user_data["is_demon"]:
            await ctx.send("Demons cannot participate in Demon Slayer raids!")
            return

        if ctx.author.id in guild_data["active_boss_raid"]["participants"]:
            await ctx.send("You've already joined this raid!")
            return

        user_strength = self.calculate_strength(user_data)
        guild_data["active_boss_raid"]["participants"].append(ctx.author.id)
        guild_data["active_boss_raid"]["total_strength"] += user_strength
        await self.config.guild(ctx.guild).set(guild_data)
        await ctx.send(f"{ctx.author.mention} has joined the raid against {guild_data['active_boss_raid']['boss']}!")

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
    @commands.is_owner()
    async def start_seasonal_event(self, ctx, duration: int = 7):
        """Start a seasonal event (Owner only)"""
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

    @ds.command(name="set_event_channel")
    @commands.admin()
    async def set_event_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for global demon events"""
        await self.config.guild(ctx.guild).event_channel.set(channel.id)
        await ctx.send(f"Global demon events will now occur in {channel.mention}")
        if self.event_task:
            self.event_task.cancel()
        self.event_task = self.bot.loop.create_task(self.event_loop(ctx.guild))

    async def event_loop(self, guild):
        while True:
            await asyncio.sleep(random.randint(3600, 7200))  # Random time between 1-2 hours
            channel_id = await self.config.guild(guild).event_channel()
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    await self.spawn_demon(channel)

    async def spawn_demon(self, channel):
        demon_types = {
            "Lower Demon": 0.5,
            "Lower Moon": 0.3,
            "Upper Moon": 0.2
        }
        demon_type = random.choices(list(demon_types.keys()), weights=list(demon_types.values()))[0]
        
        if demon_type == "Lower Demon":
            demon = random.choice(["Swamp Demon", "Temple Demon", "Drum Demon"])
            strength = random.randint(300, 500)
        elif demon_type == "Lower Moon":
            demon = f"Lower Moon {random.randint(1, 6)}"
            strength = random.randint(600, 1000)
        else:
            demon = f"Upper Moon {random.randint(1, 6)}"
            strength = random.randint(1500, 3000)

        embed = discord.Embed(title="Demon Attack!", color=discord.Color.dark_red())
        embed.description = f"A {demon} has appeared! Type `.ds join` to join the battle!"
        embed.add_field(name="Demon Strength", value=strength)
        embed.add_field(name="Participants", value="None yet")
        message = await channel.send(embed=embed)

        guild_data = await self.config.guild(channel.guild).all()
        guild_data["active_global_event"] = {
            'channel_id': channel.id,
            'demon': demon,
            'strength': strength,
            'participants': [],
            'total_strength': 0,
            'embed': embed,
            'message': message,
            'start_time': datetime.now().isoformat()
        }
        await self.config.guild(channel.guild).set(guild_data)

        await asyncio.sleep(300)  # 5 minutes for the battle
        await self.conclude_global_event(channel.guild)

    async def conclude_global_event(self, guild):
        guild_data = await self.config.guild(guild).all()
        if not guild_data["active_global_event"]:
            return

        event = guild_data["active_global_event"]
        victory = event['total_strength'] > event['strength']
        embed = event['embed']

        if victory:
            embed.color = discord.Color.green()
            embed.description = f"The {event['demon']} has been defeated!"
            xp_reward = event['strength'] // len(event['participants']) if event['participants'] else 0
            for participant_id in event['participants']:
                user = self.bot.get_user(participant_id)
                if user:
                    user_data = await self.config.user(user).all()
                    user_data["experience"] += xp_reward
                    user_data["demons_slayed"] += 1
                    await self.config.user(user).set(user_data)
            embed.add_field(name="Reward", value=f"Each participant gains {xp_reward} XP and 1 demon slayed!")
        else:
            embed.color = discord.Color.red()
            embed.description = f"The {event['demon']} was too powerful and escaped..."

        channel = self.bot.get_channel(event['channel_id'])
        if channel:
            await channel.send(embed=embed)
        
        guild_data["active_global_event"] = None
        await self.config.guild(guild).set(guild_data)

def setup(bot):
    cog = DemonSlayer(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.initialize_guild_data())
