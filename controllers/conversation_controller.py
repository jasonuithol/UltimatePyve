import pygame

from dark_libraries.dark_math import Vector2
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent     import PartyAgent
from models.agents.town_npc_agent  import TownNpcAgent
from models.tlk_file               import NpcDialog, ScriptLine, TalkCommand

from services.console_service import ConsoleService
from services.input_service   import InputService, keycode_to_char
from services.npc_service     import NpcService


KEYWORD_MAX_CHARS = 4


class ConversationController(LoggerMixin):

    # Injectable
    party_agent:     PartyAgent
    global_registry: GlobalRegistry
    console_service: ConsoleService
    input_service:   InputService
    npc_service:     NpcService

    def talk(self, direction: Vector2[int]):
        try:
            self._talk(direction)
        finally:
            # Restore the normal '>' command prompt for the next gameplay line.
            self.console_service.print_ascii("")

    def _talk(self, direction: Vector2[int]):
        party_location = self.party_agent.get_current_location()
        target_coord   = party_location.coord + direction
        target_npc     = self.npc_service.get_npc_at(target_coord)

        if not isinstance(target_npc, TownNpcAgent):
            self.console_service.print_ascii("No response", no_prompt=True)
            return

        dialogs = self.global_registry.npc_dialogs.get(party_location.location_index)
        if dialogs is None:
            self.console_service.print_ascii("No response", no_prompt=True)
            return
        dialog = dialogs.get(target_npc.dialog_number)
        if dialog is None:
            self.console_service.print_ascii("No response", no_prompt=True)
            return

        avatar_name = self._avatar_name()

        self._say(f"You meet {self._render(dialog.name, avatar_name)}")
        self._say(self._render(dialog.description, avatar_name))
        self._say(self._render(dialog.greeting, avatar_name))

        while True:
            keyword = self._read_keyword()
            if keyword is None or keyword == "":
                self._say(self._render(dialog.bye, avatar_name))
                return
            if keyword == "bye":
                self._say(self._render(dialog.bye, avatar_name))
                return

            response = self._lookup(dialog, keyword)
            if response is None:
                self._say("That I cannot help thee with.")
                continue
            self._say(self._render(response, avatar_name))

    def _say(self, msg: str):
        # Conversation mode: suppress the '>' command prompt between lines.
        self.console_service.print_ascii(msg, no_prompt=True)

    def _read_keyword(self) -> str | None:
        """
        Read a keyword of up to KEYWORD_MAX_CHARS characters, terminated by
        Enter. Escape or a synthetic-quit event returns None to abort the
        conversation.
        """
        self.console_service.print_ascii("Your interest: ", include_carriage_return=False)
        buffer = ""
        while True:
            event = self.input_service.get_next_event()
            if getattr(event, "type", 0) == pygame.QUIT or getattr(event, "key", 0) == -1:
                return None
            if event.key == pygame.K_RETURN:
                self.console_service.print_ascii("", no_prompt=True)
                return buffer.lower()
            if event.key == pygame.K_ESCAPE:
                self.console_service.print_ascii("", no_prompt=True)
                return None
            if event.key == pygame.K_BACKSPACE:
                if buffer:
                    buffer = buffer[:-1]
                continue
            if len(buffer) >= KEYWORD_MAX_CHARS:
                continue
            char = keycode_to_char(event.key)
            if char is None or char in ("\n", "\t"):
                continue
            buffer += char
            self.console_service.print_ascii(char, include_carriage_return=False, no_prompt=True)

    def _lookup(self, dialog: NpcDialog, keyword: str) -> ScriptLine | None:
        # Baked-in keywords that every NPC answers.
        if keyword == "name":
            return dialog.name
        if keyword in ("job", "work"):
            return dialog.job
        if keyword == "look":
            return dialog.description

        # Custom keywords: U5 matches on the first 4 characters.
        prefix = keyword[:KEYWORD_MAX_CHARS]
        for kw, response in dialog.keyword_responses.items():
            if kw[:KEYWORD_MAX_CHARS] == prefix:
                return response
        return None

    def _avatar_name(self) -> str:
        saved = self.global_registry.saved_game
        if saved is None:
            return "Avatar"
        name = saved.create_character_record(0).name
        return name if name else "Avatar"

    def _render(self, line: ScriptLine, avatar_name: str) -> str:
        parts: list[str] = []
        for item in line.items:
            if item.command == TalkCommand.PLAIN_STRING:
                parts.append(item.text)
            elif item.command == TalkCommand.AVATARS_NAME:
                parts.append(avatar_name)
            elif item.command == TalkCommand.NEW_LINE:
                parts.append("\n")
            # Other command bytes (KEY_WAIT, PAUSE, KARMA_*, etc.) are
            # silently dropped in this first pass.
        return "".join(parts).strip()
