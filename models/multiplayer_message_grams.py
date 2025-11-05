from collections import namedtuple

ConnectRequest  = namedtuple("ConnectRequest" , ["name", "dexterity", "location"])
ConnectResponse = namedtuple("ConnectResponse", ["network_id", "location"])

LocationUpdate  = namedtuple("LocationUpdate" , ["network_id", "location"])

DELIMITER = chr(0)


def to_message_gram(message_name: str, subject_network_id: str, data: list[str]):
    return [message_name, subject_network_id] + DELIMITER.join(data)

def from_message_gram(message: str) -> tuple[str, str, tuple]:
    parts = message.split(DELIMITER)
    message_name = parts[0]
    subject_network_id = parts[1]
    data = tuple(parts[2:])
    return message_name, subject_network_id, data

class MessageGram:
    @classmethod
    def from_incoming(cls, network_data: str):
        parts = network_data.split(DELIMITER)
        message_name = parts[0]
        subject_network_id = parts[1]
        data = tuple(parts[2:])
        return message_name, subject_network_id, data        

    def __init__(self, message_name: str, subject_network_id: str, data: tuple):
        self.message_name = message_name
        self.subject_network_id = subject_network_id
        self.data = data

    def to_outgoing(self):
        return [self.message_name, self.subject_network_id] + DELIMITER.join(self.data)
