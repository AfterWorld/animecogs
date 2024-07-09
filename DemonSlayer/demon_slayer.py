from redbot.core import commands, Config, bank
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import box, pagify
import random
import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, List

class DemonSlayer(commands.Cog):
    """
    Demon Slayer themed cog with RPG elements.
    
    Slay demons, master breathing techniques, and rise through the ranks of the Demon Slayer Corps!
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_user = {
            "breathing_technique": None,
            "nichirin_color": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "last_mission": None,
            "technique_mastery": 0,
            "slayer_points": 0,
            "total_concentration": 0,
            "demon_moon_rank": None,
            "last_daily": None,
            "trainings_completed": 0,
            "event_points": 0,
            "form_mastery": {}
        }
        default_guild = {
            "active_missions": {},
            "group_training": None,
            "hashira_challenge": None,
            "last_invasion": None,
            "active_event": None,
            "event_end_time": None
        }
        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)
        
        self.seasonal_events = {
            "Blood Moon Festival": {
                "description": "Demons are stronger, but rewards are greater!",
                "bonus_multiplier": 1.5,
                "difficulty_increase": 1.2,
                "duration": timedelta(days=3)
            },
            "Wisteria Bloom": {
                "description": "The blooming wisteria weakens demons, making them easier to defeat!",
                "bonus_multiplier": 1.2,
                "difficulty_decrease": 0.8,
                "duration": timedelta(days=5)
            },
            "Demon Slayer Corps Anniversary": {
                "description": "Celebrate the founding of the Demon Slayer Corps with increased rewards!",
                "bonus_multiplier": 2.0,
                "difficulty_increase": 1.0,
                "duration": timedelta(days=1)
            }
        }

        
        self.breathing_techniques = {
            "Water": [
                "First Form: Water Surface Slash",
                "Second Form: Water Wheel",
                "Third Form: Flowing Dance",
                "Fourth Form: Striking Tide",
                "Fifth Form: Blessed Rain After the Drought",
                "Sixth Form: Whirlpool",
                "Seventh Form: Droplet Splash Thrust",
                "Eighth Form: Waterfall Basin",
                "Ninth Form: Splashing Water Flow",
                "Tenth Form: Constant Flux",
                "Eleventh Form: Dead Calm"
            ],
            "Thunder": [
                "First Form: Thunderclap and Flash",
                "Second Form: Rice Spirit",
                "Third Form: Thunder Swarm",
                "Fourth Form: Distant Thunder",
                "Fifth Form: Heat Lightning",
                "Sixth Form: Rumble and Flash",
                "Seventh Form: Honoikazuchi no Kami"
            ],
            "Flame": [
                "First Form: Unknowing Fire",
                "Second Form: Rising Scorching Sun",
                "Third Form: Blazing Universe",
                "Fourth Form: Blooming Flame Undulation",
                "Fifth Form: Flame Tiger",
                "Ninth Form: Rengoku"
            ],
            "Wind": [
                "First Form: Dust Whirlwind Cutter",
                "Second Form: Claws-Purifying Wind",
                "Third Form: Clean Storm Wind Tree",
                "Fourth Form: Rising Dust Storm",
                "Fifth Form: Purgatory Windmill",
                "Sixth Form: Black Wind Mountain Mist",
                "Seventh Form: Gale - Sudden Gusts"
            ],
            "Stone": [
                "First Form: Serpentine Bipedal",
                "Second Form: Upper Smash",
                "Third Form: Stone Skin",
                "Fourth Form: Volcanic Rock",
                "Fifth Form: Arcs of Justice"
            ],
            "Mist": [
                "First Form: Cloudy Mist",
                "Second Form: Layered Mist",
                "Third Form: Scattering Mist Splash",
                "Fourth Form: Advection Mist",
                "Fifth Form: Sea of Clouds and Haze",
                "Sixth Form: Moonlit Mist",
                "Seventh Form: Haze"
            ],
            "Sound": [
                "First Form: Roar",
                "Fourth Form: Constant Resounding Slashes",
                "Fifth Form: String Performance",
                "Sixth Form: Constant Resounding Slashes - Explosive Flash"
            ],
            "Love": [
                "First Form: Shivers of First Love",
                "Second Form: Love Pangs",
                "Third Form: Lovely Kitty Paws"
            ],
            "Serpent": [
                "First Form: Twisting Slash",
                "Fourth Form: Serpentine Strangle",
                "Fifth Form: Slithering Serpent"
            ],
            "Flower": [
                "First Form: Waltz of Cherry Blossoms",
                "Second Form: Plum Spirit",
                "Third Form: Peony of Futility",
                "Fourth Form: Safflower Robe",
                "Fifth Form: Peonies of Futility - Bellflower Sword"
            ],
            "Beast": [
                "First Fang: Pierce",
                "Second Fang: Rip and Tear",
                "Third Fang: Devour",
                "Fourth Fang: Mince to Bits",
                "Fifth Fang: Madness"
            ],
            "Sun": [
                "First Form: Dance",
                "Second Form: Clear Blue Sky",
                "Third Form: Fake Rainbow",
                "Fourth Form: Burning Bones, Summer Sun",
                "Fifth Form: Setting Sun Transformation",
                "Sixth Form: Solar Heat Haze",
                "Ninth Form: Dragon Sun Halo Head Dance",
                "Thirteenth Form: Burning Bones, Summer Sun Flame Waltz"
            ]
        }
        self.demons = {
            "Muzan Kibutsuji": {"difficulty": 100, "xp": 1000},
            "Akaza": {"difficulty": 85, "xp": 800},
            "Doma": {"difficulty": 90, "xp": 850},
            "Kokushibo": {"difficulty": 95, "xp": 900},
            "Gyokko": {"difficulty": 75, "xp": 700},
            "Daki": {"difficulty": 70, "xp": 650},
            "Gyutaro": {"difficulty": 80, "xp": 750},
            "Enmu": {"difficulty": 65, "xp": 600},
            "Rui": {"difficulty": 60, "xp": 550},
            "Kyogai": {"difficulty": 55, "xp": 500}
        }
        self.ranks = [
            {"name": "Mizunoto", "points": 0, "missions": 0, "tasks": 0, "trainings": 0},
            {"name": "Mizunoe", "points": 100, "missions": 5, "tasks": 10, "trainings": 20},
            {"name": "Kanoto", "points": 250, "missions": 15, "tasks": 30, "trainings": 50},
            {"name": "Kanoe", "points": 500, "missions": 30, "tasks": 60, "trainings": 100},
            {"name": "Tsuchinoto", "points": 1000, "missions": 50, "tasks": 100, "trainings": 200},
            {"name": "Tsuchinoe", "points": 2000, "missions": 75, "tasks": 150, "trainings": 300},
            {"name": "Hinoto", "points": 3500, "missions": 100, "tasks": 200, "trainings": 400},
            {"name": "Hinoe", "points": 5000, "missions": 150, "tasks": 300, "trainings": 500},
            {"name": "Kinoto", "points": 7500, "missions": 200, "tasks": 400, "trainings": 600},
            {"name": "Kinoe", "points": 10000, "missions": 250, "tasks": 500, "trainings": 700},
            {"name": "Hashira Candidate", "points": 15000, "missions": 300, "tasks": 600, "trainings": 800},
            {"name": "Hashira", "points": 20000, "missions": 350, "tasks": 700, "trainings": 1000}
        ]
        self.hashiras = ["Water", "Flame", "Wind", "Stone", "Love", "Mist", "Sound", "Flower", "Serpent"]
        
        self.bot.loop.create_task(self.migrate_user_data())
        self.bg_task = self.bot.loop.create_task(self.event_background_task())
        
        def cog_unload(self):
            self.bg_task.cancel()
            
    async def event_background_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_data = await self.config.guild(guild).all()
                if not guild_data['active_event'] or datetime.now() > guild_data['event_end_time']:
                    # Start a new event
                    event_name = random.choice(list(self.seasonal_events.keys()))
                    event_data = self.seasonal_events[event_name]
                    end_time = datetime.now() + event_data['duration']
                    await self.config.guild(guild).active_event.set(event_name)
                    await self.config.guild(guild).event_end_time.set(end_time.isoformat())
                    
                    announcement_channel = guild.system_channel or guild.text_channels[0]
                    await announcement_channel.send(f"🎉 The {event_name} has begun! {event_data['description']} This event will last for {event_data['duration'].days} days.")
            
            await asyncio.sleep(3600)  # Check every hour


    async def migrate_user_data(self):
        await self.bot.wait_until_ready()
        all_users = await self.config.all_users()
        for user_id, user_data in all_users.items():
            updated = False
            for key in ['tasks_completed', 'missions_completed', 'trainings_completed']:
                if key not in user_data:
                    user_data[key] = 0
                    updated = True
            if updated:
                await self.config.user_from_id(user_id).set(user_data)

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ds.command(name="practice_form")
    async def practice_form(self, ctx, *, form_name: str):
        """Practice a specific form to increase its mastery."""
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        
        if not technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first!")

        forms = self.breathing_techniques.get(technique, [])
        matching_forms = [f for f in forms if form_name.lower() in f.lower()]

        if not matching_forms:
            return await ctx.send(f"No matching form found for {technique} Breathing. Check your spelling or use `[p]ds forms` to see available forms.")

        if len(matching_forms) > 1:
            return await ctx.send(f"Multiple matching forms found. Please be more specific: {', '.join(matching_forms)}")

        form = matching_forms[0]
        
        # Practice the form
        mastery_gain = random.randint(1, 5)
        async with self.config.user(ctx.author).form_mastery() as form_mastery:
            form_mastery[form] = form_mastery.get(form, 0) + mastery_gain

        await ctx.send(f"{ctx.author.mention} practiced {form}. Form mastery increased by {mastery_gain}!")

    @ds.command(name="form_mastery")
    async def show_form_mastery(self, ctx):
        """Display your form mastery levels."""
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        form_mastery = user_data['form_mastery']

        if not technique:
            return await ctx.send(f"{ctx.author.mention}, you haven't been assigned a breathing technique yet.")

        embed = discord.Embed(title=f"{ctx.author.name}'s {technique} Breathing Form Mastery", color=discord.Color.blue())
        for form, mastery in form_mastery.items():
            if form in self.breathing_techniques.get(technique, []):
                embed.add_field(name=form, value=f"Mastery Level: {mastery}", inline=False)

        await ctx.send(embed=embed)
            
    @ds.command(name="event")
    async def check_event(self, ctx):
        """Check the current seasonal event."""
        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']
        
        if not active_event:
            return await ctx.send("There is no active event at the moment.")
        
        event_data = self.seasonal_events[active_event]
        end_time = datetime.fromisoformat(guild_data['event_end_time'])
        time_left = end_time - datetime.now()
        
        embed = discord.Embed(title=f"Active Event: {active_event}", color=discord.Color.gold())
        embed.add_field(name="Description", value=event_data['description'], inline=False)
        embed.add_field(name="Bonus Multiplier", value=f"{event_data['bonus_multiplier']}x", inline=True)
        embed.add_field(name="Time Left", value=f"{time_left.days}d {time_left.seconds // 3600}h {(time_left.seconds // 60) % 60}m", inline=True)
        
        await ctx.send(embed=embed)

    @ds.command(name="event_leaderboard")
    async def event_leaderboard(self, ctx):
        """View the event leaderboard."""
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]['event_points'], reverse=True)[:10]
        
        embed = discord.Embed(title="Event Leaderboard", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"Event Points: {data['event_points']}", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="assign_technique")
    async def assign_breathing_technique(self, ctx):
        """
        Assigns a random Breathing Technique to you.
        
        This command will give you a random Breathing Technique and teach you its first form.
        You can only have one Breathing Technique at a time.
        """
        """Assigns a random Breathing Technique to the user."""
        technique = random.choice(list(self.breathing_techniques.keys()))
        await self.config.user(ctx.author).breathing_technique.set(technique)
        first_form = self.breathing_techniques[technique][0]
        await self.config.user(ctx.author).known_forms.set([first_form])
        await ctx.send(f"{ctx.author.mention}, you have been assigned the **{technique} Breathing** technique! You've learned your first form: **{first_form}**!")

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @ds.command(name="slay")
    async def slay_demon(self, ctx):
        """
        Attempt to slay a random demon.
        
        This command simulates a battle with a random demon. Your success depends on your rank and experience.
        You can use this command once per hour.
        """
        """Simulates a battle with a random demon. Can be used once per hour."""
        demon, info = random.choice(list(self.demons.items()))
        user_technique = await self.config.user(ctx.author).breathing_technique()
        
        if not user_technique:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")

        success_rate = random.randint(1, 100)
        await ctx.send(f"{ctx.author.mention} encounters {demon}! The battle begins...")
        await asyncio.sleep(2)
        
        if success_rate > info["difficulty"]:
            demons_slayed = await self.config.user(ctx.author).demons_slayed()
            await self.config.user(ctx.author).demons_slayed.set(demons_slayed + 1)
            xp_gained = info["xp"]
            await self.add_xp(ctx.author, xp_gained)
            await ctx.send(f"Victory! {ctx.author.mention} has successfully slain {demon} using {user_technique} Breathing! You gained {xp_gained} XP!")
            await self.check_rank_up(ctx)
            await self.check_new_form(ctx)
        else:
            await ctx.send(f"Oh no! {demon} was too powerful. {ctx.author.mention} needs to train harder!")

    @ds.command(name="nichirin")
    async def nichirin_color(self, ctx):
        """
        Assigns a random color to your Nichirin Blade.
        
        The color of your Nichirin Blade is purely cosmetic and doesn't affect your demon-slaying abilities.
        """
        colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"]
        color = random.choice(colors)
        await self.config.user(ctx.author).nichirin_color.set(color)
        await ctx.send(f"{ctx.author.mention}, your Nichirin Blade turns **{color}**!")

    @ds.command(name="train")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def train(self, ctx):
        """Undergo training to improve your skills."""
        user_data = await self.config.user(ctx.author).all()
        breathing_technique = user_data.get('breathing_technique')

        if not breathing_technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique` to get started!")

        training_exercises = [
            f"practice {breathing_technique} Breathing forms for hours",
            "perform strength training with heavy weights",
            "run laps around the entire Demon Slayer headquarters",
            "meditate under a waterfall to improve focus",
            f"spar with other {breathing_technique} users"
        ]

        exercise = random.choice(training_exercises)
        await ctx.send(f"{ctx.author.mention} begins to {exercise}.")
        await asyncio.sleep(5)  # Simulating training time

        mastery_gained = random.randint(10, 30)
        points_earned = random.randint(5, 15)

        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']
        
        if active_event:
            event_data = self.seasonal_events[active_event]
            mastery_gained = int(mastery_gained * event_data['bonus_multiplier'])
            points_earned = int(points_earned * event_data['bonus_multiplier'])

        async with self.config.user(ctx.author).all() as user_data:
            user_data['technique_mastery'] += mastery_gained
            user_data['slayer_points'] += points_earned
            user_data['trainings_completed'] = user_data.get('trainings_completed', 0) + 1
            if active_event:
                user_data['event_points'] = user_data.get('event_points', 0) + points_earned

        await ctx.send(f"Training complete! You gained {mastery_gained} Technique Mastery and {points_earned} Slayer Points.")
        if active_event:
            await ctx.send(f"Event bonus applied! You also earned {points_earned} Event Points.")
        
        await self.check_rank_up(ctx)

    @ds.command(name="quote")
    async def demon_quote(self, ctx):
        """Shares a random quote from the Demon Slayer series."""
        quotes = [
            "The weak have no rights or choices. Their only fate is to be relentlessly crushed by the strong! - Akaza",
            "Don't ever give up. Even if it's painful, even if it's agonizing, don't try to take the easy way out. - Tanjiro Kamado",
            "Feel the rage. The powerful, pure rage of not being able to forgive will become your unswerving drive to take action. - Giyu Tomioka",
            "No matter how many people you may lose, you have no choice but to go on living. No matter how devastating the blows may be. - Shinobu Kocho"
        ]
        embed = discord.Embed(title="Demon Slayer Quote", description=random.choice(quotes), color=discord.Color.red())
        await ctx.send(embed=embed)

    @ds.command(name="form")
    async def form(self, ctx):
        """
        Perform a random form of your assigned Breathing Style.
        
        This command will randomly choose one of the forms you know and perform it.
        """
        user_technique = await self.config.user(ctx.author).breathing_technique()
        if not user_technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")
        
        known_forms = await self.config.user(ctx.author).known_forms()
        if not known_forms:
            return await ctx.send(f"{ctx.author.mention}, you haven't learned any forms yet! Train more to learn new forms.")
        
        form = random.choice(known_forms)
        await ctx.send(f"{ctx.author.mention} performs **{user_technique} Breathing: {form}**! The enemies tremble before your might!")

    @ds.command(name="profile")
    async def profile(self, ctx, user: discord.Member = None):
        """
        Display your or another user's Demon Slayer profile.
        
        This command shows information such as Breathing Technique, rank, experience, and known forms.
        If no user is specified, it will show your own profile.
        """
        if user is None:
            user = ctx.author
        user_data = await self.config.user(user).all()
        embed = discord.Embed(title=f"{user.name}'s Demon Slayer Profile", color=discord.Color.red())
        embed.add_field(name="Breathing Technique", value=user_data['breathing_technique'] or "Not assigned", inline=False)
        embed.add_field(name="Nichirin Blade Color", value=user_data['nichirin_color'] or "Not assigned", inline=False)
        embed.add_field(name="Demons Slayed", value=user_data['demons_slayed'], inline=False)
        embed.add_field(name="Rank", value=user_data['rank'], inline=False)
        embed.add_field(name="Experience", value=user_data['experience'], inline=False)
        embed.add_field(name="Known Forms", value=", ".join(user_data['known_forms']) or "None", inline=False)
        await ctx.send(embed=embed)

    @ds.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """
        Display the top 10 Demon Slayers based on demons slayed.
        
        This leaderboard ranks Demon Slayers in your server by the number of demons they've defeated.
        """
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]['demons_slayed'], reverse=True)[:10]
        
        embed = discord.Embed(title="Top 10 Demon Slayers", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"Demons Slayed: {data['demons_slayed']}\nRank: {data['rank']}", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="complete_mission")
    async def complete_mission(self, ctx):
        """
        Complete your ongoing demon-slaying mission.
        
        Use this command when your mission timer is up to claim your rewards.
        The success of your mission is determined when you complete it.
        """
        guild_data = await self.config.guild(ctx.guild).all()
        active_missions = guild_data['active_missions']
        
        if str(ctx.author.id) not in active_missions:
            return await ctx.send(f"{ctx.author.mention}, you don't have an active mission. Start one with `[p]ds mission`!")
        
        mission = active_missions[str(ctx.author.id)]
        if datetime.now() < datetime.fromisoformat(mission['end_time']):
            time_left = datetime.fromisoformat(mission['end_time']) - datetime.now()
            return await ctx.send(f"{ctx.author.mention}, your mission is not complete yet. Time remaining: {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")
        
        del active_missions[str(ctx.author.id)]
        await self.config.guild(ctx.guild).active_missions.set(active_missions)
        
        success = random.random() < 0.7  # 70% success rate
        if success:
            xp_gained = self.demons[mission['demon']]['xp']
            await self.add_xp(ctx.author, xp_gained)
            demons_slayed = await self.config.user(ctx.author).demons_slayed()
            await self.config.user(ctx.author).demons_slayed.set(demons_slayed + 1)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've successfully completed your mission and defeated {mission['demon']}! You gained {xp_gained} XP!")
            await self.check_rank_up(ctx)
            await self.check_new_form(ctx)
        else:
            await ctx.send(f"{ctx.author.mention}, despite your best efforts, {mission['demon']} managed to escape. Better luck next time!")

    async def add_xp(self, user, amount):
        current_xp = await self.config.user(user).experience()
        await self.config.user(user).experience.set(current_xp + amount)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank = self.calculate_rank(user_data)
        next_rank = self.get_next_rank(current_rank)

        if (user_data.get('slayer_points', 0) >= next_rank['points'] and
            user_data.get('missions_completed', 0) >= next_rank['missions'] and
            user_data.get('tasks_completed', 0) >= next_rank['tasks'] and
            user_data.get('trainings_completed', 0) >= next_rank['trainings']):
            
            await self.config.user(ctx.author).rank.set(next_rank['name'])
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {next_rank['name']}!")

            if next_rank['name'] == "Hashira Candidate":
                await ctx.send("You are now a Hashira Candidate! Complete the Hashira Trial to become a full-fledged Hashira.")

    async def check_new_form(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']
        all_forms = self.breathing_techniques[technique]

        if len(known_forms) < len(all_forms):
            chance = random.random()
            if chance < 0.1:  # 10% chance to learn a new form
                new_form = random.choice([form for form in all_forms if form not in known_forms])
                known_forms.append(new_form)
                await self.config.user(ctx.author).known_forms.set(known_forms)
                await ctx.send(f"Breakthrough! {ctx.author.mention} has learned a new form: **{new_form}**!")

    @ds.command(name="forms")
    async def list_forms(self, ctx):
        """
        List all the Breathing Technique forms you've learned.
        
        This command displays all the forms you currently know for your assigned Breathing Technique.
        """
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']

        if not technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")

        if not known_forms:
            return await ctx.send(f"{ctx.author.mention}, you haven't learned any forms yet! Train more to learn new forms.")

        embed = discord.Embed(title=f"{ctx.author.name}'s {technique} Breathing Forms", color=discord.Color.blue())
        for i, form in enumerate(known_forms, 1):
            embed.add_field(name=f"Form {i}", value=form, inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="shop")
    async def shop(self, ctx):
        """
        Display the Demon Slayer shop.
        
        The shop offers various items to help you in your demon-slaying journey.
        Use the 'buy' command to purchase items from the shop.
        """
        shop_items = [
            {"name": "Extra Training Session", "cost": 500, "description": "Instantly gain 200 XP"},
            {"name": "Nichirin Blade Polishing", "cost": 1000, "description": "Increase your chances of slaying demons for the next 24 hours"},
            {"name": "Rare Form Scroll", "cost": 2000, "description": "Learn a random new form of your breathing technique"}
        ]

        embed = discord.Embed(title="Demon Slayer Shop", color=discord.Color.green())
        for item in shop_items:
            embed.add_field(name=f"{item['name']} - {item['cost']} coins", value=item['description'], inline=False)

        embed.set_footer(text="Use [p]ds buy <item name> to purchase an item")
        await ctx.send(embed=embed)

    @ds.command(name="buy")
    async def buy_item(self, ctx, *, item_name: str):
        """
        Buy an item from the Demon Slayer shop.
        
        Usage: [p]ds buy <item name>
        
        Make sure you have enough coins to purchase the item.
        Use the 'shop' command to see available items and their prices.
        """
        shop_items = {
            "Extra Training Session": {"cost": 500, "effect": self.extra_training},
            "Nichirin Blade Polishing": {"cost": 1000, "effect": self.nichirin_polishing},
            "Rare Form Scroll": {"cost": 2000, "effect": self.rare_form_scroll}
        }

        if item_name not in shop_items:
            return await ctx.send("That item is not available in the shop. Use `[p]ds shop` to see available items.")

        item = shop_items[item_name]
        user_balance = await bank.get_balance(ctx.author)

        if user_balance < item["cost"]:
            return await ctx.send(f"You don't have enough coins to buy this item. You need {item['cost']} coins.")

        await bank.withdraw_credits(ctx.author, item["cost"])
        await item["effect"](ctx)
        
    @ds.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily reward of experience and materials."""
        user_data = await self.config.user(ctx.author).all()
        last_daily = user_data['last_daily']
        now = datetime.now()

        if last_daily and datetime.fromisoformat(last_daily) + timedelta(days=1) > now:
            time_left = datetime.fromisoformat(last_daily) + timedelta(days=1) - now
            return await ctx.send(f"{ctx.author.mention}, you can claim your next daily reward in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")

        reward_points = random.randint(10, 50)
        mastery_increase = random.randint(5, 15)

        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']
        
        if active_event:
            event_data = self.seasonal_events[active_event]
            reward_points = int(reward_points * event_data['bonus_multiplier'])
            mastery_increase = int(mastery_increase * event_data['bonus_multiplier'])

        async with self.config.user(ctx.author).all() as user_data:
            user_data['slayer_points'] += reward_points
            user_data['technique_mastery'] += mastery_increase
            user_data['last_daily'] = now.isoformat()
            if active_event:
                user_data['event_points'] = user_data.get('event_points', 0) + reward_points

        await ctx.send(f"{ctx.author.mention}, you've claimed your daily reward!\n"
                       f"• {reward_points} Slayer Points\n"
                       f"• {mastery_increase} Technique Mastery")
        if active_event:
            await ctx.send(f"Event bonus applied! You also earned {reward_points} Event Points.")

    @ds.command(name="boss")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def boss_battle(self, ctx):
        """Initiate a boss battle against a powerful demon."""
        user_data = await self.config.user(ctx.author).all()
        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']
        
        boss = random.choice(["Rui", "Gyutaro", "Daki", "Akaza", "Doma"])
        boss_health = random.randint(1000, 2000)
        player_health = 1000
        turns = 0
        
        if active_event:
            event_data = self.seasonal_events[active_event]
            if 'difficulty_increase' in event_data:
                boss_health = int(boss_health * event_data['difficulty_increase'])
            elif 'difficulty_decrease' in event_data:
                boss_health = int(boss_health * event_data['difficulty_decrease'])
        
        battle_log = []

        embed = discord.Embed(title=f"Boss Battle: {ctx.author.name} vs {boss}", color=discord.Color.red())
        embed.add_field(name="Boss Health", value=f"{boss_health}/{boss_health}", inline=True)
        embed.add_field(name="Your Health", value=f"{player_health}/1000", inline=True)
        message = await ctx.send(embed=embed)

        while boss_health > 0 and player_health > 0:
            turns += 1
            player_damage = random.randint(50, 200)
            boss_damage = random.randint(50, 150)

            boss_health -= player_damage
            player_health -= boss_damage

            battle_log.append(f"Turn {turns}: You deal {player_damage} damage. {boss} deals {boss_damage} damage.")

            if turns % 3 == 0 or boss_health <= 0 or player_health <= 0:
                embed.clear_fields()
                embed.add_field(name="Boss Health", value=f"{max(0, boss_health)}/{boss_health}", inline=True)
                embed.add_field(name="Your Health", value=f"{max(0, player_health)}/1000", inline=True)
                embed.add_field(name="Battle Log", value="\n".join(battle_log[-3:]), inline=False)
                await message.edit(embed=embed)
                await asyncio.sleep(2)

        if boss_health <= 0:
            xp_reward = random.randint(500, 1000)
            slayer_points = random.randint(50, 100)
            
            if active_event:
                event_data = self.seasonal_events[active_event]
                xp_reward = int(xp_reward * event_data['bonus_multiplier'])
                slayer_points = int(slayer_points * event_data['bonus_multiplier'])
            
            async with self.config.user(ctx.author).all() as user_data:
                user_data['technique_mastery'] += xp_reward
                user_data['slayer_points'] += slayer_points
                user_data['demons_slayed'] += 1
                if active_event:
                    user_data['event_points'] = user_data.get('event_points', 0) + slayer_points

            embed.add_field(name="Result", value=f"Victory! You've defeated {boss}!", inline=False)
            embed.add_field(name="Rewards", value=f"XP: {xp_reward}\nSlayer Points: {slayer_points}", inline=False)
            if active_event:
                embed.add_field(name="Event Bonus", value=f"You also earned {slayer_points} Event Points!", inline=False)
        else:
            embed.add_field(name="Result", value=f"Defeat... {boss} was too powerful. Train harder and try again!", inline=False)

        await message.edit(embed=embed)
        await self.check_rank_up(ctx)

    @ds.command(name="craft")
    async def craft_nichirin(self, ctx):
        """Craft or reforge your Nichirin Blade."""
        user_data = await self.config.user(ctx.author).all()
        materials = user_data['nichirin_materials']

        if materials['steel'] < 10 or materials['scarlet_ore'] < 5:
            return await ctx.send(f"{ctx.author.mention}, you don't have enough materials to craft a Nichirin Blade. You need 10 steel and 5 scarlet ore.")

        new_color = random.choice(["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"])
        
        async with self.config.user(ctx.author).nichirin_materials() as mats:
            mats['steel'] -= 10
            mats['scarlet_ore'] -= 5

        await self.config.user(ctx.author).nichirin_color.set(new_color)

        await ctx.send(f"{ctx.author.mention}, you've successfully crafted a new Nichirin Blade!\n"
                       f"Its color is... **{new_color}**!")

    @ds.command(name="mastery")
    async def check_mastery(self, ctx):
        """Check your breathing technique mastery level."""
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        mastery = user_data['technique_mastery']
        
        if not technique:
            return await ctx.send(f"{ctx.author.mention}, you haven't been assigned a breathing technique yet. Use `[p]ds assign_technique` to get started!")
        
        level = mastery // 100
        progress = mastery % 100
        
        await ctx.send(f"{ctx.author.mention}, your {technique} Breathing mastery:\n"
                       f"Level: {level}\n"
                       f"Progress to next level: {progress}/100")

    @ds.command(name="ranking")
    async def show_ranking(self, ctx):
        """Display your current demon slayer ranking and progress."""
        user_data = await self.config.user(ctx.author).all()
        current_rank = self.calculate_rank(user_data)
        next_rank = self.get_next_rank(current_rank)

        embed = discord.Embed(title=f"{ctx.author.name}'s Demon Slayer Ranking", color=discord.Color.red())
        embed.add_field(name="Current Rank", value=current_rank['name'], inline=False)
        embed.add_field(name="Slayer Points", value=f"{user_data.get('slayer_points', 0)}/{next_rank['points']}", inline=True)
        embed.add_field(name="Missions Completed", value=f"{user_data.get('missions_completed', 0)}/{next_rank['missions']}", inline=True)
        embed.add_field(name="Tasks Completed", value=f"{user_data.get('tasks_completed', 0)}/{next_rank['tasks']}", inline=True)
        embed.add_field(name="Trainings Completed", value=f"{user_data.get('trainings_completed', 0)}/{next_rank['trainings']}", inline=True)

        if current_rank['name'] != "Hashira":
            embed.add_field(name="Next Rank", value=next_rank['name'], inline=False)
        else:
            embed.add_field(name="Status", value="You have reached the highest rank!", inline=False)

        await ctx.send(embed=embed)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank = self.calculate_rank(user_data)
        next_rank = self.get_next_rank(current_rank)

        if (user_data.get('slayer_points', 0) >= next_rank['points'] and
            user_data.get('missions_completed', 0) >= next_rank['missions'] and
            user_data.get('tasks_completed', 0) >= next_rank['tasks'] and
            user_data.get('trainings_completed', 0) >= next_rank['trainings']):
            
            await self.config.user(ctx.author).rank.set(next_rank['name'])
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {next_rank['name']}!")

            if next_rank['name'] == "Hashira Candidate":
                await ctx.send("You are now a Hashira Candidate! Complete the Hashira Trial to become a full-fledged Hashira.")
        
    @ds.command(name="task")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def complete_task(self, ctx):
        """Complete a daily task to earn points and progress towards higher ranks."""
        tasks = [
            "Patrol the nearby forest for demon activity",
            "Help villagers with their daily chores",
            "Train your breathing technique for hours",
            "Study demon weaknesses and strategies",
            "Craft wisteria-based weapons"
        ]
        
        task = random.choice(tasks)
        points_earned = random.randint(5, 15)
        
        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']
        
        if active_event:
            event_data = self.seasonal_events[active_event]
            points_earned = int(points_earned * event_data['bonus_multiplier'])
        
        await ctx.send(f"{ctx.author.mention}, your task: {task}")
        await asyncio.sleep(5)  # Simulating task completion time
        
        async with self.config.user(ctx.author).all() as user_data:
            user_data['slayer_points'] += points_earned
            user_data['tasks_completed'] += 1
            if active_event:
                user_data['event_points'] = user_data.get('event_points', 0) + points_earned
        
        await ctx.send(f"Task completed! You earned {points_earned} Slayer Points.")
        if active_event:
            await ctx.send(f"Event bonus applied! You also earned {points_earned} Event Points.")
        await self.check_rank_up(ctx)

    @ds.command(name="invasion")
    @commands.guild_only()
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    async def trigger_invasion(self, ctx):
        """Trigger a demon invasion event in the server."""
        guild_data = await self.config.guild(ctx.guild).all()
        last_invasion = guild_data['last_invasion']
        now = datetime.now()
        
        if last_invasion and datetime.fromisoformat(last_invasion) + timedelta(hours=6) > now:
            time_left = datetime.fromisoformat(last_invasion) + timedelta(hours=6) - now
            return await ctx.send(f"The demons are still regrouping. Next invasion possible in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")
        
        await self.start_invasion(ctx.guild)
        
    @ds.command(name="mission")
    @commands.cooldown(1, 43200, commands.BucketType.user)  # 12-hour cooldown
    async def embark_mission(self, ctx):
        """Embark on a challenging mission to earn substantial rewards."""
        missions = [
            "Investigate a series of mysterious disappearances in a remote village",
            "Protect a high-ranking official from potential demon attacks",
            "Infiltrate a demon hideout and gather intelligence",
            "Rescue captured civilians from a demon-infested area",
            "Track and eliminate a powerful demon that has been terrorizing a region"
        ]
        
        mission = random.choice(missions)
        await ctx.send(f"{ctx.author.mention}, your mission: {mission}")
        await ctx.send("This is a challenging mission. Your success depends on your skill and a bit of luck. Are you ready? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("Mission request timed out. Try again later.")

        if msg.content.lower() == 'no':
            return await ctx.send("Mission declined. Stay vigilant for future opportunities.")

        await ctx.send("Mission accepted! The outcome will be determined shortly...")
        await asyncio.sleep(10)  # Simulating mission time

        guild_data = await self.config.guild(ctx.guild).all()
        active_event = guild_data['active_event']

        success = random.random() < 0.6  # 60% success rate
        if success:
            points_earned = random.randint(50, 100)
            if active_event:
                event_data = self.seasonal_events[active_event]
                points_earned = int(points_earned * event_data['bonus_multiplier'])
            
            async with self.config.user(ctx.author).all() as user_data:
                user_data['slayer_points'] += points_earned
                user_data['missions_completed'] += 1
                if active_event:
                    user_data['event_points'] = user_data.get('event_points', 0) + points_earned
            
            await ctx.send(f"Mission successful! You earned {points_earned} Slayer Points.")
            if active_event:
                await ctx.send(f"Event bonus applied! You also earned {points_earned} Event Points.")
        else:
            await ctx.send("Despite your best efforts, the mission was not successful. Keep training and try again!")

        await self.check_rank_up(ctx)

    @ds.command(name="fight_invasion")
    @commands.guild_only()
    async def fight_invasion(self, ctx):
        """Join the ongoing demon invasion battle."""
        guild_data = await self.config.guild(ctx.guild).all()
        last_invasion = guild_data['last_invasion']
        now = datetime.now()
        
        if not last_invasion or datetime.fromisoformat(last_invasion) + timedelta(minutes=30) < now:
            return await ctx.send("There's no ongoing demon invasion. Stay alert for the next one!")
        
        user_data = await self.config.user(ctx.author).all()
        if not user_data['breathing_technique']:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique to fight in the invasion! Use `[p]ds assign_technique` first.")
        
        active_event = guild_data['active_event']
        points_earned = random.randint(10, 30)
        
        if active_event:
            event_data = self.seasonal_events[active_event]
            points_earned = int(points_earned * event_data['bonus_multiplier'])
        
        async with self.config.user(ctx.author).all() as user_data:
            user_data['slayer_points'] += points_earned
            if active_event:
                user_data['event_points'] = user_data.get('event_points', 0) + points_earned
        
        await ctx.send(f"{ctx.author.mention} joins the battle against the invading demons! You earned {points_earned} Slayer Points for your bravery.")
        if active_event:
            await ctx.send(f"Event bonus applied! You also earned {points_earned} Event Points.")

    async def start_invasion(self, guild):
        channel = guild.system_channel or random.choice(guild.text_channels)
        await channel.send("🚨 **DEMON INVASION ALERT** 🚨\n"
                           "Demons are invading the area! All available Demon Slayers, prepare for battle!\n"
                           "Use `[p]ds fight_invasion` to join the battle!")
        
        await self.config.guild(guild).last_invasion.set(datetime.now().isoformat())
        
        await asyncio.sleep(1800)  # Invasion lasts for 30 minutes
        
        participants = [member for member in guild.members if await self.config.user(member).breathing_technique()]
        survivors = random.sample(participants, k=max(1, len(participants) * 2 // 3))
        
        guild_data = await self.config.guild(guild).all()
        active_event = guild_data['active_event']
        
        for survivor in survivors:
            points = random.randint(10, 50)
            if active_event:
                event_data = self.seasonal_events[active_event]
                points = int(points * event_data['bonus_multiplier'])
            
            async with self.config.user(survivor).all() as user_data:
                user_data['slayer_points'] += points
                user_data['technique_mastery'] += random.randint(5, 15)
                if active_event:
                    user_data['event_points'] = user_data.get('event_points', 0) + points
        
        await channel.send("The demon invasion has been repelled! Congratulations to all participants!\n"
                           f"Survivors: {', '.join(survivor.mention for survivor in survivors)}\n"
                           "Check your updated rankings with `[p]ds ranking`!")

    def calculate_rank(self, points):
        ranks = [
            (0, "Mizunoto"),
            (100, "Mizunoe"),
            (250, "Kanoto"),
            (500, "Kanoe"),
            (1000, "Tsuchinoto"),
            (2000, "Tsuchinoe"),
            (3500, "Hinoto"),
            (5000, "Hinoe"),
            (7500, "Kinoto"),
            (10000, "Kinoe"),
            (15000, "Hashira")
        ]
        
        for threshold, rank in reversed(ranks):
            if points >= threshold:
                return rank
        
        return "Unknown"
    
    @ds.command(name="group_train")
    async def group_training(self, ctx):
        """Start or join a group training session."""
        guild_data = await self.config.guild(ctx.guild).all()
        now = datetime.now()

        if guild_data['group_training'] and datetime.fromisoformat(guild_data['group_training']['end_time']) > now:
            # Join existing training
            guild_data['group_training']['participants'].append(ctx.author.id)
            await self.config.guild(ctx.guild).set(guild_data)
            time_left = datetime.fromisoformat(guild_data['group_training']['end_time']) - now
            await ctx.send(f"{ctx.author.mention} has joined the group training session! {len(guild_data['group_training']['participants'])} participants now. {time_left.seconds // 60} minutes remaining.")
        else:
            # Start new training
            end_time = now + timedelta(minutes=30)
            guild_data['group_training'] = {
                "participants": [ctx.author.id],
                "end_time": end_time.isoformat()
            }
            await self.config.guild(ctx.guild).set(guild_data)
            await ctx.send(f"{ctx.author.mention} has started a group training session! It will last for 30 minutes. Use `[p]ds group_train` to join!")

            # Schedule end of training
            await asyncio.sleep(1800)  # 30 minutes
            await self.end_group_training(ctx.guild)

    async def end_group_training(self, guild):
        guild_data = await self.config.guild(guild).all()
        if not guild_data['group_training']:
            return

        participants = guild_data['group_training']['participants']
        xp_reward = len(participants) * 50  # More participants = more XP

        for user_id in participants:
            user = guild.get_member(user_id)
            if user:
                await self.add_xp(user, xp_reward)

        await self.config.guild(guild).group_training.set(None)
        channel = guild.get_channel(guild.system_channel.id)  # Announce in the system channel
        if channel:
            await channel.send(f"The group training session has ended! All {len(participants)} participants gained {xp_reward} XP!")

    @ds.command(name="materials")
    async def show_materials(self, ctx):
        """Show your crafting materials for Nichirin Blades."""
        materials = await self.config.user(ctx.author).nichirin_materials()
        await ctx.send(f"{ctx.author.mention}, your crafting materials:\n"
                       f"• Steel: {materials['steel']}\n"
                       f"• Scarlet Ore: {materials['scarlet_ore']}")
        
    @ds.command(name="hashira_challenge")
    @commands.guild_only()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def hashira_challenge(self, ctx):
        """Challenge a Hashira to a duel and test your skills."""
        user_data = await self.config.user(ctx.author).all()
        if user_data['rank'] != 'Kinoe':
            return await ctx.send(f"{ctx.author.mention}, only Kinoe rank slayers can challenge a Hashira!")

        hashira = random.choice(self.hashiras)
        await ctx.send(f"{ctx.author.mention} challenges the {hashira} Hashira to a duel!")

        # Simulating the duel
        user_score = user_data['technique_mastery'] + random.randint(1, 100)
        hashira_score = random.randint(800, 1000)

        await asyncio.sleep(2)
        if user_score > hashira_score:
            await ctx.send(f"Incredible! {ctx.author.mention} has defeated the {hashira} Hashira!")
            await self.config.user(ctx.author).rank.set("Hashira")
            await ctx.send(f"Congratulations! You have been promoted to the rank of Hashira!")
        else:
            await ctx.send(f"{ctx.author.mention} fought valiantly but was defeated by the {hashira} Hashira. Keep training and try again!")

    @ds.command(name="demon_moon")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def challenge_demon_moon(self, ctx):
        """Challenge a Demon Moon to increase your demon moon rank."""
        user_data = await self.config.user(ctx.author).all()
        current_rank = user_data['demon_moon_rank']

        if current_rank is None:
            target_rank = "Lower Moon Six"
        elif current_rank.startswith("Lower Moon"):
            current_number = int(current_rank.split()[-1])
            target_rank = f"Lower Moon {current_number - 1}" if current_number > 1 else "Upper Moon Six"
        elif current_rank.startswith("Upper Moon"):
            current_number = int(current_rank.split()[-1])
            target_rank = f"Upper Moon {current_number - 1}" if current_number > 1 else "Upper Moon One"
        else:
            return await ctx.send(f"{ctx.author.mention}, you've already reached the highest demon moon rank!")

        await ctx.send(f"{ctx.author.mention} challenges {target_rank} to a battle!")

        # Simulating the battle
        user_score = user_data['technique_mastery'] + user_data['total_concentration'] + random.randint(1, 200)
        demon_score = random.randint(700, 1000)

        await asyncio.sleep(2)
        if user_score > demon_score:
            await self.config.user(ctx.author).demon_moon_rank.set(target_rank)
            await ctx.send(f"Victory! {ctx.author.mention} has defeated {target_rank} and taken their position!")
        else:
            await ctx.send(f"{ctx.author.mention} was overwhelmed by {target_rank}'s power. Train harder and try again!")

    @ds.command(name="concentrate")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def total_concentration_training(self, ctx):
        """Undergo Total Concentration Breathing training to enhance your abilities."""
        user_data = await self.config.user(ctx.author).all()
        
        training_result = random.randint(1, 10)
        await self.config.user(ctx.author).total_concentration.set(user_data['total_concentration'] + training_result)

        await ctx.send(f"{ctx.author.mention} undergoes intense Total Concentration Breathing training!")
        await asyncio.sleep(2)
        await ctx.send(f"Your Total Concentration has increased by {training_result} points!")

    @ds.command(name="forge_quest")
    @commands.cooldown(1, 604800, commands.BucketType.user)  # Once per week
    async def nichirin_forge_quest(self, ctx):
        """Embark on a quest to forge a new Nichirin Blade."""
        tasks = [
            "Climbing Mt. Sagiri to obtain rare ore",
            "Meditating under a waterfall to purify your spirit",
            "Battling a powerful demon to obtain a special alloy",
            "Studying ancient forging techniques",
            "Assisting the swordsmith in the forging process"
        ]

        await ctx.send(f"{ctx.author.mention} embarks on a quest to forge a new Nichirin Blade!")
        
        for task in tasks:
            await ctx.send(f"Task: {task}")
            await asyncio.sleep(3)
            success = random.choice([True, False])
            if success:
                await ctx.send("Success!")
            else:
                await ctx.send("The quest has failed. Try again next week!")
                return

        new_color = random.choice(["Crimson", "Navy", "Emerald", "Golden", "Violet", "Silver"])
        await self.config.user(ctx.author).nichirin_color.set(new_color)
        await ctx.send(f"Congratulations! You've successfully forged a new {new_color} Nichirin Blade!")

    @ds.command(name="corps_mission")
    @commands.cooldown(1, 43200, commands.BucketType.user)  # Twice per day
    async def demon_slayer_corps_mission(self, ctx):
        """Accept a mission from the Demon Slayer Corps."""
        missions = [
            "Investigate strange disappearances in a remote village",
            "Protect a important figure from potential demon attacks",
            "Track down and eliminate a demon that's been terrorizing a town",
            "Escort a group of civilians through demon-infested territory",
            "Retrieve a valuable artifact from a demon's lair"
        ]

        mission = random.choice(missions)
        await ctx.send(f"{ctx.author.mention}, your mission from the Demon Slayer Corps:\n{mission}")

        await ctx.send("Do you accept this mission? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("Mission request timed out. Try again later.")

        if msg.content.lower() == 'no':
            return await ctx.send("Mission declined. The Demon Slayer Corps will find another slayer for this task.")

        await ctx.send("Mission accepted! You have 1 hour to complete the mission.")
        await asyncio.sleep(5)  # In a real scenario, this would be much longer

        success = random.random() < 0.7  # 70% success rate
        if success:
            reward = random.randint(50, 200)
            await self.add_xp(ctx.author, reward)
            await ctx.send(f"Mission completed successfully! You've earned {reward} XP.")
        else:
            await ctx.send("Despite your best efforts, the mission was not successful. Keep training and try again!")

    async def add_xp(self, user, amount):
        async with self.config.user(user).experience() as xp:
            xp += amount

    async def extra_training(self, ctx):
        await self.add_xp(ctx.author, 200)
        await ctx.send(f"{ctx.author.mention}, you've completed an intense training session and gained 200 XP!")

    async def nichirin_polishing(self, ctx):
        # This effect would need to be implemented in the slay_demon method
        # For now, we'll just acknowledge the purchase
        await ctx.send(f"{ctx.author.mention}, your Nichirin Blade has been polished to perfection! Your demon-slaying chances are increased for the next 24 hours.")

    async def rare_form_scroll(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']
        all_forms = self.breathing_techniques[technique]

        if len(known_forms) == len(all_forms):
            await ctx.send(f"{ctx.author.mention}, you've already mastered all forms of {technique} Breathing!")
            return

        new_form = random.choice([form for form in all_forms if form not in known_forms])
        known_forms.append(new_form)
        await self.config.user(ctx.author).known_forms.set(known_forms)
        await ctx.send(f"Incredible! {ctx.author.mention} has learned a new form from the rare scroll: **{new_form}**!")
        
    def calculate_rank(self, user_data):
        for rank in reversed(self.ranks):
            if (user_data.get('slayer_points', 0) >= rank['points'] and
                user_data.get('missions_completed', 0) >= rank.get('missions', 0) and
                user_data.get('tasks_completed', 0) >= rank.get('tasks', 0) and
                user_data.get('trainings_completed', 0) >= rank.get('trainings', 0)):
                return rank
        return self.ranks[0]  # Default to lowest rank

    def get_next_rank(self, current_rank):
        current_index = self.ranks.index(current_rank)
        if current_index < len(self.ranks) - 1:
            return self.ranks[current_index + 1]
        return current_rank  # Return current rank if it's the highes

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
