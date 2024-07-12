import discord
from redbot.core import commands, Config
import random
import asyncio
import datetime

class OnePieceBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.spawn_channel_id = None

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
            "level": 1,
            "experience": 0,
            "stamina": 100,
            "skill_points": 0,
            "strength": 0,
            "speed": 0,
            "defense": 0,
        }
        self.config.register_user(**default_user)

        self.devil_fruits = {
            "Gomu Gomu no Mi": {
                "ability": "Elasticity",
                "modifier": 1.2
            },
            "Mera Mera no Mi": {
                "ability": "Fire Control",
                "modifier": 1.3
            },
            "Hie Hie no Mi": {
                "ability": "Ice Control",
                "modifier": 1.3
            },
            "Pika Pika no Mi": {
                "ability": "Light Manipulation",
                "modifier": 1.4
            },
            "Gura Gura no Mi": {
                "ability": "Earthquake Generation",
                "modifier": 1.5
            },
            "Yami Yami no Mi": {
                "ability": "Darkness Manipulation",
                "modifier": 1.4
            },
            "Suna Suna no Mi": {
                "ability": "Sand Control",
                "modifier": 1.3
            },
            "Magu Magu no Mi": {
                "ability": "Magma Control",
                "modifier": 1.4
            }
        }

        self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn(self.spawn_channel_id))

    def cog_unload(self):
        self.spawn_task.cancel()

    async def devil_fruit_spawn(self, channel_id):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(3600, 7200))  # Random spawn time between 1-2 hours
            channel = self.bot.get_channel(channel_id)
            if channel:
                devil_fruit = random.choice(list(self.devil_fruits.keys()))
                embed = discord.Embed(
                    title="Devil Fruit Spawn!",
                    description=f"A {devil_fruit} has spawned in this channel! React with 🍎 to claim it!",
                    color=discord.Color.gold()
                )
                message = await channel.send(embed=embed)
                await message.add_reaction("🍎")

                def check(reaction, user):
                    return str(reaction.emoji) == "🍎" and user != self.bot.user

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await message.delete()
                else:
                    user_data = await self.config.user(user).all()
                    if user_data["devil_fruit"]:
                        await channel.send(f"{user.mention}, you already have a Devil Fruit!")
                    else:
                        user_data["devil_fruit"] = devil_fruit
                        await self.config.user(user).set(user_data)
                        await channel.send(f"Congratulations {user.mention}! You have claimed the {devil_fruit}!")

    @commands.group()
    async def op(self, ctx):
        pass
    
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

        embed = discord.Embed(title="Character Creation", color=discord.Color.gold())
        embed.add_field(name="Fighting Styles", value="\n".join([f"{i+1}. {style}" for i, style in enumerate(fighting_styles)]), inline=False)

        embed.set_footer(text="Type the number of your fighting style choice")

        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, you took too long to decide. Come back when you're ready to start your journey!")
            return

        try:
            style_choice = int(msg.content) - 1
            if not (0 <= style_choice < len(fighting_styles)):
                raise ValueError
        except (ValueError, TypeError):
            await ctx.send(f"{ctx.author.mention}, invalid choice. Please try again and follow the instructions carefully.")
            return

        user_data["fighting_style"] = fighting_styles[style_choice]
        user_data["doriki"] = 500
        user_data["bounty"] = 0
        await self.config.user(ctx.author).set(user_data)

        await ctx.send(f"{ctx.author.mention}, you have begun your journey as a {user_data['fighting_style']}! Your initial Doriki is {user_data['doriki']}. Train hard and make a name for yourself!")

    @commands.command()
    @commands.is_owner()
    async def set_devil_fruit_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for Devil Fruit spawns"""
        self.spawn_channel_id = channel.id
        await ctx.send(f"Devil Fruits will now spawn in {channel.mention}")
        if self.spawn_task:
            self.spawn_task.cancel()
        self.spawn_task = self.bot.loop.create_task(self.devil_fruit_spawn(self.spawn_channel_id))
    
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
    async def allocate(self, ctx, stat: str, points: int):
        """Allocate skill points to a specific stat"""
        user_data = await self.config.user(ctx.author).all()
        valid_stats = ["strength", "speed", "defense", "haki"]
        
        if stat not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return

        if points <= 0 or points > user_data["skill_points"]:
            await ctx.send("Invalid number of points. You don't have enough skill points.")
            return

        user_data[stat] += points
        user_data["skill_points"] -= points
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You have allocated {points} points to {stat}.")

    @op.command()
    async def skill_tree(self, ctx):
        """View your skill tree"""
        user_data = await self.config.user(ctx.author).all()
        
        embed = discord.Embed(title=f"{ctx.author.name}'s Skill Tree", color=discord.Color.green())
        embed.add_field(name="Skill Points", value=user_data["skill_points"], inline=False)
        
        for stat in ["strength", "speed", "defense", "haki"]:
            embed.add_field(name=stat.capitalize(), value=user_data[stat], inline=True)
        
        await ctx.send(embed=embed)

    @op.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def train(self, ctx, stat: str):
        """Train a specific stat"""
        user_data = await self.config.user(ctx.author).all()

        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return

        valid_stats = ["doriki", "haki"]
        if stat not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return

        if user_data["stamina"] < 10:
            await ctx.send("You're too tired to train right now. Rest up and come back later!")
            return

        exp_gain = random.randint(10, 50)
        user_data["experience"] += exp_gain

        if user_data["experience"] >= user_data["level"] * 100:
            user_data["level"] += 1
            user_data["skill_points"] += 2
            await ctx.send(f"Congratulations! You have reached level {user_data['level']}. You have gained 2 skill points.")

        if stat == "doriki":
            gain = random.randint(10, 50)
            user_data["doriki"] += gain
        else:  # haki
            gain = random.randint(1, 5)
            user_data["haki"]["observation"] += gain
            user_data["haki"]["armament"] += gain
            user_data["haki"]["conquerors"] += gain // 2

        user_data["stamina"] -= 10
        user_data["last_train"] = datetime.now().isoformat()
        await self.config.user(ctx.author).set(user_data)

        await ctx.send(f"You trained your {stat} and gained {gain} points!")
        
    @op.command()
    async def devil_fruit_info(self, ctx, *, devil_fruit: str):
        """Get information about a specific Devil Fruit"""
        if devil_fruit not in self.devil_fruits:
            await ctx.send("Invalid Devil Fruit. Please provide a valid Devil Fruit name.")
            return

        fruit_info = self.devil_fruits[devil_fruit]
        embed = discord.Embed(title=devil_fruit, color=discord.Color.blue())
        embed.add_field(name="Ability", value=fruit_info["ability"], inline=False)
        embed.add_field(name="Strength Modifier", value=fruit_info["modifier"], inline=False)

        await ctx.send(embed=embed)
        
    @op.command()
    async def leaderboard(self, ctx, criteria: str = "bounty"):
        """Display the leaderboard based on the specified criteria"""
        valid_criteria = ["bounty", "wins", "level", "doriki"]
        if criteria not in valid_criteria:
            await ctx.send(f"Invalid criteria. Please choose one of: {', '.join(valid_criteria)}")
            return

        users = await self.config.all_users()
        
        if criteria == "bounty":
            leaderboard = sorted(users.items(), key=lambda x: x[1]["bounty"], reverse=True)
        elif criteria == "wins":
            leaderboard = sorted(users.items(), key=lambda x: x[1]["battles_won"], reverse=True)
        elif criteria == "level":
            leaderboard = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)
        else:  # doriki
            leaderboard = sorted(users.items(), key=lambda x: x[1]["doriki"], reverse=True)

        top_10 = leaderboard[:10]

        embed = discord.Embed(title=f"Leaderboard - Top 10 ({criteria.capitalize()})", color=discord.Color.gold())
        
        if not top_10:
            embed.description = "No users found."
        else:
            for i, (user_id, user_data) in enumerate(top_10, start=1):
                user = self.bot.get_user(user_id)
                if user:
                    value = user_data["bounty"] if criteria == "bounty" else user_data["battles_won"] if criteria == "wins" else user_data["level"] if criteria == "level" else user_data["doriki"]
                    embed.add_field(name=f"{i}. {user.name}", value=value, inline=False)

        await ctx.send(embed=embed)

    @op.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)
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

        challenge_embed = discord.Embed(
            title=f"{ctx.author.name} challenges {opponent.name} to a battle!",
            description=f"{opponent.mention}, react with ⚔️ to accept or 🏳️ to decline.",
            color=discord.Color.blue()
        )
        challenge_message = await ctx.send(embed=challenge_embed)
        await challenge_message.add_reaction('⚔️')
        await challenge_message.add_reaction('🏳️')

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ['⚔️', '🏳️'] and reaction.message == challenge_message

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Challenge Expired",
                description=f"{opponent.mention} did not respond to the challenge.",
                color=discord.Color.red()
            )
            await challenge_message.edit(embed=timeout_embed)
            return

        if str(reaction.emoji) == '🏳️':
            decline_embed = discord.Embed(
                title="Challenge Declined",
                description=f"{opponent.mention} declined the challenge.",
                color=discord.Color.red()
            )
            await challenge_message.edit(embed=decline_embed)
            return

        battle_embed = discord.Embed(
            title=f"Battle: {ctx.author.name} vs {opponent.name}",
            description="The battle begins!",
            color=discord.Color.green()
        )
        battle_message = await ctx.send(embed=battle_embed)

        user_strength = user_data["doriki"] + sum(user_data["haki"].values())
        opp_strength = opponent_data["doriki"] + sum(opponent_data["haki"].values())

        if user_data["devil_fruit"] in self.devil_fruits:
            user_strength *= self.devil_fruits[user_data["devil_fruit"]]["modifier"]
            battle_embed.add_field(name=f"{ctx.author.name}'s Devil Fruit", value=user_data["devil_fruit"], inline=False)
        if opponent_data["devil_fruit"] in self.devil_fruits:
            opp_strength *= self.devil_fruits[opponent_data["devil_fruit"]]["modifier"]
            battle_embed.add_field(name=f"{opponent.name}'s Devil Fruit", value=opponent_data["devil_fruit"], inline=False)

        await battle_message.edit(embed=battle_embed)
        await asyncio.sleep(2)

        turns = random.randint(2, 5)
        for turn in range(1, turns + 1):
            user_attack = random.randint(1, user_strength)
            opp_attack = random.randint(1, opp_strength)

            battle_embed.add_field(name=f"Turn {turn}", value=f"{ctx.author.name} attacks with {user_attack} power!\n{opponent.name} attacks with {opp_attack} power!", inline=False)
            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(2)

            if user_attack > opp_attack:
                opp_strength -= user_attack - opp_attack
            elif opp_attack > user_attack:
                user_strength -= opp_attack - user_attack

        if user_strength > opp_strength:
            winner = ctx.author
            loser = opponent
        elif opp_strength > user_strength:
            winner = opponent
            loser = ctx.author
        else:
            draw_embed = discord.Embed(
                title="Battle Ended",
                description="The battle ended in a draw!",
                color=discord.Color.gold()
            )
            await battle_message.edit(embed=draw_embed)
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

        result_embed = discord.Embed(
            title="Battle Result",
            description=f"{winner.mention} has defeated {loser.mention} in battle!",
            color=discord.Color.gold()
        )
        result_embed.add_field(name="Doriki Gained", value=doriki_gain)
        result_embed.add_field(name="Haki Gained", value=haki_gain)
        result_embed.add_field(name="Bounty Gained", value=f"{bounty_gain:,}")
        await battle_message.edit(embed=result_embed)
        
def setup(bot):
    bot.add_cog(OnePieceBattle(bot))
