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
    {"prompt": "Have anal sex tonight and let your partner set the entire pace - you don't take control back once it starts", "category": "spicy", "requires_both": True},
    {"prompt": "Spend five minutes on rimming (oral) before anything else happens tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug for the next hour while you carry on with whatever's already planned tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Spend longer on anal prep than you normally would - fingers only, no rushing to the main event", "category": "spicy", "requires_both": True},
    {"prompt": "Use whatever you already have on hand - a tie, a scarf, actual cuffs - to restrain your partner's wrists for the next round", "category": "spicy", "requires_both": True},
    {"prompt": "Blindfold your partner and don't let them touch you back for the next 10 minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner's wrists behind their back for the next round - whatever you've already got works", "category": "spicy", "requires_both": True},
    {"prompt": "Restrain your partner and don't let them finish until they've asked at least three times", "category": "spicy", "requires_both": True},
    {"prompt": "Make the next round entirely rough from the start - no gentle build-up, straight into spanking and pace", "category": "spicy", "requires_both": True},
    {"prompt": "Give your partner ten open-hand spanks before anything else starts tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Pull your partner's hair the next time you kiss, and don't stop until they ask", "category": "spicy", "requires_both": True},
    {"prompt": "Pin your partner's wrists above their head for the entire next round - no letting go", "category": "spicy", "requires_both": True},
    {"prompt": "Slap - not just spank - at least once tonight, wherever you'd already agreed is fair game", "category": "spicy", "requires_both": True},
    {"prompt": "Use whichever vibrator you already own on your partner for five straight minutes before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Bring your favourite toy into tonight instead of saving it for later", "category": "spicy", "requires_both": True},
    {"prompt": "If you own a remote-control toy, wear it out tonight - dinner, a drive, wherever you're already going - and hand your partner the control", "category": "spicy", "requires_both": True},
    {"prompt": "Film 30 seconds of tonight on your phone - decide together afterward whether to keep it or delete it", "category": "spicy", "requires_both": True},
    {"prompt": "Take one photo of tonight together, then decide on the spot whether it stays or goes", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex somewhere in the house you haven't yet - not the bedroom", "category": "spicy", "requires_both": True},
    {"prompt": "Go somewhere new tonight - a drive, a walk, anywhere you haven't been together - and see what happens when you get there", "category": "spicy", "requires_both": False},
    {"prompt": "Take control completely for the next 20 minutes - your partner doesn't get a say in anything that happens", "category": "spicy", "requires_both": True},
    {"prompt": "Talk dirty out loud the entire time tonight - no going quiet", "category": "spicy", "requires_both": True},
    {"prompt": "Tell your partner exactly what you're about to do to them, step by step, right before you do it", "category": "spicy", "requires_both": False},
    {"prompt": "Send your partner a message right now describing exactly what you want to do to them tonight", "category": "spicy", "requires_both": False},
]

# -------------------------------------------------- Spicy 🌶️ - Round Two
# Checked against the 24 above for overlap. Pushes into new ground: edging
# as an actual count, oral specifics, partner-directs-verbally, a fantasy
# recreation, a randomiser mechanic, cross-referencing a WYR answer, and a
# couple more filming/sensory variants. Still nothing requires buying
# anything.
CHALLENGES += [
    {"prompt": "Edge your partner three times before letting them finish", "category": "spicy", "requires_both": True},
    {"prompt": "Use your mouth until your partner finishes tonight - no hands", "category": "spicy", "requires_both": True},
    {"prompt": "Skip every other kind of foreplay tonight and go straight for anal", "category": "spicy", "requires_both": True},
    {"prompt": "Let your partner talk you through exactly what to do, step by step, for the whole round", "category": "spicy", "requires_both": True},
    {"prompt": "Recreate the last fantasy your partner described to you, as closely as you can, tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Pick a toy at random from your drawer, no choosing - use whatever you grab", "category": "spicy", "requires_both": True},
    {"prompt": "Keep a hand on the back of your partner's neck - holding, not choking - for the entire round", "category": "spicy", "requires_both": True},
    {"prompt": "Talk your partner through a fantasy out loud while going down on them", "category": "spicy", "requires_both": True},
    {"prompt": "Use ice on your partner for the first two minutes tonight - nothing else, just ice", "category": "spicy", "requires_both": True},
    {"prompt": "Whisper something filthy in your partner's ear the second you're alone together tonight", "category": "spicy", "requires_both": False},
    {"prompt": "Tease everywhere except where your partner wants it most for five minutes before giving in", "category": "spicy", "requires_both": True},
    {"prompt": "Pick one answer from tonight's Would You Rather round and actually do it before bed", "category": "spicy", "requires_both": True},
    {"prompt": "Record audio only - no video - for part of tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have your partner direct you with words only, no touching from them, for 10 minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Use a mirror already in the house to watch yourselves for part of tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Go a full round with zero kissing - everything else is fair game", "category": "spicy", "requires_both": True},
    {"prompt": "Whoever initiates first tonight gets to decide everything that happens", "category": "spicy", "requires_both": True},
    {"prompt": "Go for a second round tonight instead of stopping after the first", "category": "spicy", "requires_both": True},
    {"prompt": "Give your partner a hand job while keeping eye contact the entire time - no looking away", "category": "spicy", "requires_both": True},
    {"prompt": "Go down on your partner first tonight, before anything else happens", "category": "spicy", "requires_both": True},
]

# ------------------------------------------------ Spicy 🌶️ - Round Three
# Different flavour from the first two rounds on purpose: these are direct,
# specific, timed instructions rather than "try something new" prompts -
# many of them things an experienced couple already does regularly, just
# named explicitly with a duration or constraint attached. Nothing here
# requires buying anything.
CHALLENGES += [
    {"prompt": "Go down on your partner for a full 10 minutes straight, no stopping", "category": "spicy", "requires_both": True},
    {"prompt": "Get oral for 15 minutes before anything else happens tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Give oral until your partner says that's enough - no rushing it", "category": "spicy", "requires_both": True},
    {"prompt": "Take turns - five minutes of oral each, switch when the timer's up", "category": "spicy", "requires_both": True},
    {"prompt": "69 for ten minutes straight, no separate turns", "category": "spicy", "requires_both": True},
    {"prompt": "No hands for the first ten minutes tonight - mouths only", "category": "spicy", "requires_both": True},
    {"prompt": "Only kiss for ten minutes tonight - nothing else allowed", "category": "spicy", "requires_both": True},
    {"prompt": "Only touch each other with your hands for fifteen minutes - no kissing, no more", "category": "spicy", "requires_both": True},
    {"prompt": "Make out for five minutes before any clothes come off", "category": "spicy", "requires_both": True},
    {"prompt": "Kiss everywhere except the lips for ten minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Do anal tonight - no discussion beforehand, just do it", "category": "spicy", "requires_both": True},
    {"prompt": "Anal for the entire round, no switching to anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Ten minutes of anal prep before anything else happens", "category": "spicy", "requires_both": True},
    {"prompt": "Have anal with a plug that's already been in since earlier in the day", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner up for the whole round - no untying until it's over", "category": "spicy", "requires_both": True},
    {"prompt": "Tie your partner's hands to something sturdy - the headboard, a door handle, whatever you've got - for fifteen minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Blindfold your partner for the entire round, start to finish", "category": "spicy", "requires_both": True},
    {"prompt": "Use a blindfold and restraints together for at least ten minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Restrain your partner's wrists and don't touch them anywhere else for the first five minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Have your partner grip the headboard the whole round - hands never let go", "category": "spicy", "requires_both": True},
    {"prompt": "Use oil on your partner's entire body for ten minutes before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Give an oiled massage that doesn't stop until it turns into sex", "category": "spicy", "requires_both": True},
    {"prompt": "Keep it completely gentle for the whole round - no rough moments at all", "category": "spicy", "requires_both": True},
    {"prompt": "Keep it rough the entire time - no gentle moments at all", "category": "spicy", "requires_both": True},
    {"prompt": "Switch from gentle to rough halfway through, no warning", "category": "spicy", "requires_both": True},
    {"prompt": "Use a vibrator on yourself while your partner watches - no touching from them", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug for the entire time you have sex tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Wear a butt plug around the house for an hour before anything starts", "category": "spicy", "requires_both": True},
    {"prompt": "Use the same toy for the entire round - nothing else allowed", "category": "spicy", "requires_both": True},
    {"prompt": "Use a toy on your partner until they finish, then switch to something else entirely", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex in the car tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex in the shower tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex on the kitchen counter tonight", "category": "spicy", "requires_both": True},
    {"prompt": "Have sex somewhere with the curtains open a crack", "category": "spicy", "requires_both": True},
    {"prompt": "Spank your partner for a full minute straight before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Spank your partner until they ask you to stop, then switch to something gentle", "category": "spicy", "requires_both": True},
    {"prompt": "Keep eye contact for the entire round - no looking away", "category": "spicy", "requires_both": True},
    {"prompt": "Describe out loud everything you're doing while you do it", "category": "spicy", "requires_both": True},
    {"prompt": "Stay completely silent for the whole round - no talking, no moaning out loud", "category": "spicy", "requires_both": True},
    {"prompt": "Blindfold your partner and explore with only your hands for ten minutes", "category": "spicy", "requires_both": True},
    {"prompt": "Use something soft - fingertips, silk, whatever's already around - to trace your partner's body for five minutes before anything else", "category": "spicy", "requires_both": True},
    {"prompt": "Undress your partner using only your mouth, no hands, for as long as it takes", "category": "spicy", "requires_both": True},
    {"prompt": "Give your partner a slow striptease before anything else happens", "category": "spicy", "requires_both": True},
    {"prompt": "Do it fully clothed tonight - just move what needs to move", "category": "spicy", "requires_both": True},
    {"prompt": "Have your partner blindfolded while you use your hands, your mouth, and one toy on them - five minutes each", "category": "spicy", "requires_both": True},
]

# ------------------------------------------- Long Distance 📱🌶️
# For when you're apart. Deliberately no video content for now (photos,
# audio, and text only). Its own category ("longdistance"), separate from
# "spicy" - browsable as its own tab - but still gated behind the same
# dual-consent Spicy unlock, since this is equally explicit content, just
# usable while apart. See SPICY_GATED_CATEGORIES in app/models/challenge.py
# and requires_spicy_unlock() in app/services/challenges.py for how the
# gating is shared between the two categories.
CHALLENGES += [
    {"prompt": "Send your partner one explicit photo right now, no warning", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a mirror selfie in exactly what you're wearing right now, however that looks", "category": "longdistance", "requires_both": False},
    {"prompt": "Send three photos back to back, each one going further than the last", "category": "longdistance", "requires_both": False},
    {"prompt": "Ask your partner to name a body part over text, then send a photo of just that", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a photo taken somewhere you could theoretically get caught", "category": "longdistance", "requires_both": False},
    {"prompt": "Send an explicit photo with a strict rule - they delete it right after viewing", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo styled exactly how you'd want your partner to find you if they walked in right now", "category": "longdistance", "requires_both": False},
    {"prompt": "Take a photo in the mirror with nothing on, no covering up", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo using a toy you own, no explanation needed", "category": "longdistance", "requires_both": False},
    {"prompt": "Exchange one explicit photo every hour for an entire day", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a close-up photo of the last place your partner touched you in person", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate while on the phone with your partner, describing what you're doing in real time", "category": "longdistance", "requires_both": True},
    {"prompt": "Masturbate to a photo your partner sent you, then tell them afterward", "category": "longdistance", "requires_both": False},
    {"prompt": "Set a timer and masturbate for exactly 10 minutes without finishing, then message them when the timer's up", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate at the same time as your partner, even though you're apart, then compare notes after", "category": "longdistance", "requires_both": True},
    {"prompt": "Edge yourself three times over the course of an hour, texting your partner each time it happens", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate for exactly the length of one song, no more, no less", "category": "longdistance", "requires_both": False},
    {"prompt": "Use a toy on yourself while describing every second of it over text", "category": "longdistance", "requires_both": False},
    {"prompt": "Masturbate thinking about the last time you were together, then describe exactly what you pictured", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a voice note of yourself moaning, no explanation needed", "category": "longdistance", "requires_both": False},
    {"prompt": "Call your partner and talk them through exactly what you'd do to them if you were together right now, voice only", "category": "longdistance", "requires_both": True},
    {"prompt": "Send an audio recording of yourself touching yourself - audio only, no video", "category": "longdistance", "requires_both": False},
    {"prompt": "Leave your partner a voicemail describing what you want done to you tonight", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a message describing in explicit detail what you want to do to your partner the next time you see them", "category": "longdistance", "requires_both": False},
    {"prompt": "Have an entire text conversation using only dirty talk for fifteen minutes straight", "category": "longdistance", "requires_both": True},
    {"prompt": "Write out a full fantasy scene as a text message and send it in one go, no warning", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a countdown text every hour until you're back together, each one describing something different you want to do", "category": "longdistance", "requires_both": True},
    {"prompt": "Sext each other as though you're strangers meeting for the first time", "category": "longdistance", "requires_both": True},
    {"prompt": "Describe over text exactly what you're wearing right now, and what you'd want your partner to do about it", "category": "longdistance", "requires_both": False},
    {"prompt": "Roleplay an entire scenario through text messages, staying in character for at least fifteen minutes", "category": "longdistance", "requires_both": True},
    {"prompt": "If you own a remote-control toy, hand your partner control of it from wherever they are for ten minutes", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a message first thing in the morning describing exactly what you'll do to your partner the moment you're reunited", "category": "longdistance", "requires_both": False},
    {"prompt": "Plan out loud over the phone exactly what will happen the moment you're back together, in explicit detail", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a message describing the exact outfit you want your partner wearing when you're reunited", "category": "longdistance", "requires_both": False},
    {"prompt": "Text your partner the exact moment you start thinking about them today, and what you're thinking", "category": "longdistance", "requires_both": False},
    {"prompt": "Describe your day so far, but rewrite it as if something explicit happened at every stop", "category": "longdistance", "requires_both": False},
    {"prompt": "Send a photo, then make your partner guess what you were doing right before it was taken", "category": "longdistance", "requires_both": True},
    {"prompt": "Pick a specific time today - both masturbate separately at that exact moment, then confirm to each other after", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a voice note reading a fantasy out loud instead of typing it", "category": "longdistance", "requires_both": False},
    {"prompt": "Ask your partner what they're wearing, then tell them exactly what you'd do if you were there right now", "category": "longdistance", "requires_both": True},
    {"prompt": "Send a photo of your hand, and describe exactly what you wish it was doing right now", "category": "longdistance", "requires_both": False},
    {"prompt": "Recreate a specific photo your partner has said they love, and send an updated version", "category": "longdistance", "requires_both": False},
    {"prompt": "Send an explicit photo with an innocent-sounding caption, just for the thrill", "category": "longdistance", "requires_both": False},
    {"prompt": "Tell your partner exactly when to expect a photo today, then actually send it right on time", "category": "longdistance", "requires_both": False},
    {"prompt": "Have your partner pick a specific song, then send a photo or voice note timed to when it ends", "category": "longdistance", "requires_both": True},
]
