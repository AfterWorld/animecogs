from .mhagame import MHAGame

async def setup(bot):
    await bot.add_cog(MHAGame(bot))