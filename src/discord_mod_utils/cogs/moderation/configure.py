import discord
from discord.ext import commands

from ..managed import ManagedCog


class ConfigurerCog(ManagedCog):
    """A class storing all configuration commands"""

    # TODO: figure out proper permissions
    # if I understand correctly, pycord just doesn't yet
    # have discord.commands.CommandPermission implemented properly
    config = discord.SlashCommandGroup(
        "config",
        "Configure global guild settings",
    )

    @config.command(description="Choose a role for performing moderator actions.")
    @commands.has_permissions(administrator=True)
    async def moderator(self, ctx, role: discord.Role):
        """Set the moderator role"""
        guild_config = self.manager.config.database.get_guild(ctx.guild.id)
        guild_config.moderator_role = role.id
        self.manager.config.database.set_guild(ctx.guild.id, guild_config)
        await ctx.respond(f"{role.mention} is now a guild moderator")

    @config.command(
        description="Choose a channel to create moderation case threads in."
    )
    @commands.has_permissions(administrator=True)
    async def cases(self, ctx, channel: discord.TextChannel):
        """Set the moderation cases channel"""
        guild_config = self.manager.config.database.get_guild(ctx.guild.id)
        guild_config.cases_channel = channel.id
        self.manager.config.database.set_guild(ctx.guild.id, guild_config)
        await ctx.respond(f"{channel.mention} is now a moderation cases channel")

    @config.command(
        description="Forget about the moderation hook"
        + " (creates a new one when needed, doesn't delete the old one)"
    )
    @commands.has_permissions(administrator=True)
    async def reset_webhook(self, ctx):
        """Reset the moderation copy webhook"""
        self.manager.config.set_mod_hook(ctx.guild.id, None)
        await ctx.respond("Webhook was reset")
