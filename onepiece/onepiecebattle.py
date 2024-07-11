import discord
from redbot.core import commands, Config 
import random
import asyncio
from datetime import datetime, timedelta

class OnePieceBattle(commands.Cog):
    """One Piece Battle Simulation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        
        default_user = {
            "fighting_style": None,
            "devil_fruit": None,
            "haki": {
                "observation": 0,
                "armament": 0,
                "conquerors": 0
            },
            "doriki": 0,
            "bounty": 0,
            "battles_won": 0,
            "last_train": None,
            "stamina": 100
        }
        self.config.register_user(**default_user)
    
    @commands.group()
    async def op(self, ctx):
        """One Piece Battle Commands"""
    
    @op.command()
    async def begin(self, ctx):
        """Start your One Piece journey"""
        user_data = await self.config.user(ctx.author).all()
        
        if user_data["fighting_style"]:
            await ctx.send("You've already begun your journey!")
            return
        
        await ctx.send(f"{ctx.author.mention}, welcome to the world of One Piece! I am Gol D. Roger. Are you ready to start your journey and become the Pirate King? (React with ⚔️ to begin)")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '⚔️'
        
        try:
            await ctx.message.add_reaction('⚔️')
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, you took too long to decide. Come back when you're ready to start your journey!")
            return
        
        fighting_styles = ["Swordsman", "Martial Artist", "Sniper", "Brawler", "Tactician"]
        devil_fruits = ["Paramecia", "Zoan", "Logia", None]
        
        embed = discord.Embed(title="Character Creation", color=discord.Color.gold())
        embed.add_field(name="Fighting Styles", value="\n".join([f"{i+1}. {style}" for i, style in enumerate(fighting_styles)]), inline=False)  
        embed.add_field(name="Devil Fruits", value="\n".join([f"{i+1}. {fruit}" if fruit else f"{i+1}. No Devil Fruit" for i, fruit in enumerate(devil_fruits)]) or "None", inline=False)
        
        embed.set_footer(text="Type the number of your choices (e.g., 1 3 for Swordsman with Logia fruit)")
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, you took too long to decide. Come back when you're ready to start your journey!")
            return
        
        try:
            style_choice, fruit_choice = map(int, msg.content.split())
            style_choice -= 1
            fruit_choice -= 1
            if not (0 <= style_choice < len(fighting_styles) and 0 <= fruit_choice < len(devil_fruits)):
                raise ValueError
        except (ValueError, TypeError):
            await ctx.send(f"{ctx.author.mention}, invalid choices. Please try again and follow the instructions carefully.")
            return
        
        user_data["fighting_style"] = fighting_styles[style_choice]
        user_data["devil_fruit"] = devil_fruits[fruit_choice]
        user_data["doriki"] = 500
        user_data["bounty"] = 0
        await self.config.user(ctx.author).set(user_data)
        
        await ctx.send(f"{ctx.author.mention}, you have begun your journey as a {user_data['fighting_style']} {f'with the {user_data["devil_fruit"]} Devil Fruit' if user_data['devil_fruit'] else 'without a Devil Fruit'}! Your initial Doriki is {user_data['doriki']}. Train hard and make a name for yourself!")
    
    @op.command()
    async def profile(self, ctx, user: discord.Member = None):
        """View your or another user's profile"""
        user = user or ctx.author
        user_data = await self.config.user(user).all()
        
        if not user_data["fighting_style"]:
            await ctx.send(f"{user.mention} has not begun their One Piece journey yet!")
            return
        
        embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.blue())
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Fighting Style", value=user_data["fighting_style"])
        embed.add_field(name="Devil Fruit", value=user_data["devil_fruit"] or "None")
        embed.add_field(name="Haki", value="\n".join([f"{k.capitalize()}: {v}" for k, v in user_data["haki"].items()]), inline=False)
        embed.add_field(name="Doriki", value=user_data["doriki"])
        embed.add_field(name="Bounty", value=f"{user_data['bounty']:,}")
        embed.add_field(name="Battles Won", value=user_data["battles_won"])
        
        await ctx.send(embed=embed)
    
    @op.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def train(self, ctx, stat: str):
        """Train a specific stat"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        valid_stats = ["doriki", "observation", "armament", "conquerors"]
        if stat not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return
        
        if user_data["stamina"] < 10:
            await ctx.send("You're too tired to train right now. Rest up and come back later!")
            return
                       
        if stat == "doriki":
            gain = random.randint(10, 50)
        else:
            gain = random.randint(1, 5)
        
        if stat == "doriki":
            user_data["doriki"] += gain
        else:
            user_data["haki"][stat] += gain
        
        user_data["stamina"] -= 10
        user_data["last_train"] = datetime.now().isoformat()        
        await self.config.user(ctx.author).set(user_data)
        
        await ctx.send(f"You trained your {stat} and gained {gain} points!")
        
    @op.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def battle(self, ctx, opponent: discord.Member):
        """Challenge another player to a battle"""
        user_data = await self.config.user(ctx.author).all()
        opponent_data = await self.config.user(opponent).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        if not opponent_data["fighting_style"]:
            await ctx.send(f"{opponent.mention} has not begun their journey yet!")
            return
        
        if user_data["stamina"] < 20:
            await ctx.send("You're too tired to battle right now. Rest up and come back later!")
            return
        
        if opponent_data["stamina"] < 20:
            await ctx.send(f"{opponent.mention} is too tired to battle right now.")
            return
        
        await ctx.send(f"{opponent.mention}, {ctx.author.mention} has challenged you to a battle! React with ⚔️ to accept or 🏳️ to decline.")
        
        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ['⚔️', '🏳️']
        
        try:
            await ctx.message.add_reaction('⚔️')
            await ctx.message.add_reaction('🏳️')
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{opponent.mention} did not respond to the challenge.")
            return
        
        if str(reaction.emoji) == '🏳️':
            await ctx.send(f"{opponent.mention} declined the challenge.")
            return
        
        await ctx.send(f"Let the battle between {ctx.author.mention} and {opponent.mention} begin!")
        
        user_strength = user_data["doriki"] + sum(user_data["haki"].values())
        opp_strength = opponent_data["doriki"] + sum(opponent_data["haki"].values())
        
        if user_data["devil_fruit"] == "Logia":
            user_strength *= 1.2
        if opponent_data["devil_fruit"] == "Logia":
            opp_strength *= 1.2
        
        user_roll = random.randint(1, 20)
        opp_roll = random.randint(1, 20)
        
        user_total = user_strength + user_roll
        opp_total = opp_strength + opp_roll
        
        if user_total > opp_total:
            winner = ctx.author
            loser = opponent
        elif opp_total > user_total:
            winner = opponent
            loser = ctx.author
        else:
            await ctx.send("The battle ended in a draw!")
            return
        
        winner_data = await self.config.user(winner).all()
        loser_data = await self.config.user(loser).all()
        
        doriki_gain = random.randint(50, 100)
        haki_gain = random.randint(1, 10)
        bounty_gain = loser_data["bounty"] // 10
        
        winner_data["doriki"] += doriki_gain
        winner_data["haki"]["observation"] += haki_gain
        winner_data["haki"]["armament"] += haki_gain
        winner_data["haki"]["conquerors"] += haki_gain // 2
        winner_data["bounty"] += bounty_gain
        winner_data["battles_won"] += 1
        winner_data["stamina"] -= 20
        
        loser_data["stamina"] -= 20
        
        await self.config.user(winner).set(winner_data)
        await self.config.user(loser).set(loser_data)
        
        await ctx.send(f"{winner.mention} has defeated {loser.mention} in battle! They gain {doriki_gain} Doriki, {haki_gain} Haki, and {bounty_gain:,} bounty!")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.0f} seconds.")

def setup(bot):
    bot.add_cog(OnePieceBattle(bot))