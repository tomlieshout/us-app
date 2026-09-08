"""
Mode 1 (app-provided / "guess") Emoji Story content. Seeded directly into
ActivityContent (activity_type="emoji_story", category="guess") - no
legacy-system equivalent, this game never existed before the Activity
architecture.

Each entry: emoji_sequence (what's shown) and explanation (the intended
meaning, hidden from the player until they've submitted their own guess -
see EmojiStoryActivity.redact_content_payload).
"""

EMOJI_STORY_GUESS_STORIES = [
    {"emoji_sequence": "🎬🍿😱", "explanation": "Watching a scary movie together"},
    {"emoji_sequence": "✈️🏖️🍹", "explanation": "A beach vacation"},
    {"emoji_sequence": "🌧️☂️🏃", "explanation": "Getting caught in the rain without an umbrella"},
    {"emoji_sequence": "🎂🎉🥳", "explanation": "A birthday party"},
    {"emoji_sequence": "😴⏰😫", "explanation": "The alarm going off way too early"},
    {"emoji_sequence": "🍳🔥🚨", "explanation": "Accidentally burning breakfast"},
    {"emoji_sequence": "💌📬😊", "explanation": "Getting a sweet message from someone you love"},
    {"emoji_sequence": "🚗🎶🛣️", "explanation": "A road trip with the music turned up"},
    {"emoji_sequence": "🐶🎾😄", "explanation": "Playing fetch with a dog at the park"},
    {"emoji_sequence": "☕📖🌧️", "explanation": "A cozy rainy day with coffee and a good book"},
    {"emoji_sequence": "🛒💸😅", "explanation": "Grocery shopping and spending more than planned"},
    {"emoji_sequence": "📱🔋0️⃣", "explanation": "Your phone dying at the worst possible moment"},
    {"emoji_sequence": "🍕🛋️📺", "explanation": "A lazy night in with pizza and a show"},
    {"emoji_sequence": "🏔️🥾😤", "explanation": "A tough but rewarding hike"},
    {"emoji_sequence": "🎁🤔🎀", "explanation": "Trying to guess what's inside a wrapped gift"},
    {"emoji_sequence": "🚿🎤🎶", "explanation": "Singing in the shower"},
    {"emoji_sequence": "🌙✨💭", "explanation": "Lying awake thinking about everything at once"},
    {"emoji_sequence": "🍜🥢😋", "explanation": "A satisfying bowl of noodles"},
    {"emoji_sequence": "🧹🏠😮‍💨", "explanation": "Finally finishing a big cleaning day"},
    {"emoji_sequence": "📦🚪😍", "explanation": "A package arriving that you were excited about"},
]
