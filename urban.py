from maubot import Plugin, MessageEvent
from maubot.handlers import event, command
from mautrix.types import TextMessageEventContent, MessageType, Format

import random

url_ud = 'http://api.urbandictionary.com/v0'
url_ud_random = f"{url_ud}/random"
url_ud_define = f"{url_ud}/define"

class UrbanDictBot(Plugin):
    @command.new("ud", help="Lookup urbandictionary.com. Syntax: !ud <term> [index]")
    @command.argument("term", pass_raw=True, required=False)
    async def handler(self, event: MessageEvent, term: str) -> None:
        
        # optional index for result set
        index = None

        if term:
            # Lookup specific term
            term = term.lower().strip() # sanitize

            # split input into term and index
            term_parts = term.split()
            if term_parts[-1].isdigit():
                index = int(term_parts[-1])
                del term_parts[-1]
                term = " ".join(term_parts)
            else:
                index = 1 # default to pick first element
                

            self.log.info(f"Looking up: {term}[{index}]")
            params = {'term': term}
            async with self.http.get(url_ud_define, params=params) as response:
                self.log.debug(response)
                if response.status != 200:
                    # quit with error message
                    await event.respond(f"Response error! (status: {response.status})")
                data = await response.json()

        else:
            # No search term passed, so get something random
            self.log.debug("Looking up random term")
            response = await self.http.get(url_ud_random)
            if response.status != 200:
                # quit with error message
                await event.respond(f"Response error! (status: {response.status})")
            data = await response.json()

        # Handle result
        self.log.debug(f"Result: {data}")
        result_list = data['list']

        # Quit if result is empty
        if not result_list:
            await event.respond(f"Term {term} not found.")

        # Pick definition from result list
        if index:
            # Try getting the requested definition
            try:
                definition = result_list[index - 1]
                def_text = " ".join(definition['definition'].split())
                def_text = self.truncate(def_text)
            except IndexError:
                return 'Not found.'
        else:
            # Pick a random entry
            definition = random.choice(result_list)
            
        # extract data
        word = definition['word']
        link = definition['permalink']
        text = " ".join(definition['definition'].split())
        text = self.truncate(text)

        content = TextMessageEventContent(
            msgtype = MessageType.NOTICE,
            body = self.get_output_plaintext(word, text, link, index),
            format = Format.HTML,
            formatted_body = self.get_output_html(word, text, link, index)
        )

        await event.respond(content)

    def truncate(self, text: str, length: int = 1000) -> str:
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '..'

    def get_output_plaintext(self, word: str, text: str, link: str, index: int) -> str:
        if index:
            return f"{word} [{index}]: {text} ({link})"
        else:
            return f"{word}: {text} ({link})"

    def get_output_html(self, word: str, text: str, link: str, index: int) -> str:
        if index:
            return f"<strong>{word}</strong> [{index}]: {text} (<a href='{link}'>link</a>)"
        else:
            return f"<strong>{word}</strong>: {text} (<a href='{link}'>link</a>)"
