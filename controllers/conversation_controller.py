import pygame

from dark_libraries.dark_math import Vector2
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent     import PartyAgent
from models.agents.town_npc_agent  import TownNpcAgent
from models.enums.inventory_offset import InventoryOffset
from models.party_inventory        import PartyInventory
from models.tlk_file               import (
    NpcDialog,
    ScriptItem,
    ScriptLine,
    TalkCommand,
    TlkLabel,
    change_operand_kind,
    change_operand_to_inventory,
    is_label_byte,
    label_byte_to_num,
)

from services.console_service import ConsoleService
from services.input_service   import InputService, keycode_to_char
from services.npc_service     import NpcService


KEYWORD_MAX_CHARS = 4


class ConversationController(LoggerMixin):

    # Injectable
    party_agent:     PartyAgent
    party_inventory: PartyInventory
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
        description = self._render_text_only(dialog, dialog.description, target_npc, avatar_name)
        self._say(f"You see {description}" if description else "You see someone.")

        # Greeting may be just a label byte (Eb the busboy) — _render_and_speak
        # follows the goto into the label's initial_line.
        active_label = self._render_and_speak(dialog, dialog.greeting, target_npc, avatar_name)

        while True:
            keyword = self._read_keyword()
            if keyword is None or keyword == "" or keyword == "bye":
                self._render_and_speak(dialog, dialog.bye, target_npc, avatar_name)
                return

            response_line = self._lookup(dialog, keyword, target_npc, active_label, avatar_name)
            if response_line is None:
                # The user typed a keyword that matched nothing in the NPC-
                # level or label-level Q&A. If we're inside a label, fall
                # back to its default answers (Redux ScriptTalkLabel pattern);
                # otherwise give the generic deflection.
                if active_label and active_label.default_answers:
                    new_active = None
                    for default in active_label.default_answers:
                        result = self._render_and_speak(dialog, default, target_npc, avatar_name)
                        if result is not None:
                            new_active = result
                    active_label = new_active
                else:
                    self._npc_speak("That I cannot help thee with.")
                continue

            active_label = self._render_and_speak(dialog, response_line, target_npc, avatar_name)

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

    def _read_keyword(self, prompt: str = "Your interest?") -> str | None:
        """
        Read a word terminated by Enter. Escape or a synthetic-quit event
        returns None to abort the conversation. The match limit (first
        KEYWORD_MAX_CHARS characters) is applied later at lookup time; the
        user is free to type the whole word for immersion.
        """
        self.console_service.print_ascii(prompt, no_prompt=True)
        self.console_service.print_ascii(":", include_carriage_return=False, no_prompt=True)
        buffer = ""
        while True:
            event = self.input_service.get_next_event()
            if getattr(event, "type", 0) == pygame.QUIT or getattr(event, "key", 0) == -1:
                return None
            if event.key == pygame.K_RETURN:
                self.console_service.print_ascii("", no_prompt=True)
                self.console_service.print_ascii("", no_prompt=True)
                return buffer.lower()
            if event.key == pygame.K_ESCAPE:
                self.console_service.print_ascii("", no_prompt=True)
                self.console_service.print_ascii("", no_prompt=True)
                return None
            if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                if buffer:
                    buffer = buffer[:-1]
                    self.console_service.backspace()
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
        active_label: TlkLabel | None,
        avatar_name: str,
    ) -> ScriptLine | None:
        # Baked-in keywords that every NPC answers. Note: "name" synthesises a
        # "My name is ..." prefix and then renders the real name line, which
        # may carry ASK_NAME at the end — we build a combined line so the
        # rendering pipeline handles both cases uniformly.
        if keyword == "name":
            name_text = self._render_text_only(dialog, dialog.name, npc, avatar_name)
            if not name_text and not dialog.name.contains_command(TalkCommand.ASK_NAME):
                return None
            prefix = ScriptItem(TalkCommand.PLAIN_STRING, "My name is ")
            return ScriptLine(items=[prefix] + list(dialog.name.items))
        if keyword in ("job", "work"):
            return dialog.job
        if keyword == "look":
            return dialog.description

        prefix = keyword[:KEYWORD_MAX_CHARS]

        # Label-scoped keywords take precedence when we're in a label —
        # Redux checks ScriptTalkLabel.QuestionAnswers first before falling
        # through to the NPC-level bank.
        if active_label:
            for kw, response_line in active_label.keyword_responses.items():
                if kw[:KEYWORD_MAX_CHARS] == prefix:
                    return response_line

        for kw, response_line in dialog.keyword_responses.items():
            if kw[:KEYWORD_MAX_CHARS] == prefix:
                return response_line
        return None

    def _avatar_name(self) -> str:
        saved = self.global_registry.saved_game
        if saved is None:
            return "Avatar"
        name = saved.create_character_record(0).name
        return name if name else "Avatar"

    # -----------------------------------------------------------------
    # Rendering / speaking pipeline
    # -----------------------------------------------------------------

    def _render_and_speak(
        self,
        dialog: NpcDialog,
        line: ScriptLine,
        npc: TownNpcAgent,
        avatar_name: str,
    ) -> TlkLabel | None:
        """
        Render a ScriptLine as an NPC utterance. Follows label gotos by
        switching to the label's initial_line and continuing. Handles
        ASK_NAME inline — when encountered, the text accumulated so far is
        spoken, the Avatar is prompted for a name, and the result
        (match/mismatch) is spoken as a follow-up.

        Returns the last label that a goto landed on, so the caller can
        scope subsequent keyword lookups to that label.
        """
        pending_lines: list[ScriptLine] = [line]
        buffer: list[str] = []
        active_label: TlkLabel | None = None
        visited_labels: set[int] = set()

        def flush_buffered():
            text = "".join(buffer).strip()
            buffer.clear()
            if text:
                self._npc_speak(text)

        while pending_lines:
            current = pending_lines.pop(0)
            goto_label, aborted = self._render_line_to_buffer(
                dialog, current, npc, avatar_name, buffer, flush_buffered,
                apply_changes=True,
            )
            if aborted:
                break
            if goto_label is not None:
                # Cyclic label graph (A→B→A) — stop following gotos and
                # emit whatever we've accumulated so far.
                if goto_label.label_num in visited_labels:
                    self.log(
                        f"DEBUG: cyclic label goto detected at label "
                        f"{goto_label.label_num}; aborting render"
                    )
                    break
                visited_labels.add(goto_label.label_num)
                active_label = goto_label
                pending_lines = [goto_label.initial_line]

        flush_buffered()
        return active_label

    def _render_text_only(
        self,
        dialog: NpcDialog,
        line: ScriptLine,
        npc: TownNpcAgent,
        avatar_name: str,
    ) -> str:
        """
        Render a ScriptLine to plain text without emitting anything to the
        console. Follows label gotos. ASK_NAME is skipped (descriptions and
        preview text don't trigger interactive prompts).
        """
        pending_lines: list[ScriptLine] = [line]
        buffer: list[str] = []
        visited_labels: set[int] = set()

        def do_nothing():
            return

        while pending_lines:
            current = pending_lines.pop(0)
            goto_label, _aborted = self._render_line_to_buffer(
                dialog, current, npc, avatar_name, buffer, do_nothing,
                skip_ask_name=True,
                apply_changes=False,
            )
            if goto_label is not None:
                if goto_label.label_num in visited_labels:
                    break
                visited_labels.add(goto_label.label_num)
                pending_lines = [goto_label.initial_line]

        return "".join(buffer).strip()

    def _render_line_to_buffer(
        self,
        dialog: NpcDialog,
        line: ScriptLine,
        npc: TownNpcAgent,
        avatar_name: str,
        buffer: list[str],
        flush_callback,
        skip_ask_name: bool = False,
        apply_changes: bool = False,
    ) -> tuple[TlkLabel | None, bool]:
        """
        Walk the sections of a ScriptLine, appending rendered text to buffer.
        Honours IF_ELSE_KNOWS_NAME skip-instructions (mirrors Ultima5Redux's
        ProcessMultipleLines). Returns (goto_label, aborted): goto_label is
        set when a label byte was encountered; aborted is True when a GOLD
        transaction failed and the caller should stop rendering this line.
        """
        has_met  = npc.has_met_avatar
        sections = line.split_into_sections()
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

            # A section that references the Avatar's name but the NPC hasn't
            # been introduced yet is dropped entirely.
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
                goto_label, aborted = self._render_section_items(
                    section, dialog, npc, avatar_name, buffer, flush_callback,
                    skip_ask_name, apply_changes,
                )
                if aborted:
                    return None, True
                if goto_label is not None:
                    return goto_label, False

            if skip_counter != -1:
                skip_counter -= 1

            if skip_instruction == "skip_after_next":
                skip_counter = 1
            elif skip_instruction == "skip_next":
                i += 1

            i += 1
        return None, False

    def _render_section_items(
        self,
        section: list[ScriptItem],
        dialog: NpcDialog,
        npc: TownNpcAgent,
        avatar_name: str,
        buffer: list[str],
        flush_callback,
        skip_ask_name: bool,
        apply_changes: bool,
    ) -> tuple[TlkLabel | None, bool]:
        skip_next = False
        for item in section:
            if skip_next:
                # The label byte immediately after START_LABEL_DEFINITION is
                # the label's OWN identifier, not a goto. Mirrors Redux's
                # ProcessLine nItem++ — without this, rendering a label's
                # initial_line would infinite-loop back into itself.
                skip_next = False
                continue
            cmd = item.command
            if cmd == TalkCommand.PLAIN_STRING:
                buffer.append(item.text)
            elif cmd == TalkCommand.AVATARS_NAME:
                buffer.append(avatar_name)
            elif cmd == TalkCommand.NEW_LINE:
                buffer.append("\n")
            elif cmd == TalkCommand.ASK_NAME:
                if skip_ask_name or npc.has_met_avatar:
                    continue
                flush_callback()
                self._handle_ask_name(npc, avatar_name)
            elif cmd == TalkCommand.CHANGE:
                if apply_changes and item.operand is not None:
                    self._apply_change(item.operand)
            elif cmd == TalkCommand.GOLD:
                # Inline transaction: deduct `operand` gold. If the avatar
                # can't afford it, replace the response with a refusal and
                # signal the caller to abort the rest of the line so the
                # subsequent thank-you text and any CHANGE-bytes don't fire.
                if apply_changes and item.operand is not None:
                    if not self.party_inventory.use(InventoryOffset.GOLD, item.operand):
                        buffer.clear()
                        buffer.append("Thou hast not the gold.")
                        return None, True
            elif cmd == TalkCommand.START_LABEL_DEFINITION:
                skip_next = True
            elif is_label_byte(cmd):
                label = dialog.labels.get(label_byte_to_num(cmd))
                if label is not None:
                    return label, False
            # KEY_WAIT, PAUSE, KARMA_*, END_CONVERSATION, DO_NOTHING_SECTION,
            # and other command bytes are silently dropped.
        return None, False

    def _apply_change(self, operand: int):
        # Mirrors TALK.OVL's CHANGE (0x86) handler at file offset 0x0682:
        # most operands add 1 to a slot (capped); the SEXTANTS / SPY_GLASSES /
        # BLACK_BADGE flags are written as 0xFF instead of being incremented.
        target = change_operand_to_inventory(operand)
        if target is None:
            return
        kind = change_operand_kind(operand)
        if kind == "set_flag":
            saved = self.global_registry.saved_game
            if saved is None:
                return
            saved.write_u8(target.value, 0xFF)
        elif kind == "add":
            self.party_inventory.safe_add(target, 1)

    def _handle_ask_name(self, npc: TownNpcAgent, avatar_name: str):
        response = self._read_keyword(prompt="What is thy name?")
        if response is None:
            return
        if response.strip().lower() == avatar_name.strip().lower():
            npc.has_met_avatar = True
            self._npc_speak("A pleasure")
        else:
            self._npc_speak("If you say so")
