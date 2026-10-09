"""Split a bill, tip included, between people, in whole cents.

Take this change from plan to commit with Claude Code (see "Your exercise" in the lesson).
Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""


def split_bill(total_cents, tip_percent, people):
    """Return a list with what each person pays, in cents, largest share first.

    - total_cents (int): the bill before the tip, in cents. Must not be negative.
    - tip_percent (int): the tip, as a percent of the bill. Must not be negative.
    - people (int): how many people share the bill. Must be at least 1.

    The tip is tip_percent of total_cents, rounded to the nearest cent (a half cent rounds up).
    The shares add up to exactly the bill plus the tip, and no two shares differ by more than one
    cent: the cents that do not divide evenly go one each to the first people in the list.
    A negative total or tip, or fewer than one person, raises ValueError.
    """
    raise NotImplementedError("write split_bill")
