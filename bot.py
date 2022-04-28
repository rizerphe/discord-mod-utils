import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import click
import discord
import humanize
from discord.ext import commands
from dotenv import load_dotenv
from typing import Callable


@dataclass
class Config:
    mod_cases_channel: int
    mod_role: int
    token: str


async def is_mod(user, config: Config, respond: Callable):
    if config.mod_role in [role.id for role in user.roles]:
        return True
    await respond("This command is reserved for moderators")
    return False


class ModInviteViewContainer:
    def __init__(self, mods, thread):
        self.mods = mods
        self.thread = thread
        self.create_view()

    def create_view(self):
        self.view = discord.ui.View()
        self.create_select()

    def create_select(self):
        if self.mods:
            self.select = discord.ui.Select(
                placeholder="Invite a mod to the thread",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(
                        label=mod.display_name,
                        description=f"Ping {mod.display_name} in the newly created thread",
                        value=mod.mention,
                    )
                    for mod in self.mods
                ],
            )
            self.select.callback = self.select_mod
            self.view.add_item(self.select)

    async def select_mod(self, interaction):
        await self.thread.send(
            f"{self.select.values[0]} was invited to join the discussion"
        )
        await interaction.response.send_message(
            f"Invited {self.select.values[0]}", ephemeral=True
        )


class UserActionsView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        self.__member = kwargs.pop("member")
        self.__config = kwargs.pop("config")
        super().__init__(*args, **kwargs)

    @discord.ui.button(label="Timeout 1m", style=discord.ButtonStyle.primary, row=0)
    async def timeout_1m(self, button, interaction: discord.Interaction):
        if await is_mod(
            interaction.user,
            self.__config,
            lambda response: interaction.response.send_message(
                response, ephemeral=True
            ),
        ):
            await self.__member.timeout_for(timedelta(minutes=1))
            await interaction.response.send_message(
                "Timed out for a minute", ephemeral=True
            )

    @discord.ui.button(label="Timeout 1h", style=discord.ButtonStyle.primary, row=0)
    async def timeout_1h(self, button, interaction):
        if await is_mod(
            interaction.user,
            self.__config,
            lambda response: interaction.response.send_message(
                response, ephemeral=True
            ),
        ):
            await self.__member.timeout_for(timedelta(hours=1))
            await interaction.response.send_message(
                "Timed out for an hour", ephemeral=True
            )

    @discord.ui.button(label="Timeout 1d", style=discord.ButtonStyle.primary, row=0)
    async def timeout_1d(self, button, interaction):
        if await is_mod(
            interaction.user,
            self.__config,
            lambda response: interaction.response.send_message(
                response, ephemeral=True
            ),
        ):
            await self.__member.timeout_for(timedelta(days=1))
            await interaction.response.send_message(
                "Timed out for a day", ephemeral=True
            )

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.red, row=1)
    async def kick(self, button, interaction):
        if await is_mod(
            interaction.user,
            self.__config,
            lambda response: interaction.response.send_message(
                response, ephemeral=True
            ),
        ):
            await self.__member.kick()
            await interaction.response.send_message("User kicked", ephemeral=True)

    @discord.ui.button(
        label="Ban and delete a day worth of messages",
        style=discord.ButtonStyle.red,
        row=1,
    )
    async def ban(self, button, interaction):
        if await is_mod(
            interaction.user,
            self.__config,
            lambda response: interaction.response.send_message(
                response, ephemeral=True
            ),
        ):
            await self.__member.ban()
            await interaction.response.send_message("User banned", ephemeral=True)


class ModerationManager:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def datetime_to_text(self, time):
        ago = humanize.naturaltime(time, when=datetime.now(timezone.utc))
        absolute = time.strftime("%H:%M:%S, %d %b, %Y")
        return f"{ago}; {absolute}"

    def form_message_info_embed(self, message, requested_by):
        embed = discord.Embed(title="Message info")
        embed.add_field(name="Moderator", value=requested_by.mention, inline=True)
        embed.add_field(
            name="Original message",
            value=f"[link]({message.jump_url})",
            inline=True,
        )
        embed.add_field(
            name="Original author", value=message.author.mention, inline=True
        )
        embed.add_field(
            name="Sent", value=self.datetime_to_text(message.created_at), inline=True
        )
        if message.edited_at:
            embed.add_field(
                name="Edited",
                value=self.datetime_to_text(message.edited_at),
                inline=True,
            )
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        return embed

    def form_user_info_embed(self, member, channel=None, short=False):
        user_info = discord.Embed(title="User info")

        user_info.add_field(name="ID", value=str(member.id), inline=True)
        user_info.add_field(
            name="Joined Discord",
            value=self.datetime_to_text(member.created_at),
            inline=True,
        )
        if isinstance(member, discord.Member):
            user_info.add_field(
                name="Joined Server",
                value=self.datetime_to_text(member.joined_at),
                inline=True,
            )
        user_info.add_field(
            name="Roles",
            value=",".join(role.mention for role in member.roles),
            inline=False,
        )
        if not short:
            user_info.add_field(
                name="Guild permissions",
                value=", ".join(
                    perm.replace("_", " ").capitalize()
                    for perm, value in member.guild_permissions
                    if value
                ),
                inline=False,
            )
        if channel and not short:
            user_info.add_field(
                name="Original channel permissions",
                value=", ".join(
                    perm.replace("_", " ").capitalize()
                    for perm, value in channel.permissions_for(member)
                    if value
                ),
                inline=False,
            )
        name = f"{member.name}#{member.discriminator}"
        if member.avatar:
            user_info.set_thumbnail(url=member.avatar.url)
            user_info.set_author(name=name, icon_url=member.avatar.url)
        else:
            user_info.set_author(name=name)
        return user_info

    async def duplicate_message_into_webhook(self, message, channel, thread, member):
        webhooks = [
            webhook
            for webhook in await channel.guild.webhooks()
            if webhook.channel_id == channel.id
        ]
        if webhooks:
            webhook = webhooks[0]
        else:
            webhook = await channel.create_webhook(
                name="Moderation messages duplicator"
            )
        await webhook.send(
            content=message.content,
            username=member.display_name,
            avatar_url=member.avatar and member.avatar.url,
            embeds=message.embeds,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False, replied_user=False
            ),
            thread=thread,
        )

    async def get_active_mods(self, message: discord.TextChannel):
        if (datetime.now(timezone.utc) - message.created_at).total_seconds() > 15 * 60:
            # We are operating on an old message; don't care
            # The limit is arbitrarily set to 15 minutes
            return []
        active_mods = []
        analyzed = []
        async for message in message.channel.history(
            limit=100, after=datetime.now(timezone.utc) - timedelta(seconds=15 * 60)
        ):
            if message.author.id in analyzed:
                continue  #  don't wanna refetch a member
            author = await message.guild.fetch_member(message.author.id)
            analyzed.append(message.author.id)
            if self.config.mod_role in [role.id for role in author.roles]:
                active_mods.append(message.author)
        return active_mods

    async def create_thread(self, title: str, description: str):
        cases_channel: discord.Channel = await self.bot.fetch_channel(
            self.config.mod_cases_channel
        )
        message: discord.Message = await cases_channel.send(description)
        thread: discord.Thread = await message.create_thread(name=title)
        return thread

    async def populate_thread(self, thread: discord.Thread, requester, member, message):
        await thread.send(
            embed=self.form_message_info_embed(message, requester),
            view=UserActionsView(member=member, config=self.config),
        )
        await self.duplicate_message_into_webhook(
            message, thread.parent, thread, member
        )
        await thread.send(
            embed=self.form_user_info_embed(member, message.channel, True)
        )


class ModThreadCreationModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.__message: discord.Message = kwargs.pop("message")
        self.__manager = kwargs.pop("manager")
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(
                label="Short description",
                placeholder="Will be used as the name for the thread",
            )
        )
        self.add_item(
            discord.ui.InputText(
                label="Longer description",
                style=discord.InputTextStyle.long,
                placeholder="Will be used as the introduction message",
                required=False,
            )
        )

    @property
    def __title(self):
        return self.children[0].value

    @property
    def __description(self):
        if self.children[1].value:
            return self.children[1].value
        return self.__title

    async def callback(self, interaction: discord.Interaction):
        response = await interaction.response.send_message(
            "Setting up the thread...", ephemeral=True
        )

        thread = await self.__manager.create_thread(
            title=self.__title, description=self.__description
        )

        member = await interaction.guild.fetch_member(self.__message.author.id)
        await self.__manager.populate_thread(
            thread, interaction.user, member, self.__message
        )

        mods = await self.__manager.get_active_mods(self.__message)
        await response.edit_original_message(
            content=f"Created a new moderation thread: {thread.mention}",
            view=ModInviteViewContainer(mods=mods, thread=thread).view,
        )


class ModerationUtilsCog(commands.Cog):
    def __init__(self, manager):
        self.manager = manager

    @commands.message_command(name="Start a moderation thread")
    async def start_mod_thread(self, ctx, message: discord.Message):
        member = await ctx.guild.fetch_member(message.author.id)
        if await is_mod(
            member,
            self.manager.config,
            lambda response: ctx.respond(response, ephemeral=True),
        ):
            await ctx.send_modal(
                ModThreadCreationModal(
                    title="Create a new moderation thread",
                    message=message,
                    manager=self.manager,
                )
            )

    @commands.message_command(name="Get message info")
    async def get_message_info(self, ctx, message: discord.Message):
        member = await ctx.guild.fetch_member(message.author.id)
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
        member = await ctx.guild.fetch_member(message.author.id)
        if await is_mod(
            member,
            self.manager.config,
            lambda response: ctx.respond(response, ephemeral=True),
        ):
            await ctx.respond(
                embed=self.manager.form_user_info_embed(member, message.channel),
                view=UserActionsView(member=member, config=self.manager.config),
                ephemeral=True,
            )


class PromptWhenNoDefault(click.Option):
    def prompt_for_value(self, ctx):
        if (default := self.get_default(ctx)) is None:
            return super().prompt_for_value(ctx)
        return default


load_dotenv()


@click.command()
@click.option(
    "--token",
    prompt=True,
    cls=PromptWhenNoDefault,
    default=lambda: os.getenv("TOKEN", None),
    show_default="envvar 'TOKEN'",
    type=str,
)
@click.option(
    "--mod-cases-channel",
    default=lambda: os.getenv("MOD_CASES_CHANNEL", None),
    show_default="envvar 'MOD_CASES_CHANNEL'",
    type=int,
)
@click.option(
    "--mod-role",
    default=lambda: os.getenv("MOD_ROLE", None),
    show_default="envvar 'MOD_ROLE'",
    type=int,
)
def main(token, mod_cases_channel, mod_role):
    config = Config(mod_cases_channel=mod_cases_channel, mod_role=mod_role, token=token)
    bot = discord.Bot()
    bot.add_cog(ModerationUtilsCog(ModerationManager(bot, config)))
    bot.run(token)


if __name__ == "__main__":
    main()
