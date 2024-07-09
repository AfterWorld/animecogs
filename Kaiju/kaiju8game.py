import random
import asyncio
from datetime import datetime, timedelta
from redbot.core import commands, checks, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import discord

class Kaiju8Game(commands.Cog):
    """An enhanced Kaiju #8 themed Defense Force game cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8991100, force_registration=True)
        default_user = {
            "rank": "Trainee",
            "exp": 0,
            "strength": 1,
            "agility": 1,
            "intelligence": 1,
            "is_kaiju": False,
            "kaiju_revealed": False,
            "missions_completed": 0,
            "weapon_specialization": None,
            "squad": None,
            "bestiary": [],
            "equipment": {},
            "class": None,
            "kaiju_compatibility": 0,
            "injuries": 0,
            "mentee": None,
            "mentor": None,
        }
        default_guild = {
            "base_level": 1,
            "ongoing_event": None,
            "research_projects": {},
        }
        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)
        self.event_task = bot.loop.create_task(self.run_regular_events())

    def cog_unload(self):
        self.event_task.cancel()

    async def run_regular_events(self):
        while True:
            await asyncio.sleep(3600)  # Check every hour
            for guild in self.bot.guilds:
                if random.random() < 0.1:  # 10% chance every hour
                    await self.start_event(guild)

    async def start_event(self, guild):
        events = [
            self.kaiju_attack_event,
            self.resource_gathering_event,
            self.training_drill_event,
        ]
        event = random.choice(events)
        await event(guild)

    async def kaiju_attack_event(self, guild):
        channel = guild.text_channels[0]  # Choose an appropriate channel
        await channel.send("🚨 **ALERT: KAIJU ATTACK!** 🚨 All Defense Force members report for duty! Use `[p]df defend` to join the battle!")
        await self.config.guild(guild).ongoing_event.set("kaiju_attack")
        await asyncio.sleep(1800)  # Event lasts 30 minutes
        await self.config.guild(guild).ongoing_event.set(None)
        await channel.send("The Kaiju attack has been repelled! Great job, Defense Force!")

    async def resource_gathering_event(self, guild):
        channel = guild.text_channels[0]  # Choose an appropriate channel
        await channel.send("🔍 **Resource Gathering Operation** 🔍 Rare materials detected! Use `[p]df gather` to collect resources!")
        await self.config.guild(guild).ongoing_event.set("resource_gathering")
        await asyncio.sleep(3600)  # Event lasts 1 hour
        await self.config.guild(guild).ongoing_event.set(None)
        await channel.send("The resource gathering operation has concluded. Well done, Defense Force!")

    async def training_drill_event(self, guild):
        channel = guild.text_channels[0]  # Choose an appropriate channel
        await channel.send("🏋️ **Special Training Drill** 🏋️ Improve your skills! Use `[p]df drill` to participate!")
        await self.config.guild(guild).ongoing_event.set("training_drill")
        await asyncio.sleep(3600)  # Event lasts 1 hour
        await self.config.guild(guild).ongoing_event.set(None)
        await channel.send("The special training drill has ended. Great effort, Defense Force!")

    @commands.group()
    async def df(self, ctx):
        """Defense Force game commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Type `[p]help df` for more info.")

    @df.command()
    async def join(self, ctx):
        """Join the Defense Force"""
        user_data = await self.config.user(ctx.author).all()
        if user_data['rank'] != "Trainee":
            await ctx.send("You're already a member of the Defense Force!")
            return

        is_kaiju = random.random() < 0.05
        kaiju_compatibility = random.randint(1, 100) if is_kaiju else 0
        await self.config.user(ctx.author).is_kaiju.set(is_kaiju)
        await self.config.user(ctx.author).kaiju_compatibility.set(kaiju_compatibility)
        
        classes = ["Frontline Fighter", "Tactical Support", "Research & Development", "Medical Support"]
        chosen_class = random.choice(classes)
        await self.config.user(ctx.author).character_class.set(chosen_class)
        
        await ctx.send(f"Welcome to the Defense Force, {ctx.author.mention}! You've been assigned to the {chosen_class} class. Your training begins now.")

    @df.command()
    async def status(self, ctx):
        """Check your Defense Force status"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(title=f"{ctx.author.name}'s Defense Force Status", color=discord.Color.blue())
        embed.add_field(name="Rank", value=user_data['rank'])
        embed.add_field(name="Class", value=user_data['class'])
        embed.add_field(name="EXP", value=user_data['exp'])
        embed.add_field(name="Missions Completed", value=user_data['missions_completed'])
        embed.add_field(name="Strength", value=user_data['strength'])
        embed.add_field(name="Agility", value=user_data['agility'])
        embed.add_field(name="Intelligence", value=user_data['intelligence'])
        embed.add_field(name="Weapon Specialization", value=user_data['weapon_specialization'] or "None")
        embed.add_field(name="Squad", value=user_data['squad'] or "None")
        if user_data['kaiju_revealed']:
            embed.add_field(name="Kaiju Compatibility", value=f"{user_data['kaiju_compatibility']}%")
        await ctx.send(embed=embed)

    @df.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour cooldown
    async def train(self, ctx):
        """Train to improve your abilities"""
        user_data = await self.config.user(ctx.author).all()
        if user_data['rank'] == "Trainee":
            await ctx.send("You need to join the Defense Force first! Use `[p]df join`")
            return

        attribute = random.choice(['strength', 'agility', 'intelligence'])
        gain = random.randint(1, 3)
        
        await self.config.user(ctx.author).set_raw(attribute, value=user_data[attribute] + gain)
        await self.config.user(ctx.author).exp.set(user_data['exp'] + 10)
        
        await ctx.send(f"You trained hard and improved your {attribute} by {gain} points! You also gained 10 EXP.")
        await self._check_rankup(ctx)

    @df.command()
    @commands.cooldown(1, 7200, commands.BucketType.user)  # 2 hour cooldown
    async def mission(self, ctx):
        """Embark on a Defense Force mission"""
        user_data = await self.config.user(ctx.author).all()
        if user_data['rank'] == "Trainee":
            await ctx.send("You need to join the Defense Force first! Use `[p]df join`")
            return

        scenarios = [
            "A Kaiju is attacking Tokyo! Defend the city and minimize casualties.",
            "Investigate strange readings in Osaka Bay. Could it be a new Kaiju?",
            "Assist in the evacuation of a coastal town under Kaiju threat.",
            "Provide security for a convoy transporting a captured Kaiju specimen.",
            "Defend a research facility developing new anti-Kaiju technology."
        ]
        mission = random.choice(scenarios)
        embed = discord.Embed(title="Defense Force Mission", description=mission, color=discord.Color.green())
        await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating mission time

        success_chance = (user_data['strength'] + user_data['agility'] + user_data['intelligence']) / 30
        success = random.random() < success_chance

        if success:
            exp_gain = random.randint(50, 100)
            await self.config.user(ctx.author).exp.set(user_data['exp'] + exp_gain)
            await self.config.user(ctx.author).missions_completed.set(user_data['missions_completed'] + 1)
            await ctx.send(f"Mission successful! You gained {exp_gain} EXP.")
            
            if user_data['is_kaiju'] and not user_data['kaiju_revealed'] and random.random() < 0.1:
                await self.config.user(ctx.author).kaiju_revealed.set(True)
                await ctx.send("During the intense mission, you discovered your hidden Kaiju powers!")
            
            # Chance to add Kaiju to bestiary
            if random.random() < 0.3:
                new_kaiju = f"Kaiju #{random.randint(1, 100)}"
                bestiary = user_data['bestiary']
                if new_kaiju not in bestiary:
                    bestiary.append(new_kaiju)
                    await self.config.user(ctx.author).bestiary.set(bestiary)
                    await ctx.send(f"You've added {new_kaiju} to your bestiary!")
            
            await self._check_rankup(ctx)
        else:
            await ctx.send("Mission failed. Better luck next time!")
            # Chance of injury
            if random.random() < 0.2:
                await self.config.user(ctx.author).injuries.set(user_data['injuries'] + 1)
                await ctx.send("You've been injured during the mission. Take some time to recover!")

    @df.command()
    async def specialize(self, ctx, weapon_type: str):
        """Specialize in a weapon type (melee, ranged, or support)"""
        if weapon_type not in ['melee', 'ranged', 'support']:
            await ctx.send("Invalid weapon type. Choose melee, ranged, or support.")
            return
        await self.config.user(ctx.author).weapon_specialization.set(weapon_type)
        await ctx.send(f"You have specialized in {weapon_type} weapons!")

    @df.command()
    async def squad(self, ctx, action: str, squad_name: str = None):
        """Manage your squad (join, leave, or create)"""
        if action == 'create' and squad_name:
            await self.config.user(ctx.author).squad.set(squad_name)
            await ctx.send(f"You have created the squad {squad_name}!")
        elif action == 'join' and squad_name:
            await self.config.user(ctx.author).squad.set(squad_name)
            await ctx.send(f"You have joined the squad {squad_name}!")
        elif action == 'leave':
            await self.config.user(ctx.author).squad.set(None)
            await ctx.send("You have left your squad.")
        else:
            await ctx.send("Invalid action. Use 'create', 'join', or 'leave'.")

    @df.command()
    async def bestiary(self, ctx):
        """View your Kaiju bestiary"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data['bestiary']:
            await ctx.send("Your bestiary is empty. Encounter more Kaiju to fill it!")
        else:
            bestiary_list = "\n".join(user_data['bestiary'])
            await ctx.send(f"Your Kaiju Bestiary:\n{bestiary_list}")

    @df.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def upgrade_base(self, ctx):
        """Upgrade the Defense Force base"""
        guild_data = await self.config.guild(ctx.guild).all()
        cost = guild_data['base_level'] * 1000
        if guild_data['base_level'] < 10:
            await self.config.guild(ctx.guild).base_level.set(guild_data['base_level'] + 1)
            await ctx.send(f"Base upgraded to level {guild_data['base_level'] + 1}! All Defense Force members get a stat boost.")
        else:
            await ctx.send("The base is already at maximum level!")

    @df.command()
    async def craft(self, ctx, item: str):
        """Craft or upgrade equipment"""
        user_data = await self.config.user(ctx.author).all()
        if item in user_data['equipment']:
            user_data['equipment'][item] += 1
            await ctx.send(f"You've upgraded your {item}!")
        else:
            user_data['equipment'][item] = 1
            await ctx.send(f"You've crafted a new {item}!")
        await self.config.user(ctx.author).equipment.set(user_data['equipment'])

    @df.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def transform(self, ctx):
        """Attempt to transform into Kaiju form (if you have the ability)"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data['kaiju_revealed']:
            await ctx.send("You don't have the ability to transform into a Kaiju.")
            return

        success = random.random() < (user_data['kaiju_compatibility'] / 100)
        if success:
            await ctx.send(f"{ctx.author.mention} successfully transforms into Kaiju #8! Your power is overwhelming, but remember to use it responsibly.")
        else:
            await ctx.send(f"{ctx.author.mention} attempts to transform, but fails. It seems your Kaiju powers are still unstable.")

    @df.command()
    async def mentor(self, ctx, mentee: discord.Member):
        """Take on a mentee to train"""
        mentor_data = await self.config.user(ctx.author).all()
        mentee_data = await self.config.user(mentee).all()
        
        if mentor_data['rank'] == 'Trainee' or mentee_data['rank'] != 'Trainee':
            await ctx.send("Only non-Trainees can mentor, and only Trainees can be mentored.")
            return

        await self.config.user(ctx.author).mentee.set(mentee.id)
        await self.config.user(mentee).mentor.set(ctx.author.id)
        await ctx.send(f"{ctx.author.mention} is now mentoring {mentee.mention}!")

    @df.command()
    async def research(self, ctx, project: str):
        """Contribute to a research project"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_data = await self.config.user(ctx.author).all()
        
        if 'research_projects' not in guild_data:
            guild_data['research_projects'] = {}

        if project not in guild_data['research_projects']:
            guild_data['research_projects'][project] = {'progress': 0, 'contributors': [], 'completed': False}
        
        if ctx.author.id not in guild_data['research_projects'][project]['contributors']:
            # Check if user has required resources
            required_resources = {"metal": 2, "energy_core": 1, "bio_sample": 1}
            if not all(user_data.get('resources', {}).get(r, 0) >= c for r, c in required_resources.items()):
                await ctx.send("You don't have enough resources to contribute to this project.")
                return

            # Deduct resources
            for resource, count in required_resources.items():
                user_data['resources'][resource] -= count

            contribution = random.randint(5, 15)
            guild_data['research_projects'][project]['progress'] += contribution
            guild_data['research_projects'][project]['contributors'].append(ctx.author.id)
            
            await self.config.guild(ctx.guild).set(guild_data)
            await self.config.user(ctx.author).set(user_data)
            
            await ctx.send(f"You contributed {contribution} points to the {project} research project!")
            
            if guild_data['research_projects'][project]['progress'] >= 100 and not guild_data['research_projects'][project]['completed']:
                guild_data['research_projects'][project]['completed'] = True
                await self.config.guild(ctx.guild).set(guild_data)
                await ctx.send(f"The {project} research project is complete! New technology is now available to all Defense Force members.")
                
                # Implement rewards for completed research
                await self._distribute_research_rewards(ctx, project)
        else:
            await ctx.send("You've already contributed to this research project today.")

    async def _distribute_research_rewards(self, ctx, project):
        guild_data = await self.config.guild(ctx.guild).all()
        
        # Define rewards for different projects
        rewards = {
            "advanced_weaponry": {"strength": 5},
            "enhanced_armor": {"defense": 5},
            "kaiju_biology": {"kaiju_compatibility": 10},
            "tactical_systems": {"intelligence": 5},
            "medical_advancements": {"healing_power": 5}
        }

        if project in rewards:
            for user_id in guild_data['research_projects'][project]['contributors']:
                user_data = await self.config.user_from_id(user_id).all()
                for stat, value in rewards[project].items():
                    if stat not in user_data:
                        user_data[stat] = 0
                    user_data[stat] += value
                await self.config.user_from_id(user_id).set(user_data)
                user = self.bot.get_user(user_id)
                if user:
                    await ctx.send(f"{user.mention} received a {list(rewards[project].keys())[0]} boost for contributing to the {project} research!")

    @df.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour cooldown
    async def heal(self, ctx):
        """Heal your injuries (Medical Support class only)"""
        user_data = await self.config.user(ctx.author).all()
        if user_data['class'] != "Medical Support":
            await ctx.send("Only Medical Support class members can use this command.")
            return
        
        if user_data['injuries'] > 0:
            healed = random.randint(1, user_data['injuries'])
            await self.config.user(ctx.author).injuries.set(user_data['injuries'] - healed)
            await ctx.send(f"You've healed {healed} injuries. Remaining injuries: {user_data['injuries'] - healed}")
        else:
            await ctx.send("You don't have any injuries to heal.")

    @df.command()
    async def leaderboard(self, ctx, category: str = "exp"):
        """View the Defense Force leaderboard"""
        valid_categories = ["exp", "missions", "kaiju_compatibility"]
        if category not in valid_categories:
            await ctx.send(f"Invalid category. Choose from: {', '.join(valid_categories)}")
            return

        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1][category], reverse=True)[:10]

        embed = discord.Embed(title=f"Defense Force Leaderboard - {category.capitalize()}", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"{data[category]}", inline=False)

        await ctx.send(embed=embed)

    @df.command()
    @commands.cooldown(1, 300, commands.BucketType.user)  # 5 minute cooldown
    async def defend(self, ctx):
        """Defend against a Kaiju attack (event)"""
        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data['ongoing_event'] != "kaiju_attack":
            await ctx.send("There's no ongoing Kaiju attack event.")
            return

        user_data = await self.config.user(ctx.author).all()
        success_chance = (user_data['strength'] + user_data['agility'] + user_data['intelligence']) / 40
        success = random.random() < success_chance

        if success:
            exp_gain = random.randint(100, 200)
            await self.config.user(ctx.author).exp.set(user_data['exp'] + exp_gain)
            await ctx.send(f"You successfully defended against the Kaiju! Gained {exp_gain} EXP.")
        else:
            await ctx.send("Despite your best efforts, the Kaiju overpowered you. Keep trying!")

    @df.command()
    @commands.cooldown(1, 300, commands.BucketType.user)  # 5 minute cooldown
    async def gather(self, ctx):
        """Gather resources (event)"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_data = await self.config.user(ctx.author).all()

        if guild_data['ongoing_event'] != "resource_gathering":
            await ctx.send("There's no ongoing resource gathering event.")
            return

        # Define possible resources
        resources = ["metal", "energy_core", "bio_sample", "nanofiber", "quantum_particle"]
        gathered = random.choices(resources, k=random.randint(1, 3))

        # Update user's resource storage
        if 'resources' not in user_data:
            user_data['resources'] = {}

        for resource in gathered:
            if resource not in user_data['resources']:
                user_data['resources'][resource] = 0
            user_data['resources'][resource] += 1

        await self.config.user(ctx.author).set(user_data)

        resource_string = ", ".join(gathered)
        await ctx.send(f"You gathered: {resource_string}")
        
        # Show updated resource totals
        totals = ", ".join([f"{r}: {c}" for r, c in user_data['resources'].items()])
        await ctx.send(f"Your current resources: {totals}")

    @df.command()
    async def inventory(self, ctx):
        """Check your resource inventory"""
        user_data = await self.config.user(ctx.author).all()
        if 'resources' not in user_data or not user_data['resources']:
            await ctx.send("You don't have any resources.")
            return

        embed = discord.Embed(title=f"{ctx.author.name}'s Resource Inventory", color=discord.Color.green())
        for resource, count in user_data['resources'].items():
            embed.add_field(name=resource.replace('_', ' ').title(), value=str(count))
        await ctx.send(embed=embed)

    @df.command()
    @commands.cooldown(1, 300, commands.BucketType.user)  # 5 minute cooldown
    async def drill(self, ctx):
        """Participate in a training drill (event)"""
        guild_data = await self.config.guild(ctx.guild).all()
        if guild_data['ongoing_event'] != "training_drill":
            await ctx.send("There's no ongoing training drill event.")
            return

        user_data = await self.config.user(ctx.author).all()
        attribute = random.choice(['strength', 'agility', 'intelligence'])
        gain = random.randint(2, 5)
        await self.config.user(ctx.author).set_raw(attribute, value=user_data[attribute] + gain)
        await ctx.send(f"You completed the training drill and gained {gain} {attribute}!")

    async def _check_rankup(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        ranks = ["Trainee", "Private", "Corporal", "Sergeant", "Lieutenant", "Captain", "Major", "Colonel", "General"]
        current_rank_index = ranks.index(user_data['rank'])
        
        if current_rank_index < len(ranks) - 1:
            exp_needed = (current_rank_index + 1) * 1000
            if user_data['exp'] >= exp_needed:
                new_rank = ranks[current_rank_index + 1]
                await self.config.user(ctx.author).rank.set(new_rank)
                await ctx.send(f"Congratulations {ctx.author.mention}! You've been promoted to {new_rank}!")

async def setup(bot):
    await bot.add_cog(Kaiju8Game(bot))
