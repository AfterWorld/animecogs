from .onepiece import OnePieceBattle

async def setup(bot):
    cog = OnePieceBattle(bot)
    await bot.add_cog(cog)
