from datetime import timedelta

import discord

from .config import Config
from .guards import is_mod


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

    def __init__(self, member, config: Config, *args, **kwargs) -> None:
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
