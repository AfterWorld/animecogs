import discord
from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
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
            "nichirin_color": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "last_daily": None,
            "slayer_points": 0,
            "form_levels": {},
            "last_hunt": None,
        }
        default_guild = {
            "event_channel": None,
            "last_event": None,
        }
        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)
        self.active_global_event = None
        self.event_task = None

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
        embed.add_field(name="Nichirin Blade", value=user_data["nichirin_color"], inline=False)
        embed.add_field(name="Rank", value=user_data["rank"], inline=True)
        embed.add_field(name="Demons Slayed", value=user_data["demons_slayed"], inline=True)
        embed.add_field(name="Experience", value=user_data["experience"], inline=True)
        
        forms = "\n".join([f"{form} (Level {user_data['form_levels'].get(form, 1)})" for form in user_data["known_forms"]])
        embed.add_field(name="Known Forms", value=forms, inline=False)

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
        victory = user_strength > strength

        if victory:
            xp_gained = strength // 2
            await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)
            await self.config.user(ctx.author).demons_slayed.set(user_data["demons_slayed"] + 1)
            embed.color = discord.Color.green()
            embed.description += f"\n\nVictory! You've defeated {demon} and gained {xp_gained} XP!"
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

    @ds.command(name="seteventchannel")
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

        self.active_global_event = {
            'channel_id': channel.id,
            'demon': demon,
            'strength': strength,
            'participants': [],
            'total_strength': 0,
            'embed': embed,
            'message': message,
            'start_time': datetime.now()
        }

        await asyncio.sleep(300)  # 5 minutes for the battle
        await self.conclude_event()

    async def join_global_event(self, ctx):
        if ctx.channel.id != self.active_global_event['channel_id']:
            return

        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        if ctx.author not in self.active_global_event['participants']:
            user_strength = user_data["experience"] + sum(user_data["form_levels"].values()) * 10
            self.active_global_event['participants'].append(ctx.author)
            self.active_global_event['total_strength'] += user_strength

            embed = self.active_global_event['embed']
            embed.set_field_at(1, name="Participants", value="\n".join([p.mention for p in self.active_global_event['participants']]) or "None yet")
            await self.active_global_event['message'].edit(embed=embed)

            await ctx.send(f"{ctx.author.mention} has joined the battle!", delete_after=5)
        else:
            await ctx.send(f"{ctx.author.mention}, you've already joined this battle!", delete_after=5)

    async def conclude_event(self):
        if not self.active_global_event:
            return

        victory = self.active_global_event['total_strength'] > self.active_global_event['strength']
        embed = self.active_global_event['embed']

        if victory:
            embed.color = discord.Color.green()
            embed.description = f"The {self.active_global_event['demon']} has been defeated!"
            xp_reward = self.active_global_event['strength'] // len(self.active_global_event['participants']) if self.active_global_event['participants'] else 0
            for participant in self.active_global_event['participants']:
                user_data = await self.config.user(participant).all()
                await self.config.user(participant).experience.set(user_data["experience"] + xp_reward)
                await self.config.user(participant).demons_slayed.set(user_data["demons_slayed"] + 1)
            embed.add_field(name="Reward", value=f"Each participant gains {xp_reward} XP and 1 demon slayed!")
        else:
            embed.color = discord.Color.red()
            embed.description = f"The {self.active_global_event['demon']} was too powerful and escaped..."

        channel = self.bot.get_channel(self.active_global_event['channel_id'])
        if channel:
            await channel.send(embed=embed)
        self.active_global_event = None

    @ds.command(name="hashira_training")
    @commands.cooldown(1, 1800, commands.BucketType.user)  # 30-minute cooldown
    async def hashira_training(self, ctx):
        """Undergo Hashira training for a chance at significant XP gain"""
        user_data = await self.config.user(ctx.author).all()
        
        if user_data["rank"] == "Hashira":
            await ctx.send("You are already a Hashira. Your training now focuses on mentoring others.")
            return

        embed = discord.Embed(title="Hashira Training", color=discord.Color.gold())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.description = f"{ctx.author.mention} begins intense Hashira training..."
        message = await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating training time

        success = random.random() < 0.4  # 40% success rate
        xp_gained = random.randint(100, 500) if success else random.randint(10, 50)

        await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)

        if success:
            embed.description += f"\n\nTraining successful! You gained {xp_gained} XP!"
            embed.color = discord.Color.green()
        else:
            embed.description += f"\n\nTraining was tough. You gained {xp_gained} XP. Keep trying!"
            embed.color = discord.Color.red()

        await message.edit(embed=embed)
        await self.check_rank_up(ctx)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000

        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            await self.config.user(ctx.author).rank.set(new_rank)
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
            await self.config.user(ctx.author).known_forms.set(known_forms)
            await self.config.user(ctx.author).form_levels.set({**user_data["form_levels"], new_form: 1})
            embed.add_field(name="New Form Learned!", value=f"You've learned {new_form}!")
        else:
            embed.add_field(name="Mastery", value="You've mastered all forms of your breathing technique!")

    @ds.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily reward"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        last_daily = user_data["last_daily"]
        now = datetime.now()
        if last_daily and datetime.fromisoformat(last_daily) + timedelta(days=1) > now:
            time_left = datetime.fromisoformat(last_daily) + timedelta(days=1) - now
            await ctx.send(f"{ctx.author.mention}, you can claim your next daily reward in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")
            return

        reward = random.randint(50, 100)
        await self.config.user(ctx.author).experience.set(user_data["experience"] + reward)
        await self.config.user(ctx.author).last_daily.set(now.isoformat())
        await ctx.send(f"{ctx.author.mention}, you've claimed your daily reward of {reward} XP!")
        await self.check_rank_up(ctx)

    def cog_unload(self):
        if self.event_task:
            self.event_task.cancel()

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
