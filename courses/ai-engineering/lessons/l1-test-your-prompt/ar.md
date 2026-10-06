# اختبر موجّهك (prompt)

## ما الذي ستتمكن من فعله

- أن تكتب مجموعة صغيرة من حالات الاختبار للموجّه (prompt)، لكل حالة مُدخل وإجابة تتوقعها.
- أن تُقيّم إجابات النموذج بالكود: بالمطابقة التامة أولًا، ثم بمُقيِّم (grader) أكثر تسامحًا.
- أن تشغّل كل الحالات، وتحسب نسبة النجاح، وتقرأ الحالات الفاشلة لتقرّر ما الذي يجب إصلاحه.

## الفكرة

كتبت في الدرس السابق موجّهًا واضحًا. كيف تعرف أنه يعمل؟ يجرّبه أغلب الناس مرة واحدة، فيرون إجابة جيدة
وينتقلون إلى غيره. لكن إجابة واحدة لا تثبت إلا القليل. إنها تخبرك عن مُدخل واحد، في تشغيل واحد. سيرسل
المستخدمون مُدخلات لم تجرّبها قط. والموجّه نفسه قد يجيب إجابة مختلفة في تشغيل آخر.
درجة الحرارة (temperature) إعداد يحدّد مقدار العشوائية في الإجابة. يقول مرجع الواجهة البرمجية (API) إن
النتائج لن تكون حتمية تمامًا حتى مع درجة حرارة 0.0[^nondet]. ولا يمكنك خفضها أصلًا في النماذج الحديثة: النماذج
التي صدرت بعد Claude Opus 4.6 لا تدعم ضبط درجة الحرارة[^temperature].

لذلك عامِل الموجّه كما تعامل الكود: اختبره. يقول دليل Anthropic إن بناء تطبيق قائم على نموذج لغوي كبير (LLM) يبدأ
بتحديد معايير النجاح بوضوح، ثم بتصميم تقييمات تقيس الأداء مقابل هذه المعايير[^cycle]. وتفترض نظرته العامة
على هندسة الموجّهات أن لديك طرقًا لاختبار هذه المعايير تجريبيًا قبل أن تبدأ في تحسين الموجّه[^before].

يُسمّى اختبار الموجّه *تقييمًا* (evaluation، واختصارًا eval). لأول تقييم ثلاثة أجزاء:

- **الحالات.** مُدخلات، لكل منها الإجابة التي تتوقعها (وتُسمّى أحيانًا *الإجابة الذهبية*). اخترها لتشبه
  ما يصلك فعلًا: يوصي الدليل بتصميم تقييمات تعكس توزيع المهام في العالم الحقيقي، ويضيف: لا تنسَ أن تحسب حساب
  الحالات الحدّية (edge cases)[^taskspecific]. الحالة الحدّية مُدخل نادر أو غير مألوف يقع عند حدود ما يجب أن
  يتعامل معه موجّهك. ضع فيها هذه المُدخلات الصعبة، لا السهلة وحدها.
- **المُقيِّم.** كود يقارن إجابة النموذج بالإجابة المتوقعة ويقرّر: نجاح أو فشل. يوصي الدليل بصياغة الأسئلة
  بحيث يمكن تقييمها آليًا[^automate]. ويصف التقييم بالكود بأنه الأسرع والأكثر موثوقية، لكنه يفتقر إلى مراعاة
  الفروق الدقيقة في الأحكام المعقدة[^codegrade].
- **نسبة النجاح.** حصة الحالات الناجحة: عدد الحالات التي نجحت مقسومًا على عدد كل الحالات.

إليك مثالًا صغيرًا. يطلب الموجّه من النموذج أن يصنّف مراجعة منتج: إيجابية أو سلبية أو مختلطة. إحدى
الحالات هي المراجعة "Great screen, terrible battery." والإجابة المتوقعة "mixed". إن أجاب النموذج
"mixed" نجحت الحالة.

أبسط مُقيِّم هو *المطابقة التامة*: يجب أن تكون الإجابة هي النص المتوقع حرفًا بحرف. إنه صارم. يُفشل
"Mixed" و"mixed." مع أن أي إنسان سيقبلهما. أما المُقيِّم *المتسامح* فينظّف النصين قبل المقارنة. يصف الدليل
تقييمات المطابقة التامة بأنها تتحقق من تطابق المُخرج مع إجابة صحيحة محددة مسبقًا، عادةً بعد توحيد
المسافات وحالة الأحرف[^exact]. أي إن "المطابقة التامة" في الدليل تشمل عادةً هذا التنظيف؛ أما هذا الدرس فيعطي
الخطوتين اسمين منفصلين لترى الفرق بينهما. والمُقيِّم المتسامح في هذا الدرس يتجاهل أيضًا النقطة في آخر الإجابة.

للتسامح حدود. المُقيِّم الذي يقبل أي إجابة *تحتوي* كلمة "positive" سيقبل أيضًا "not positive". والمُقيِّم
المتساهل أكثر من اللازم يعطيك نسبة نجاح عالية لا معنى لها. لكن فحص "الاحتواء" ليس خطأً دائمًا: يذكر الدليل
*مطابقة النص الجزئي* (string match)، أي التحقق من أن عبارة أساسية موجودة في المُخرج[^stringmatch]. قد يناسب
ذلك إجابة طويلة يجب أن تذكر عبارة بعينها. أما مع تصنيفات قصيرة مثل positive أو not positive فهو خطِر.

الحالات البسيطة الكثيرة أفضل من الحالات المثالية القليلة: يقول الدليل إن أسئلة أكثر بتقييم آلي أقل دقة
قليلًا أفضل من أسئلة أقل بتقييم بشري يدوي عالي الجودة[^volume]. ابدأ بعدد صغير، وأضف حالة كلما وجدت
فشلًا جديدًا.

## جرّبها

احفظ هذا الكود في `try_eval.py` وشغّله بالأمر `python3 try_eval.py`. النموذج هنا *بديل* (stand-in): دالة
تعيد إجابات مُختلَقة تشبه ردود النموذج. لا يحتاج إلى شبكة ولا إلى مفتاح، ويعطي النتيجة نفسها في كل تشغيل،
لترى بالضبط ما يفعله كل مُقيِّم.

```python
"""Test a prompt on ten cases with two graders. No network: the model is a stand-in."""

PROMPT = (
    "Classify the sentiment of this product review as positive, negative or mixed. "
    "Answer with one word.\n\nReview: {review}"
)

CASES = [
    {"input": "Arrived on time and works perfectly.", "expected": "positive"},
    {"input": "Broke after two days.", "expected": "negative"},
    {"input": "Great screen, terrible battery.", "expected": "mixed"},
    {"input": "Exactly what I ordered.", "expected": "positive"},
    {"input": "The worst purchase I have made.", "expected": "negative"},
    {"input": "Fast delivery, but the box was damaged.", "expected": "mixed"},
    {"input": "I love it.", "expected": "positive"},
    {"input": "Oh great, it stopped working again.", "expected": "negative"},
    {"input": "Not bad at all.", "expected": "positive"},
    {"input": "It does the job, but I expected more.", "expected": "mixed"},
]

# Made-up answers in the style of a model's replies, so this example gives the same result on every run.
CANNED = {
    "Arrived on time and works perfectly.": "positive",
    "Broke after two days.": "negative",
    "Great screen, terrible battery.": "mixed",
    "Exactly what I ordered.": "Positive",
    "The worst purchase I have made.": "negative.",
    "Fast delivery, but the box was damaged.": "Mixed\n",
    "I love it.": "positive",
    "Oh great, it stopped working again.": "positive",
    "Not bad at all.": " POSITIVE ",
    "It does the job, but I expected more.": "The sentiment is mixed.",
}


def stand_in_model(review):
    """Plays the model. A real one would receive PROMPT.format(review=review)."""
    return CANNED[review]


def exact_match(output, expected):
    return output == expected


def normalized_match(output, expected):
    def clean(text):
        return " ".join(text.split()).lower().rstrip(".")

    return clean(output) == clean(expected)


def run_eval(cases, model, grader):
    failures = []
    for case in cases:
        output = model(case["input"])
        if not grader(output, case["expected"]):
            failures.append({**case, "output": output})
    passed = len(cases) - len(failures)
    return passed / len(cases), failures


if __name__ == "__main__":
    for name, grader in [("exact match", exact_match), ("normalized match", normalized_match)]:
        rate, failures = run_eval(CASES, stand_in_model, grader)
        print(f"{name}: {len(CASES) - len(failures)} of {len(CASES)} passed, pass rate {rate:.0%}")
        for failure in failures:
            print(f"  FAIL {failure['input']!r}: expected {failure['expected']!r}, got {failure['output']!r}")
```

يطبع:

```text
exact match: 4 of 10 passed, pass rate 40%
  FAIL 'Exactly what I ordered.': expected 'positive', got 'Positive'
  FAIL 'The worst purchase I have made.': expected 'negative', got 'negative.'
  FAIL 'Fast delivery, but the box was damaged.': expected 'mixed', got 'Mixed\n'
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'Not bad at all.': expected 'positive', got ' POSITIVE '
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
normalized match: 8 of 10 passed, pass rate 80%
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
```

### اقرأ النتائج

مع مُقيِّم المطابقة التامة تنجح 4 من 10 حالات، أي نسبة نجاح 40%. وأغلب هذه الإخفاقات ليست إجابات خاطئة:
"Positive" و"negative." فيهما التصنيف الصحيح بشكل مختلف قليلًا.

مع المُقيِّم المتسامح تنجح 8 من 10 حالات، أي نسبة نجاح 80%. الإخفاقان الباقيان حقيقيان، وكلٌّ منهما مشكلة
مختلفة:

- "Oh great, it stopped working again." سخرية، وقد أخطأ النموذج في تصنيفها. ويَعُدّ مثال التقييم الذي
  تقدّمه Anthropic نفسها السخريةَ حالةً حدّية (edge case)[^sarcasm]. الإصلاح مكانه الموجّه، كأن تضيف جملة عن
  السخرية، ثم تشغّل التقييم من جديد.
- "The sentiment is mixed." فيها التصنيف الصحيح، لكن الموجّه طلب كلمة واحدة. اجعل الموجّه أكثر صرامة في
  الشكل قبل أن تجعل المُقيِّم أكثر تساهلًا.

انظر إلى الحالة الأولى وحدها: إجابة مثالية. لو جرّبتها وحدها لما رأيت أي مشكلة.

### استبدل البديل بنموذج حقيقي

تتيح حزمة Python الرسمية (SDK) الوصول إلى واجهة Claude البرمجية من Python[^sdk]. إن كان لديك مفتاح API،
يمكنك استبدال البديل باستدعاء حقيقي. اسم النموذج أدناه أحد معرّفات النماذج في الواجهة البرمجية كما تسردها صفحة نظرة عامة على النماذج من Anthropic؛
وأسماء النماذج تتغيّر، فراجع تلك القائمة قبل التشغيل[^model]. وكما في أول استدعاء لواجهة Claude البرمجية،
يأخذ الكود كتلة النص (text block) من الرد، لا `content[0]`، ويترك متسعًا في `max_tokens`.

```python
import anthropic

client = anthropic.Anthropic()  # reads your key from the ANTHROPIC_API_KEY environment variable


def ask_claude(review):
    message = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT.format(review=review)}],
    )
    return next(block.text for block in message.content if block.type == "text")


rate, failures = run_eval(CASES, ask_claude, normalized_match)
```

شغّله أكثر من مرة. مع نموذج حقيقي قد تتغيّر نسبة النجاح من تشغيل إلى آخر، وهذا سبب إضافي لعدم الثقة في
إجابة واحدة.

## أخطاء شائعة

- **"لقد نجح عندما جرّبته."** مُدخل واحد وتشغيل واحد. اختبر مجموعة من الحالات وانظر إلى نسبة النجاح.
- **حالات سهلة فقط.** إن كانت كل الحالات واضحة، فلن تخبرك نسبة النجاح العالية بشيء. أضف المُدخلات التي
  تقلقك: السخرية، والمشاعر المختلطة، والنصوص القصيرة جدًا أو الطويلة جدًا.
- **تعديل الإجابات المتوقعة حتى تنجح الاختبارات.** الإجابة المتوقعة هي ما تحتاجه أنت، وتقرّرها قبل أن ترى
  المُخرج. لا تغيّرها إلا إذا اكتشفت أنها كانت خاطئة.
- **مُقيِّم صارم جدًا أو متساهل جدًا.** إن كان صارمًا جدًا بدت أخطاء الشكل كأنها إجابات خاطئة. وإن كان
  متساهلًا جدًا نجحت إجابات خاطئة. اقرأ بعض الحالات الناجحة أيضًا، لا الفاشلة وحدها.
- **الاكتفاء بالرقم.** نسبة النجاح تخبرك كم مرة؛ والحالات الفاشلة تخبرك لماذا.
- **الظن أن المطابقة التامة تكفي لكل مهمة.** إنها تناسب الإجابات القصيرة والقاطعة مثل التصنيفات. أما
  الإجابات التي تحتاج إلى حكم، فستستخدم الدروس اللاحقة نموذجًا مُقيِّمًا لها: يصف الدليل التقييم بنموذج لغوي
  بأنه سريع ومرن وقابل للتوسّع ومناسب للأحكام المعقدة، ويضيف: اختبر موثوقيته أولًا ثم وسّع
  استخدامه[^llmgrade].

## تمرينك

افتح `exercise/starter/evaluate.py`. فيه بعض الحالات ونموذج بديل وثلاث دوال عليك كتابتها:

- `exact_match(output, expected)`: تعيد صحيحًا فقط إذا كان النصان متطابقين تمامًا.
- `normalized_match(output, expected)`: تعيد صحيحًا إذا تساوى النصان بعد تجاهل الأحرف الكبيرة والصغيرة،
  والمسافات الزائدة، ونقطة أو علامة تعجب في النهاية. ويجب أن تفشل "not positive" أمام "positive".
  المُقيِّم في "جرّبها" يتجاهل النقطة وحدها؛ أما مُقيِّمك فيتجاهل أيضًا علامة "!" في النهاية.
- `run_eval(cases, model, grader)`: اسأل النموذج عن كل حالة مرة واحدة وبالترتيب، وقيّم كل إجابة بـ
  `grader(output, expected)`، وأعد زوجًا: نسبة النجاح (الحالات الناجحة مقسومة على كل الحالات) وقائمة
  الحالات الفاشلة. كل حالة فاشلة قاموس (dictionary) فيه `input` و`expected` و`output` و`error`.

وقاعدتان إضافيتان، لأن التقييمات الحقيقية تواجههما:

- قائمة الحالات الفارغة تُطلق `ValueError`. نسبة نجاح على لا شيء لا معنى لها.
- إذا أطلق النموذج استثناءً في حالة ما، تفشل هذه الحالة وتكون `output` فيها `None` و`error` فيها نص
  الخطأ، ثم يستمر التشغيل مع الحالة التالية. استدعاء API الحقيقي قد يفشل، وفشل واحد يجب ألا يوقف التقييم كله.

شغّل الاختبارات من مجلد البداية:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

ستفشل حتى تكتب دوالك. عندما تنجح، شغّل `python3 evaluate.py` لترى نسبة نجاح كل مُقيِّم، ثم جرّب حالاتك
الخاصة أو استبدل البديل بـ `ask_claude`. يوجد حل كامل في `exercise/solution/`: افتحه بعد أن تحاول.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إن وجدته صعبًا، فاقرأ "الفكرة" من جديد، ثم قارن مُخرجَي "جرّبها" حالةً حالة.
