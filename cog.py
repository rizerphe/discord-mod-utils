import discord
from discord.ext import commands

from guards import is_mod
from manager import ModerationManager
from thread_modal import ModThreadCreationModal
from views import UserActionsView


class ManagedCog(commands.Cog):
    """My parent Cog

    Diferent sets of tools are stored in different classes
    This class stores the properties shared between them

    """

    def __init__(self, manager: ModerationManager):
        """Initialize the cog"""
        self.manager = manager


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


class UtilsCog(ManagedCog):
    """A class storing all message context commands"""

    @commands.message_command(name="Start a moderation thread")
    async def start_mod_thread(self, ctx, message: discord.Message):
        """Start a moderation case thread for a message"""
        member = await ctx.guild.fetch_member(ctx.user.id)
        if await is_mod(
            member,
            self.manager.config,
            lambda response: ctx.respond(response, ephemeral=True),
        ):
            thread_channel = self.manager.config.get_mod_cases(ctx.guild.id)
            if thread_channel is None:
                await ctx.respond(
                    "You didn't set up a moderation cases channel. "
                    + "Use `/config cases` to choose one",
                    ephemeral=True,
                )
                return
            await ctx.send_modal(
                ModThreadCreationModal(
                    title="Create a new moderation thread",
                    message=message,
                    manager=self.manager,
                    thread_channel=thread_channel,
                )
            )

    @commands.message_command(name="Get message info")
    async def get_message_info(self, ctx, message: discord.Message):
        """Get basic message info"""
        member = await ctx.guild.fetch_member(ctx.user.id)
        if await is_mod(
            member,
            self.manager.config,
            lambda response: ctx.respond(response, ephemeral=True),
        ):
            await ctx.respond(
                embed=self.manager.form_message_info_embed(message, ctx.author),
                ephemeral=True,
            )

    @commands.message_command(name="Get user info")
    async def get_user_info(self, ctx, message: discord.Message):
        """Get basic user info"""
        member = await ctx.guild.fetch_member(ctx.user.id)
        if await is_mod(
            member,
            self.manager.config,
            lambda response: ctx.respond(response, ephemeral=True),
        ):
            member = await ctx.guild.fetch_member(message.author.id)
            await ctx.respond(
                embed=self.manager.form_user_info_embed(member, message.channel),
                view=UserActionsView(member=member, config=self.manager.config),
                ephemeral=True,
            )


class ModerationCog(ConfigurerCog, UtilsCog):
    """This just unites all cogs into one"""

    pass
