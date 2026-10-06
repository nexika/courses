# أول استدعاء لواجهة Claude البرمجية

## ما الذي ستتمكن من فعله

- تستدعي Claude من Python بحزمة SDK الرسمية، وتقرأ الإجابة وعدد الرموز (tokens) التي استهلكتها.
- تبني محادثة: موجّه النظام (system prompt)، ثم جولات للمستخدم والمساعد.
- تختار النموذج وقيمة `max_tokens` لطلبك، وتتعامل مع إجابة توقفت لأن الرموز المسموح بها نفدت.
- تقرأ إجابة متدفقة قطعةً قطعة أثناء وصولها.

## الفكرة

واجهة برمجة التطبيقات (API) باب يفتحه برنامج لبرامج أخرى. باب Claude اسمه Messages API: يرسل
برنامجك طلبًا عبر الإنترنت، فتعود إليه إجابة.

تستخدم استدعاءاتك مفتاح API: نص سري يعرّف حسابك، فاحفظه بعيدًا عن أعين الآخرين. المكان المعتاد له
متغيّر بيئة (environment variable) على جهازك[^start-key]: قيمة لها اسم تمرّرها الطرفية (terminal) إلى
البرامج التي تشغّلها، خارج الكود. وحزمة SDK الرسمية لـ Python (أي حزمة تطوير البرمجيات: مكتبة
تثبّتها) تقرؤه من `ANTHROPIC_API_KEY` دون أن تمرّره لها بنفسك[^start-env]. وهذه الحزمة تتيح لبرامج
Python الوصول إلى Claude API[^sdk].

الطلب كائن JSON صغير. وJSON صيغة نصية للبيانات تشبه قاموس Python (dict): أسماء بين علامتي تنصيص،
يتبع كلًّا منها نقطتان ثم قيمة. هذه هي الحقول التي ستستخدمها أولًا:

- `model`: النموذج الذي يجيب. إن لم تكن متأكدًا، تقترح وثائق Anthropic البدء بـ Claude Opus
  5.5[^models-start]، واسمه في الواجهة `claude-opus-5-5`[^model-id]. أسماء النماذج تتغيّر، فراجع صفحة
  النماذج قبل أن تختار.
- `max_tokens`: الحد الأقصى لعدد الرموز التي يولّدها النموذج قبل أن يتوقف[^max-tokens]. إنه سقف وليس
  هدفًا: قد يتوقف النموذج قبل بلوغه[^max-early].
- `system` (اختياري): موجّه النظام، وهو طريقة لتعطي Claude سياقًا وتعليمات، مثل هدف أو دور
  يؤديه[^system].
- `messages`: المحادثة حتى الآن، من الأقدم إلى الأحدث. لكل جولة `role`، أي `user` أو `assistant`،
  ومحتوى `content`. في الطلب، يمكن أن يكون `content` نصًا عاديًا كما في المثال أدناه[^content-string]؛
  أما في الإجابة فهو قائمة من الكتل، كما سترى لاحقًا. دُرّبت النماذج على جولات تتناوب بين المستخدم
  والمساعد[^alternating]، فرتّب جولاتك على هذا النحو: المستخدم، ثم المساعد، ثم المستخدم، وهكذا.

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "system": "You are a patient tutor. Answer in two sentences.",
  "messages": [
    {"role": "user", "content": "What is a token?"}
  ]
}
```

الواجهة عديمة الحالة (stateless): لا تتذكر استدعاءاتك السابقة، لذلك ترسل تاريخ المحادثة كاملًا في كل
مرة[^stateless]. لتطرح سؤالًا تابعًا، تضيف إجابة Claude جولةً من نوع `assistant` وسؤالك الجديد جولةً
من نوع `user`، ثم ترسل كل ذلك من جديد. ينبغي أن تكون الجولة الأخيرة للمستخدم. فإنهاء الطلب بجولة
للمساعد (ما يسمى prefill) غير مدعوم على Claude 4.6 والنماذج الأحدث، ومنها Claude Opus 5.5 الذي نستخدمه هنا[^prefill]. ومثل هذا الطلب يعود
بخطأ[^prefill-error].

قد تصادف `temperature` في أمثلة قديمة: وهو يحدد مقدار العشوائية في الإجابة[^temperature]. على
Claude 4.7 والنماذج الأحدث، ومنها Claude Opus 5.5، لا يُدعم `temperature` ولا إعدادات أخذ العيّنات
(sampling) الأخرى `top_p` و`top_k`[^sampling]، وأي قيمة
غير القيمة الافتراضية تُفشل الطلب[^sampling-error]. وجّه الإجابة بالموجّه (prompt) بدلًا من ذلك.

هذه إجابة معروضة بصيغة JSON. إنها عيّنة على شكل الإجابة الحقيقية، وليست تسجيلًا لاستدعاء حقيقي،
فأعداد الرموز فيها للتوضيح فقط.

```json
{
  "id": "msg_sample_01",
  "type": "message",
  "role": "assistant",
  "model": "claude-opus-5-5",
  "content": [
    {
      "type": "text",
      "text": "A token is a small piece of text, such as a word or part of a word. Claude reads your prompt and writes its answer as tokens."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 41,
    "output_tokens": 28
  }
}
```

أهم ثلاثة أجزاء:

- `content` قائمة من الكتل (blocks)، وليس نصًا واحدًا. كتلة `text` تحمل كلمات الإجابة. وهناك أنواع
  أخرى من الكتل. فمثلًا، حين يكون التفكير (thinking) مفعّلًا، يفكّر Claude في كتل تفكير قبل أن يجيب،
  وتصل هذه الكتل قبل كتل النص[^thinking-blocks]. لذلك اجمع الكتل التي نوعها `text` بدل أن تفترض أن
  الكتلة الأولى هي الإجابة.
- `stop_reason` يخبرك لماذا توقف Claude عن الكتابة[^stop-every]. القيمة `end_turn` تعني أن Claude أنهى
  إجابته بشكل طبيعي[^stop-end]. والقيمة `max_tokens` تعني أنه بلغ حد `max_tokens` الذي وضعته في
  طلبك[^stop-max]: النص مقطوع، والحل أن ترفع `max_tokens`[^stop-max-do]. سبب التوقف
  ليس خطأً: إنه يخبرك لماذا انتهت إجابة ناجحة[^stop-not-error]. توجد قيم أخرى ستلتقيها في دروس لاحقة.
- `usage` يعدّ رموز الإدخال (ما أرسلته)[^usage] ورموز الإخراج (ما كتبه Claude)[^usage-output]. وعدد رموز
  الإخراج يشمل كل رموز الإخراج، ومنها رموز التفكير، وهو الرقم الذي تُحتسب عليه الفاتورة للإخراج[^usage-billing]. ولأنك تعيد إرسال التاريخ في كل استدعاء، يكبر عدد رموز
  الإدخال كلما طالت المحادثة.

التدفق (streaming) يغيّر طريقة وصول الإجابة، لا مضمونها. مع `"stream": true` ترسل الواجهة الإجابة على
قطع، في صورة أحداث يرسلها الخادم (server-sent events)، وهي طريقة قياسية يرسل بها الخادم رسائل صغيرة كثيرة
عبر اتصال واحد مفتوح[^stream-sse]، فتستطيع عرض النص بينما Claude ما
زال يكتب. وفي الطلبات ذات قيم `max_tokens` الكبيرة، تشترط حزمة SDK التدفق لتجنّب انتهاء مهلة
الاتصال (timeout)، أي أن يُقطع الاتصال لأن الإجابة استغرقت وقتًا أطول من اللازم[^stream-timeout]. يبدأ التدفق بحدث `message_start` يحمل رسالة محتواها فارغ[^stream-start]. ثم
تصل كل كتلة محتوى في صورة حدث `content_block_start`، ثم حدث `content_block_delta` واحد أو أكثر، ثم حدث
`content_block_stop`[^stream-flow]. والـ delta تغيير صغير. وحدث `content_block_delta` الذي نوع الـ delta فيه `text_delta` يحمل القطعة التالية من النص[^stream-text-delta]. كل delta يحدّث الكتلة التي في موضع معيّن (index)،
أي ترتيب الكتلة في قائمة `content` الخاصة بالإجابة[^stream-delta].
أعداد الرموز في حدث `message_delta` مجاميع متراكمة، لا أرقام تجمعها بنفسك[^stream-cumulative]. وقد
يحمل التدفق أيضًا أحداث `ping`[^stream-ping]، وعلى برنامجك أن يتعامل مع أنواع الأحداث التي لا يعرفها
دون أن يتعطل[^stream-unknown].

## جرّبها

### بمفتاحك الخاص (اختياري)

هذا الجزء يستدعي الواجهة الحقيقية، فهو يحتاج مفتاح API، والرموز التي يستهلكها تُحتسب عليك في
الفاتورة[^pricing]. تجاوزه إن لم يكن لديك مفتاح: الجزء التالي والتمرين يعملان بدونه. ضع المفتاح
في بيئتك، لا في الكود أبدًا، ولا تضفه إلى أي commit (والـ commit لقطة محفوظة من مشروعك في Git قد يراها غيرك لاحقًا). السطر الأول
أدناه يضبط متغيّر البيئة لنافذة الطرفية هذه. السطر الثاني ينشئ بيئة افتراضية (venv): بيئة Python منفصلة لهذا المشروع، فيبقى ما
تثبّته فيها بعيدًا عن بقية نظامك. والسطر الثالث يستخدم pip، أداة تثبيت الحزم في Python، لتثبيت حزمة SDK.

```bash
export ANTHROPIC_API_KEY="your-key-here"
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
```

```python
import os

import anthropic

if "ANTHROPIC_API_KEY" not in os.environ:
    raise SystemExit("Set ANTHROPIC_API_KEY in your environment first.")

client = anthropic.Anthropic()  # يقرأ ANTHROPIC_API_KEY من البيئة

history = [{"role": "user", "content": "What is a token?"}]
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
)
answer = "".join(block.text for block in message.content if block.type == "text")
print(answer)
print("stop_reason:", message.stop_reason)
print("tokens in:", message.usage.input_tokens, "out:", message.usage.output_tokens)

# سؤال تابع: أرسل المحادثة كلها من جديد، والسؤال الجديد في آخرها.
history += [
    {"role": "assistant", "content": answer},
    {"role": "user", "content": "And what is a context window?"},
]
with client.messages.stream(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # تظهر كل قطعة فور وصولها
print()
```

احفظ هذا الكود في ملف، مثل `live_call.py`، وشغّله بالأمر `python3 live_call.py`. لن تطابق إجابتك العيّنات
أدناه كلمةً بكلمة، ولا أعداد رموزها كذلك.

### بلا مفتاح: اقرأ إجابة نموذجية

يحتوي مجلد الدرس على العيّنة السابقة، وعلى إجابة مقطوعة، وعلى عيّنة تدفق، في `exercise/tests/`. احفظ هذا
الكود في ملف داخل مجلد الدرس، مثل `read_samples.py`، وشغّله من ذلك المجلد بالأمر `python3 read_samples.py`:

```python
import json
from pathlib import Path

folder = Path("exercise/tests")
for name in ("sample_reply.json", "sample_cut_off.json"):
    reply = json.loads((folder / name).read_text(encoding="utf-8"))
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    print(name, "->", reply["stop_reason"], reply["usage"])
    print("  ", text)
```

استهلكت الإجابة الأولى 41 رمزًا للإدخال و28 رمزًا للإخراج، وانتهت بـ `end_turn`. أما الثانية فانتهت
بـ `max_tokens`: كتب Claude ما مجموعه 16 رمزًا للإخراج وتوقف في منتصف الجملة، لأنه بلغ حد `max_tokens` في
الطلب. ينتهي نصها بعبارة "that a model can"، وهي جملة بلا نهاية. وفي `sample_stream.json` تصل الإجابة
الأولى نفسها في 6 قطع نصية.

## أخطاء شائعة

- **كتابة المفتاح داخل الكود.** الكود يُشارَك ويُضاف إلى commits. اقرأ المفتاح من البيئة
  بدلًا من ذلك[^start-env].
- **توقّع أن تتذكر الواجهة.** كل استدعاء قائم بذاته[^stateless]. إن أرسلت السؤال الجديد وحده، فإن
  Claude لم يرَ السؤال الأول قط.
- **وضع موجّه النظام داخل `messages`.** التعليمات التي تسري من البداية مكانها الحقل `system` في أعلى
  الطلب[^system-top].
- **اعتبار `content[0]` هو الإجابة.** الإجابة هي كتل النص، وقد تكون الكتلة الأولى من نوع
  آخر[^thinking-blocks].
- **تجاهل `stop_reason`.** الإجابة التي قطعها `max_tokens` تبدو كإجابة عادية تنتهي في منتصف جملة. افحص
  `stop_reason` قبل أن تثق بالنص[^stop-every].
- **جمع أعداد الرموز في التدفق.** الأعداد في `message_delta` مجاميع متراكمة: احتفظ
  بآخرها[^stream-cumulative].

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/first_call.py` واكتب ثلاث دوال. تعمل كلها دون اتصال، على العيّنات الموجودة في
`exercise/tests/`:

- `build_request(model, max_tokens, turns, system=None)` تعيد جسم الطلب في صورة dict (قاموس Python، يربط أسماءً
  بقيم، مثل JSON أعلاه). المعامل `turns`
  قائمة من أزواج `(role, text)`. أضف `system` فقط إن وُجد موجّه نظام. ارفع `ValueError` (الخطأ المعتاد في Python لقيمة غير صالحة) إن كانت
  `max_tokens` أقل من واحد أو ليست عددًا صحيحًا، أو لم توجد أي جولة، أو كان الدور غير `user` أو
  `assistant`، أو لم تكن الجولة الأخيرة للمستخدم. شرط `max_tokens` هذا قاعدة هذا المقرر لطلب ينتظر إجابة:
  فالواجهة نفسها تقبل القيمة 0 أيضًا، وهي تملأ ذاكرة الموجّهات المؤقتة (prompt cache)، أي مخزنًا يتيح
  للطلبات اللاحقة إعادة استخدام الموجّه نفسه، دون أن تكتب أي إجابة[^max-zero].
- `read_reply(response)` تعيد dict فيه `text` (كل كتل النص مجموعة)، و`stop_reason`، و`input_tokens`،
  و`output_tokens`، و`cut_off` الذي تكون قيمته True حين تتوقف الإجابة عند `max_tokens`.
- `join_stream(events)` تعيد الـ dict نفسه انطلاقًا من قائمة أحداث التدفق.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

`unittest` هو مشغّل الاختبارات المدمج في Python. تفشل الاختبارات حتى تعمل دوالك. يوجد حلّ في `exercise/solution/`: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إن صعب عليك سؤال، فأعد قراءة جزء "الفكرة" عن حقول الطلب، أو `stop_reason`، أو
التدفق.

[^start-key]: Get started with Claude, <https://platform.claude.com/docs/en/get-started>
[^start-env]: Get started with Claude, <https://platform.claude.com/docs/en/get-started>
[^sdk]: Claude SDK for Python (README), <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/README.md>
[^models-start]: Models overview, <https://platform.claude.com/docs/en/models/overview>
[^model-id]: Claude SDK for Python (README), <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/README.md>
[^max-tokens]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^max-early]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^system]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^content-string]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^alternating]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^prefill]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^prefill-error]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^temperature]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
[^sampling]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^sampling-error]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^thinking-blocks]: Building with thinking, <https://platform.claude.com/docs/en/build-with-claude/thinking>
[^stop-every]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^stop-end]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^stop-max]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^stop-max-do]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^stop-not-error]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^usage]: anthropic-sdk-python: types/usage.py, <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/types/usage.py>
[^usage-output]: anthropic-sdk-python: types/usage.py, <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/types/usage.py>
[^usage-billing]: anthropic-sdk-python: types/usage.py, <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/types/usage.py>
[^stream-sse]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-timeout]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-start]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-flow]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-text-delta]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-delta]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-cumulative]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-ping]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^stream-unknown]: Streaming Messages, <https://platform.claude.com/docs/en/build-with-claude/streaming>
[^pricing]: Pricing, <https://platform.claude.com/docs/en/about-claude/pricing>
[^system-top]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^max-zero]: Create a Message - Claude API reference, <https://platform.claude.com/docs/en/api/messages/create>
