"""
The Challenges content bank. Seeded into ActivityContent
(activity_type="challenge"). No spicy challenges here by explicit
instruction - that belongs to a later Spicy-specific phase, not this one.

Each entry: prompt (the challenge text) and requires_both (whether both
partners need to explicitly confirm completion, or either partner alone
can mark it done).
"""

CHALLENGES = []

# ------------------------------------------------------------------- Cute
CHALLENGES += [
    {"prompt": "Write down 3 things you love about each other and swap notes", "category": "cute", "requires_both": True},
    {"prompt": "Give each other a compliment you've never said out loud before", "category": "cute", "requires_both": True},
    {"prompt": "Hold hands for the next 10 minutes, no matter what you're doing", "category": "cute", "requires_both": True},
    {"prompt": "Send your partner a photo that makes you think of them, right now", "category": "cute", "requires_both": False},
    {"prompt": "Leave a sweet note somewhere your partner will find it today", "category": "cute", "requires_both": False},
    {"prompt": "Tell your partner your favourite memory of them from this past month", "category": "cute", "requires_both": False},
    {"prompt": "Give your partner a genuine compliment about something non-physical", "category": "cute", "requires_both": False},
    {"prompt": "Recreate your first photo together, as closely as you can", "category": "cute", "requires_both": True},
]

# ------------------------------------------------------------------ Funny
CHALLENGES += [
    {"prompt": "Do your best impression of each other for 30 seconds", "category": "funny", "requires_both": True},
    {"prompt": "Try to make each other laugh without touching or talking", "category": "funny", "requires_both": True},
    {"prompt": "Text each other using only emojis for the next hour", "category": "funny", "requires_both": True},
    {"prompt": "Come up with a secret handshake together", "category": "funny", "requires_both": True},
    {"prompt": "Give your partner a ridiculous new nickname and use it all day", "category": "funny", "requires_both": False},
    {"prompt": "Have a 60-second dance-off in your kitchen", "category": "funny", "requires_both": True},
    {"prompt": "Tell each other the most embarrassing thing that happened this week", "category": "funny", "requires_both": True},
    {"prompt": "Speak only in movie quotes for the next 15 minutes", "category": "funny", "requires_both": True},
]

# ------------------------------------------------------------------- Deep
CHALLENGES += [
    {"prompt": "Share a fear you haven't told your partner about", "category": "deep", "requires_both": False},
    {"prompt": "Talk about a moment you felt truly proud of your partner", "category": "deep", "requires_both": False},
    {"prompt": "Discuss one thing you each want to improve about how you communicate", "category": "deep", "requires_both": True},
    {"prompt": "Share what 'home' means to you, beyond a physical place", "category": "deep", "requires_both": False},
    {"prompt": "Talk about a lesson your younger self would be surprised you learned", "category": "deep", "requires_both": False},
    {"prompt": "Share something you're grateful for that you don't say often enough", "category": "deep", "requires_both": False},
    {"prompt": "Talk about a goal you have for the next year and how your partner can support it", "category": "deep", "requires_both": False},
    {"prompt": "Discuss what you each need most when you're going through a hard time", "category": "deep", "requires_both": True},
]

# --------------------------------------------------------------- Romantic
CHALLENGES += [
    {"prompt": "Plan a surprise date night for your partner, even a small one", "category": "romantic", "requires_both": False},
    {"prompt": "Write your partner a short love letter", "category": "romantic", "requires_both": False},
    {"prompt": "Slow dance together to one song, right now", "category": "romantic", "requires_both": True},
    {"prompt": "Recreate your first date somehow, even in a small way", "category": "romantic", "requires_both": True},
    {"prompt": "Tell your partner three reasons you'd choose them again", "category": "romantic", "requires_both": False},
    {"prompt": "Give each other a genuine, uninterrupted 5-minute hug", "category": "romantic", "requires_both": True},
    {"prompt": "Plan your dream trip together, no budget limits", "category": "romantic", "requires_both": True},
    {"prompt": "Write down your favourite thing about your relationship and share it", "category": "romantic", "requires_both": False},
]
