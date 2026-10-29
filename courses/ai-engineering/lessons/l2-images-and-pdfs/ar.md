# الصور وملفات PDF

## ما الذي ستتمكن من فعله

- ترسل صورة أو ملف PDF إلى Claude في طلب، على شكل كتلة محتوى، وتعرف الصيغ والحدود.
- تقدّر كلفة الصورة بالرموز (tokens) قبل أن ترسلها.
- تتحقق مما يستخرجه Claude من صورة أو ملف PDF قبل أن تستخدمه، وتعرف متى يجب أن ينظر فيه شخص.

## الفكرة

حتى الآن أرسلت إلى Claude نصًا. لكن Claude يستطيع أيضًا أن يفهم الصور ويحلّلها[^v-what]. وتستطيع أن تسأله
عن النص والصور والرسوم البيانية والجداول في ملف PDF[^p-what]. ومن الاستخدامات تحويل مستند إلى
بيانات منظمة، مثل حقول فاتورة[^p-what].

**الصورة كتلة محتوى**

في درس "أول استدعاء لواجهة Claude البرمجية"، كان `content` في جولة المستخدم نصًا، وكان `content` في الإجابة
قائمة من الكتل. ويمكن أن يكون `content` في جولة المستخدم أيضًا قائمة من كتل المحتوى، والصورة واحدة منها[^v-sources]. وتأخذ الواجهة الصورة بإحدى
ثلاث طرق: بايتات الصورة داخل الطلب، مرمّزة بـ `base64`؛ أو رابط (URL) للصورة على الإنترنت؛ أو `file_id` من
Files API، حيث ترفع الملف مرة واحدة وتشير إليه مرات كثيرة[^v-sources]. هذه هي الطريقة الأولى:

```json
{"role": "user", "content": [
  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
  {"type": "text", "text": "What does this receipt say?"}
]}
```

`base64` يحوّل أي بايتات إلى حروف وأرقام وبعض العلامات، كي ينتقل الملف داخل JSON. وفي Python،
محتوى الملف الخام قيمة من النوع `bytes`، تُكتب مثل `b"GIF89a"`؛ وفيها `\x89` بايت واحد مكتوب بالنظام الست
عشري (انظر أدناه). و`.decode("ascii")` تحوّل بايتات `base64` إلى نص عادي، وهو ما يحتاجه JSON؛ و ASCII هي
المجموعة الأساسية من الحروف الإنجليزية والأرقام والعلامات. و*نوع الوسائط* (media type)
تسمية تقول ما نوع الملف، مثل `image/png`. يقبل Claude صور JPEG و PNG و GIF و WebP، ومن الصورة المتحركة
لا يستخدم إلا الإطار الأول[^v-formats]. ضع الصورة قبل سؤالك: فهكذا يعمل Claude أفضل، وإن كان الترتيب الآخر
يعمل أيضًا[^v-order].

لا تعتمد على اسم الملف لتعرف نوعه. انظر إلى بايتاته الأولى: كل ملف PNG يبدأ بالبايتات الثمانية نفسها،
`89 50 4E 47 0D 0A 1A 0A` بالنظام الست عشري[^png-sig]، وللصيغ الأخرى تواقيعها الخاصة، وهي مذكورة في التمرين.
(تُكتب البايتات عادةً بالنظام الست عشري، وهو طريقة لكتابة الأعداد تستخدم أيضًا الحروف من A إلى F.)

**ملف PDF كتلة مستند**

يوضع ملف PDF في كتلة من النوع `document`، بنوع الوسائط `application/pdf`[^p-type]. ويمكن إرساله، مثل الصور، برابط،
أو بـ `base64`، أو بـ `file_id`[^p-ways]. تحوّل الواجهة كل صفحة إلى صورة، وتستخرج نص كل صفحة أيضًا، فيقرأ
Claude الاثنين. ولهذا يستطيع أن يجيب عن أسئلة حول الرسوم البيانية والمخططات، لا عن النص وحده[^p-how].

**الكلفة والحدود**

يرى Claude الصورة رقعًا من 28 × 28 بكسل، وكل رقعة *رمز مرئي* (visual token) واحد[^v-cost]. وتكلّف الصورة
⌈width / 28⌉ × ⌈height / 28⌉ رمزًا مرئيًا، حيث ⌈ ⌉ تعني "التقريب إلى الأعلى"[^v-cost]. فصورة بحجم
1000 × 1000 تكلّف 36 × 36 = 1296 رمزًا مرئيًا[^v-table]. والصور التي تتجاوز حدود النموذج تُصغَّر قبل أن يراها
Claude[^v-downscale]. وعلى نماذج Claude 4.7 وما بعدها، الحد 2576 بكسل على الضلع الأطول و 4784 رمزًا
مرئيًا[^v-tiers]. و Claude Opus 5.5، النموذج الذي يستخدمه هذا المقرر، واحد من هذه النماذج اللاحقة، فتنطبق
عليه هذه الحدود[^v-tiers].
وعلى هذا النموذج تكلّف صورة بحجم 1920 × 1080 عددًا من الرموز المرئية قدره 2691، دون أن تُصغَّر[^v-table-hd]. لا ترسل صورة أكبر مما تحتاجه المهمة.

وصفحة PDF تكلّف رموزًا مرتين. فنص كل صفحة يستخدم عادةً من 1,500 إلى 3,000 رمز، وصورة كل صفحة تُحسب مثل أي
صورة أخرى[^p-cost]. وملفات PDF الكثيفة، بخطوط صغيرة أو جداول معقدة أو رسوم كثيرة، قد تملأ نافذة السياق قبل
بلوغ حد الصفحات[^p-dense].

أهم الحدود على Claude API. ويُقدَّم Claude أيضًا عبر خدمات سحابية أخرى، مثل Amazon Bedrock و Google Cloud،
وبعض الحدود هناك أقل[^v-size]:

- الصورة 8000 × 8000 بكسل على الأكثر[^v-dims] (أو، احتياطًا على كل الخدمات، 2000 × 2000 حين يحمل الطلب
  أكثر من 20 صورة[^v-many])، و 10 MB على الأكثر بعد ترميزها بـ `base64`[^v-size].
- الطلب يحمل حتى 600 صورة، أو 100 على النماذج التي نافذة سياقها 200k رمز[^v-count].
- طلب PDF يحمل حتى 600 صفحة، أو 100 حين تكون نافذة السياق أقل من 1M رمز؛ والطلب كله 32 MB على الأكثر على Claude API (ويختلف في الخدمات الأخرى)، ولا
  يجوز أن يكون للملف كلمة مرور أو أن يكون مشفّرًا[^p-limits].

**تحقّق مما يستخرجه Claude**

قد يخطئ Claude فيما يراه. قد يخطئ في الصور المنخفضة الجودة أو المائلة أو الصغيرة جدًا (أقل من 200 بكسل)،
وعدّه للأشياء الصغيرة الكثيرة تقريبي، ولا يستطيع أن يعرف هل صُنعت الصورة بالذكاء الاصطناعي[^v-limits]. ولا يرى
البيانات الوصفية للصورة (metadata)، مثل التاريخ المحفوظ في صورة فوتوغرافية[^v-meta]. ولملفات PDF الحدود نفسها،
لأن Claude يقرأ صفحاتها صورًا[^p-vision]. ويطلب دليل Anthropic أن تراجع ما يقوله Claude عن الصور وتتحقق منه،
وألا تستخدمه في مهام تحتاج إلى دقة تامة دون أن يفحصها شخص[^v-verify].

فتعامل مع الاستخراج كما تتعامل مع أي مخرجات للنموذج، كما في درس مخرجات JSON: افحصه قبل أن تستخدمه. وتساعدك
ثلاثة فحوص:

1) **الشكل:** في JSON الحقول التي تحتاجها، بالأنواع الصحيحة (دالتك `validate` من ذلك الدرس).
2) **المجاميع:** الأرقام متفقة فيما بينها. في الفاتورة، مجموع البنود يساوي الإجمالي.
3) **المصدر:** القيم موجودة في شيء حصلت عليه بطريقة أخرى، مثل سجلّ النظام الذي أصدر الفاتورة.

وحين يفشل فحص، لا تخمّن: أرسل المستند إلى شخص.

## جرّبها

### دون مفتاح: ابنِ طلبًا وافحص استخراجًا

يقرأ هذا السكربت صورة PNG صغيرة جدًا، هي صورة المثال من دليل الرؤية في Anthropic[^v-example]، مكتوبة نصًا بـ `base64`.
يفحص البايتات الأولى للملف، ويقرأ حجمه، ويعدّ الرموز المرئية، ويبني الطلب. ثم يفحص استخراجين نموذجيين
لفاتورة: أحدهما صحيح، والآخر قُرئ فيه مبلغ خطأً. احفظه باسم `look_and_check.py` في مجلد الدرس، وشغّل
`python3 look_and_check.py` من ذلك المجلد:

```python
"""Build an image request and check an extraction, offline. No network, no key."""
import base64
import json
import math
import struct
from pathlib import Path

# 1. A tiny PNG (one pixel), written as base64 text. Real code reads a file: Path("photo.png").read_bytes()
data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")
print("starts like a PNG:", data.startswith(b"\x89PNG\r\n\x1a\n"))
width, height = struct.unpack(">II", data[16:24])
print("size:", width, "x", height)

# 2. What it costs: one visual token per 28 x 28 patch.
for w, h in ((width, height), (1000, 1000), (1920, 1080)):
    print(f"{w} x {h}:", math.ceil(w / 28) * math.ceil(h / 28), "visual tokens")

# 3. The request: the image first, then the question.
request = {"model": "claude-opus-5-5", "max_tokens": 1024, "messages": [{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                 "data": base64.standard_b64encode(data).decode("ascii")}},
    {"type": "text", "text": "What colour is this pixel?"}]}]}
print(json.dumps(request)[:160], "...")

# 4. Check an extraction: do the line amounts add up to the total?
folder = Path("exercise/tests")
for name in ("sample_extracted_ok.json", "sample_extracted_misread.json"):
    invoice = json.loads((folder / name).read_text(encoding="utf-8"))
    lines = sum(line["amount"] for line in invoice["lines"])
    print(name, "lines add up to", lines, "total says", invoice["total"],
          "OK" if abs(lines - invoice["total"]) < 0.005 else "CHECK BY HAND")
```

`math.ceil` تقرّب إلى الأعلى، مثل ⌈ ⌉ أعلاه. و`struct.unpack(">II", ...)` تقرأ عددين صحيحين من أربعة
بايتات لكلٍّ منهما، هما العرض والارتفاع؛ و`>` تعني الترتيب big-endian، حيث البايت الأول هو الأثقل وزنًا، كما
أن الخانة الأولى في العدد المكتوب هي الأثقل وزنًا. يتكوّن ملف
PNG من *قطع* (chunks)، وهي أجزاء من البيانات لها أسماء، وبيانات القطعة الأولى تبدأ بالعرض والارتفاع[^png-ihdr]؛ وهما
في الملف يأتيان مباشرة بعد البايتات الست عشرة الأولى.

في الاستخراج الخاطئ، مجموع البنود 1404.5، أي أقل من الإجمالي: أحد المبالغ خاطئ، وقد كشفه فحص المجموع دون
أن يعرف أيها. ويسمح السكربت بفرق صغير جدًا، لأن الأعداد العشرية ليست دقيقة في Python:
`0.1 + 0.2` تعطي `0.30000000000000004`.

الاستخراجان النموذجيان على شكل استخراجات حقيقية لكنهما كُتبا باليد، والفاتورة مختلَقة.

### بمفتاحك الخاص (اختياري)

هذا يرسل صورة حقيقية، فيحتاج إلى مفتاح، ورموزه مدفوعة. جهّز المفتاح و SDK كما في درس "أول استدعاء لواجهة Claude البرمجية".
استخدم صورة أو مسحًا ضوئيًا لإيصال يخصك، محفوظًا باسم `receipt.jpg`:

```python
import base64
from pathlib import Path

import anthropic

data = Path("receipt.jpg").read_bytes()
client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                     "data": base64.standard_b64encode(data).decode("ascii")}},
        {"type": "text", "text": "List each item and its price as JSON, then the total."},
    ]}],
)
print("".join(block.text for block in message.content if block.type == "text"))
print("input tokens:", message.usage.input_tokens)
```

ولملف PDF، استخدم `"type": "document"` و`"media_type": "application/pdf"`. وقارن ما يعود بالإيصال نفسه،
سطرًا سطرًا.

## أخطاء شائعة

- **الثقة بالاستخراج لأنه يبدو مرتبًا.** قد يحمل JSON النظيف رقمًا مقروءًا خطأً. افحص الشكل والمجاميع
  والمصدر[^v-verify].
- **تخمين النوع من اسم الملف.** قد يكون الملف المسمّى `scan.png` صورة JPEG، ويجب أن يطابق نوع الوسائط الذي
  ترسله البايتات. اقرأ البايتات الأولى[^png-sig].
- **إرسال صور ضخمة.** تكلّف رموزًا أكثر، وتُصغَّر على أي حال[^v-downscale]. صغّرها بنفسك إلى ما تحتاجه المهمة.
- **وضع السؤال قبل الصورة.** يعمل ذلك، لكن Claude يعمل أفضل حين تأتي الصورة أولًا[^v-order].
- **أن تطلب من Claude عدّ أشياء صغيرة كثيرة أو تسمية شخص.** العدّ تقريبي، ولن يتعرّف Claude على الأشخاص في
  الصور[^v-limits].
- **إرسال ملف Word أو Excel على أنه مستند.** الصيغ مثل `.docx` و`.xlsx` غير مقبولة في كتل المستندات؛ حوّلها
  إلى نص أو PDF أولًا[^p-binary].

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/media.py`. ستجد فيه تواقيع الملفات والحدود ثوابتَ جاهزة. اكتب خمس دوال؛ تعمل دون
اتصال، والاختبارات تصنع ملفات PNG صغيرة خاصة بها.

- `media_type(data)` تعيد نوع الوسائط من البايتات الأولى للملف، أو ترفع `ValueError`.
- `content_block(data)` تعيد كتلة الصورة أو المستند، والبايتات مرمّزة بـ `base64`. وترفض الصورة التي يزيد
  نصها بـ `base64` على حد 10 MB[^v-size].
- `png_size(data)` تعيد عرض صورة PNG وارتفاعها، مقروءين من قطعتها الأولى (يشرح ملف البداية مكانهما).
- `visual_tokens(width, height)` تعيد الكلفة بالرموز المرئية، وترفع `ValueError` لصورة ستصغّرها الواجهة،
  لتصغّرها أنت أولًا.
- `check_invoice(extracted, source_text)` تعيد المشكلات في فاتورة استخرجها Claude: حقول ناقصة، وبنود لا
  يساوي مجموعها الإجمالي، وقيم غير موجودة في نص المصدر.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. يوجد حل في `exercise/solution/`: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إذا صعب عليك سؤال، فاقرأ "الكلفة والحدود" و"تحقّق مما يستخرجه Claude" من جديد.

[^v-what]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-what]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-sources]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-formats]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-order]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-sig]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^p-ways]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-how]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-cost]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-tiers]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-cost]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-dense]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-dims]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-size]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-count]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-limits]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-limits]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-meta]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-vision]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-verify]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-ihdr]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^v-downscale]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table-hd]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-many]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-example]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-type]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-binary]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
