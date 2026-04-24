import pygame

from dark_libraries.dark_math import Vector2
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent     import PartyAgent
from models.agents.town_npc_agent  import TownNpcAgent
from models.tlk_file               import NpcDialog, ScriptItem, ScriptLine, TalkCommand

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

        # Ultima V opens a conversation with Description, then Greeting. The
        # NPC's Name line is only revealed if the Avatar asks for it (and even
        # then, NPCs with IF_ELSE_KNOWS_NAME hide themselves until introduced).
        description = self._render(dialog.description, target_npc, avatar_name)
        self._say(f"You see {description}" if description else "You see someone.")
        greeting = self._render(dialog.greeting, target_npc, avatar_name)
        if greeting:
            self._npc_speak(greeting)

        while True:
            keyword = self._read_keyword()
            if keyword is None or keyword == "":
                self._npc_speak(self._render(dialog.bye, target_npc, avatar_name))
                return
            if keyword == "bye":
                self._npc_speak(self._render(dialog.bye, target_npc, avatar_name))
                return

            response_text = self._lookup(dialog, keyword, target_npc, avatar_name)
            if response_text is None:
                self._npc_speak("That I cannot help thee with.")
                continue
            self._npc_speak(response_text)

    def _say(self, msg: str):
        # Conversation mode: suppress the '>' command prompt between lines,
        # and trail a blank line so separate messages are visually distinct
        # from a single message that wrapped across rows.
        self.console_service.print_ascii(msg, no_prompt=True)
        self.console_service.print_ascii("", no_prompt=True)

    def _npc_speak(self, msg: str):
        # NPC utterances are wrapped in "double quotes" to distinguish them
        # from narrator lines like "You see ...".
        self._say(f'"{msg}"')

    def _read_keyword(self) -> str | None:
        """
        Read a keyword of up to KEYWORD_MAX_CHARS characters, terminated by
        Enter. Escape or a synthetic-quit event returns None to abort the
        conversation.
        """
        self.console_service.print_ascii("Your interest?", no_prompt=True)
        self.console_service.print_ascii(":", include_carriage_return=False, no_prompt=True)
        buffer = ""
        while True:
            event = self.input_service.get_next_event()
            if getattr(event, "type", 0) == pygame.QUIT or getattr(event, "key", 0) == -1:
                return None
            if event.key == pygame.K_RETURN:
                # End the input line, then a blank row so the NPC's response
                # is visually separated from what the Avatar typed.
                self.console_service.print_ascii("", no_prompt=True)
                self.console_service.print_ascii("", no_prompt=True)
                return buffer.lower()
            if event.key == pygame.K_ESCAPE:
                self.console_service.print_ascii("", no_prompt=True)
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

    def _lookup(
        self,
        dialog: NpcDialog,
        keyword: str,
        npc: TownNpcAgent,
        avatar_name: str,
    ) -> str | None:
        # Baked-in keywords that every NPC answers.
        if keyword == "name":
            name_text = self._render(dialog.name, npc, avatar_name)
            return f"My name is {name_text}" if name_text else None
        if keyword in ("job", "work"):
            return self._render(dialog.job, npc, avatar_name)
        if keyword == "look":
            return self._render(dialog.description, npc, avatar_name)

        # Custom keywords: U5 matches on the first 4 characters.
        prefix = keyword[:KEYWORD_MAX_CHARS]
        for kw, response_line in dialog.keyword_responses.items():
            if kw[:KEYWORD_MAX_CHARS] == prefix:
                return self._render(response_line, npc, avatar_name)
        return None

    def _avatar_name(self) -> str:
        saved = self.global_registry.saved_game
        if saved is None:
            return "Avatar"
        name = saved.create_character_record(0).name
        return name if name else "Avatar"

    def _render(self, line: ScriptLine, npc: TownNpcAgent, avatar_name: str) -> str:
        """
        Render a ScriptLine to plain text, honouring IF_ELSE_KNOWS_NAME
        sections and skipping AVATARS_NAME sections when the NPC has not yet
        been introduced to the Avatar. Mirrors Ultima5Redux's
        Conversation.ProcessMultipleLines skip-instruction state machine.
        """
        has_met  = npc.has_met_avatar
        sections = line.split_into_sections()
        parts: list[str] = []
        skip_counter = -1
        i = 0
        while i < len(sections):
            if skip_counter == 0:
                skip_counter = -1
                i += 1
                continue
            section = sections[i]

            if not section:
                i += 1
                continue

            # If this section needs to address the Avatar by name but we
            # haven't been introduced yet, drop the whole section.
            if not has_met and any(it.command == TalkCommand.AVATARS_NAME for it in section):
                i += 1
                continue

            skip_instruction = "dont_skip"
            if (
                len(section) == 1
                and section[0].command == TalkCommand.IF_ELSE_KNOWS_NAME
            ):
                # Two sections follow: the "known" branch first, then the
                # "unknown" branch. Pick one based on has_met_avatar.
                skip_instruction = "skip_after_next" if has_met else "skip_next"
            else:
                self._render_section(section, avatar_name, parts)

            if skip_counter != -1:
                skip_counter -= 1

            if skip_instruction == "skip_after_next":
                skip_counter = 1
            elif skip_instruction == "skip_next":
                i += 1

            i += 1

        return "".join(parts).strip()

    @staticmethod
    def _render_section(
        section: list[ScriptItem],
        avatar_name: str,
        parts: list[str],
    ) -> None:
        for item in section:
            if item.command == TalkCommand.PLAIN_STRING:
                parts.append(item.text)
            elif item.command == TalkCommand.AVATARS_NAME:
                parts.append(avatar_name)
            elif item.command == TalkCommand.NEW_LINE:
                parts.append("\n")
            # Other command bytes (KEY_WAIT, PAUSE, KARMA_*, ASK_NAME, labels,
            # etc.) are silently dropped in this pass.
