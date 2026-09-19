"""
The Challenges content bank. Seeded into ActivityContent
(activity_type="challenge"). Spicy challenges (category="spicy") were
deliberately held back until this phase - see app/routes/challenges.py and
app/services/challenges.py for the dual-consent gating that now covers them
(hidden entirely while locked, normal - including in /mine - once
unlocked, same policy as every other Spicy content type in the app).

Each entry: prompt (the challenge text), category, and requires_both
(whether both partners need to explicitly confirm completion, or either
partner alone can mark it done).
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

# -------------------------------------------------------------- Spicy 🌶️
# Rewritten for an experienced couple: no "try a new position"-style vanilla
# prompts, and nothing that requires buying anything new - everything here
# either needs nothing at all, or reuses toys/restraints/gear you already
# have. "Going somewhere new" (a drive, a different room) is fine and used
# a couple of times - that's not a purchase, just a change of scene.
CHALLENGES += [
    {"prompt": "Have anal sex tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Spend five minutes on rimming (oral) before anything else happens tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug for the next hour while you carry on with whatever's already planned tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Spend longer on anal prep than you normally would", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner up for the next round", "category": "spicy", "requires_both": True},
    {"prompt": "Blindfold your partner for the next 10 minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner's wrists behind their back for the next round - whatever you've already got works", "category": "spicy", "requires_both": True},
    {"prompt": "Make the next round entirely rough from the start - no gentle build-up, straight into spanking and pace", "category": "spicy", "requires_both": True},
    {"prompt": "Pin your partner's wrists above their head for the entire next round - no letting go", "category": "spicy", "requires_both": True},
    {"prompt": "Slap - not just spank - at least once tonight, wherever you'd already agreed is fair game", "category": "spicy", "requires_both": True},
    {"prompt": "Use whichever vibrator you already own on your partner for five straight minutes before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Bring your favourite toy into tonight instead of saving it for later", "category": "spicy", "requires_both": True},
    {"prompt": "If you own a remote-control toy, wear it out tonight - dinner, a drive, wherever you're already going - and hand your partner the control", "category": "spicy", "requires_both": True},
    {"prompt": "Film 30 seconds of tonight on your phone - decide together afterward whether to keep it or delete it", "category": "spicy", "requires_both": True},
    {"prompt": "Film a whole sex tape tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex somewhere in the house you haven't yet - not the bedroom", "category": "spicy", "requires_both": True},
    {"prompt": "Go somewhere new tonight - a drive, a walk, anywhere you haven't been together - and have sex when you get there", "category": "spicy", "requires_both": False},
]

# -------------------------------------------------- Spicy 🌶️ - Round Two
# Checked against the 24 above for overlap. Pushes into new ground: edging
# as an actual count, oral specifics, partner-directs-verbally, a fantasy
# recreation, a randomiser mechanic, cross-referencing a WYR answer, and a
# couple more filming/sensory variants. Still nothing requires buying
# anything.
CHALLENGES += [
    {"prompt": "Suck your partners dick until they finish- no hands", "category": "spicy", "requires_both": True},\
    {"prompt": "Eat your partner out until they finish- no hands", "category": "spicy", "requires_both": True},
    {"prompt": "Skip every other kind of sex tonight and go straight for anal", "category": "spicy", "requires_both": True},
    {"prompt": "Pick a toy at random from your drawer, no choosing - use whatever you grab", "category": "spicy", "requires_both": True},
    {"prompt": "Use ice on your partner tonight - nothing else, just ice", "category": "spicy", "requires_both": True},
    {"prompt": "Tease everywhere except where your partner wants it most for five minutes before giving in", "category": "spicy", "requires_both": True},
    {"prompt": "Pick one answer from tonight's Would You Rather round and actually do it before bed", "category": "spicy", "requires_both": True},
    {"prompt": "Use a mirror already in the house to watch yourselves for part of tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Go for multiple rounds tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Whoever wakes up first has to wake the other one up by sitting on their face or putting their dick in the partners mouth", "category": "spicy", "requires_both": True},
    {"prompt": "Whoever wakes up first has to wake the other one up with oral, no matter the time", "category": "spicy", "requires_both": True},
]

# ------------------------------------------------ Spicy 🌶️ - Round Three
# Different flavour from the first two rounds on purpose: these are direct,
# specific, timed instructions rather than "try something new" prompts -
# many of them things an experienced couple already does regularly, just
# named explicitly with a duration or constraint attached. Nothing here
# requires buying anything.
CHALLENGES += [
    {"prompt": "Get oral for 10 minutes each before anything else happens tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Take turns - five minutes of oral each, switch when the timer's up", "category": "spicy", "requires_both": True},
    {"prompt": "69 for ten minutes straight, no separate turns", "category": "spicy", "requires_both": True},
    {"prompt": "No hands for the first ten minutes tonight - mouths only", "category": "spicy", "requires_both": True},
    {"prompt": "Only kiss for 20 minutes tonight - nothing else allowed", "category": "spicy", "requires_both": True},
    {"prompt": "Only touch each other with your hands for 15 minutes - no kissing, no more", "category": "spicy", "requires_both": True},
    {"prompt": "Make out for 20 minutes before any clothes come off", "category": "spicy", "requires_both": True},
    {"prompt": "Kiss everywhere except the lips for 5 minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Do anal tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Anal for the entire round, no switching to anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Ten minutes of anal prep before anything else happens", "category": "spicy", "requires_both": True},
    {"prompt": "Have anal with a plug that's already been in since earlier in the day", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner up for the whole round - no untying until it's over", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner's hands to something sturdy - the headboard, a door handle, whatever you've got - for fifteen minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Blindfold your partner for the entire round, start to finish", "category": "spicy", "requires_both": True},
    {"prompt": "Use a blindfold and restraints together for at least ten minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Have your partner grip the headboard the whole round - hands never let go", "category": "spicy", "requires_both": True},
    {"prompt": "Use oil on your partner's entire body for ten minutes before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Give an oiled massage that doesn't stop until it turns into sex", "category": "spicy", "requires_both": True},
    {"prompt": "Keep it completely gentle for the whole round - no rough moments at all", "category": "spicy", "requires_both": True},
    {"prompt": "Keep it rough the entire time - no gentle moments at all", "category": "spicy", "requires_both": True},
    {"prompt": "Switch from gentle to rough halfway through", "category": "spicy", "requires_both": True},
    {"prompt": "Use a vibrator on yourself while your partner watches for 5 minutes - no touching from them", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug for the entire time you have sex tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug around the house for an hour before anything starts", "category": "spicy", "requires_both": True},
    {"prompt": "Switch from rough to gentle halfway through", "category": "spicy", "requires_both": True},
    {"prompt": "Use a toy on your partner until they finish", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex in the car tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex in the shower tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex on the kitchen counter tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Give your partner a slow striptease before anything else happens", "category": "spicy", "requires_both": True},
    {"prompt": "Do it fully clothed tonight - just move what needs to move", "category": "spicy", "requires_both": True},
    {"prompt": "Have your partner blindfolded while you use your hands, your mouth, and one toy on them - five minutes each", "category": "spicy", "requires_both": True},
]

# ------------------------------------------- Long Distance 📱🌶️
# For when you're apart. No video, no audio (voice notes/calls), and no
# masturbation challenges that involve both partners at the same time -
# photos and text only. Its own category ("longdistance"), separate from
# "spicy" - browsable as its own tab - but still gated behind the same
# dual-consent Spicy unlock, since this is equally explicit content, just
# usable while apart. See SPICY_GATED_CATEGORIES in app/models/challenge.py
# and requires_spicy_unlock() in app/services/challenges.py for how the
# gating is shared between the two categories.
CHALLENGES += [
    {"prompt": "Send your partner one explicit photo", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a mirror selfie in exactly what you're wearing right now, however that looks", "category": "longdistance", "requires_both": False},
    {"prompt": "Send three photos back to back, each one going further than the last", "category": "longdistance", "requires_both": False},
    {"prompt": "Ask your partner to name a body part over text, then send a photo of just that", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a close-up photo of just your lips", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your chest, cropped so nothing else is visible", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your hands - one on your neck, one lower", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your thighs, pressed together", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your stomach and hips - nothing above or below", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your ass, taken from directly behind", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of your inner thigh, close up", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of your back, arched", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of just your neck and collarbone", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo taken from directly above, looking down at yourself", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo taken from below, looking up", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo taken in the mirror from across the room, full body", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo taken over your shoulder, looking back at the camera", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo taken lying down, camera held above you", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo from directly side-on, profile only", "category": "longdistance", "requires_both": False},
    {"prompt": "Send exactly one photo - no caption, no context, just the photo", "category": "longdistance", "requires_both": False},
    {"prompt": "Send five photos in a row, each one a closer crop than the last", "category": "longdistance", "requires_both": False},
    {"prompt": "Send two photos - one fully dressed, one seconds later with one item removed", "category": "longdistance", "requires_both": False},
    {"prompt": "Send four photos - front, back, and both sides", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a before-and-after pair - one photo now, one right after you finish", "category": "longdistance", "requires_both": False},
    {"prompt": "Send three photos of the exact same pose from three different angles", "category": "longdistance", "requires_both": False},
    {"prompt": "Send one photo a minute for five minutes straight", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a single close-up photo of just your hands, taken from above", "category": "longdistance", "requires_both": False},
    {"prompt": "Send two close-up photos of your chest, one from each side", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of your ass taken from below, like you're being looked up at", "category": "longdistance", "requires_both": False},
    {"prompt": "Send three photos, each one closer to your hips than the last", "category": "longdistance", "requires_both": False},
    {"prompt": "Ask your partner to pick a number from 1 to 5, then send exactly that many photos", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a photo, then make your partner guess what you were doing right before it was taken", "category": "longdistance", "requires_both": True},
    {"prompt": "Recreate a specific photo your partner has said they love, and send an updated version", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo of your hand, and describe over text exactly what you wish it was doing right now", "category": "longdistance", "requires_both": False},
    {"prompt": "Send an explicit photo with an innocent-sounding caption, just for the thrill", "category": "longdistance", "requires_both": False},
    {"prompt": "Tell your partner exactly when to expect a photo today, then actually send it right on time", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate, then send a photo the second you finish - no waiting, no cleaning up first", "category": "longdistance", "requires_both": False},
    {"prompt": "Set a timer and masturbate for exactly 10 minutes without finishing, then text your partner when the timer's up", "category": "longdistance", "requires_both": False},
    {"prompt": "Edge yourself three times over the course of an hour, texting your partner each time it happens", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate for exactly the length of one song, no more, no less", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate thinking about one specific memory, then describe over text exactly what you pictured", "category": "longdistance", "requires_both": False},
    {"prompt": "Use a toy on yourself, then send a photo of it right after", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate at a specific time your partner picks earlier in the day, then confirm by text afterward", "category": "longdistance", "requires_both": True},
    {"prompt": "Take a photo of yourself mid-masturbation, from the angle you'd want your partner watching from", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a message describing in explicit detail what you want to do to your partner the next time you see them", "category": "longdistance", "requires_both": False},
    {"prompt": "Have an entire text conversation using only dirty talk for fifteen minutes straight", "category": "longdistance", "requires_both": True},
    {"prompt": "Write out a full fantasy scene as a text message and send it in one go, no warning", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a countdown text every hour until you're back together, each one describing something different you want to do", "category": "longdistance", "requires_both": True},
    {"prompt": "Sext each other as though you're strangers meeting for the first time", "category": "longdistance", "requires_both": True},
    {"prompt": "Describe over text exactly what you're wearing right now, and what you'd want your partner to do about it", "category": "longdistance", "requires_both": False},
    {"prompt": "Roleplay an entire scenario through text messages, staying in character for at least fifteen minutes", "category": "longdistance", "requires_both": True},
    {"prompt": "If you own a remote-control toy, hand your partner control of it from wherever they are for ten minutes", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a message first thing in the morning describing exactly what you'll do to your partner the moment you're reunited", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a message describing the exact outfit you want your partner wearing when you're reunited", "category": "longdistance", "requires_both": False},
    {"prompt": "Text your partner the exact moment you start thinking about them today, and what you're thinking", "category": "longdistance", "requires_both": False},
]
