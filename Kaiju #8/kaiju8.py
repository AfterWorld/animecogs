import random
from redbot.core import commands, checks, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import discord
import asyncio

class Kaiju8Game(commands.Cog):
    """A Kaiju #8 themed Defense Force game cog"""

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
        }
        self.config.register_user(**default_user)

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

        # 5% chance of being a Kaiju
        is_kaiju = random.random() < 0.05
        await self.config.user(ctx.author).is_kaiju.set(is_kaiju)
        
        await ctx.send(f"Welcome to the Defense Force, {ctx.author.mention}! Your training begins now.")

    @df.command()
    async def status(self, ctx):
        """Check your Defense Force status"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(title=f"{ctx.author.name}'s Defense Force Status", color=discord.Color.blue())
        embed.add_field(name="Rank", value=user_data['rank'])
        embed.add_field(name="EXP", value=user_data['exp'])
        embed.add_field(name="Missions Completed", value=user_data['missions_completed'])
        embed.add_field(name="Strength", value=user_data['strength'])
        embed.add_field(name="Agility", value=user_data['agility'])
        embed.add_field(name="Intelligence", value=user_data['intelligence'])
        if user_data['kaiju_revealed']:
            embed.add_field(name="Special Ability", value="Kaiju Transformation")
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
            
            await self._check_rankup(ctx)
        else:
            await ctx.send("Mission failed. Better luck next time!")

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

    @df.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def transform(self, ctx):
        """Attempt to transform into Kaiju form (if you have the ability)"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data['kaiju_revealed']:
            await ctx.send("You don't have the ability to transform into a Kaiju.")
            return

        success = random.random() < 0.5  # 50% chance of successful transformation
        if success:
            await ctx.send(f"{ctx.author.mention} successfully transforms into Kaiju #8! Your power is overwhelming, but remember to use it responsibly.")
        else:
            await ctx.send(f"{ctx.author.mention} attempts to transform, but fails. It seems your Kaiju powers are still unstable.")

async def setup(bot):
    await bot.add_cog(Kaiju8Game(bot))
