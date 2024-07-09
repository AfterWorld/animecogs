import random
from redbot.core import commands, checks, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import discord
import asyncio

class Kaiju8Game(commands.Cog):
    """A Kaiju #8 themed game cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8991100, force_registration=True)
        default_user = {
            "level": 1,
            "exp": 0,
            "kaiju_form": False,
            "cooldowns": {},
        }
        self.config.register_user(**default_user)

    @commands.group()
    async def kaiju8(self, ctx):
        """Kaiju #8 game commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Type `[p]help kaiju8` for more info.")

    @kaiju8.command()
    async def status(self, ctx):
        """Check your Kaiju #8 game status"""
        user_data = await self.config.user(ctx.author).all()
        embed = discord.Embed(title=f"{ctx.author.name}'s Kaiju #8 Status", color=discord.Color.blue())
        embed.add_field(name="Level", value=user_data['level'])
        embed.add_field(name="EXP", value=user_data['exp'])
        embed.add_field(name="Kaiju Form", value="Active" if user_data['kaiju_form'] else "Inactive")
        await ctx.send(embed=embed)

    @kaiju8.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour cooldown
    async def transform(self, ctx):
        """Transform into your Kaiju form"""
        user_data = await self.config.user(ctx.author).all()
        if user_data['kaiju_form']:
            await ctx.send("You're already in Kaiju form!")
        else:
            await self.config.user(ctx.author).kaiju_form.set(True)
            await ctx.send(f"{ctx.author.mention} transforms into a terrifying Kaiju! Your powers have awakened.")

    @kaiju8.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)  # 30 minutes cooldown
    async def fight(self, ctx):
        """Engage in a fight with a random Kaiju"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data['kaiju_form']:
            await ctx.send("You need to transform first! Use `[p]kaiju8 transform`")
            return

        kaiju_names = ["Daikaiju", "Honju", "Riju", "Tero", "Hikari"]
        enemy = random.choice(kaiju_names)
        player_hp = user_data['level'] * 10
        enemy_hp = random.randint(50, 100)

        embed = discord.Embed(title=f"Battle: {ctx.author.name} vs {enemy}", color=discord.Color.red())
        embed.add_field(name=f"{ctx.author.name}", value=f"HP: {player_hp}")
        embed.add_field(name=enemy, value=f"HP: {enemy_hp}")
        message = await ctx.send(embed=embed)

        while player_hp > 0 and enemy_hp > 0:
            player_dmg = random.randint(5, 15) + user_data['level']
            enemy_dmg = random.randint(5, 15)

            enemy_hp -= player_dmg
            player_hp -= enemy_dmg

            embed.set_field_at(0, name=f"{ctx.author.name}", value=f"HP: {max(0, player_hp)}")
            embed.set_field_at(1, name=enemy, value=f"HP: {max(0, enemy_hp)}")
            await message.edit(embed=embed)
            await asyncio.sleep(2)

        if player_hp > 0:
            exp_gain = random.randint(10, 50)
            await self.config.user(ctx.author).exp.set(user_data['exp'] + exp_gain)
            await ctx.send(f"You defeated {enemy}! Gained {exp_gain} EXP.")
            await self._check_levelup(ctx)
        else:
            await ctx.send(f"{enemy} has defeated you! Rest and try again later.")

        await self.config.user(ctx.author).kaiju_form.set(False)

    async def _check_levelup(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        exp_needed = user_data['level'] * 100
        if user_data['exp'] >= exp_needed:
            await self.config.user(ctx.author).level.set(user_data['level'] + 1)
            await self.config.user(ctx.author).exp.set(user_data['exp'] - exp_needed)
            await ctx.send(f"Congratulations {ctx.author.mention}! You've leveled up to level {user_data['level'] + 1}!")

    @kaiju8.command()
    @commands.cooldown(1, 43200, commands.BucketType.user)  # 12 hour cooldown
    async def mission(self, ctx):
        """Embark on a Defense Force mission"""
        scenarios = [
            "A Kaiju is attacking Tokyo! Defend the city and minimize casualties.",
            "Investigate strange readings in Osaka Bay. Could it be a new Kaiju?",
            "Train new Defense Force recruits in anti-Kaiju tactics.",
            "Assist in the development of new anti-Kaiju weaponry.",
            "Contain a Kaiju outbreak in a rural area before it spreads."
        ]
        mission = random.choice(scenarios)
        embed = discord.Embed(title="Defense Force Mission", description=mission, color=discord.Color.green())
        await ctx.send(embed=embed)

        await asyncio.sleep(5)  # Simulating mission time

        success = random.choice([True, False])
        if success:
            exp_gain = random.randint(50, 100)
            user_data = await self.config.user(ctx.author).all()
            await self.config.user(ctx.author).exp.set(user_data['exp'] + exp_gain)
            await ctx.send(f"Mission successful! You gained {exp_gain} EXP.")
            await self._check_levelup(ctx)
        else:
            await ctx.send("Mission failed. Better luck next time!")

async def setup(bot):
    await bot.add_cog(Kaiju8Game(bot))
