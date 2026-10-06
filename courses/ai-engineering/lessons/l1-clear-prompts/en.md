# Writing clear prompts

## What you will be able to do

- Turn a vague request into a prompt that states the task directly and gives Claude the context it lacks.
- Add examples and say exactly what shape the answer must have.
- Separate the parts of a prompt with XML tags, and leave out the parts you do not need.

## The idea

A prompt is the text you send to the model: your instructions, plus everything the model needs to
follow them. In the previous lesson you sent one through the API. This lesson is about what to put in it.

Claude sees only the prompt. It does not know your product, your users, or what your code will do
with its answer. Anthropic's guide asks you to think of Claude as "a brilliant but new employee who
lacks context on your norms and workflows"[^employee]. It also gives a test you can use on any prompt:
show it to a colleague who knows little about the task and ask them to follow it; if they would be
confused, Claude will be too[^golden].

Here is a vague prompt:

```text
Sort this ticket: "I was charged twice this month."
```

Sort it into what? Which answers are allowed? Should the reply be one word, a sentence, or a
paragraph that explains its reasoning? Claude has to guess. The model's predictions have some randomness[^random], so two calls can guess
differently.

Here is the same request, written clearly:

```text
<task>
Classify the support ticket below into exactly one category: billing, bug or feature_request.
</task>

<context>
We sell a photo-editing app. Each ticket goes to the team that owns its category, so a wrong category makes the customer wait for the wrong team.
</context>

<examples>
<example>
Ticket: The export button does nothing since the last update.
Category: bug
</example>
<example>
Ticket: Could you add a dark mode?
Category: feature_request
</example>
</examples>

<output_format>
Reply with the category name only, in lowercase, with nothing before or after it.
</output_format>

<ticket>
I was charged twice this month.
</ticket>
```

It makes five moves. Each one comes from Anthropic's prompting guide.

**Say the task directly.** Claude responds well to clear, explicit instructions[^clear]. Name the
action and the answers you accept: "classify into exactly one category: billing, bug or
feature_request", not "sort this".

**Give the context Claude lacks.** Explaining the reason behind an instruction can help Claude
understand your goals and give more targeted answers[^context]. Here the context says who the
company is and what a wrong category costs. Claude cannot know either fact unless you write it.

**Show examples.** Examples are one of the most reliable ways to steer the format, tone and
structure of Claude's answers[^examples]. The guide recommends three to five of them[^count], and
asks that they be diverse: they should cover edge cases (unusual or borderline inputs) and vary enough that Claude does not pick up
patterns you did not intend[^diverse]. The prompt above has only two, to stay short. A real
classifier (a program that sorts inputs into fixed categories) would add more, including a hard case such as a refund request caused by a bug.

**Specify the output format.** Be specific about the format and the constraints you want[^format].
Your code will compare Claude's reply with a list of categories: `billing` matches,
`This looks like a billing issue.` does not. Say what to do rather than only what not to
do[^positive]: "reply with the category name only" works better than "do not explain".

**Separate the parts with XML tags.** XML tags help Claude read a prompt that mixes instructions,
context, examples and variable inputs without confusing one part for another[^xml]. A tag is a name
in angle brackets, `<context>`, closed by the same name with a slash, `</context>`. Examples go in
`<example>` tags, all inside one `<examples>` tag, so Claude can tell them apart from the
instructions[^example-tags]. The ticket is a variable input: it changes on every call, so it gets a
tag of its own and the customer's words never run into your instructions.

XML is a way of marking up text with tags like these. Your prompt does not have to be valid XML,
and there is no fixed list of tag names: a consistent, descriptive name such as `<ticket>` is
enough[^tag-names].

A clear prompt makes a good answer more likely. It does not guarantee one: Claude can still choose
the wrong category. And not every problem is best solved by changing the prompt: latency or cost,
for example, can sometimes be improved more easily by choosing a different model[^not-always]. The next lesson shows how to test a prompt against expected
answers, so you know whether a change helped.

## Try it

This script builds both prompts and prints them. It uses only the standard library and makes no
network call. Save it as `try_prompt.py` and run `python3 try_prompt.py`.

```python
"""Print a vague prompt and a clear one built from tagged parts."""


def tag(name, text):
    return f"<{name}>\n{text.strip()}\n</{name}>"


vague = 'Sort this ticket: "I was charged twice this month."'

examples = [
    "Ticket: The export button does nothing since the last update.\nCategory: bug",
    "Ticket: Could you add a dark mode?\nCategory: feature_request",
]
clear = "\n\n".join([
    tag("task", "Classify the support ticket below into exactly one category: billing, bug or feature_request."),
    tag("context", "We sell a photo-editing app. Each ticket goes to the team that owns its category, "
                   "so a wrong category makes the customer wait for the wrong team."),
    tag("examples", "\n".join(tag("example", example) for example in examples)),
    tag("output_format", "Reply with the category name only, in lowercase, with nothing before or after it."),
    tag("ticket", "I was charged twice this month."),
])

print("--- vague ---")
print(vague)
print()
print("--- clear ---")
print(clear)
```

The output is the two prompts from "The idea". Change one part, for example delete the
`output_format` line, and look at what Claude would no longer be told.

The prompts here are in English so the code is the same in every language of this course. Claude
works well in many other languages[^languages], so you can write your own prompts in yours.

### Send it to Claude

If you have an API key from the previous lesson, you can send both prompts and compare the answers.
Add these lines at the end of `try_prompt.py`. This part calls the network and costs a little; it is
optional.

```python
import anthropic

MODEL = "..."  # the model id you used in the previous lesson
client = anthropic.Anthropic()
for prompt in (vague, clear):
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    # the reply can start with other blocks, such as thinking: print the first text block
    print(next(block.text for block in message.content if block.type == "text"))
    print("---")
```

Run it a few times. Look at whether the answer to the vague prompt is something your code could use.

## Common mistakes

**"Claude knows what I mean."** It knows only what is in the prompt. If a new colleague would need
to ask a question, write the answer into the prompt.

**"A longer prompt is a better prompt."** Length is not the goal. Every part should tell Claude
something it needs. An empty `<context>` tag, or a section that says "none", adds noise and no
information. Leave it out.

**"Telling Claude what not to do is enough."** "Do not explain" leaves the shape of the answer open.
Say what the answer should be instead[^positive].

**"My examples all look alike, so they are consistent."** Examples that all share an accident, such
as the same length or the same category, can teach Claude that accident[^diverse]. Vary them on
purpose.

**"XML tags are special commands I must learn."** There is no list to memorize: use consistent,
descriptive tag names across your prompts[^tag-names]. `<ticket>` is fine because it says what is
inside.

**"Tags make the input safe."** Tags show Claude where the input starts and ends. Do not count on
them alone to stop text inside the input from acting like an instruction. The course comes back to
this when it covers prompt injection.

## Your exercise

Open `exercise/starter/prompt_builder.py` and write
`build_prompt(task, context, examples, output_format, input_text)`.
It returns one string:

- each part, with the spaces around it removed, in its own tag, in this order: `<task>`,
  `<context>`, `<examples>`, `<output_format>`, and last `<input>`;
- each example in its own `<example>` tag, all inside `<examples>`;
- the variable input (such as the ticket) in `<input>`, last, so it never runs into your instructions;
- a tag on its own line before and after its content, and one blank line between parts;
- an empty or blank part, or a blank example, left out entirely;
- an empty task refused with a `ValueError`, because a prompt with no task has nothing to ask.

Run the tests from the starter folder:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your function is right. A solution is in `exercise/solution/`; try on your own first.

## Check yourself

Answer the questions in `quiz.json`. If they are hard, read "The idea" again and look at what each
of the five parts of the clear prompt gives Claude.

[^employee]: Anthropic, Prompting best practices.
[^golden]: Anthropic, Prompting best practices.
[^clear]: Anthropic, Prompting best practices.
[^context]: Anthropic, Prompting best practices.
[^examples]: Anthropic, Prompting best practices.
[^count]: Anthropic, Prompting best practices.
[^diverse]: Anthropic, Prompting best practices.
[^format]: Anthropic, Prompting best practices.
[^positive]: Anthropic, Prompting best practices.
[^xml]: Anthropic, Prompting best practices.
[^example-tags]: Anthropic, Prompting best practices.
[^tag-names]: Anthropic, Prompting best practices.
[^not-always]: Anthropic, Prompt engineering overview.
[^random]: Anthropic, Glossary, "Temperature".
[^languages]: Anthropic, Multilingual support.
