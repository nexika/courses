"""Split a bill, tip included, between people, in whole cents."""


def split_bill(total_cents, tip_percent, people):
    """Return a list with what each person pays, in cents, largest share first."""
    if total_cents < 0:
        raise ValueError("the bill cannot be negative")
    if tip_percent < 0:
        raise ValueError("the tip cannot be negative")
    if people < 1:
        raise ValueError("at least one person must pay")
    tip_cents = (total_cents * tip_percent + 50) // 100  # nearest cent, a half cent rounds up
    share, left_over = divmod(total_cents + tip_cents, people)
    return [share + 1] * left_over + [share] * (people - left_over)
