import discord
from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import box, pagify
import random
import asyncio
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
            "last_daily": None,
            "slayer_points": 0,
        }
        default_guild = {
            "active_event": None,
            "event_end_time": None,
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

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""
        if ctx.invoked_subcommand is None:
            # Remove or comment out the following line:
            # await ctx.send_help(ctx.command)
            pass  # Do nothing if no subcommand is invoked

    @ds.command(name="start")
    async def start_journey(self, ctx):
        """Begin your journey as a Demon Slayer"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you've already begun your journey!")
            return
    
        technique = random.choice(list(self.breathing_techniques.keys()))
        color = random.choice(["Red", "Blue", "Green", "Yellow", "Purple", "Black"])
        first_form = random.choice(self.breathing_techniques[technique])
        
        await self.config.user(ctx.author).breathing_technique.set(technique)
        await self.config.user(ctx.author).nichirin_color.set(color)
        await self.config.user(ctx.author).known_forms.set([first_form])
    
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
        embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"], inline=False)
        embed.add_field(name="Nichirin Blade", value=user_data["nichirin_color"], inline=False)
        embed.add_field(name="Rank", value=user_data["rank"], inline=True)
        embed.add_field(name="Demons Slayed", value=user_data["demons_slayed"], inline=True)
        embed.add_field(name="Experience", value=user_data["experience"], inline=True)
        embed.add_field(name="Known Forms", value="\n".join(user_data["known_forms"]), inline=False)
    
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

        await ctx.send(f"{ctx.author.mention} trains intensively and gains {xp_gained} experience!")
        
        # Chance to learn a new form
        if random.random() < 0.2:  # 20% chance to learn a new form
            await self.learn_new_form(ctx)
        
        await self.check_rank_up(ctx)

    async def learn_new_form(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data["breathing_technique"]
        known_forms = user_data["known_forms"]
        all_forms = self.breathing_techniques[technique]
        
        unknown_forms = [form for form in all_forms if form not in known_forms]
        
        if unknown_forms:
            new_form = random.choice(unknown_forms)
            known_forms.append(new_form)
            await self.config.user(ctx.author).known_forms.set(known_forms)
            await ctx.send(f"Breakthrough! {ctx.author.mention} has learned a new form: **{new_form}**!")
        else:
            await ctx.send(f"{ctx.author.mention} has mastered all forms of {technique} Breathing!")

    @ds.command(name="slay")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def slay_demon(self, ctx):
        """Attempt to slay a demon"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["breathing_technique"]:
            await ctx.send(f"{ctx.author.mention}, you need to start your journey first!")
            return

        demon, info = random.choice(list(self.demons.items()))
        success_rate = random.randint(1, 100)

        await ctx.send(f"{ctx.author.mention} encounters {demon}! The battle begins...")
        await asyncio.sleep(2)

        if success_rate > info["difficulty"]:
            xp_gained = info["xp"]
            await self.config.user(ctx.author).demons_slayed.set(user_data["demons_slayed"] + 1)
            await self.config.user(ctx.author).experience.set(user_data["experience"] + xp_gained)
            await ctx.send(f"Victory! {ctx.author.mention} has successfully slain {demon} and gained {xp_gained} XP!")
            await self.check_rank_up(ctx)
            await self.check_new_form(ctx)
        else:
            await ctx.send(f"Oh no! {demon} was too powerful. {ctx.author.mention} needs to train harder!")

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000

        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            await self.config.user(ctx.author).rank.set(new_rank)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")

    async def check_new_form(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data["breathing_technique"]
        known_forms = user_data["known_forms"]
        all_forms = self.breathing_techniques[technique]

        if len(known_forms) < len(all_forms):
            chance = random.random()
            if chance < 0.1:  # 10% chance to learn a new form
                new_form = random.choice([form for form in all_forms if form not in known_forms])
                known_forms.append(new_form)
                await self.config.user(ctx.author).known_forms.set(known_forms)
                await ctx.send(f"Breakthrough! {ctx.author.mention} has learned a new form: **{new_form}**!")

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

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
