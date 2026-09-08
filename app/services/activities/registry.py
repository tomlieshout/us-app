"""Maps activity_type -> the ActivityHandler instance that knows how to
run it. Adding a future game is: write a new handler module, import it and
add one line here - nothing else in the routes/serialization layer needs
to change."""

from app.services.activities.classic_question import ClassicQuestionActivity
from app.services.activities.emoji_story import EmojiStoryActivity
from app.services.activities.know_each_other import KnowEachOtherActivity
from app.services.activities.who_would import WhoWouldActivity
from app.services.activities.would_you_rather import WouldYouRatherActivity

_HANDLERS = {
    "classic_question": ClassicQuestionActivity(),
    "would_you_rather": WouldYouRatherActivity(),
    "know_each_other": KnowEachOtherActivity(),
    "emoji_story": EmojiStoryActivity(),
    "who_would": WhoWouldActivity(),
}


def get_handler(activity_type):
    handler = _HANDLERS.get(activity_type)
    if handler is None:
        raise ValueError(f"No activity handler registered for activity_type={activity_type!r}")
    return handler
