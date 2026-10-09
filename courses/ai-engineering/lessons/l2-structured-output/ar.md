# احصل على JSON تثق به

## ما الذي ستتمكن من فعله

- تصف البيانات التي تريدها بمخطط JSON Schema: الحقول وأنواعها، وأيّها إلزامي.
- تطلب من Claude نص JSON يتبع المخطط، عبر `output_config.format`.
- تفحص كل إجابة قبل أن يستخدمها كودك، وتقرّر متى تعيد السؤال ومتى تتوقف.

## الفكرة

لا يستطيع كودك أن يقرأ جملة لطيفة. إذا طلب تطبيق دعم فني من Claude أن يصنّف رسالة عميل، فالتطبيق
يحتاج إلى ثلاثة حقول يثق بها: الفئة والأولوية وملخص قصير. ومن دون مساعدة، قد يكتب Claude نص JSON
معطوبًا، أو نصًا ينقصه حقل إلزامي، فيتعطّل تطبيقك[^so-without].

مخطط **JSON Schema** يصف شكل البيانات التي تنتظرها. والمخطط نفسه مكتوب بصيغة JSON: إنه بيانات، لا
برنامج[^js-data]. هذا مخطط تذكرة دعم:

```json
{
  "type": "object",
  "properties": {
    "category": {"type": "string", "enum": ["bug", "billing", "question"]},
    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
    "summary": {"type": "string"}
  },
  "required": ["category", "priority", "summary"],
  "additionalProperties": false
}
```

اقرأه من الأعلى. القيمة كائن (object)، أي كائن JSON يشبه قاموس Python ‏(dict). يسرد `properties`
حقوله ومخطط كل حقل. ويسمّي `type` نوع القيمة: `string` أو `integer` أو `number` أو `boolean` أو
`array` أو `object` أو `null`[^so-types]. فالنوع `integer` عدد
صحيح[^js-integer]، و`number` أي عدد، ولو كان فيه كسر عشري[^js-number]. وفي Python، يقابل `object` القاموس
`dict`، ويقابل `array` (المصفوفة) القائمة `list`، ويقابل `boolean` (أي `true` أو `false`) النوع `bool`،
ويقابل `null` القيمة `None`[^js-python]. ويقصر `enum` القيمة على مجموعة
ثابتة من القيم[^js-enum]. ويحدّد `minimum` و`maximum` مدى الرقم[^js-range]. وقاعدتان تفاجئان كثيرين. في JSON Schema، الحقل المذكور في `properties` ليس
إلزاميًا ما لم تذكره في `required`[^js-required]. والحقول الإضافية مسموح بها ما لم تضبط
`additionalProperties` على `false`[^js-additional].

**المخرجات المنظمة (structured outputs)** ميزة في Claude API تجعل Claude يتبع مخططًا[^so-intro].
تضع المخطط في الطلب، داخل `output_config.format`، مع ضبط `type` على `json_schema`[^so-send]. فيكتب
Claude نص JSON صالحًا يطابق مخططك، في كتلة النص من الإجابة[^so-read]. وهي تعمل بتحويل مخططك إلى
قواعد نحوية (grammar)، أي مجموعة قواعد تحدّ ما يستطيع Claude أن يكتبه بعد ذلك[^so-grammar].

لا تقبل هذه الميزة كل مخطط. يجب أن يضبط كل كائن في المخطط `additionalProperties` على `false`[^so-supported].
وقيود الأرقام مثل `minimum` و`maximum` غير مدعومة، والطلب الذي يستخدم ميزة لا تدعمها الواجهة يفشل
بخطأ[^so-unsupported]. لذلك تحتفظ بنسختين: المخطط الذي ترسله، بلا `minimum` ولا `maximum`، والمخطط
الكامل الذي يفحص به كودك. وتوفّر حزم SDK الرسمية أيضًا دوالّ مساعدة (helpers) تفعل ذلك عنك. معظمها
يحوّل المخطط الذي يستخدم ميزات لا تدعمها الواجهة[^so-sdk-most]: فيرسل إلى Claude مخططًا أبسط، والدالة المساعدة التي تفحص الإجابات تظل تفحص كل قاعدة في مخططك
الكامل[^so-sdk]. أما في هذا الدرس فتفعل ذلك بيدك، لترى كل خطوة.

فلماذا الفحص إذن؟ لأن عبارة «يتبع المخطط» لها استثناءات:

- **الرفض.** قد يرفض Claude طلبًا. عندها يكون سبب التوقف `refusal`، وقد لا تطابق مخرجات الإجابة
  مخططك[^so-refusal]. والرفض إجابة عادية ناجحة، وليس خطأً[^stop-refusal]. وإعادة الطلب نفسه ليست
  الحل الموثّق: فالطلب الذي يرفضه Claude Opus 5.5 يُجاب عنه عادةً إذا أرسلته إلى نموذج Claude آخر،
  بتغيير `model`[^refusal-fallback].
- **الإجابة المقطوعة.** إذا بلغت الإجابة `max_tokens`، فقد يكون JSON ناقصًا. والحل الموثّق أن تعيد
  المحاولة بقيمة `max_tokens` أعلى[^so-max].
- **حالة الأحرف في قيم `enum`.** قد يعيد Claude ‏`"Bug"` ومخططك يقول `"bug"`: فحالة الأحرف (الكبيرة
  والصغيرة) في قيم enum غير مضمونة[^so-enum-case]. وتقول الوثائق: قارِن قيم enum دون اعتبار لحالة
  الأحرف[^so-enum].
- **قواعد لا تفحصها الواجهة،** مثل `minimum` و`maximum` أعلاه، وقواعد لا يستطيع المخطط أن يعبّر عنها
  أصلًا، مثل «يجب أن يكون التاريخ في المستقبل». هذه لا يفحصها إلا كودك.

الإجابة التي تخالف إحدى قواعدك يمكن أن تطلبها من جديد، لكن الطلب نفسه قد يخالف القاعدة مرة أخرى. وكل طلب جديد يكلّف رموزًا (tokens)، فضع حدًا،
ثم توقف وأبلغ عن المشكلة. وللمخرجات المنظمة كلفة صغيرة أيضًا: يتلقى Claude موجّه نظام (system prompt)
إضافيًا يشرح الصيغة، فيزيد عدد رموز الإدخال قليلًا[^so-cost].

## جرّبها

### بمفتاحك الخاص (اختياري)

هذا الكود يستدعي الواجهة الحقيقية، فيحتاج إلى مفتاح، والرموز التي يستهلكها مدفوعة. جهّز المفتاح وحزمة
SDK كما في درس «أول استدعاء لواجهة Claude البرمجية». المخطط المرسَل هنا بلا `minimum` ولا `maximum`؛
ويخبر وصفٌ (description) ‏Claude بالمدى بدلًا منهما.

```python
import json

import anthropic

SENT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["bug", "billing", "question"]},
        "priority": {"type": "integer", "description": "1 = low, 2 = normal, 3 = urgent"},
        "summary": {"type": "string"},
    },
    "required": ["category", "priority", "summary"],
    "additionalProperties": False,
}

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Sort this support message: I was charged twice in March."}],
    output_config={"format": {"type": "json_schema", "schema": SENT_SCHEMA}},
)
print("stop_reason:", response.stop_reason)
text = "".join(block.text for block in response.content if block.type == "text")
print(json.loads(text) if response.stop_reason == "end_turn" else text)
```

يتبع هذا الكود مثال JSON Schema العادي (دون دالة مساعدة) في دليل المخرجات المنظمة من Anthropic[^so-raw]. ستختلف إجابتك عن
العيّنات أدناه.

### دون مفتاح: اقرأ ست إجابات نموذجية

في المجلد `exercise/tests/` ست إجابات نموذجية لطلب التذكرة. إنها على شكل الإجابات الحقيقية، وليست
تسجيلًا لاستدعاءات حقيقية. إحداها، `sample_not_json.json`، تمثّل ما قد يعيده طلب بلا `output_config`:
نص JSON تسبقه جملة. احفظ هذا الكود باسم `read_samples.py` في مجلد الدرس، وشغّل
`python3 read_samples.py` من ذلك المجلد:

```python
"""Read six sample replies and say which ones your code could use. No network, no key."""
import json
from pathlib import Path

CATEGORIES = ("bug", "billing", "question")
folder = Path("exercise/tests")

for path in sorted(folder.glob("sample_*.json")):
    reply = json.loads(path.read_text(encoding="utf-8"))
    if reply["stop_reason"] != "end_turn":
        print(f"{path.name}: not usable, stop_reason is {reply['stop_reason']}")
        continue
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    try:
        ticket = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"{path.name}: not usable, not JSON ({error})")
        continue
    problems = []
    if str(ticket.get("category")).lower() not in CATEGORIES:
        problems.append("unknown category")
    priority = ticket.get("priority")
    if type(priority) is not int or not 1 <= priority <= 3:
        problems.append("priority must be a whole number from 1 to 3")
    if not isinstance(ticket.get("summary"), str):
        problems.append("no summary")
    print(f"{path.name}: " + ("not usable, " + ", ".join(problems) if problems else "usable"))
```

لا يصلح للاستخدام إلا 2 من الإجابات الست. تنجح `sample_enum_case.json` لأن فحص الفئة يتجاهل حالة
الأحرف. أما `sample_out_of_range.json` فنص JSON صالح فيه كل الحقول، لكنه يضبط الأولوية على 5: لم
يمنع ذلك أيُّ شيء أُرسل في المخطط إلى الواجهة، فلا يكشفه إلا فحصك. وتوقفت إجابتان مبكرًا، واحدة بسبب
`max_tokens` وأخرى بسبب `refusal`، وواحدة تسبق JSON فيها جملة، فلا تستطيع `json.loads` تحليلها (parse)، أي تحويل النص إلى
قيم Python.

## أخطاء شائعة

- **«المخرجات المنظمة تعني أنني لا أفحص أبدًا».** الرفض أو الإجابة المقطوعة قد لا يطابقان
  المخطط[^so-refusal] [^so-max]، وقيود الأرقام لا تُرسَل إلى الواجهة[^so-unsupported]. افحص كل إجابة.
- **إرسال `minimum` أو `maximum` في المخطط.** يفشل الطلب[^so-unsupported]. احتفظ بالمخطط الكامل في
  كودك وأرسل المخطط الأبسط.
- **نسيان `required`.** من دونه يصبح كل حقل اختياريًا[^js-required]، ويصطدم كودك لاحقًا بمفتاح مفقود.
- **مقارنة قيم enum حرفيًا.** قد تعود `"Bug"` بدل `"bug"`[^so-enum-case]. قارِن دون اعتبار لحالة الأحرف،
  ثم استخدم تهجئة مخططك.
- **معاملة `True` على أنها رقم.** في Python، النوع `bool` نوع فرعي من `int`[^py-bool]، فقيمة
  `isinstance(True, int)` هي `True`. والفحص الذي ينتظر عددًا صحيحًا يجب أن يرفض القيم المنطقية.
- **طلب تفكير Claude في حقل.** الحقل الذي يطلب تفكير النموذج أو استدلاله خطوة بخطوة قد يسبّب رفضًا.
  اطلب شرحًا قصيرًا بدلًا من ذلك[^so-reasoning].
- **إعادة المحاولة بلا حد.** كل محاولة تكلّف رموزًا. توقف بعد بضع محاولات، ولا تُعِد إرسال طلب مرفوض
  كما هو: فالحل الموثّق نموذج آخر[^refusal-fallback].

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/structured.py`. ستجد فيه `TYPES` (ما يقبله كل نوع من أنواع JSON Schema في
Python)، والاستثناء `ReplyError` (خطأ يرفعه كودك، ومعه سبب `reason`)، والدالة `use_schema_spelling()`
التي تعيد قيم enum إلى تهجئة المخطط. اكتب ثلاث دوال:

- `validate(value, schema)` تعيد قائمة بالمشكلات، فارغة إذا كانت القيمة صالحة. وهي تدعم `type`
  و`enum` (دون اعتبار لحالة الأحرف) و`minimum` و`maximum` و`properties` و`required`
  و`additionalProperties: false` و`items` (مخطط كل عنصر في المصفوفة). أبلغ عن كل مشكلة، وابدأ كلًّا
  منها بموضعها، مثل `$.priority` (الرمز `$` يعني القيمة كلها).
- `parse_reply(response, schema)` تعيد القيمة بعد فحصها، أو ترفع `ReplyError` مع السبب `refusal` أو
  `cut_off` أو `not_json` أو `invalid`.
- `ask_until_valid(ask, schema, max_tokens, attempts)` تستدعي `ask(max_tokens)` حتى تنجح إحدى
  الإجابات. في الاختبارات، `ask` بديل (stand-in): دالة تؤدي دور الواجهة وتعيد إجابات نموذجية، فلا
  يُدفع أي استدعاء. تتوقف فورًا عند الرفض، وتضاعف `max_tokens` بعد الإجابة المقطوعة (المضاعفة اختيار
  هذه الدورة؛ والوثائق تقول فقط ارفعها)، وترفع `ReplyError` مع السبب `gave_up` بعد آخر محاولة.

المخطط الكامل للتذكرة في `exercise/tests/ticket_schema.json`.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. وفي `exercise/solution/` حلّ جاهز: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إن صعب عليك سؤال، فأعد قراءة قائمة الاستثناءات في «الفكرة»: الرفض، والإجابة
المقطوعة، وحالة الأحرف في enum، والقواعد التي لا تفحصها الواجهة.

[^so-without]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^js-data]: What is a schema? (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/about>
[^js-required]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^js-additional]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^so-intro]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-send]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-read]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-grammar]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-supported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-unsupported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-sdk]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-refusal]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^stop-refusal]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^refusal-fallback]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^so-max]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum-case]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-cost]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-types]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^js-enum]: Enumerated values (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/enum>
[^js-range]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-integer]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-number]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-python]: Type-specific keywords (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/type>
[^so-sdk-most]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-raw]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^py-bool]: Built-in Types (Python documentation), <https://docs.python.org/3/library/stdtypes.html>
[^so-reasoning]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
