# كتابة موجّه (prompt) واضح

## ما الذي ستتمكن من فعله

- تحويل طلب غامض إلى موجّه يذكر المهمة مباشرة ويعطي Claude السياق الذي ينقصه.
- إضافة أمثلة وتحديد الشكل الذي يجب أن تأتي عليه الإجابة بدقة.
- فصل أجزاء الموجّه بوسوم XML، وحذف الأجزاء التي لا تحتاج إليها.

## الفكرة

الموجّه (prompt) هو النص الذي ترسله إلى النموذج: تعليماتك، ومعها كل ما يحتاج إليه النموذج لتنفيذها.
في الدرس السابق أرسلت موجّهًا عبر الواجهة البرمجية (API). هذا الدرس عمّا تضعه فيه.

لا يرى Claude إلا الموجّه. لا يعرف منتجك ولا مستخدميك ولا ما سيفعله برنامجك بإجابته. يطلب منك
دليل Anthropic أن تتخيّل Claude موظفًا لامعًا لكنه جديد، لا يعرف أعرافكم ولا طريقة عملكم[^employee].
ويقترح اختبارًا يصلح لأي موجّه: اعرضه على زميل لا يعرف الكثير عن المهمة واطلب منه أن ينفّذه؛ فإن
احتار هو، فسيحتار Claude أيضًا[^golden].

تصنّف أمثلة هذا الدرس تذاكر الدعم: تذكرة الدعم (ticket) رسالة يرسلها العميل يطلب فيها المساعدة.
هذا موجّه غامض:

```text
Sort this ticket: "I was charged twice this month."
```

ومعناه: «صنّف هذه التذكرة: "خُصم مني المبلغ مرتين هذا الشهر."». صنّفها إلى ماذا؟ ما الإجابات
المقبولة؟ هل الرد كلمة واحدة أم جملة أم فقرة تشرح السبب؟ سيضطر Claude إلى التخمين. وفي تنبّؤات النموذج قدر من
العشوائية[^random]، لذلك قد يخمّن استدعاءان بطريقتين مختلفتين.

وهذا الطلب نفسه مكتوبًا بوضوح:

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

يطلب هذا الموجّه من Claude أن يصنّف التذكرة في فئة واحدة فقط من ثلاث: الفوترة (billing) أو خلل
(bug) أو طلب ميزة (feature_request)، ويشرح أن الشركة تبيع تطبيقًا لتحرير الصور وأن الفئة الخاطئة
تُرسل العميل إلى الفريق الخطأ، ويعطي مثالين، ويطلب اسم الفئة وحده بحروف صغيرة.

فيه خمس خطوات، وكل واحدة منها مأخوذة من دليل Anthropic لكتابة الموجّهات.

**اذكر المهمة مباشرة.** يستجيب Claude جيدًا للتعليمات الواضحة الصريحة[^clear]. سمِّ الفعل والإجابات
التي تقبلها: «صنّف في فئة واحدة فقط: billing أو bug أو feature_request»، لا «صنّف هذه».

**أعطِ السياق الذي ينقص Claude.** شرح السبب وراء التعليمة قد يساعد Claude على فهم أهدافك وتقديم إجابات
أكثر استهدافًا لما تريد[^context]. السياق هنا يقول من هي الشركة وما ثمن الفئة الخاطئة. لا يستطيع Claude
أن يعرف أيًّا من الأمرين ما لم تكتبه.

**أرِه أمثلة.** الأمثلة من أكثر الطرق موثوقية لتوجيه شكل إجابات Claude ونبرتها وبنيتها[^examples].
يوصي الدليل بثلاثة إلى خمسة أمثلة[^count]، ويطلب أن تكون متنوعة: تغطي الحالات الحدّية (المدخلات غير المعتادة أو التي تقع على الحدّ بين فئتين) وتختلف بما
يكفي كي لا يلتقط Claude أنماطًا لم تقصدها[^diverse]. في الموجّه أعلاه مثالان فقط ليبقى قصيرًا.
المصنِّف الحقيقي (برنامج يفرز المدخلات في فئات ثابتة) يضيف أمثلة أكثر، منها حالة صعبة مثل طلب استرداد مال سببه خلل في التطبيق.

**حدّد شكل المخرجات.** كن دقيقًا في الشكل الذي تريده وفي القيود[^format]. سيقارن برنامجك رد Claude
بقائمة الفئات: `billing` تطابق، و`This looks like a billing issue.` لا تطابق. قل ما يجب فعله بدل
الاكتفاء بما يجب تجنّبه[^positive]: «أجب باسم الفئة وحده» أنفع من «لا تشرح».

**افصل الأجزاء بوسوم XML.** تساعد وسوم XML Claude على قراءة موجّه يخلط التعليمات والسياق والأمثلة
والمدخلات المتغيرة دون أن يخلط جزءًا بآخر[^xml]. الوسم اسم بين قوسين زاويين، `<context>`، يُغلق
بالاسم نفسه مع شرطة مائلة، `</context>`. توضع الأمثلة في وسوم `<example>`، كلها داخل وسم `<examples>`
واحد، ليميّزها Claude عن التعليمات[^example-tags]. التذكرة مُدخل متغير: تتبدّل في كل استدعاء، لذلك
تأخذ وسمًا خاصًا بها فلا تختلط كلمات العميل بتعليماتك.

لغة XML طريقة لتمييز أجزاء النص بوسوم كهذه. استخدم أسماء وسوم ثابتة تصف ما بداخلها، مثل `<ticket>`
للتذكرة[^tag-names].

الموجّه الواضح يجعل الإجابة الجيدة أرجح، لكنه لا يضمنها: قد يختار Claude الفئة الخطأ رغم ذلك. وليست
كل مشكلة تُحل بتعديل الموجّه: سرعة الاستجابة أو التكلفة مثلًا قد يكون تحسينهما أسهل أحيانًا باختيار
نموذج آخر[^not-always]. يعلّمك الدرس
التالي كيف تختبر الموجّه مقابل إجابات متوقعة، لتعرف هل أفاد التعديل أم لا.

## جرّبها

هذا البرنامج يبني الموجّهين ويطبعهما. يستخدم المكتبة القياسية وحدها ولا يتصل بالشبكة. احفظه باسم
`try_prompt.py` وشغّل `python3 try_prompt.py`.

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

الناتج هو الموجّهان المعروضان في «الفكرة». غيّر جزءًا واحدًا، كأن تحذف سطر `output_format`، وانظر
ما الذي لن يُقال لـ Claude بعد ذلك.

الموجّهات هنا بالإنجليزية كي تبقى الشيفرة واحدة في كل لغات هذه الدورة. يعمل Claude جيدًا بلغات
كثيرة غير الإنجليزية[^languages]، فيمكنك أن تكتب موجّهاتك بالعربية.

### أرسله إلى Claude

إن كان لديك مفتاح API من الدرس السابق، فيمكنك إرسال الموجّهين ومقارنة الإجابتين. أضف هذه الأسطر
في آخر `try_prompt.py`. هذا الجزء يتصل بالشبكة وله تكلفة صغيرة، وهو اختياري.

```python
import anthropic

MODEL = "..."  # معرّف النموذج الذي استخدمته في الدرس السابق
client = anthropic.Anthropic()
for prompt in (vague, clear):
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    # قد يبدأ الرد بكتل أخرى، كالتفكير (thinking): اطبع أول كتلة نصية
    print(next(block.text for block in message.content if block.type == "text"))
    print("---")
```

شغّله أكثر من مرة. وانظر: هل يستطيع برنامجك أن يستخدم الإجابة عن الموجّه الغامض؟

## أخطاء شائعة

**«Claude يعرف ما أقصده.»** لا يعرف إلا ما في الموجّه. إن كان زميل جديد سيحتاج إلى أن يسأل سؤالًا،
فاكتب جوابه في الموجّه.

**«الموجّه الأطول أفضل.»** الطول ليس هدفًا. كل جزء يجب أن يخبر Claude بشيء يحتاج إليه. وسم `<context>`
فارغ، أو قسم مكتوب فيه «لا يوجد»، يضيف ضجيجًا بلا معلومة. احذفه.

**«يكفي أن أقول لـ Claude ما لا يفعله.»** عبارة «لا تشرح» تترك شكل الإجابة مفتوحًا. قل ما يجب أن تكون
عليه الإجابة[^positive].

**«أمثلتي متشابهة، إذن هي متّسقة.»** الأمثلة التي تشترك كلها في صدفة، كالطول نفسه أو الفئة نفسها،
قد تعلّم Claude تلك الصدفة[^diverse]. نوّعها عن قصد.

**«وسوم XML أوامر خاصة يجب أن أحفظها.»** الوسم عنوان لجزء من موجّهك. استخدم أسماء وسوم ثابتة ووصفية في
كل موجّهاتك[^tag-names]. الوسم `<ticket>` مناسب لأنه يقول ما بداخله.

**«الوسوم تجعل المدخلات آمنة.»** الوسوم تُري Claude أين يبدأ المُدخل وأين ينتهي. لا تعتمد عليها
وحدها لمنع نص داخل المُدخل من أن يتصرّف كأنه تعليمة. تعود الدورة إلى هذا حين تشرح حقن الموجّهات
(prompt injection)، أي نص يوضع في المُدخل ليتّبعه Claude بدل تعليماتك.

## تمرينك

افتح `exercise/starter/prompt_builder.py` واكتب الدالة
`build_prompt(task, context, examples, output_format, input_text)`.
تعيد نصًا واحدًا فيه:

- كل جزء، بعد إزالة المسافات من حوله، داخل وسم خاص به، بهذا الترتيب: `<task>` ثم `<context>` ثم
  `<examples>` ثم `<output_format>`، وأخيرًا `<input>`؛
- كل مثال داخل وسم `<example>` خاص به، وكل الأمثلة داخل `<examples>`؛
- المُدخل المتغير (كالتذكرة) داخل `<input>`، في الآخر، فلا يختلط بتعليماتك؛
- الوسم على سطر مستقل قبل محتواه وبعده، وسطر فارغ واحد بين كل جزأين؛
- الجزء الفارغ أو الذي لا يحوي إلا مسافات، والمثال الفارغ، يُحذفان تمامًا؛
- المهمة الفارغة تُرفض برفع `ValueError`، لأن موجّهًا بلا مهمة لا يطلب شيئًا.

شغّل الاختبارات من مجلد البداية:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

ستفشل حتى تصبح دالتك صحيحة. يوجد حل في `exercise/solution/`؛ حاول بنفسك أولًا.

## اختبر نفسك

أجب عن الأسئلة في `quiz.json`. إن وجدتها صعبة، فاقرأ «الفكرة» مرة أخرى وانظر ما الذي يعطيه كل جزء
من أجزاء الموجّه الواضح الخمسة لـ Claude.

[^employee]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^golden]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^clear]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^context]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^examples]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^count]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^diverse]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^format]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^positive]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^xml]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^example-tags]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^tag-names]: Anthropic، أفضل ممارسات كتابة الموجّهات (Prompting best practices).
[^not-always]: Anthropic، نظرة عامة على هندسة الموجّهات (Prompt engineering overview).
[^random]: Anthropic، مسرد المصطلحات، «درجة الحرارة» (Glossary, Temperature).
[^languages]: Anthropic، دعم اللغات المتعددة (Multilingual support).
