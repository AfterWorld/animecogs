import discord
from redbot.core import commands, Config
import random
import asyncio
from datetime import datetime, timedelta
import json

class DemonSlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        default_user = {
            "has_passed_exam": False,
            "exam_cooldown": None,
            "breathing_technique": None,
            "breathing_mastery": {},  # This will be stored as a JSON string
            "nichirin_blade_color": None,
            "nichirin_blade_level": 0,
            "material_scarlet_iron_sand": 0,
            "material_scarlet_ore": 0,
            "material_spirit_wood": 0,
            "demons_slayed": 0,
            "rank": None,
            "experience": 0,
            "companion": None,
            "last_hunt": None,
            "upper_moon_defeated": False,
        }
        
        default_guild = {
            "active_hashira_training": None,  # This will be stored as a JSON string
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
        
        self.companions = ["Kasugai Crow", "Nichirin Ore Fox", "Demon Slayer Cat"]

        
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
        
        self.companions = ["Kasugai Crow", "Nichirin Ore Fox", "Demon Slayer Cat"]

        async def _save_breathing_mastery(self, user, breathing_mastery):
        await self.config.user(user).breathing_mastery.set(json.dumps(breathing_mastery))

        async def _get_breathing_mastery(self, user):
            breathing_mastery_json = await self.config.user(user).breathing_mastery()
            return json.loads(breathing_mastery_json) if breathing_mastery_json else {}
    
        async def _save_hashira_training(self, guild, training_data):
            await self.config.guild(guild).active_hashira_training.set(json.dumps(training_data))
    
        async def _get_hashira_training(self, guild):
            training_data_json = await self.config.guild(guild).active_hashira_training()
            return json.loads(training_data_json) if training_data_json else None

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ds.command(name="exam")
    async def take_exam(self, ctx):
        """Take the Demon Slayer Corps Entrance Exam"""
        user_data = await self.config.user(ctx.author).all()
        
        if user_data["has_passed_exam"]:
            await ctx.send("You've already passed the exam and joined the Demon Slayer Corps!")
            return
        
        if user_data["exam_cooldown"] and user_data["exam_cooldown"] > datetime.now().timestamp():
            cooldown = datetime.fromtimestamp(user_data["exam_cooldown"]) - datetime.now()
            await ctx.send(f"You must wait {cooldown.seconds // 60} minutes before retaking the exam.")
            return
        
        questions = [
            ("What is the primary weakness of demons?", "Sunlight"),
            ("What material are Nichirin Blades made from?", "Scarlet Ore"),
            ("How many forms are there in Water Breathing?", "11"),
            ("Who is the current leader of the Demon Slayer Corps?", "Kagaya Ubuyashiki"),
            ("What is the name of the demon who turns humans into demons?", "Muzan Kibutsuji")
        ]
        
        score = 0
        for i, (question, answer) in enumerate(questions, 1):
            embed = discord.Embed(title=f"Entrance Exam - Question {i}", description=question, color=discord.Color.blue())
            await ctx.send(embed=embed)
            
            try:
                user_answer = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send("Time's up! Moving to the next question.")
                continue
            
            if user_answer.content.lower() == answer.lower():
                score += 1
                await ctx.send("Correct!")
            else:
                await ctx.send(f"Incorrect. The correct answer is: {answer}")
        
        if score >= 3:
            user_data["has_passed_exam"] = True
            user_data["rank"] = "Mizunoto"
            user_data["breathing_technique"] = random.choice(list(self.breathing_techniques.keys()))
            user_data["companion"] = random.choice(self.companions)
            user_data["nichirin_blade"]["color"] = random.choice(["Red", "Blue", "Green", "Yellow", "Purple", "Black"])
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations! You've passed the exam with a score of {score}/5. Welcome to the Demon Slayer Corps!")
            await ctx.send(f"Your assigned Breathing Technique is: {user_data['breathing_technique']}")
            await ctx.send(f"Your companion is: {user_data['companion']}")
            await ctx.send(f"Your Nichirin Blade color is: {user_data['nichirin_blade']['color']}")
        else:
            user_data["exam_cooldown"] = (datetime.now() + timedelta(minutes=5)).timestamp()
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"You've failed the exam with a score of {score}/5. You can retake it in 5 minutes.")

    @ds.command(name="hunt")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def ds_hunt(self, ctx):
        """Hunt for demons"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can hunt demons!")
            return
        
        demon_types = ["Lesser Demon", "Strong Demon", "Lower Moon", "Upper Moon"]
        weights = [0.6, 0.3, 0.09, 0.01]
        demon = random.choices(demon_types, weights=weights)[0]
        
        embed = discord.Embed(title="Demon Hunt", color=discord.Color.red())
        embed.add_field(name="Demon Type", value=demon)
        
        if demon == "Upper Moon":
            embed.add_field(name="WARNING", value="You've encountered an Upper Moon demon! This will be an extremely difficult battle!")
        
        await ctx.send(embed=embed)
        
        # Simulate battle
        await asyncio.sleep(3)
        
        success_chance = {
            "Lesser Demon": 0.8,
            "Strong Demon": 0.6,
            "Lower Moon": 0.3,
            "Upper Moon": 0.05
        }
        
        if random.random() < success_chance[demon]:
            xp_gain = {
                "Lesser Demon": random.randint(10, 50),
                "Strong Demon": random.randint(50, 100),
                "Lower Moon": random.randint(100, 500),
                "Upper Moon": random.randint(500, 1000)
            }[demon]
            
            material_gain = {
                "scarlet_iron_sand": random.randint(1, 5),
                "scarlet_ore": random.randint(0, 2),
                "spirit_wood": random.randint(1, 3)
            }
            
            user_data["experience"] += xp_gain
            user_data["demons_slayed"] += 1
            for material, amount in material_gain.items():
                user_data["materials"][material] += amount
            
            await self.config.user(ctx.author).set(user_data)
            
            result_embed = discord.Embed(title="Hunt Result", color=discord.Color.green())
            result_embed.add_field(name="Outcome", value="Victory!")
            result_embed.add_field(name="XP Gained", value=str(xp_gain))
            result_embed.add_field(name="Materials Gained", value="\n".join([f"{mat.replace('_', ' ').title()}: {amt}" for mat, amt in material_gain.items()]))
            
            await ctx.send(embed=result_embed)
            await self.check_rank_up(ctx)
        else:
            await ctx.send("You were defeated by the demon and had to retreat. Better luck next time!")

    @ds.command(name="upgrade")
    async def upgrade_blade(self, ctx):
        """Upgrade your Nichirin Blade"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can upgrade your blade!")
            return
        
        current_level = user_data["nichirin_blade"]["level"]
        cost = {
            "scarlet_iron_sand": (current_level + 1) * 5,
            "scarlet_ore": (current_level + 1) * 2,
            "spirit_wood": (current_level + 1) * 3
        }
        
        embed = discord.Embed(title="Nichirin Blade Upgrade", color=discord.Color.gold())
        embed.add_field(name="Current Level", value=f"+{current_level}")
        embed.add_field(name="Upgrade Cost", value="\n".join([f"{mat.replace('_', ' ').title()}: {amt}" for mat, amt in cost.items()]))
        
        if all(user_data["materials"][mat] >= amt for mat, amt in cost.items()):
            embed.add_field(name="Upgrade Possible", value="Yes", inline=False)
            embed.add_field(name="Instructions", value="React with ✅ to upgrade or ❌ to cancel.", inline=False)
            message = await ctx.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Upgrade cancelled due to timeout.")
                return
            
            if str(reaction.emoji) == "✅":
                for mat, amt in cost.items():
                    user_data["materials"][mat] -= amt
                user_data["nichirin_blade"]["level"] += 1
                await self.config.user(ctx.author).set(user_data)
                await ctx.send(f"Your Nichirin Blade has been upgraded to +{user_data['nichirin_blade']['level']}!")
            else:
                await ctx.send("Upgrade cancelled.")
        else:
            embed.add_field(name="Upgrade Possible", value="No", inline=False)
            embed.add_field(name="Reason", value="Insufficient materials", inline=False)
            await ctx.send(embed=embed)

    @ds.command(name="train")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def train_breathing(self, ctx):
        """Train your breathing technique"""
        user_data = await self.config.user(ctx.author).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can train!")
            return
        
        technique = user_data["breathing_technique"]
        forms = self.breathing_techniques[technique]
        
        if technique not in user_data["breathing_mastery"]:
            user_data["breathing_mastery"][technique] = {}
        
        form_to_train = random.choice(forms)
        mastery_gain = random.randint(1, 10)
        
        if form_to_train not in user_data["breathing_mastery"][technique]:
            user_data["breathing_mastery"][technique][form_to_train] = 0
        
        user_data["breathing_mastery"][technique][form_to_train] += mastery_gain
        await self.config.user(ctx.author).set(user_data)
        
        embed = discord.Embed(title="Breathing Technique Training", color=discord.Color.blue())
        embed.add_field(name="Technique", value=technique)
        embed.add_field(name="Form Trained", value=form_to_train)
        embed.add_field(name="Mastery Gained", value=str(mastery_gain))
        embed.add_field(name="Current Mastery", value=str(user_data["breathing_mastery"][technique][form_to_train]))
        
        await ctx.send(embed=embed)

    @ds.command(name="profile")
    async def show_profile(self, ctx, user: discord.Member = None):
        """Display your Demon Slayer profile"""
        if user is None:
            user = ctx.author
        
        user_data = await self.config.user(user).all()
        
        if not user_data["has_passed_exam"]:
            await ctx.send("This user hasn't passed the Demon Slayer Corps entrance exam yet!")
            return
        
        embed = discord.Embed(title=f"{user.name}'s Demon Slayer Profile", color=discord.Color.blue())
        embed.add_field(name="Rank", value=user_data["rank"])
        embed.add_field(name="Breathing Technique", value=user_data["breathing_technique"])
        embed.add_field(name="Demons Slayed", value=str(user_data["demons_slayed"]))
        embed.add_field(name="Experience", value=str(user_data["experience"]))
        embed.add_field(name="Companion", value=user_data["companion"])
        embed.add_field(name="Nichirin Blade", value=f"{user_data['nichirin_blade']['color']} (+{user_data['nichirin_blade']['level']})")
        
        breathing_mastery = user_data["breathing_mastery"].get(user_data["breathing_technique"], {})
        mastery_text = "\n".join([f"{form}: {mastery}" for form, mastery in breathing_mastery.items()])
        embed.add_field(name="Breathing Mastery", value=mastery_text or "No forms mastered yet", inline=False)
        
        materials_text = "\n".join([f"{mat.replace('_', ' ').title()}: {amt}" for mat, amt in user_data["materials"].items()])
        embed.add_field(name="Materials", value=materials_text, inline=False)
        
        await ctx.send(embed=embed)

    @commands.is_owner()
    @ds.command(name="start_hashira_training")
    async def start_hashira_training(self, ctx):
        """Start a Hashira training event (Owner only)"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        if guild_data["active_hashira_training"]:
            await ctx.send("A Hashira training event is already active!")
            return
        
        guild_data["active_hashira_training"] = {
            "hashira": random.choice(["Water", "Flame", "Wind", "Stone", "Love"]),
            "difficulty": random.randint(1, 5),
            "participants": []
        }
        await self.config.guild(ctx.guild).set(guild_data)
        
        embed = discord.Embed(title="Hashira Training Event", color=discord.Color.purple())
        embed.add_field(name="Hashira", value=guild_data["active_hashira_training"]["hashira"])
        embed.add_field(name="Difficulty", value="⭐" * guild_data["active_hashira_training"]["difficulty"])
        embed.add_field(name="How to Join", value="Use the command `[p]ds join_hashira_training` to participate!", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="join_hashira_training")
    async def join_hashira_training(self, ctx):
        """Join the active Hashira training event"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_data = await self.config.user(ctx.author).all()
        
        if not guild_data["active_hashira_training"]:
            await ctx.send("There is no active Hashira training event!")
            return
        
        if not user_data["has_passed_exam"]:
            await ctx.send("You must pass the entrance exam before you can participate in Hashira training!")
            return
        
        if ctx.author.id in guild_data["active_hashira_training"]["participants"]:
            await ctx.send("You're already participating in this Hashira training event!")
            return
        
        # Check if the user has defeated an Upper Moon demon
        if user_data.get("upper_moon_defeated", False) or self.ranks.index(user_data["rank"]) >= self.ranks.index("Kinoe"):
            guild_data["active_hashira_training"]["participants"].append(ctx.author.id)
            await self.config.guild(ctx.guild).set(guild_data)
            await ctx.send(f"{ctx.author.mention} has joined the Hashira training event!")
        else:
            await ctx.send("You need to have defeated an Upper Moon demon or be at least Kinoe rank to participate in Hashira training!")

    @commands.is_owner()
    @ds.command(name="end_hashira_training")
    async def end_hashira_training(self, ctx):
        """End the current Hashira training event and distribute rewards"""
        guild_data = await self.config.guild(ctx.guild).all()
        
        if not guild_data["active_hashira_training"]:
            await ctx.send("There is no active Hashira training event!")
            return
        
        embed = discord.Embed(title="Hashira Training Results", color=discord.Color.gold())
        embed.add_field(name="Hashira", value=guild_data["active_hashira_training"]["hashira"])
        embed.add_field(name="Difficulty", value="⭐" * guild_data["active_hashira_training"]["difficulty"])
        
        for participant_id in guild_data["active_hashira_training"]["participants"]:
            user = self.bot.get_user(participant_id)
            if user:
                user_data = await self.config.user(user).all()
                xp_gain = random.randint(100, 500) * guild_data["active_hashira_training"]["difficulty"]
                user_data["experience"] += xp_gain
                
                # Chance to learn a new form
                if random.random() < 0.1 * guild_data["active_hashira_training"]["difficulty"]:
                    new_form = random.choice(self.breathing_techniques[guild_data["active_hashira_training"]["hashira"]])
                    if guild_data["active_hashira_training"]["hashira"] not in user_data["breathing_mastery"]:
                        user_data["breathing_mastery"][guild_data["active_hashira_training"]["hashira"]] = {}
                    user_data["breathing_mastery"][guild_data["active_hashira_training"]["hashira"]][new_form] = 1
                    embed.add_field(name=f"{user.name} Learned New Form", value=f"{new_form} ({guild_data['active_hashira_training']['hashira']} Breathing)", inline=False)
                
                await self.config.user(user).set(user_data)
                embed.add_field(name=f"{user.name} Rewards", value=f"XP Gained: {xp_gain}", inline=False)
        
        await ctx.send(embed=embed)
        guild_data["active_hashira_training"] = None
        await self.config.guild(ctx.guild).set(guild_data)

    @ds.command(name="leaderboard")
    async def show_leaderboard(self, ctx):
        """Display the Demon Slayer leaderboard"""
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]["experience"], reverse=True)[:10]
        
        embed = discord.Embed(title="Demon Slayer Leaderboard", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"Rank: {data['rank']}\nXP: {data['experience']}\nDemons Slayed: {data['demons_slayed']}", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="stats")
    async def show_stats(self, ctx):
        """Display global Demon Slayer stats"""
        all_users = await self.config.all_users()
        total_demons_slayed = sum(user_data["demons_slayed"] for user_data in all_users.values())
        total_slayers = sum(1 for user_data in all_users.values() if user_data["has_passed_exam"])
        
        embed = discord.Embed(title="Demon Slayer Global Stats", color=discord.Color.blue())
        embed.add_field(name="Total Demons Slayed", value=str(total_demons_slayed))
        embed.add_field(name="Total Demon Slayers", value=str(total_slayers))
        
        # Count of each rank
        rank_counts = {rank: sum(1 for user_data in all_users.values() if user_data["rank"] == rank) for rank in self.ranks}
        rank_stats = "\n".join([f"{rank}: {count}" for rank, count in rank_counts.items() if count > 0])
        embed.add_field(name="Ranks", value=rank_stats, inline=False)
        
        await ctx.send(embed=embed)

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data["rank"])
        xp_threshold = (current_rank_index + 1) * 1000
        
        if user_data["experience"] >= xp_threshold and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            user_data["rank"] = new_rank
            await self.config.user(ctx.author).set(user_data)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've been promoted to {new_rank}!")

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
