#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import logging
import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

import websockets as websockets
from bs4 import BeautifulSoup

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Package:
    class Type(Enum):
        chat = "chat"

    type: Type
    data: str

    @classmethod
    def from_json(cls, json_data: str) -> Package:
        dct = json.loads(json_data)
        return cls(type=Package.Type(dct["type"]), data=dct.get("data", ""))

    def to_chat_entry(self) -> ChatEntry:
        return ChatEntry.from_package(self)


@dataclass(frozen=True)
class ChatEntry:
    id: str
    message: str

    @classmethod
    def from_package(cls, package: Package) -> ChatEntry:
        return cls.from_html_str(package.data)

    @classmethod
    def from_html_str(cls, html: str) -> ChatEntry:
        soup = BeautifulSoup(html, 'html.parser')
        attrs = soup.find('div').attrs
        return cls(id=attrs.get('data-messageid', ''), message=soup.get_text())


class ChatBot:
    def __init__(self, msg_handler_func: Callable[[Package], Optional[str]],
                 address: str = "127.0.0.1", port: int = 5678):
        self._address = address
        self._port = port
        self._msg_handler_func = msg_handler_func
        self._handled_messages = set()

    def run_forever(self):
        LOG.info(f"Starting at: '{self._address}:{self._port}'")
        server = websockets.serve(ws_handler=self.handle, host=self._address, port=self._port)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    async def handle(self, s: websockets.WebSocketServerProtocol, path: str):
        LOG.debug(f"Opened a new connection")
        while True:
            msg = await s.recv()
            hashed_msg = hash(msg)
            if hashed_msg not in self._handled_messages:
                self._handled_messages.add(hashed_msg)
                p = Package.from_json(msg)
                LOG.debug(f"Received the following new message: {p}")
                try:
                    if answer := self._msg_handler_func(p):
                        LOG.debug(f"Sending the following answer: {answer}")
                        await s.send(answer)
                    else:
                        LOG.debug("Sending no answer")
                except Exception as e:
                    LOG.warning(f"While handling the message the following exception occurred: {e}")
            else:
                LOG.debug(f"Already received the following message: '{msg}'")


if __name__ == '__main__':
    def example_message_handler(p: Package) -> Optional[str]:
        """If the message is a '#' it returns a random number"""
        if p.type == Package.Type.chat:
            chat_msg = p.to_chat_entry()
            print(f"\texample_message_handler: {chat_msg}")
            return str(random.randint(0, 10)) if chat_msg.message == "#" else None


    logging.basicConfig(stream=sys.stdout, format='[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s')
    LOG.setLevel(logging.DEBUG)

    bot = ChatBot(example_message_handler)
    bot.run_forever()
