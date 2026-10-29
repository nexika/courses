"""Visual tokens for a 1920 x 1080 image: ceil(1920 / 28) * ceil(1080 / 28), as the "Try it" code computes."""
import json
import math

width, height = 1920, 1080
assert max(width, height) <= 2576  # within the high-resolution tier's long edge, so it is not resized
tokens = math.ceil(width / 28) * math.ceil(height / 28)
assert tokens <= 4784
print(json.dumps(tokens))
