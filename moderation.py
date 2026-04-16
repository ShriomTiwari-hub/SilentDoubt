# filter.py — content moderation
# basic toxicity check using keyword matching
# not perfect but good enough for our project
# TODO: maybe expand this list later

# rude/harmful keywords and phrases to block
# keeping this simple — pure string matching, no ML needed
_BAD_WORDS = [
    # profanity
    "fuck", "shit", "bitch", "bastard", "asshole", "ass", "damn", "crap",
    # general insults targeting teachers/students
    "stupid teacher", "dumb teacher", "useless teacher", "trash teacher",
    "idiot teacher", "stupid student", "dumb student",
    "you are stupid", "ur stupid", "ur dumb", "you're dumb",
    "you're stupid", "your dumb", "your stupid",
    # spam/nonsense signals
    "aaaaaaa", "hahahaha", "lololol",
]

def is_toxic(text):
    """
    Check if the given text contains harmful or rude content.
    Returns (is_bad: bool, reason: str)
    """
    t = text.lower().strip()
    for word in _BAD_WORDS:
        if word in t:
            return True, word
    return False, ""
