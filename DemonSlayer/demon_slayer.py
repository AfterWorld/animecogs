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
            "nichirin_blade_level": 1,
            "nichirin_blade_appearance": "Standard",
            "nichirin_blade_ability": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "form_levels": {},
            "last_daily": None,
            "slayer_points": 0,
            "guild": None,
            "companion": None,
            "companion_level": 1,
            "materials": {"steel": 0, "wisteria": 0, "scarlet_ore": 0},
            "completed_missions": {"daily": [], "weekly": [], "rank": []},
            "last_hunt": None,
            "is_demon": False,
            "demon_rank": None,
            "blood_demon_art": None,
            "corps_division": None,
            "breathing_mastery": 0,
            "special_abilities": [],
            "active_daily_mission": None,
            "active_weekly_mission": None,
            "demon_transformation_pending": False,
        }
        
        default_guild = {
            "event_channel": None,
            "active_boss_raid": None,
            "seasonal_event": None,
            "guilds": {},
            "active_hashira_trial": None,
            "active_tournament": None,
            "active_hashira_training": None,
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
        
        self.demon_ranks = [
            "Demon", "Lower Moon Six", "Lower Moon Five", "Lower Moon Four", "Lower Moon Three", "Lower Moon Two", "Lower Moon One",
            "Upper Moon Six", "Upper Moon Five", "Upper Moon Four", "Upper Moon Three", "Upper Moon Two", "Upper Moon One"
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
            ],
            "rank": {
                "Kinoe": ["Defeat an Upper Moon demon", "Master a breathing technique"],
                "Hashira": ["Train 100 lower-ranked slayers", "Slay 1000 demons"]
            }
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
            embed.add_field(name="Demon Rank", value=user_data["demon_rank"], inline=True)
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
        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        if user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, as a demon, you cannot hunt other demons!")
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

        embed = discord.Embed(title="Demon Hunt", color=discord.Color.dark_red())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} encounters {demon}! The battle begins..."
        embed.add_field(name="Demon Strength", value=strength)
        message = await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating battle time

        user_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10
        if user_data["companion"]:
            user_strength += self.companions[user_data["companion"]]["strength"] * user_data["companion_level"]
        
        # Apply special abilities
        if "Enhanced Speed" in user_data["special_abilities"]:
            user_strength *= 1.1
        if "Total Concentration: Constant" in user_data["special_abilities"]:
            user_strength *= 1.2

        victory = user_strength > strength

        if victory:
            xp_gained = strength // 2
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

    @ds.command(name="transform")
    async def transform(self, ctx, choice: str):
        """Accept or deny demon transformation"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data.get("demon_transformation_pending", False):
            await ctx.send("You don't have a pending demon transformation.")
            return

        if choice.lower() == "accept":
            user_data["is_demon"] = True
            user_data["demon_rank"] = "Demon"
            user_data["blood_demon_art"] = random.choice(self.blood_demon_arts)
            user_data["breathing_technique"] = None
            user_data["rank"] = None
            user_data["corps_division"] = None
            await ctx.send(f"{ctx.author.mention} has transformed into a demon! Your Blood Demon Art is {user_data['blood_demon_art']}.")
        elif choice.lower() == "deny":
            await ctx.send(f"{ctx.author.mention} has resisted the demon blood and remained human.")
        else:
            await ctx.send("Invalid choice. Please use 'accept' or 'deny'.")
            return

        user_data["demon_transformation_pending"] = False
        await self.config.user(ctx.author).set(user_data)

    @ds.command(name="demon_rank")
    @commands.cooldown(1, 86400, commands.BucketType.user)  # Daily cooldown
    async def demon_rank_challenge(self, ctx):
        """Challenge for a higher demon rank"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["is_demon"]:
            await ctx.send("Only demons can challenge for demon ranks.")
            return

        current_rank_index = self.demon_ranks.index(user_data["demon_rank"])
        if current_rank_index == len(self.demon_ranks) - 1:
            await ctx.send("You've already reached the highest demon rank!")
            return

        target_rank = self.demon_ranks[current_rank_index + 1]
        challenge_strength = (current_rank_index + 2) * 500  # Increasing difficulty

        embed = discord.Embed(title="Demon Rank Challenge", color=discord.Color.purple())
        embed.description = f"{ctx.author.mention} is challenging for the rank of {target_rank}!"
        embed.add_field(name="Challenge Strength", value=challenge_strength)
        message = await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating challenge time

        user_strength = user_data["experience"] * 1.5  # Demons are stronger
        if user_data["blood_demon_art"] == "Blood Manipulation":
            user_strength *= 1.2  # Blood Manipulation gives an advantage

        victory = user_strength > challenge_strength

        if victory:
            user_data["demon_rank"] = target_rank
            embed.color = discord.Color.green()
            embed.description += f"\n\nSuccess! You've earned the rank of {target_rank}!"
        else:
            embed.color = discord.Color.red()
            embed.description += "\n\nFailure. You were not strong enough to claim the higher rank."

        await self.config.user(ctx.author).set(user_data)
        await message.edit(embed=embed)

    @ds.command(name="customize_blade")
    async def customize_nichirin_blade(self, ctx, appearance: str = None, ability: str = None):
        """Customize your Nichirin Blade's appearance and ability"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons can't customize Nichirin Blades!")
            return

        if not appearance and not ability:
            await ctx.send("Please specify an appearance or ability to customize.")
            return

        cost = 100 * user_data["nichirin_blade_level"]
        if user_data["experience"] < cost:
            await ctx.send(f"You need {cost} XP to customize your blade. You only have {user_data['experience']} XP.")
            return

        embed = discord.Embed(title="Nichirin Blade Customization", color=discord.Color.gold())

        if appearance:
            user_data["nichirin_blade_appearance"] = appearance
            embed.add_field(name="New Appearance", value=appearance, inline=False)

        if ability:
            available_abilities = ["Flame Generation", "Water Manipulation", "Lightning Conduction", "Wind Enhancement", "Earth Fortification"]
            if ability not in available_abilities:
                await ctx.send(f"Invalid ability. Choose from: {', '.join(available_abilities)}")
                return
            user_data["nichirin_blade_ability"] = ability
            embed.add_field(name="New Ability", value=ability, inline=False)

        user_data["experience"] -= cost
        await self.config.user(ctx.author).set(user_data)

        embed.description = f"Your Nichirin Blade has been customized! Cost: {cost} XP"
        await ctx.send(embed=embed)

    @ds.command(name="tournament")
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    async def start_tournament(self, ctx):
        """Start a PvE tournament"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        # Initialize guild_data if it doesn't exist
        if "active_tournament" not in guild_data:
            guild_data["active_tournament"] = None

        if guild_data["active_tournament"]:
            await ctx.send("A tournament is already in progress!")
            return

        guild_data["active_tournament"] = {
            "participants": [],
            "round": 0,
            "matches": []
        }
        await self.config.guild(ctx.guild).set(guild_data)

        await ctx.send("A new PvE tournament has started! Use `[p]ds join_tournament` to participate. Registration closes in 5 minutes.")
        await asyncio.sleep(300)  # 5 minutes registration period
        await self.start_tournament_rounds(ctx)

    @ds.command(name="join_tournament")
    async def join_tournament(self, ctx):
        """Join the active tournament"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        # Initialize guild_data if it doesn't exist
        if "active_tournament" not in guild_data:
            guild_data["active_tournament"] = None
            await self.config.guild(ctx.guild).set(guild_data)

        if not guild_data["active_tournament"]:
            await ctx.send("There's no active tournament to join!")
            return

        user_data = await self.config.user(ctx.author).all()
        if user_data["is_demon"]:
            await ctx.send("Demons cannot participate in Demon Slayer tournaments!")
            return

        if ctx.author.id in guild_data["active_tournament"]["participants"]:
            await ctx.send("You've already joined this tournament!")
            return

        guild_data["active_tournament"]["participants"].append(ctx.author.id)
        await self.config.guild(ctx.guild).set(guild_data)
        await ctx.send(f"{ctx.author.mention} has joined the tournament!")

    async def start_tournament_rounds(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        
        # Initialize guild_data if it doesn't exist
        if "active_tournament" not in guild_data:
            guild_data["active_tournament"] = None
            await self.config.guild(ctx.guild).set(guild_data)
            await ctx.send("There's no active tournament.")
            return

        tournament = guild_data["active_tournament"]
        
        if not tournament:
            await ctx.send("There's no active tournament.")
            return

        if len(tournament["participants"]) < 2:
            await ctx.send("Not enough participants. The tournament has been cancelled.")
            guild_data["active_tournament"] = None
            await self.config.guild(ctx.guild).set(guild_data)
            return

        random.shuffle(tournament["participants"])
        tournament["round"] += 1
        tournament["matches"] = []

        for i in range(0, len(tournament["participants"]), 2):
            if i + 1 < len(tournament["participants"]):
                tournament["matches"].append((tournament["participants"][i], tournament["participants"][i+1]))
            else:
                # Odd number of participants, last one gets a bye
                tournament["matches"].append((tournament["participants"][i], None))

        await self.config.guild(ctx.guild).set(guild_data)
        await self.run_tournament_round(ctx)

    async def run_tournament_round(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        tournament = guild_data["active_tournament"]

        embed = discord.Embed(title=f"Tournament Round {tournament['round']}", color=discord.Color.blue())
        for i, match in enumerate(tournament["matches"], 1):
            player1 = self.bot.get_user(match[0])
            player2 = self.bot.get_user(match[1]) if match[1] else "Bye"
            embed.add_field(name=f"Match {i}", value=f"{player1.mention} vs {player2.mention if isinstance(player2, discord.User) else player2}", inline=False)

        await ctx.send(embed=embed)
        await asyncio.sleep(10)  # Time for dramatic effect

        winners = []
        for match in tournament["matches"]:
            if match[1] is None:
                winners.append(match[0])  # Player with a bye automatically advances
            else:
                winner = await self.simulate_match(match[0], match[1])
                winners.append(winner)
                user = self.bot.get_user(winner)
                await ctx.send(f"{user.mention} has won their match!")

        tournament["participants"] = winners
        if len(winners) > 1:
            await self.start_tournament_rounds(ctx)
        else:
            await self.conclude_tournament(ctx)

    async def simulate_match(self, player1_id, player2_id):
        player1_data = await self.config.user_from_id(player1_id).all()
        player2_data = await self.config.user_from_id(player2_id).all()

        player1_strength = player1_data["experience"] + sum(player1_data["form_levels"].values()) * 10
        player2_strength = player2_data["experience"] + sum(player2_data["form_levels"].values()) * 10

        if random.random() < player1_strength / (player1_strength + player2_strength):
            return player1_id
        else:
            return player2_id

    async def conclude_tournament(self, ctx):
        guild_data = await self.config.guild(ctx.guild).all()
        tournament = guild_data["active_tournament"]
        winner_id = tournament["participants"][0]
        winner = self.bot.get_user(winner_id)
        
        winner_data = await self.config.user(winner).all()
        xp_reward = 1000 * tournament["round"]
        winner_data["experience"] += xp_reward
        await self.config.user(winner).set(winner_data)

        embed = discord.Embed(title="Tournament Concluded", color=discord.Color.gold())
        embed.description = f"Congratulations to {winner.mention} for winning the tournament!"
        embed.add_field(name="Reward", value=f"{xp_reward} XP")
        await ctx.send(embed=embed)

        guild_data["active_tournament"] = None
        await self.config.guild(ctx.guild).set(guild_data)

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

    @ds.command(name="daily_mission")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily_mission(self, ctx):
        """Get a daily mission"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        if user_data["active_daily_mission"]:
            await ctx.send("You already have an active daily mission. Complete it first!")
            return

        mission = random.choice(self.missions["daily"])
        user_data["active_daily_mission"] = mission
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="Daily Mission", color=discord.Color.blue())
        embed.description = f"Your daily mission: {mission}"
        embed.set_footer(text="Complete this mission for bonus XP and rewards!")
        await ctx.send(embed=embed)

    @ds.command(name="weekly_mission")
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def weekly_mission(self, ctx):
        """Get a weekly mission"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"] and not user_data["is_demon"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        if user_data["active_weekly_mission"]:
            await ctx.send("You already have an active weekly mission. Complete it first!")
            return

        mission = random.choice(self.missions["weekly"])
        user_data["active_weekly_mission"] = mission
        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="Weekly Mission", color=discord.Color.purple())
        embed.description = f"Your weekly mission: {mission}"
        embed.set_footer(text="Complete this mission for significant XP and special rewards!")
        await ctx.send(embed=embed)

    @ds.command(name="check_mission")
    async def check_mission(self, ctx, mission_type: str):
        """Check the status of your daily or weekly mission"""
        user_data = await self.config.user(ctx.author).all()
        if mission_type not in ["daily", "weekly"]:
            await ctx.send("Invalid mission type. Choose 'daily' or 'weekly'.")
            return

        mission = user_data[f"active_{mission_type}_mission"]
        if not mission:
            await ctx.send(f"You don't have an active {mission_type} mission. Use `[p]ds {mission_type}_mission` to get one.")
            return

        embed = discord.Embed(title=f"Active {mission_type.capitalize()} Mission", color=discord.Color.gold())
        embed.description = mission
        embed.set_footer(text="Use `[p]ds complete_mission {daily/weekly}` when you've finished the mission.")
        await ctx.send(embed=embed)

    @ds.command(name="complete_mission")
    async def complete_mission(self, ctx, mission_type: str):
        """Mark your daily or weekly mission as complete"""
        user_data = await self.config.user(ctx.author).all()
        if mission_type not in ["daily", "weekly"]:
            await ctx.send("Invalid mission type. Choose 'daily' or 'weekly'.")
            return

        mission = user_data[f"active_{mission_type}_mission"]
        if not mission:
            await ctx.send(f"You don't have an active {mission_type} mission to complete.")
            return

        # Here you would normally check if the mission conditions are actually met
        # For simplicity, we'll assume the user has completed the mission

        xp_reward = 100 if mission_type == "daily" else 500
        user_data["experience"] += xp_reward
        user_data[f"active_{mission_type}_mission"] = None
        user_data["completed_missions"][mission_type].append(mission)

        await self.config.user(ctx.author).set(user_data)

        embed = discord.Embed(title="Mission Completed", color=discord.Color.green())
        embed.description = f"Congratulations! You've completed your {mission_type} mission: {mission}"
        embed.add_field(name="Reward", value=f"{xp_reward} XP")
        await ctx.send(embed=embed)

        await self.check_rank_up(ctx)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000

        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            user_data["rank"] = new_rank
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")

    @ds.command(name="leaderboard")
    async def show_leaderboard(self, ctx, category: str = "experience"):
        """Show the leaderboard for a specific category"""
        valid_categories = ["experience", "demons_slayed", "rank"]
        if category not in valid_categories:
            await ctx.send(f"Invalid category. Please choose from: {', '.join(valid_categories)}")
            return

        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get(category, 0), reverse=True)[:10]

        embed = discord.Embed(title=f"Demon Slayer Leaderboard - {category.capitalize()}", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, start=1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"{data.get(category, 0)} {category}", inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="status")
    async def check_status(self, ctx):
        """Check your current status, cooldowns, and active events"""
        user_data = await self.config.user(ctx.author).all()
        guild_data = await self.config.guild(ctx.guild).all()

        embed = discord.Embed(title=f"{ctx.author.name}'s Status", color=discord.Color.blue())

        # Basic Info
        embed.add_field(name="Type", value="Demon" if user_data["is_demon"] else "Demon Slayer", inline=True)
        embed.add_field(name="Rank", value=user_data["demon_rank"] if user_data["is_demon"] else user_data["rank"], inline=True)
        embed.add_field(name="XP", value=user_data["experience"], inline=True)

        # Cooldowns
        for command in [self.train, self.hunt, self.daily_mission, self.weekly_mission]:
            cooldown = command._buckets.get_bucket(ctx.message).get_retry_after()
            if cooldown:
                embed.add_field(name=f"{command.name.capitalize()} Cooldown", value=f"{cooldown:.2f} seconds", inline=True)

        # Active Events
        if guild_data["active_boss_raid"]:
            embed.add_field(name="Active Boss Raid", value="Ongoing", inline=True)
        if guild_data["seasonal_event"]:
            embed.add_field(name="Seasonal Event", value=guild_data["seasonal_event"]["name"], inline=True)
        if guild_data["active_tournament"]:
            embed.add_field(name="Tournament", value=f"Round {guild_data['active_tournament']['round']}", inline=True)

        # Active Missions
        if user_data["active_daily_mission"]:
            embed.add_field(name="Active Daily Mission", value=user_data["active_daily_mission"], inline=False)
        if user_data["active_weekly_mission"]:
            embed.add_field(name="Active Weekly Mission", value=user_data["active_weekly_mission"], inline=False)

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
        elif subject in self.corps_divisions:
            embed = discord.Embed(title=f"{subject.capitalize()} Division", color=discord.Color.green())
            embed.add_field(name="Bonus", value=self.corps_divisions[subject]["bonus"])
            embed.add_field(name="Requirement", value=self.corps_divisions[subject]["requirement"])
        elif subject == "demons":
            embed = discord.Embed(title="Demon Types", color=discord.Color.red())
            for demon, info in self.demons.items():
                embed.add_field(name=demon, value=f"Difficulty: {info['difficulty']}, XP: {info['xp']}", inline=False)
        elif subject == "ranks":
            embed = discord.Embed(title="Demon Slayer Ranks", color=discord.Color.gold())
            for rank in self.ranks:
                embed.add_field(name=rank, value="‎", inline=True)  # Using an invisible character for value
        elif subject == "demon ranks":
            embed = discord.Embed(title="Demon Ranks", color=discord.Color.purple())
            for rank in self.demon_ranks:
                embed.add_field(name=rank, value="‎", inline=True)  # Using an invisible character for value
        else:
            await ctx.send("Subject not found. Try breathing techniques, divisions, demons, ranks, or demon ranks.")
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
            ("daily_mission", "Get a daily mission"),
            ("weekly_mission", "Get a weekly mission"),
            ("check_mission", "Check the status of your active mission"),
            ("complete_mission", "Mark your mission as complete"),
            ("customize_blade", "Customize your Nichirin Blade"),
            ("tournament", "Start or join a PvE tournament"),
            ("fuse_breathing", "Attempt to fuse breathing techniques"),
            ("train_companion", "Train your companion"),
            ("hashira_training", "Participate in Hashira training"),
            ("join_division", "Join a Demon Slayer Corps division"),
            ("transform", "Accept or deny demon transformation"),
            ("demon_rank", "Challenge for a higher demon rank (for demons)"),
            ("status", "Check your current status and cooldowns"),
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

    async def initialize_guild_data(self):
        for guild in self.bot.guilds:
            guild_data = await self.config.guild(guild).all()
            if "active_tournament" not in guild_data:
                guild_data["active_tournament"] = None
                await self.config.guild(guild).set(guild_data)

def setup(bot):
    cog = DemonSlayer(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.initialize_guild_data())
