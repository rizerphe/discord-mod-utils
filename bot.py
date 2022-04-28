import os
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from typing import Coroutine
from typing import Optional
from typing import Union

import click
import discord
import humanize
from discord.ext import commands
from dotenv import load_dotenv

from database import Database
from firebase_db import FirestoreDatabase


@dataclass
class Config:
    """A dataclass for storing the app config"""

    database: Database
    token: str

    def get_mod_cases(self, guild_id: int) -> Optional[int]:
        """Get the ID of the channel used for storing mod cases"""
        return self.database.get_guild(guild_id).cases_channel

    def get_mod_role(self, guild_id: int) -> Optional[int]:
        """Get the ID of the moderator role"""
        return self.database.get_guild(guild_id).moderator_role

    def get_mod_hook(self, guild_id: int) -> Optional[int]:
        """Get the ID of the moderation webhook"""
        return self.database.get_guild(guild_id).duplication_webhook

    def set_mod_hook(self, guild_id: int, mod_hook_id: Optional[int]) -> None:
        """Set the ID of the moderation webhook"""
        guild = self.database.get_guild(guild_id)
        guild.duplication_webhook = mod_hook_id
        self.database.set_guild(guild_id, guild)


async def is_mod(
    user: discord.Member, config: Config, respond: Callable[[str], Coroutine]
) -> bool:
    """Check if the user us a moderator and send an error message if not

    Args:
        user: the member to check the roles of
        config: the configuration that contains the guild database
        respond: the function to respond with

    Returns:
        True if the user is a moderator; False otherwise

    """
    role = config.get_mod_role(user.guild.id)
    if role is None:
        await respond(
            "You didn't set up a moderator. " + "Use `/config moderator` to choose one"
        )
        return False
    if role in [role.id for role in user.roles]:
        return True
    await respond("This command is reserved for moderators")
    return False


class ModInviteViewContainer:
    """Responsible for creating the view with a select for creating a mod"""

    def __init__(self, mods: list[discord.Member], thread: discord.Thread) -> None:
        """Create a view for selecting a mod

        Args:
            mods: the list of moderators to let the user choose from
            thread: the thread to which the mods should be invited

        """
        self.mods = mods
        self.thread = thread
        self.create_view()

    def create_view(self) -> None:
        """Initialuze the view with a select in it"""
        self.view = discord.ui.View()
        self.create_select()

    def create_select(self) -> None:
        """Initialize the select and add it to the view"""
        if self.mods:
            self.select: discord.ui.Select = discord.ui.Select(
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

    async def select_mod(self, interaction) -> None:
        """Select the moderator and invite them to the thread

        An invitation is just the moderator being pinged inside the thread

        """
        await self.thread.send(
            f"{self.select.values[0]} was invited to join the discussion"
        )
        await interaction.response.send_message(
            f"Invited {self.select.values[0]}", ephemeral=True
        )


class UserActionsView(discord.ui.View):
    """A view containing a set of buttons for quick user moderation"""

    def __init__(self, member, config, *args, **kwargs) -> None:
        """Initialize the view"""
        self.__member = member
        self.__config = config
        super().__init__(*args, **kwargs)

    @discord.ui.button(label="Timeout 1m", style=discord.ButtonStyle.primary, row=0)
    async def timeout_1m(self, button, interaction: discord.Interaction) -> None:
        """Timeout the user for one minute"""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Something went wrong, we're unable to verify if you're a moderator."
            )
            return
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
    async def timeout_1h(self, button, interaction: discord.Interaction) -> None:
        """Timeout the user for one hour"""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Something went wrong, we're unable to verify if you're a moderator."
            )
            return
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
    async def timeout_1d(self, button, interaction: discord.Interaction) -> None:
        """Timeout the user for one day"""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Something went wrong, we're unable to verify if you're a moderator."
            )
            return
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
    async def kick(self, button, interaction: discord.Interaction) -> None:
        """Kick the user"""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Something went wrong, we're unable to verify if you're a moderator."
            )
            return
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
    async def ban(self, button, interaction: discord.Interaction) -> None:
        """Ban the user"""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Something went wrong, we're unable to verify if you're a moderator."
            )
            return
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
    """A class that actually manages all of the actions"""

    def __init__(self, bot: discord.Bot, config: Config):
        self.bot = bot
        self.config = config

    def datetime_to_text(self, time: datetime) -> str:
        """Convert a datetime.datetime to a human-readable representation"""
        ago = humanize.naturaltime(time, when=datetime.now(timezone.utc))
        absolute = time.strftime("%H:%M:%S, %d %b, %Y")
        return f"{ago}; {absolute}"

    def form_message_info_embed(
        self, message: discord.Message, requested_by: discord.Member
    ) -> discord.Embed:
        """Create a message info embed"""
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
        if isinstance(message.channel, discord.TextChannel):
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        return embed

    def form_user_info_embed(
        self,
        member: Union[discord.User, discord.Member],
        channel=None,
        short: bool = False,
    ) -> discord.Embed:
        """Create a member info embed"""
        user_info = discord.Embed(title="User info")

        user_info.add_field(name="ID", value=str(member.id), inline=True)
        user_info.add_field(
            name="Joined Discord",
            value=self.datetime_to_text(member.created_at),
            inline=True,
        )
        if isinstance(member, discord.Member) and member.joined_at:
            user_info.add_field(
                name="Joined Server",
                value=self.datetime_to_text(member.joined_at),
                inline=True,
            )
        if isinstance(member, discord.Member):
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
                if channel and isinstance(channel, discord.abc.GuildChannel):
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

    async def duplicate_message_into_webhook(
        self, message: discord.Message, thread: discord.Thread, member: discord.Member
    ) -> None:
        """Duplicates a message into a thread using a webhook"""
        channel = thread.parent
        if channel is None:
            return
        hook_id = self.config.get_mod_hook(channel.guild.id)
        webhooks = [
            webhook
            for webhook in await channel.guild.webhooks()
            if webhook.channel_id == channel.id and webhook.id == hook_id
        ]
        if webhooks:
            webhook = webhooks[0]
        else:
            webhook = await channel.create_webhook(
                name="Moderation messages duplicator"
            )
            self.config.set_mod_hook(channel.guild.id, webhook.id)
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

    async def get_active_mods(self, message: discord.Message) -> list[discord.Member]:
        """Given a message, get list of mods who were participating

        Given a message, provided that it is recent, get a list of
        mods who were participating in the conversation. If the
        message is not recent, returns an empty list

        """
        if message.guild is None:
            # There are no mods outside of guilds
            return []
        if (datetime.now(timezone.utc) - message.created_at).total_seconds() > 15 * 60:
            # We are operating on an old message; don't care
            # The limit is arbitrarily set to 15 minutes
            return []
        active_mods = []
        analyzed = []
        async for message in message.channel.history(
            limit=100, after=datetime.now(timezone.utc) - timedelta(seconds=15 * 60)
        ):
            if message.guild is None:
                continue  # so that mypy shuts up
            if message.author.id in analyzed:
                continue  #  don't wanna refetch a member
            author = await message.guild.fetch_member(message.author.id)
            analyzed.append(message.author.id)
            if self.config.get_mod_role(message.guild.id) in [
                role.id for role in author.roles
            ]:
                active_mods.append(author)
        return active_mods

    async def create_thread(
        self, title: str, description: str, channel_id: int
    ) -> Optional[discord.Thread]:
        """Creates a modcase thread in a given channel

        Args:
            title: will be used as the name for that thread
            description: will be used as the moderation case summary
            channel_id: the channel to create the thread in

        Returns:
            None if the channel wasn't a discord.TextChannel
            the created thread otherwise

        """
        cases_channel = await self.bot.fetch_channel(channel_id)
        if not isinstance(cases_channel, discord.TextChannel):
            return None
        message: discord.Message = await cases_channel.send(description)
        thread: discord.Thread = await message.create_thread(name=title)
        return thread

    async def populate_thread(
        self,
        thread: discord.Thread,
        requester,
        member: discord.Member,
        message: discord.Message,
    ) -> None:
        """Populate the mod case thread

        Sends the message and user info and replicates the original
        message with a webhook

        Args:
            thread: the thread to post to
            requester: the moderator who requested the ccase
            member: the user being reported
            message: the reported message

        """
        await thread.send(
            embed=self.form_message_info_embed(message, requester),
            view=UserActionsView(member=member, config=self.config),
        )
        await self.duplicate_message_into_webhook(message, thread, member)
        await thread.send(
            embed=self.form_user_info_embed(member, message.channel, True)
        )


class ModThreadCreationModal(discord.ui.Modal):
    """The modal for creating a new moderation case thread"""

    def __init__(
        self,
        message: discord.Message,
        thread_channel: int,
        manager: ModerationManager,
        *args,
        **kwargs,
    ) -> None:
        """Initialize moderation case creation modal"""
        self.__message = message
        self.__thread_channel = thread_channel
        self.__manager = manager
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
        """If we don't have the description, just use the title"""
        if self.children[1].value:
            return self.children[1].value
        return self.__title

    async def callback(self, interaction: discord.Interaction):
        """Create a moderation thread"""
        response = await interaction.response.send_message(
            "Setting up the thread...", ephemeral=True
        )

        if interaction.guild is None:
            await response.edit_original_message(
                content="Can't determine a moderator cases channel outside of a guild"
            )
            return
        thread = await self.__manager.create_thread(
            title=self.__title,
            description=self.__description,
            channel_id=self.__thread_channel,
        )
        if thread is None:
            await response.edit_original_message(content="Failed to create the thread")
            return
        member = await interaction.guild.fetch_member(self.__message.author.id)
        await self.__manager.populate_thread(
            thread, interaction.user, member, self.__message
        )

        mods = await self.__manager.get_active_mods(self.__message)
        await response.edit_original_message(
            content=f"Created a new moderation thread: {thread.mention}",
            view=ModInviteViewContainer(mods=mods, thread=thread).view,
        )


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
        await ctx.respond(f"Webhook was reset")


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


class PromptWhenNoDefault(click.Option):
    """Propmts when no default is set

    A class responsible for only prompting for input when tjere is no
    default value set (for use with @click.option)

    """

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
    "--firebase-creds",
    default="credentials.json",
    type=click.Path(exists=True),
)
def main(token, firebase_creds):
    """Main function

    Connects to a firestore database and starts the bot

    """
    database = FirestoreDatabase(firebase_creds)
    config = Config(token=token, database=database)
    bot = discord.Bot()
    bot.add_cog(ModerationCog(ModerationManager(bot, config)))
    bot.run(token)


if __name__ == "__main__":
    main()
