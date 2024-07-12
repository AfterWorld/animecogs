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
            "strength": 1,  # Changed from 0 to 1
            "speed": 1,     # Changed from 0 to 1
            "defense": 1,   # Changed from 0 to 1
            "learned_techniques": [],
            "equipped_items": []
        }
        self.config.register_user(**default_user)

        self.devil_fruits = {
            "Gomu Gomu no Mi": {"ability": "Elasticity", "modifier": 1.2},
            "Mera Mera no Mi": {"ability": "Fire Control", "modifier": 1.3},
            "Hie Hie no Mi": {"ability": "Ice Control", "modifier": 1.3},
            "Pika Pika no Mi": {"ability": "Light Manipulation", "modifier": 1.4},
            "Gura Gura no Mi": {"ability": "Earthquake Generation", "modifier": 1.5},
            "Yami Yami no Mi": {"ability": "Darkness Manipulation", "modifier": 1.4},
            "Suna Suna no Mi": {"ability": "Sand Control", "modifier": 1.3},
            "Magu Magu no Mi": {"ability": "Magma Control", "modifier": 1.4}
        }

        self.techniques = {
            "Swordsman": ["Three Sword Style", "Flying Slash Attack", "Lion's Song"],
            "Martial Artist": ["Shigan", "Tekkai", "Rankyaku"],
            "Sniper": ["Exploding Star", "Lead Star", "Fire Bird Star"],
            "Brawler": ["Gomu Gomu no Pistol", "Gomu Gomu no Bazooka", "Gear Second"],
            "Tactician": ["Mirage Tempo", "Thunderbolt Tempo", "Weather Egg"]
        }

        self.equipment = {
            "Sword": {"strength": 20, "speed": 10},
            "Gun": {"strength": 15, "speed": 15},
            "Armor": {"defense": 30},
            "Boots": {"speed": 20},
            "Gloves": {"strength": 10, "speed": 10}
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
    async def reset(self, ctx, user: discord.Member = None):
        """Reset your own data or the data of a specific user (admin only)"""
        if user is None:
            user = ctx.author
        elif not ctx.author.guild_permissions.administrator:
            await ctx.send("You need administrator permissions to reset someone else's data.")
            return
    
        await ctx.send(f"Are you sure you want to reset {'your' if user == ctx.author else user.mention + 's'} One Piece battle data? This action cannot be undone. React with ✅ to confirm.")
        
        def check(reaction, user_react):
            return user_react == ctx.author and str(reaction.emoji) == '✅'
    
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Data reset canceled due to inactivity.")
            return
    
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
    
    @op.command(name="view_techniques")
    async def op_view_techniques(self, ctx):
        """View available techniques for your fighting style"""
        user_data = await self.config.user(ctx.author).all()
        fighting_style = user_data["fighting_style"]
        
        if not fighting_style:
            await ctx.send("You need to begin your journey first!")
            return
        
        available_techniques = self.techniques.get(fighting_style, [])
        learned_techniques = user_data["learned_techniques"]
        
        embed = discord.Embed(title=f"Techniques for {fighting_style}", color=discord.Color.blue())
        for technique in available_techniques:
            status = "Learned" if technique in learned_techniques else "Not Learned"
            embed.add_field(name=technique, value=status, inline=False)
        
        await ctx.send(embed=embed)

    @op.command(name="view_equipment")
    async def op_view_equipment(self, ctx):
        """View available equipment and their stats"""
        embed = discord.Embed(title="Available Equipment", color=discord.Color.green())
        for item, stats in self.equipment.items():
            stat_string = ", ".join([f"{stat}: {value}" for stat, value in stats.items()])
            embed.add_field(name=item, value=stat_string, inline=False)
        
        await ctx.send(embed=embed)

    @op.command(name="learn_technique")
    async def op_learn_technique(self, ctx, *, technique_name: str):
        """Learn a new technique"""
        user_data = await self.config.user(ctx.author).all()
        fighting_style = user_data["fighting_style"]
        
        if not fighting_style:
            await ctx.send("You need to begin your journey first!")
            return
        
        if technique_name not in self.techniques[fighting_style]:
            await ctx.send(f"That technique is not available for your fighting style.")
            return
        
        if technique_name in user_data["learned_techniques"]:
            await ctx.send("You've already learned this technique.")
            return
        
        user_data["learned_techniques"].append(technique_name)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've learned the {technique_name} technique!")

    @op.command(name="equip")
    async def op_equip(self, ctx, *, item: str):
        """Equip an item"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        if item not in self.equipment:
            await ctx.send("That item doesn't exist.")
            return
        
        if len(user_data["equipped_items"]) >= 3:
            await ctx.send("You can't equip more than 3 items. Unequip something first.")
            return
        
        user_data["equipped_items"].append(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've equipped the {item}!")

    @op.command(name="unequip")
    async def op_unequip(self, ctx, *, item: str):
        """Unequip an item"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return
        
        if item not in user_data["equipped_items"]:
            await ctx.send("You don't have that item equipped.")
            return
        
        user_data["equipped_items"].remove(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've unequipped the {item}.")

    @op.command(name="rest")
    async def op_rest(self, ctx):
        """Rest to recover stamina"""
        user_data = await self.config.user(ctx.author).all()
        stamina_gain = random.randint(20, 40)
        user_data["stamina"] = min(100, user_data["stamina"] + stamina_gain)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You rested and recovered {stamina_gain} stamina. Current stamina: {user_data['stamina']}")

    @op.command(name="battle")
    async def op_battle(self, ctx, opponent: discord.Member = None):
        """Start a battle with another user or a strong AI opponent"""
        user_data = await self.config.user(ctx.author).all()

        if not user_data["fighting_style"]:
            await ctx.send("You need to begin your journey first!")
            return

        if opponent:
            opponent_data = await self.config.user(opponent).all()
            if not opponent_data["fighting_style"]:
                await ctx.send(f"{opponent.mention} has not begun their journey yet!")
                return
        else:
            # Create a strong AI opponent
            ai_names = ["Admiral Akainu", "Yonko Kaido", "Shichibukai Doflamingo", "CP0 Rob Lucci", "Revolutionary Dragon"]
            opponent_name = random.choice(ai_names)
            opponent = ctx.author  # This is just to reuse the existing logic
            opponent_data = {
                "name": opponent_name,
                "fighting_style": random.choice(list(self.techniques.keys())),
                "devil_fruit": random.choice(list(self.devil_fruits.keys())),
                "haki": {
                    "observation": random.randint(50, 100),
                    "armament": random.randint(50, 100),
                    "conquerors": random.randint(30, 80)
                },
                "doriki": random.randint(1000, 2000),
                "strength": random.randint(100, 200),
                "speed": random.randint(100, 200),
                "defense": random.randint(100, 200),
                "learned_techniques": random.sample(self.techniques[random.choice(list(self.techniques.keys()))], 5),
                "equipped_items": random.sample(list(self.equipment.keys()), 3),
                "stamina": 150,
                "bounty": random.randint(500000000, 1500000000)
            }

        battle_embed = discord.Embed(
            title=f"Epic Battle: {ctx.author.name} vs {opponent_data['name'] if 'name' in opponent_data else opponent.name}",
            description="The battle begins! ⚔️",
            color=discord.Color.red()
        )

        user_strength = max(1, user_data["doriki"] + sum(user_data["haki"].values()) + user_data["strength"])
        opp_strength = max(1, opponent_data["doriki"] + sum(opponent_data["haki"].values()) + opponent_data["strength"])

        # Calculate HP based on strength
        user_hp = user_strength * 20
        opp_hp = opp_strength * 20

        # Apply equipment bonuses
        for item in user_data["equipped_items"]:
            for stat, value in self.equipment[item].items():
                if stat == "strength":
                    user_strength += value
                elif stat == "speed":
                    user_data["speed"] += value
                elif stat == "defense":
                    user_data["defense"] += value

        for item in opponent_data["equipped_items"]:
            for stat, value in self.equipment[item].items():
                if stat == "strength":
                    opp_strength += value
                elif stat == "speed":
                    opponent_data["speed"] += value
                elif stat == "defense":
                    opponent_data["defense"] += value

        if user_data["devil_fruit"] in self.devil_fruits:
            user_strength = int(user_strength * self.devil_fruits[user_data["devil_fruit"]]["modifier"])
            battle_embed.add_field(name=f"{ctx.author.name}'s Devil Fruit", value=user_data["devil_fruit"], inline=True)
        if opponent_data["devil_fruit"] in self.devil_fruits:
            opp_strength = int(opp_strength * self.devil_fruits[opponent_data["devil_fruit"]]["modifier"])
            battle_embed.add_field(name=f"{opponent_data['name'] if 'name' in opponent_data else opponent.name}'s Devil Fruit", value=opponent_data["devil_fruit"], inline=True)

        battle_log = []
        battle_message = await ctx.send(embed=battle_embed)

        def get_health_bar(current_hp, max_hp, bar_length=20):
            fill = int(current_hp / max_hp * bar_length)
            return f"[{'■' * fill}{'□' * (bar_length - fill)}]"

        async def update_battle_embed():
            battle_embed.description = "\n".join(battle_log[-5:])
            user_health = get_health_bar(user_hp, user_strength * 20)
            opp_health = get_health_bar(opp_hp, opp_strength * 20)
            battle_embed.set_field_at(0, name=f"{ctx.author.name}'s HP", value=f"{user_health} {user_hp:.0f}/{user_strength * 20:.0f}", inline=False)
            battle_embed.set_field_at(1, name=f"{opponent_data['name'] if 'name' in opponent_data else opponent.name}'s HP", value=f"{opp_health} {opp_hp:.0f}/{opp_strength * 20:.0f}", inline=False)
            await battle_message.edit(embed=battle_embed)

        battle_embed.add_field(name=f"{ctx.author.name}'s HP", value="", inline=False)
        battle_embed.add_field(name=f"{opponent_data['name'] if 'name' in opponent_data else opponent.name}'s HP", value="", inline=False)

        turns = random.randint(5, 10)
        for turn in range(1, turns + 1):
            user_technique = random.choice(user_data["learned_techniques"]) if user_data["learned_techniques"] else "Basic Attack"
            opp_technique = random.choice(opponent_data["learned_techniques"]) if opponent_data["learned_techniques"] else "Basic Attack"
            
            user_attack = random.randint(1, max(1, int(user_strength))) * (1.5 if user_technique != "Basic Attack" else 1)
            opp_attack = random.randint(1, max(1, int(opp_strength))) * (1.5 if opp_technique != "Basic Attack" else 1)

            # Critical hit chance (10%)
            if random.random() < 0.1:
                user_attack *= 2
                battle_log.append(f"💥 Critical Hit! {ctx.author.name} lands a devastating blow!")

            # Dodge chance (based on speed)
            total_speed = max(1, user_data["speed"] + opponent_data["speed"])
            user_dodge_chance = user_data["speed"] / total_speed
            if random.random() < user_dodge_chance:
                opp_attack = 0
                battle_log.append(f"💨 {ctx.author.name} swiftly dodges the attack!")

            # Apply damage
            opp_hp -= user_attack
            user_hp -= opp_attack

            battle_log.append(f"Turn {turn}")
            battle_log.append(f"{ctx.author.name} uses {user_technique} with {user_attack:.0f} power!")
            battle_log.append(f"{opponent_data['name'] if 'name' in opponent_data else opponent.name} counters with {opp_technique}, dealing {opp_attack:.0f} damage!")

            await update_battle_embed()
            await asyncio.sleep(2)

            if user_hp <= 0 or opp_hp <= 0:
                break

        if user_hp > opp_hp:
            winner = ctx.author
            loser = opponent
            winner_data = user_data
            loser_data = opponent_data
        elif opp_hp > user_hp:
            winner = opponent
            loser = ctx.author
            winner_data = opponent_data
            loser_data = user_data
        else:
            battle_embed.add_field(name="Battle Ended", value="The epic clash ends in a draw! Both fighters stand exhausted but undefeated.", inline=False)
            await battle_message.edit(embed=battle_embed)
            return

        doriki_gain = random.randint(100, 250)
        haki_gain = random.randint(5, 15)
        bounty_gain = loser_data.get("bounty", 0) // 20 if loser_data.get("bounty", 0) > 0 else random.randint(10000000, 50000000)

        winner_data["doriki"] += doriki_gain
        winner_data["haki"]["observation"] += haki_gain
        winner_data["haki"]["armament"] += haki_gain
        winner_data["haki"]["conquerors"] += haki_gain // 2
        winner_data["bounty"] = winner_data.get("bounty", 0) + bounty_gain
        winner_data["battles_won"] = winner_data.get("battles_won", 0) + 1
        winner_data["stamina"] = max(0, winner_data.get("stamina", 100) - 20)

        if winner == ctx.author:
            await self.config.user(winner).set(winner_data)

        result_embed = discord.Embed(
            title="Battle Result",
            description=f"In an epic clash, {winner.name} emerges victorious against {loser.name if isinstance(loser, discord.Member) else loser_data['name']}!",
            color=discord.Color.gold()
        )
        result_embed.add_field(name="Doriki Gained", value=f"{doriki_gain} 💪")
        result_embed.add_field(name="Haki Improved", value=f"{haki_gain} 🔮")
        result_embed.add_field(name="Bounty Increased", value=f"{bounty_gain:,} 💰")
        await battle_message.edit(embed=result_embed)
    
def setup(bot):
    bot.add_cog(OnePieceBattle(bot))
