import discord
from discord.ext import commands

from ...guards import is_mod
from ...thread_modal import ModThreadCreationModal
from ...views import UserActionsView
from ..managed import ManagedCog


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
