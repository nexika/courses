# حين تفشل الأداة

## ما الذي ستتمكن من فعله

- تبلّغ Claude بفشل الأداة في كتلة `tool_result` مع `is_error`، بدل أن ينهار برنامجك أو تختلق نتيجة.
- تكتب رسائل خطأ تخبر Claude بما حدث وبما يجرّبه بعد ذلك.
- تفحص مُدخلات Claude قبل تشغيل الأداة، وتجيب عن كل استدعاء، حتى لو فشل معظمها.

## الفكرة

الأدوات تفشل. قد تتعطل خدمة، أو لا يوجد رقم الطلبية، أو يستدعي Claude أداة بمُدخلات لا تناسبها. أمام
كودك ثلاثة خيارات سيئة وخيار واحد جيد.

- **الانهيار.** يتوقف برنامجك، ولا يحصل المستخدم على شيء. والتقاط الخطأ دون إرسال أي نتيجة ليس أفضل:
  فكل كتلة `tool_use` تحتاج نتيجتها `tool_result` بعدها مباشرة[^hc-follow]، وإلا فشل الطلب
  التالي[^hc-missing].
- **إرسال ما لا ينفع،** مثل نتيجة فارغة أو `"failed"`. لا يجد Claude ما يعمل به.
- **اختلاق نتيجة،** مثل حالة افتراضية. لا يرى Claude إلا النتيجة التي تعيدها، لا كيف حصلت
  عليها[^hw-sees]، فلا يستطيع أن يميّز النتيجة المختلَقة من الحقيقية.
- **الإبلاغ عن الفشل.** أرسل `tool_result` يقول `content` فيها ما الذي حدث، مع `"is_error":
  true`[^hc-exec]. فيدمج Claude الخطأ في إجابته، كأن يخبر المستخدم أن الخدمة غير متاحة[^hc-exec-claude].

الحقل `is_error` اختياري في كتلة `tool_result`: اضبطه على `true` حين ينتهي تشغيل الأداة بخطأ[^hc-is-error].
هذا بحث فاشل عن طلبية:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_sample_02",
      "content": "No order A-999. Ask the user to check the number: order numbers are A- followed by four digits.",
      "is_error": true
    }
  ]
}
```

الرسالة مكتوبة لـ Claude. ويطلب دليل Anthropic رسائل خطأ إرشادية: بدل `"failed"` العامة، قل ما الخطأ وما الذي
ينبغي أن يجرّبه Claude بعد ذلك. فهذا يعطي Claude السياق الذي يحتاجه ليتعافى أو يتكيّف دون
تخمين[^hc-instructive]. وتذكّر من يقرأ الرسالة بعدك: قد يكررها Claude للمستخدم[^hc-exec-claude]. فاحذف منها
ما لا ينبغي أن يراه أيٌّ منهما، مثل تتبّع الاستدعاءات (stack trace: قائمة الاستدعاءات التي يطبعها Python
حين لا يُلتقط الخطأ)، وعناوين الخوادم، وكلمات المرور.

والفشل نوعان:

- **الأداة عملت وفشلت:** الطلبية غير موجودة، أو انتهت مهلة الخدمة. أبلغ عمّا حدث.
- **استدعاء Claude خاطئ:** حقل إلزامي ناقص، أو حقل بنوع خاطئ، أو حقل غير مسموح به، أو اسم أداة غير موجود. افحص المُدخلات مقابل
  `input_schema` الخاص بالأداة قبل أن تشغّل أي شيء، وأبلغ عن المشكلات. فيعيد Claude محاولة استخدام
  الأداة بعد أن يملأ المعلومة الناقصة[^hc-invalid]: إذا كان الطلب غير صالح أو تنقصه معاملات، يعيد Claude
  المحاولة من 2 إلى 3 مرات مع تصحيحات قبل أن يعتذر للمستخدم[^hc-retries]. وفي أثناء التطوير، يعني
  الاستدعاء الخاطئ في الغالب أن `description` الأداة يحتاج إلى تفصيل أكثر[^hc-desc]. وإذا احتجت إلى
  مُدخلات تطابق المخطط دائمًا، فالواجهة توفر الاستخدام الصارم للأدوات (strict tool use)، بإضافة
  `strict: true` إلى تعريف الأداة[^hc-strict]. لكن الأداة نفسها قد تفشل حتى عندئذ، فتظل بحاجة إلى نتائج
  الخطأ.

كل إعادة محاولة تكلّف جولة، وحدّ الجولات من الدرس السابق ما زال قائمًا.

## جرّبها

في المجلد `exercise/tests/` إجابة نموذجية فيها أربعة استدعاءات لأدوات. إنها على شكل إجابة حقيقية وليست
تسجيلًا لاستدعاء حقيقي، والإجابة الحقيقية نادرًا ما تجمع هذا العدد من الأخطاء معًا. استدعاء واحد سليم.
وآخر يطلب طلبية غير موجودة. وثالث يرسل حقلًا اسمه `order` بدل `order_id`. ورابع يستدعي `track_parcel`،
وهي أداة غير موجودة. احفظ هذا الكود باسم `four_calls.py` في مجلد الدرس، وشغّل `python3 four_calls.py`
من ذلك المجلد:

```python
"""Four tool calls, three failures: every call still gets a tool_result. No network, no key."""
import json
from pathlib import Path

reply = json.loads(Path("exercise/tests/sample_four_calls.json").read_text(encoding="utf-8"))
ORDERS = {"A-1042": "shipped"}


def lookup_order(order_id):
    if order_id not in ORDERS:
        raise LookupError(f"No order {order_id}. Ask the user to check the number: order numbers are A- followed by four digits.")
    return {"order_id": order_id, "status": ORDERS[order_id]}


FUNCTIONS = {"lookup_order": lookup_order}
results = []
for block in reply["content"]:
    if block["type"] != "tool_use":
        continue
    result = {"type": "tool_result", "tool_use_id": block["id"]}
    if block["name"] not in FUNCTIONS:
        result.update(content=f"Unknown tool '{block['name']}'. Available tools: lookup_order.", is_error=True)
    else:
        try:
            result["content"] = json.dumps(FUNCTIONS[block["name"]](**block["input"]))
        except LookupError as error:
            result.update(content=str(error), is_error=True)
        except TypeError:  # the input's fields do not fit the function
            result.update(content="Invalid input for lookup_order: it takes one field, order_id. "
                                  "Call it again with a corrected input.", is_error=True)
    results.append(result)
    print(json.dumps(result))
print(sum(1 for r in results if r.get("is_error")), "of", len(results), "results have is_error set")
```

يحصل كل استدعاء على `tool_result`، بالترتيب، وتحمل 3 من النتائج الأربع العلامة `is_error`. لم ينهَر شيء، ولم يُختلَق شيء. والتقاط `TypeError` اختصار هنا: فهو ما يرفعه
Python حين لا تناسب حقولُ المُدخلات الدالةَ. أما تمرينك فيفحص المُدخلات مقابل المخطط قبل تشغيل الأداة،
فيعطي Claude رسالة أدق.

## أخطاء شائعة

- **ترك الاستثناء يفلت.** تتوقف الحلقة، ولا تحصل كتلة `tool_use` على نتيجتها `tool_result`[^hc-missing].
  التقط الفشل وأبلغ عنه.
- **إعادة الخطأ على أنه نتيجة عادية.** دون `is_error`، يبدو النص `No order A-999` بيانات. اضبط
  `"is_error": true`[^hc-is-error].
- **رسائل عامة.** `"failed"` لا تعطي Claude ما يعمل به. قل ما الخطأ وما الذي يجرّبه بعد
  ذلك[^hc-instructive].
- **إرسال الاستثناء كما هو.** قد يحمل تتبّع الاستدعاءات مسارات ملفات أو عناوين أو أسرارًا، وقد يكرر Claude
  الخطأ للمستخدم[^hc-exec-claude]. سمِّ نوع الفشل، واحفظ التفاصيل في سجلاتك
  (logs: ما يدوّنه برنامجك لك، كملف من الرسائل).
- **تشغيل الأداة على مُدخلات لم تفحصها.** افحص الحقول الإلزامية والحقول غير المسموح بها والأنواع أولًا.
  ويُبلَّغ عن الاستدعاء الخاطئ كي يصحّحه Claude[^hc-invalid].
- **تخطّي الاستدعاءات بعد أول فشل.** كل كتلة `tool_use` تحتاج نتيجتها `tool_result`
  الخاصة[^hc-missing]. أجب عنها كلها.

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/errors.py`. ستجد فيه `JSON_TYPES` و`ToolError`، وهو استثناء ترفعه أدواتك حين
تفشل بطريقة تستطيع شرحها. اكتب ثلاث دوال:

- `check_input(tool, args)` تعيد المشكلات في مُدخلات Claude: حقول إلزامية ناقصة، وقيم من نوع خاطئ،
  وحقول لا يذكرها المخطط حين يضبط `additionalProperties` على `false`. فكما رأيت في درس JSON، المخطط الذي
  لا يضبط ذلك يسمح بالحقول الإضافية.
- `run_one(call, tools, functions)` تشغّل استدعاءً واحدًا وتعيد دائمًا كتلة `tool_result`. أبلغ عن الأداة
  غير المعروفة بسرد الأدوات الحقيقية؛ وأبلغ عن المُدخلات الخاطئة دون تشغيل الأداة؛ ومرّر رسالة
  `ToolError` إلى Claude؛ ولأي استثناء آخر، سمِّ الأداة ونوع الاستثناء، لا رسالته.
- `tool_results(response, tools, functions)` تعيد رسالة `user` فيها نتيجة لكل استدعاء، بالترتيب. ولا
  ترفع أي استثناء أبدًا.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. وفي `exercise/solution/` حلّ جاهز: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إن صعب عليك سؤال، فأعد قراءة الخيارات الأربعة في بداية «الفكرة».

[^hc-missing]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec-claude]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-is-error]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-instructive]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-invalid]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-retries]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-desc]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-follow]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hc-strict]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
