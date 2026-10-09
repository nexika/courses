"""The split function before and after the change shown in the lesson (the same code as see_the_diff.py)."""


def tip(total, percent):
    return round(total * percent / 100, 2)


def split_before(total, percent, people):
    return round((total + tip(total, percent)) / people, 2)


def split_after(total, percent, people):
    if people < 1:
        raise ValueError("people must be at least 1")
    return round(total / people + tip(total, percent), 2)
