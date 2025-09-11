# based on meta/llama's idea of what needs capturing after scanning the first three NPC's dialog
# https://wiki.ultimacodex.com/wiki/Ultima_V_transcript

class Character:
    def __init__(self, name, description, greeting, job, goodbye):
        self.name = name
        self.description = description
        self.greeting = greeting
        self.job = job
        self.goodbye = goodbye
        self.dialogue = []

class DialogueEntry:
    def __init__(self, trigger, response, label=None, actions=None):
        self.trigger = trigger
        self.response = response
        self.label = label
        self.actions = actions if actions else []

class Label:
    def __init__(self, id, text):
        self.id = id
        self.text = text

class Trigger:
    def __init__(self, keyword):
        self.keyword = keyword

class Response:
    def __init__(self, text):
        self.text = text

class Action:
    def __init__(self, type, value):
        self.type = type
        self.value = value

# Example usage:
alistair = Character("Alistair", "a melancholy musician", "A fine day to thee!", "I try to lift people's spirits through my music!", "Good day to thee, friend!")

trigger = Trigger("spir or musi")
response = Response("Once, this was a happy place, where all could come to shed the worries of the world for a brief time.")
dialogue_entry = DialogueEntry(trigger, response)

alistair.dialogue.append(dialogue_entry)