import unittest
from unittest.mock import AsyncMock, patch

from bot import FEEDS, LABELS, format_stories, get_stories, main_menu, news_menu, Story


class BotTests(unittest.IsolatedAsyncioTestCase):
    def test_exactly_three_core_functions(self):
        self.assertEqual(set(FEEDS), {"latest", "us", "world"})
        self.assertEqual(len(LABELS), 3)

    def test_menu_has_three_core_buttons(self):
        markup = main_menu()
        buttons = [button for row in markup.inline_keyboard for button in row]
        self.assertEqual([b.callback_data for b in buttons], [
            "news:latest", "news:us", "news:world"
        ])

    def test_news_menu_has_refresh_and_home(self):
        markup = news_menu("latest")
        callbacks = [b.callback_data for row in markup.inline_keyboard for b in row if b.callback_data]
        self.assertIn("news:latest", callbacks)
        self.assertIn("home", callbacks)

    def test_story_formatting(self):
        stories = [Story("Example headline", "https://example.com/story", "Example Source")]
        text = format_stories("latest", stories)
        self.assertIn("Example headline", text)
        self.assertIn("Example Source", text)

    @patch("bot.fetch_feed", new_callable=AsyncMock)
    async def test_feed_fallback(self, fetch_feed):
        fetch_feed.side_effect = [
            RuntimeError("first source unavailable"),
            [Story("Working headline", "https://example.com", "Fallback")],
        ]
        stories = await get_stories("latest")
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0].source, "Fallback")


if __name__ == "__main__":
    unittest.main()
