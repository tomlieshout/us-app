"""
The initial question bank. Kept as plain data (not hardcoded into templates
or route code) so more questions can be added later just by editing this
list and re-running `python seed/seed.py` - see section 41/42 of the brief.

Each entry is a dict. Defaults are filled in by seed.py:
    text            (required)
    category        (required) one of app.models.question.CATEGORIES
    qtype           (required) one of app.models.question.QUESTION_TYPES
    options         (optional) list[str] - required for multiple_choice,
                    rating, structured_scale, and prediction
    predict_text    (optional) only for qtype == "prediction"
    spicy_level     (optional) 1/2/3, only for category == "spicy"
    match_eligible  (optional) bool, only meaningful for spicy structured_scale
"""

from app.models.question import INTEREST_SCALE

RATING_1_10 = [str(i) for i in range(1, 11)]

QUESTIONS = []

# ---------------------------------------------------------------- Relationship
QUESTIONS += [
    {"text": "What's your favourite memory of us so far?", "category": "relationship", "qtype": "free_text"},
    {"text": "What do I do that makes you feel most loved?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something about our relationship you're proud of?", "category": "relationship", "qtype": "free_text"},
    {"text": "When did you first realise you were falling for me?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something we should do more often?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a small thing I do that means more to you than I probably realise?", "category": "relationship", "qtype": "free_text"},
    {"text": "How do you like to be comforted when you're having a hard day?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a habit of mine you've grown to love?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something you've learned about love from being with me?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's your favourite way for us to spend a lazy day?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's one thing that's gotten better about us over time?", "category": "relationship", "qtype": "free_text"},
    {"text": "How do you know when I'm stressed, even if I don't say anything?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a tradition (big or small) you'd like us to start?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something I do that always makes you smile?", "category": "relationship", "qtype": "free_text"},
    {"text": "How important is it to you that we say 'I love you' often?", "category": "relationship", "qtype": "rating", "options": RATING_1_10},
    {"text": "What's your love language, and do you think I speak it well?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something you appreciate about how we handle disagreements?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a compliment you wish I gave you more often?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's the most 'us' thing we do together?", "category": "relationship", "qtype": "free_text"},
    {"text": "How do you like to be supported when you're chasing a big goal?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something you've never told me about why you love me?", "category": "relationship", "qtype": "free_text"},
    {"text": "On a scale of 1-10, how good are we at communicating right now?", "category": "relationship", "qtype": "rating", "options": RATING_1_10},
    {"text": "What's a moment you felt closest to me recently?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something I could do to make an ordinary day feel special?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a strength of mine you rely on in our relationship?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's something you want me to know you're grateful for?", "category": "relationship", "qtype": "free_text"},
    {"text": "How do you like to celebrate the small wins in our relationship?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's a nickname or inside joke of ours that always makes you laugh?", "category": "relationship", "qtype": "free_text"},
    {"text": "What does 'home' mean to you when you think of us?", "category": "relationship", "qtype": "free_text"},
    {"text": "What's one thing you never want to change about us?", "category": "relationship", "qtype": "free_text"},
]

# --------------------------------------------------------- How Well Do You Know Me
QUESTIONS += [
    {"text": "What's your idea of the perfect night in?", "category": "know_me", "qtype": "prediction",
     "options": ["Movie & takeout", "Cooking together", "Board games or a puzzle", "Just talking for hours", "Curled up with a book each"],
     "predict_text": "What do you think your partner would pick as the perfect night in?"},
    {"text": "If we had a free Saturday with no plans, what would you want to do?", "category": "know_me", "qtype": "prediction",
     "options": ["Sleep in and do nothing", "Go on a spontaneous adventure", "Get productive around the house", "See friends", "Have a whole day just for us"],
     "predict_text": "What do you think your partner would want to do with a free Saturday?"},
    {"text": "What's your go-to comfort food?", "category": "know_me", "qtype": "prediction",
     "options": ["Pizza", "Pasta", "Ice cream", "Something spicy", "Baked goods"],
     "predict_text": "What do you think your partner's comfort food is?"},
    {"text": "Which of these describes your ideal holiday?", "category": "know_me", "qtype": "prediction",
     "options": ["Beach relaxation", "City exploring", "Mountains & hiking", "Road trip", "Somewhere cosy and remote"],
     "predict_text": "What would your partner choose for the perfect holiday?"},
    {"text": "What's your biggest love language?", "category": "know_me", "qtype": "prediction",
     "options": ["Words of affirmation", "Quality time", "Physical touch", "Acts of service", "Gifts"],
     "predict_text": "Which love language do you think matters most to your partner?"},
    {"text": "If you could instantly master one skill, what would it be?", "category": "know_me", "qtype": "prediction",
     "options": ["Cooking", "A musical instrument", "A new language", "Painting or drawing", "Dancing"],
     "predict_text": "What skill do you think your partner would want to instantly master?"},
    {"text": "What's your favourite season?", "category": "know_me", "qtype": "prediction",
     "options": ["Spring", "Summer", "Autumn", "Winter"],
     "predict_text": "What's your partner's favourite season?"},
    {"text": "How do you prefer to spend a birthday?", "category": "know_me", "qtype": "prediction",
     "options": ["A big party", "A quiet dinner for two", "A weekend away", "Surrounded by family", "Something low-key at home"],
     "predict_text": "How do you think your partner prefers to spend their birthday?"},
    {"text": "What's your biggest pet peeve?", "category": "know_me", "qtype": "prediction",
     "options": ["Being late", "Loud chewing", "Leaving lights on", "Messy spaces", "Interrupting"],
     "predict_text": "What do you think is your partner's biggest pet peeve?"},
    {"text": "What's your ideal way to unwind after a hard day?", "category": "know_me", "qtype": "prediction",
     "options": ["Exercise", "Watching something", "Talking it out", "Being alone for a bit", "Music"],
     "predict_text": "How do you think your partner unwinds after a hard day?"},
    {"text": "Which would you pick for a date night?", "category": "know_me", "qtype": "prediction",
     "options": ["Fancy dinner out", "Cooking together at home", "A concert or show", "An outdoor activity", "Something new and unexpected"],
     "predict_text": "What would your partner pick for date night?"},
    {"text": "What's more you: mornings or nights?", "category": "know_me", "qtype": "prediction",
     "options": ["Definitely mornings", "Definitely nights", "A bit of both", "Neither, honestly"],
     "predict_text": "Is your partner more of a morning or night person?"},
    {"text": "What's your dream pet, if you could have any?", "category": "know_me", "qtype": "prediction",
     "options": ["Dog", "Cat", "Something exotic", "No pets, thanks", "All of the above"],
     "predict_text": "What pet do you think your partner secretly wants?"},
    {"text": "Which superpower would you choose?", "category": "know_me", "qtype": "prediction",
     "options": ["Flying", "Reading minds", "Time travel", "Invisibility", "Teleportation"],
     "predict_text": "Which superpower do you think your partner would choose?"},
    {"text": "What's your ideal home vibe?", "category": "know_me", "qtype": "prediction",
     "options": ["Minimalist and calm", "Cosy, full of memories", "Modern and sleek", "Full of plants", "Somewhere with a great view"],
     "predict_text": "What home vibe do you think your partner is drawn to?"},
    {"text": "Which would you rather give up for a year?", "category": "know_me", "qtype": "prediction",
     "options": ["Coffee", "Social media", "Sweets", "Music", "Streaming shows"],
     "predict_text": "What do you think your partner would rather give up for a year?"},
    {"text": "What's your go-to karaoke song style?", "category": "know_me", "qtype": "prediction",
     "options": ["A power ballad", "Something upbeat and fun", "A duet", "I'd refuse to sing", "A song from my teenage years"],
     "predict_text": "What kind of song do you think your partner would pick for karaoke?"},
    {"text": "What's your biggest source of day-to-day stress?", "category": "know_me", "qtype": "prediction",
     "options": ["Work or study", "Money", "Time management", "Family stuff", "Overthinking"],
     "predict_text": "What do you think stresses your partner out the most day-to-day?"},
    {"text": "What kind of movie do you reach for most?", "category": "know_me", "qtype": "prediction",
     "options": ["Comedy", "Romance", "Action or thriller", "Horror", "Documentary"],
     "predict_text": "What genre do you think your partner reaches for most?"},
    {"text": "How do you like to be woken up?", "category": "know_me", "qtype": "prediction",
     "options": ["Gently, time to wake slowly", "Straight to coffee, no talking", "With music", "Cuddles first", "Honestly, don't wake me"],
     "predict_text": "How do you think your partner likes to be woken up?"},
    {"text": "What's your ideal way to work through an argument?", "category": "know_me", "qtype": "prediction",
     "options": ["Talk it out immediately", "Take space first, then talk", "Write it out before speaking", "Humour to break the tension", "A mix of all of these"],
     "predict_text": "How do you think your partner prefers to work through an argument?"},
    {"text": "What's your dream 'someday' purchase?", "category": "know_me", "qtype": "prediction",
     "options": ["A house", "A big trip", "A car", "Something creative", "I'd rather save it"],
     "predict_text": "What do you think your partner's dream someday purchase is?"},
    {"text": "What show or movie do you always rewatch for comfort?", "category": "know_me", "qtype": "prediction",
     "options": ["A sitcom", "A childhood favourite", "One specific movie on repeat", "I don't really rewatch things", "Something with you specifically"],
     "predict_text": "What do you think your partner rewatches for comfort?"},
    {"text": "Which best describes your ideal Sunday?", "category": "know_me", "qtype": "prediction",
     "options": ["Slow mornings, no alarms", "Get things done early, then relax", "Outdoors for most of the day", "Social, seeing people", "A mix of chores and rest"],
     "predict_text": "What does your partner's ideal Sunday look like?"},
    {"text": "What's the first thing you'd do with unexpected free time?", "category": "know_me", "qtype": "prediction",
     "options": ["Nap", "Call you", "Get creative", "Catch up on a show", "Go outside"],
     "predict_text": "What do you think your partner would do first with unexpected free time?"},
]

# ------------------------------------------------------------------- Future
QUESTIONS += [
    {"text": "Where would you love for us to travel together?", "category": "future", "qtype": "free_text"},
    {"text": "What would our ideal home look like?", "category": "future", "qtype": "free_text"},
    {"text": "What do you hope we're doing in five years?", "category": "future", "qtype": "free_text"},
    {"text": "What's one experience you definitely want us to share?", "category": "future", "qtype": "free_text"},
    {"text": "What's a skill you'd love for us to learn together?", "category": "future", "qtype": "free_text"},
    {"text": "What's something you hope never changes about us, even years from now?", "category": "future", "qtype": "free_text"},
    {"text": "What's a tradition you'd want to build together over time?", "category": "future", "qtype": "free_text"},
    {"text": "If we could live anywhere for a year, where would you choose?", "category": "future", "qtype": "free_text"},
    {"text": "What's a goal of yours that you'd love my support with?", "category": "future", "qtype": "free_text"},
    {"text": "What does your ideal future weekend routine with me look like?", "category": "future", "qtype": "free_text"},
    {"text": "What's something you're looking forward to doing together this year?", "category": "future", "qtype": "free_text"},
    {"text": "What kind of home do you picture us in one day - city, countryside, somewhere else?", "category": "future", "qtype": "free_text"},
    {"text": "What's a big adventure you want us to have before we're too old for it?", "category": "future", "qtype": "free_text"},
    {"text": "What's something on your bucket list you'd only want to do with me?", "category": "future", "qtype": "free_text"},
    {"text": "How do you imagine us celebrating a big milestone, like an anniversary?", "category": "future", "qtype": "free_text"},
    {"text": "What's a value you hope we always build our future around?", "category": "future", "qtype": "free_text"},
    {"text": "What's something about getting older together that excites you?", "category": "future", "qtype": "free_text"},
    {"text": "What's a project you'd love us to take on together someday?", "category": "future", "qtype": "free_text"},
    {"text": "What's one way you'd like us to grow, individually, over the next few years?", "category": "future", "qtype": "free_text"},
    {"text": "How important is it to you that we plan things out versus stay spontaneous?", "category": "future", "qtype": "rating", "options": RATING_1_10},
]

# --------------------------------------------------------------- Random/Funny
QUESTIONS += [
    {"text": "If I were an animal, what would I be?", "category": "random", "qtype": "free_text"},
    {"text": "Which one of us would survive longer in a zombie apocalypse?", "category": "random", "qtype": "multiple_choice",
     "options": ["Definitely me", "Definitely you", "We'd survive together or not at all", "Neither of us, let's be honest"]},
    {"text": "If we started a business together, what would we sell?", "category": "random", "qtype": "free_text"},
    {"text": "What's the dumbest thing we've ever argued about?", "category": "random", "qtype": "free_text"},
    {"text": "If our relationship were a movie genre, what would it be?", "category": "random", "qtype": "multiple_choice",
     "options": ["Romantic comedy", "Buddy adventure", "Slow-burn drama", "Action movie", "A mockumentary, honestly"]},
    {"text": "What's the weirdest food combination you actually enjoy?", "category": "random", "qtype": "free_text"},
    {"text": "If you had to describe me as a weather forecast, what would it be?", "category": "random", "qtype": "free_text"},
    {"text": "What's a completely useless talent you have?", "category": "random", "qtype": "free_text"},
    {"text": "If we swapped bodies for a day, what's the first thing you'd do?", "category": "random", "qtype": "free_text"},
    {"text": "What's the most ridiculous thing you've caught yourself doing when you thought no one was watching?", "category": "random", "qtype": "free_text"},
    {"text": "Which fictional couple do we remind you of most?", "category": "random", "qtype": "free_text"},
    {"text": "If our relationship had a theme song, what genre would it be?", "category": "random", "qtype": "multiple_choice",
     "options": ["Pop anthem", "Slow romantic ballad", "Something chaotic and upbeat", "A duet", "An epic movie score"]},
    {"text": "What's the most 'you' thing you've ever done?", "category": "random", "qtype": "free_text"},
    {"text": "If you could give past-you one piece of relationship advice, what would it be?", "category": "random", "qtype": "free_text"},
    {"text": "What's a food you refuse to compromise on when we're deciding what to eat?", "category": "random", "qtype": "free_text"},
    {"text": "If we were cast in a sitcom, what would the show be called?", "category": "random", "qtype": "free_text"},
    {"text": "What's something small that always makes you laugh, no matter how many times it happens?", "category": "random", "qtype": "free_text"},
    {"text": "If you had to pick a mascot for our relationship, what would it be?", "category": "random", "qtype": "free_text"},
    {"text": "What's the most chaotic plan we've ever actually pulled off?", "category": "random", "qtype": "free_text"},
    {"text": "On a scale of 1-10, how competitive are you when we play games together?", "category": "random", "qtype": "rating", "options": RATING_1_10},
]

# ----------------------------------------------------------------------- Deep
QUESTIONS += [
    {"text": "What's something you're afraid to lose?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you've changed your mind about since we started dating?", "category": "deep", "qtype": "free_text"},
    {"text": "What do you think makes a relationship last?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you wish people understood about you?", "category": "deep", "qtype": "free_text"},
    {"text": "What's a fear you've never fully told me about?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something from your childhood that still shapes how you love people?", "category": "deep", "qtype": "free_text"},
    {"text": "What does being truly understood feel like to you?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you're still learning to forgive yourself for?", "category": "deep", "qtype": "free_text"},
    {"text": "What's a belief about love you held before us that's changed?", "category": "deep", "qtype": "free_text"},
    {"text": "What does emotional safety look like to you in a relationship?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you need more of from the people who love you?", "category": "deep", "qtype": "free_text"},
    {"text": "What's a moment that quietly changed who you are?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you're proud of that you rarely get credit for?", "category": "deep", "qtype": "free_text"},
    {"text": "What does it mean to you to be truly known by someone?", "category": "deep", "qtype": "free_text"},
    {"text": "What's a part of yourself you're still working on accepting?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something you wish you'd learned earlier about relationships?", "category": "deep", "qtype": "free_text"},
    {"text": "How do you personally define happiness right now in your life?", "category": "deep", "qtype": "free_text"},
    {"text": "What's a value you'd never compromise on, even for love?", "category": "deep", "qtype": "free_text"},
    {"text": "What's something difficult you've grown from in the past year?", "category": "deep", "qtype": "free_text"},
    {"text": "How do you want to be remembered by the people closest to you?", "category": "deep", "qtype": "free_text"},
]

# ------------------------------------------------------------------ Memories
QUESTIONS += [
    {"text": "What do you remember most about our first date?", "category": "memories", "qtype": "free_text"},
    {"text": "What's one trip together you'll never forget?", "category": "memories", "qtype": "free_text"},
    {"text": "What was your funniest moment together?", "category": "memories", "qtype": "free_text"},
    {"text": "What's the first thing you noticed about me?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a memory of us that always makes you smile when you think of it?", "category": "memories", "qtype": "free_text"},
    {"text": "What's the most 'we really did that' moment we've shared?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a small, ordinary moment with me that stuck with you?", "category": "memories", "qtype": "free_text"},
    {"text": "What's your favourite photo of us, and why?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a meal or restaurant that holds a special memory for us?", "category": "memories", "qtype": "free_text"},
    {"text": "What's the first gift I gave you that you remember?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a memory from early on that told you this could be something real?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a moment we got through something hard together that you're proud of?", "category": "memories", "qtype": "free_text"},
    {"text": "What's the silliest inside joke that started from a real memory?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a memory of us that you'd want to relive exactly as it happened?", "category": "memories", "qtype": "free_text"},
    {"text": "What's a moment when you knew you could just be fully yourself with me?", "category": "memories", "qtype": "free_text"},
]

# ------------------------------------------------------------- Long Distance
QUESTIONS += [
    {"text": "What's something you wish we could do together right now?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's the first thing you want to do when we're together again?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What part of our calls do you look forward to most?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's something we could start doing together despite the distance?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's the hardest part of being apart for you right now?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's something small you do that makes the distance feel a little smaller?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's a way I can support you better while we're apart?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What do you miss most about being in the same room as me?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's something you look forward to about the next time we see each other?", "category": "longdistance", "qtype": "free_text"},
    {"text": "How do you like to stay connected on a day when we can't talk much?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's something about long distance that's surprised you, good or bad?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's a way we could 'do' something together virtually that we haven't tried yet?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's a countdown or goal that's helping you get through the distance?", "category": "longdistance", "qtype": "free_text"},
    {"text": "What's something you've learned about yourself from being in a long-distance relationship?", "category": "longdistance", "qtype": "free_text"},
    {"text": "On a scale of 1-10, how are you really feeling about the distance lately?", "category": "longdistance", "qtype": "rating", "options": RATING_1_10},
]

# ------------------------------------------------------------------- Spicy 🌶️
# Optional, disabled by default, requires both partners to opt in
# independently (see app/routes/settings.py + services/privacy.spicy_unlocked).
# Kept tasteful and relationship-focused per the brief - none of this is
# graphic; it's phrased as discussion/comfort-level prompts.

# 🌶️ Flirty
QUESTIONS += [
    {"text": "What was your first real 'butterflies' moment with me?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's something I do without realising that you find really attractive?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What outfit of mine do you secretly love the most?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's your favourite way for us to flirt with each other?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's a compliment about your looks you'd love to hear from me more?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "Where's your favourite place for me to kiss you?", "category": "spicy", "qtype": "multiple_choice", "spicy_level": 1,
     "options": ["Forehead", "Cheek", "Neck", "Lips", "Hands"]},
    {"text": "What's a moment our chemistry felt undeniable to you?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's something about the way we look at each other that you love?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "Do you prefer slow-burn tension or getting straight to the point?", "category": "spicy", "qtype": "multiple_choice", "spicy_level": 1,
     "options": ["Slow burn, all the way", "A bit of both", "Straight to the point", "Depends on my mood"]},
    {"text": "What's a small, everyday moment that turns you on more than people would expect?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's your love language when it comes to physical affection specifically?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
    {"text": "What's a way I could surprise you that would make you blush?", "category": "spicy", "qtype": "free_text", "spicy_level": 1},
]

# 🌶️🌶️ Intimate - mostly structured_scale so answers can feed "Find your matches"
QUESTIONS += [
    {"text": "Trying a new date-night ritual built around romance and anticipation", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Writing each other a private, intimate letter to read together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Setting aside a phone-free evening focused entirely on each other", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Planning a surprise 'just for us' evening with no explanation beforehand", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Talking more openly about what makes each of us feel desired", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Trying a slower, more intentional pace during intimate time together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Exploring a new kind of massage or touch together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Creating a shared 'yes / no / maybe' list to talk through comfort levels", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Being more verbal about what feels good in the moment", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Trying some light roleplay or pretend together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Being more spontaneous about intimacy rather than always planning it", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Incorporating more anticipation or teasing before getting intimate", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 2, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "What makes you feel most desired by me?", "category": "spicy", "qtype": "free_text", "spicy_level": 2},
]

# 🌶️🌶️🌶️ Adventurous
QUESTIONS += [
    {"text": "Exploring a new setting or location together for intimacy (within reason)", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Trying a blindfold or another simple sensory-focused experience", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Incorporating toys or props into intimate time together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Trying a themed night with a costume or roleplay scenario", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Exploring light power-dynamic play, taking turns leading", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Trying a room or spot at home you haven't been intimate in before", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Being more spontaneous - initiating intimacy in an unplanned moment", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "Exploring light restraint play together", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
    {"text": "What's a fantasy you're comfortable sharing that we haven't talked about before?", "category": "spicy", "qtype": "free_text", "spicy_level": 3},
    {"text": "Trying a 'surprise' day where one partner plans an intimate experience for the other", "category": "spicy", "qtype": "structured_scale",
     "spicy_level": 3, "options": INTEREST_SCALE, "match_eligible": True},
]
