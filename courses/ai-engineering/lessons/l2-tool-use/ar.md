# أعطِ Claude أداة

## ما الذي ستتمكن من فعله

- تعرّف أداة: اسمها، ووصفًا يقول متى تُستخدم، ومخطط JSON Schema لمُدخلاتها.
- تقرأ طلب Claude لأداة، وتشغّل الأداة في كودك، وتعيد إليه النتيجة.
- تشغّل حلقة الأدوات: تستمر ما دام Claude يطلب أدوات، وتتوقف حين يجيب.

## الفكرة

لا يستطيع Claude أن يبحث عن طلبية في قاعدة بيانات متجرك، فهو لم يرَ هذه البيانات قط. لكن كودك يستطيع.
**استخدام الأدوات (tool use)**، ويُسمّى أيضًا استدعاء الدوال (function calling)، يتيح لـ Claude أن يستدعي
دوال تعرّفها أنت[^ov-what]. أنت تصف الأداة، وClaude يقرّر متى يستدعيها، بناءً على طلب المستخدم ووصف
الأداة[^ov-what].

النموذج لا يشغّل شيئًا بنفسه أبدًا. إنه يكتب طلبًا منظّمًا، فيشغّل كودك العملية، وتعود النتيجة إلى
المحادثة[^hw-contract]. ولا يرى Claude كودك: لا يرى إلا التعريف الذي أعطيته والنتيجة التي
أعدتها[^hw-sees].

يوضع تعريف الأداة في القائمة `tools` داخل الطلب[^dt-tools]. وله ثلاثة أجزاء[^dt-fields]:

- `name`: أحرف لاتينية وأرقام و`_` أو `-`، وطوله 128 حرفًا على الأكثر[^dt-fields].
- `description`: ما تفعله الأداة، ومتى تُستخدم، وكيف تتصرف.
- `input_schema`: مخطط JSON Schema لمُدخلات الأداة، مثل مخططات الدرس السابق.

```json
{
  "name": "lookup_order",
  "description": "Look up a customer's order by its order number and return its status. Use it when the user asks where an order is or whether it has shipped. It returns only the status and the days to delivery, not what the order contains.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {"type": "string", "description": "The order number, such as A-1042."}
    },
    "required": ["order_id"]
  }
}
```

الوصف أهم من أي شيء آخر: يعدّه دليل Anthropic أهم عامل على الإطلاق في جودة عمل الأداة[^dt-desc]، ويطلب ثلاث جمل
أو أربعًا على الأقل[^dt-sentences].

هذا هو **تبادل الأدوات**، للسؤال `Where is order A-1042?`:

1) ترسل السؤال والقائمة `tools`.
2) يجيب Claude بسبب التوقف `tool_use` وكتلة `tool_use`. في الكتلة معرّف `id`، واسم الأداة `name`،
   وكائن مُدخلات `input` لها[^hc-block]. وكثيرًا ما يكتب Claude قبلها كتلة نص قصيرة، مثل
   "I'll look up that order."[^dt-comment]
3) يشغّل كودك الأداة بهذه المُدخلات.
4) ترسل طلبًا جديدًا: المحادثة كلها حتى الآن، وإجابة Claude جولةً للمساعد `assistant`، وجولة للمستخدم
   `user` فيها كتلة `tool_result`. قيمة `tool_use_id` فيها هي `id` الاستدعاء الذي تجيب عنه، و`content`
   فيها هو النتيجة[^hc-result].
5) يقرأ Claude النتيجة ويكتب إجابته[^hc-continue].

الخطوات من الثانية إلى الرابعة تشكّل **دورة** واحدة: إجابة تطلب أدوات، مع النتائج التي يعيدها كودك.

قد تحمل الإجابة كتلة `tool_use` واحدة أو أكثر[^hc-block]: أجب عن كل واحدة. وليس في Claude API دور خاص
اسمه `tool`: استدعاءات الأدوات تأتي في جولات `assistant`، والنتائج في جولات `user`[^hc-roles]. وهناك
قاعدتان في الترتيب. يجب أن تأتي نتائج الأدوات مباشرة بعد الجولة التي طلبتها، دون أي رسالة بينهما. وفي
جولة `user` هذه، تأتي كتل `tool_result` أولًا، قبل أي نص[^hc-order].

**حلقة الأدوات** تكرّر ذلك. ما دام سبب التوقف `tool_use`، شغّل الأدوات وتابع المحادثة. وأي سبب توقف آخر
ينهي الحلقة: فإما أن Claude أجاب، وإما أنه توقف لسبب يجب أن يعالجه كودك[^hw-loop]. وكل دورة تكلّف طلبًا جديدًا،
وكل طلب يرسل التاريخ كله من جديد[^stateless]، فضع حدًا لعدد الدورات.

للأدوات كلفة بالرموز (tokens). تُحسب تعريفات الأدوات رموزًا للإدخال[^ov-price]، وتضيف الواجهة موجّه نظام
(system prompt) يفعّل استخدام الأدوات[^ov-enables]: 286 رمزًا على Claude Opus 5.5[^ov-prompt].

## جرّبها

### دون مفتاح: دورة واحدة بيدك

في المجلد `exercise/tests/` إجابتان نموذجيتان، على شكل الإجابات الحقيقية لكنهما ليستا تسجيلًا لاستدعاءات
حقيقية: استدعاء Claude للأداة `lookup_order`، ثم إجابته الأخيرة. هنا تقومان مقام Claude. احفظ هذا
الكود باسم `one_round.py` في مجلد الدرس، وشغّل `python3 one_round.py` من ذلك المجلد:

```python
"""One round of the tool exchange, offline: two sample replies stand in for Claude."""
import json
from pathlib import Path

folder = Path("exercise/tests")
replies = [json.loads((folder / name).read_text(encoding="utf-8"))
           for name in ("sample_tool_call.json", "sample_final_answer.json")]


def lookup_order(order_id):
    """Real code would ask the shop's database. This one knows a single order."""
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
reply = replies[0]  # the reply to request 1: Claude asks for the tool
print("stop_reason:", reply["stop_reason"])
messages.append({"role": "assistant", "content": reply["content"]})
results = []
for block in reply["content"]:
    if block["type"] == "tool_use":
        print("Claude calls", block["name"], "with", block["input"])
        output = lookup_order(**block["input"])
        results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(output)})
messages.append({"role": "user", "content": results})
print("request 2 sends", len(messages), "messages:", [m["role"] for m in messages])
reply = replies[1]  # the reply to request 2: Claude answers with the result
print("stop_reason:", reply["stop_reason"])
print("".join(block["text"] for block in reply["content"] if block["type"] == "text"))
```

تمرّر `lookup_order(**block["input"])` حقول المُدخلات وسائطَ مسمّاة (keyword arguments)، فيصبح
`{"order_id": "A-1042"}` هو `lookup_order(order_id="A-1042")`. يرسل الطلب الثاني 3 رسائل: السؤال،
واستدعاء Claude، والنتيجة.

### بمفتاحك الخاص (اختياري)

هذا الكود يشغّل الحلقة الحقيقية، فيحتاج إلى مفتاح، والرموز التي يستهلكها مدفوعة. جهّز المفتاح وحزمة
SDK كما في درس «أول استدعاء لواجهة Claude البرمجية».

```python
import json

import anthropic

client = anthropic.Anthropic()
tools = [{
    "name": "lookup_order",
    "description": ("Look up a customer's order by its order number and return its status. "
                    "Use it when the user asks where an order is or whether it has shipped. "
                    "It returns only the status and the days to delivery, not what the order contains."),
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order number, such as A-1042."}},
        "required": ["order_id"],
    },
}]


def lookup_order(order_id):
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
for request_number in range(6):  # at most 5 rounds, then the answer: the loop cannot run forever
    response = client.messages.create(model="claude-opus-5-5", max_tokens=1024, tools=tools, messages=messages)
    if response.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": response.content})
    results = []
    for block in response.content:
        if block.type == "tool_use":
            output = lookup_order(**block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
    messages.append({"role": "user", "content": results})
if response.stop_reason == "tool_use":
    print("Stopped: Claude still wanted tools after 5 rounds.")
print("stop_reason:", response.stop_reason)
print("".join(block.text for block in response.content if block.type == "text"))
```

تستطيع حزمة SDK أيضًا أن تشغّل هذه الحلقة عنك، عبر Tool Runner فيها[^hc-runner]. اكتب الحلقة بيدك
أولًا، كي تعرف ما الذي تفعله.

## أخطاء شائعة

- **«Claude يشغّل دالتي».** لا يفعل أبدًا. إنه يطلب، وكودك يشغّل ويُبلغ بالنتيجة[^hw-contract]. وكودك
  هو الذي يقرّر ما يُسمح للأداة بفعله.
- **وصف من سطر واحد.** الوصف هو أهم ما لدى Claude ليختار الأداة ويملأ مُدخلاتها[^dt-desc]. قل ما تفعله
  الأداة، ومتى تُستخدم، وما الذي لا تعيده.
- **نسيان جولة `assistant`.** يجب أن يحمل الطلب التالي إجابة Claude، بكتل `tool_use` فيها، قبل نتائجك.
  فالواجهة عديمة الحالة (stateless): لا تتذكر الاستدعاء[^stateless].
- **نص قبل النتائج.** في جولة النتائج، تأتي كتل `tool_result` أولًا. والنص قبلها يجعل الطلب يفشل بخطأ[^hc-400].
- **الإجابة عن الاستدعاء الأول وحده.** قد تحمل الإجابة عدة كتل `tool_use`[^hc-block]. أرسل نتيجة لكل
  واحدة، مربوطة بقيمة `tool_use_id`.
- **الثقة العمياء بالمُدخلات.** حين يُغفل المستخدم قيمة إلزامية، يكون احتمال أن يطلبها Claude Opus
  أكبر بكثير من احتمال أن يطلبها Claude Sonnet[^ov-ask]، لكن Claude قد يخمّن قيمة أيضًا، مثل رقم طلبية لم يذكره المستخدم قط[^ov-guess]. افحص المُدخلات قبل أن تعمل بها.
- **الثقة بما تعيده الأداة.** صفحات الويب والرسائل وغيرها من المحتوى الخارجي قد تخفي تعليمات موجّهة إلى
  Claude[^hc-untrusted2]. عامل نتائج الأدوات على أنها غير موثوقة، وأبقِ هذا المحتوى داخل كتل `tool_result`، لا في
  موجّه النظام ولا في نصك أنت[^hc-untrusted].
- **فرض أداة عبر `tool_choice`.** الحقل `tool_choice` حقل اختياري في الطلب يمكنه أن يُلزم Claude
  باستخدام أداة[^dt-choice]: `auto` يترك الخيار لـ Claude، و`any` يُلزمه باستدعاء أداة ما، و`tool` يُلزمه
  بأداة محددة بالاسم. وعلى Claude Opus 5.5، إذا ضبطته على `any` أو `tool` أعاد الطلب خطأً[^dt-forced]. اتركه على `auto`، القيمة الافتراضية[^ov-auto]، واكتب وصفًا أو موجّهًا
  (prompt) أفضل.

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/tools.py` واكتب أربع دوال. إنها تعمل دون اتصال: في الاختبارات، يؤدي بديل
(stand-in) دور Claude، كما في الدرس السابق.

- `define_tool(name, description, properties, required)` تعيد تعريف أداة. ارفع `ValueError` لاسم سترفضه
  الواجهة، أو لوصف فارغ، أو لحقل إلزامي غير موجود في `properties`.
- `tool_calls(response)` تعيد استدعاءات الأدوات في الإجابة، بترتيبها، قواميسَ فيها `id` و`name` و`input`.
- `tool_results(response, functions)` تشغّل كل استدعاء وتعيد رسالة `user` فيها كتلة `tool_result` لكل
  استدعاء. و`functions` قاموس يربط اسم كل أداة بدالة Python التي تشغّلها.
- `run_tool_loop(ask, question, tools, functions, max_rounds)` تشغّل الحلقة: `ask(messages, tools)` بديل
  لاستدعاء الواجهة. تعيد نص الإجابة والمحادثة كلها، وترفع `RuntimeError` إذا ظل Claude يستدعي أداة بعد
  `max_rounds` دورة. فمع `max_rounds=3`، ترسل أربعة طلبات على الأكثر: ثلاثة تطلب إجاباتها أدوات، ورابعًا
  يجب أن تكون إجابته هي الجواب.

في هذا الدرس تنجح كل أداة. أما الأدوات التي تفشل فهي موضوع الدرس التالي.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. وفي `exercise/solution/` حلّ جاهز: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إن صعب عليك سؤال، فأعد قراءة الخطوات الخمس لتبادل الأدوات في «الفكرة».

[^dt-sentences]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^ov-ask]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-400]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-choice]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-untrusted2]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^ov-what]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hw-contract]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^dt-tools]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-fields]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-desc]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-block]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-comment]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-result]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-continue]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-roles]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-order]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-loop]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^ov-price]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-prompt]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-enables]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-runner]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^ov-guess]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-untrusted]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-forced]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^ov-auto]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
