# ثبّت Claude Code ووافق على أفعاله

## ما الذي ستتمكن من فعله

- تثبيت Claude Code وبدء جلسة في مجلد مشروع.
- أن تطلب من Claude Code قراءة الكود وشرحه، ثم تعديله.
- معرفة الإجراءات التي يستأذنك فيها Claude Code، والموافقة على كل منها أو رفضه.

## الفكرة

Claude Code مساعد برمجة يعمل بالذكاء الاصطناعي، يساعدك على بناء الميزات وإصلاح الأخطاء وأتمتة مهام
التطوير[^what]. تتحدث إليه من الطرفية (terminal). ستستخدمه هذه الدورة في كل وحدة، لذلك يدور هذا الدرس الأول حول العمل معه بأمان.

اسمان يهمّاننا هنا. Claude هو نموذج الذكاء الاصطناعي: البرنامج الذي يقرأ طلبك ويختار ما يفعله. أما
Claude Code فهو البرنامج الذي يحيط به على حاسوبك: يعطي Claude أدواته ويدير ما يراه Claude[^harness].

يفترض هذا الدرس أنك تعلّمت ما تعلّمه الدورة الخارجية في المستوى 0: أن تفتح الطرفية، وتتنقّل بين المجلدات،
وتشغّل ملف Python، وتستخدم git لإنشاء إيداع (commit) وقراءة الفروق (diff)، أي الأسطر التي تغيّرت بين
نسختين من الملف.

**ماذا يحدث حين تطلب منه شيئًا.** حين تعطي Claude مهمة، يمرّ بثلاث مراحل: يجمع السياق، ثم يتّخذ
إجراءً، ثم يتحقّق من النتيجة[^loop]. ويفعل ذلك بالأدوات. فمن دون أدوات لا يستطيع Claude إلا الرد
بالنص؛ أما بالأدوات فيستطيع قراءة الكود وتعديل الملفات وتشغيل الأوامر والبحث في الويب والتعامل مع
خدمات خارجية[^tools].

مثال ذلك أن تكتب:

```text
add a function that splits the bill between people
```

ومعناه: «أضف دالة تقسّم الفاتورة بين الأشخاص». يقرأ Claude ملفاتك ليجد أين تُحسب الفاتورة (جمع
السياق). ثم يعدّل ملفًا ليضيف الدالة (اتخاذ الإجراء). وقد يشغّل الملف ليرى أنه يعمل (التحقّق). كل
خطوة من هذه إجراءٌ على حاسوبك.

**من يقرّر ما الذي يعمل.** بعض الإجراءات لا ضرر فيها: قراءة ملف لا تغيّر شيئًا. وبعضها يغيّر ملفاتك
أو يشغّل برامج. في Claude Code أوضاعٌ للأذونات (permission modes) تحدّد الإجراءات التي يتّخذها دون أن
يسألك. في الوضع اليدوي (Manual) يتوقّف Claude Code ويسألك قبل معظم الإجراءات التي تعدّل الملفات أو
تشغّل أوامر الطرفية أو تتصل بالشبكة[^manual]. وأمر الطرفية (shell command) أمرٌ تكتبه في الطرفية،
مثل `python3 tip.py`.

حين يسألك، يظهر لك طلب إذن (permission prompt). يعرض طلب الإذن ما يوشك Claude أن يفعله، ثم
خياراتك[^prompt]. تختار **Yes** (نعم) لتوافق[^first-change] أو **No** (لا) لترفض[^deny]. وكثير من الطلبات يعرض أيضًا
**Yes, and don't ask again** (نعم، ولا تسألني مجددًا)، وهذا الخيار يوافق أيضًا على ما يأتي بعده من إجراءات من النوع نفسه، وتختلف
مدّته باختلاف الإجراء[^bash-approval]. اقرأ الطلب قبل أن تجيب: هذه هي لحظة القرار.

ولا يسأل كل أمر. يتعرّف Claude Code على مجموعة مدمجة من أوامر Bash على أنها للقراءة فقط، ويشغّلها
دون طلب إذن في كل الأوضاع[^read-only]. و Bash هو البرنامج الذي يشغّل أوامر الطرفية. تضم هذه
المجموعة `ls` و `cat` و `echo` و `pwd` و `head` و `tail` و `grep` و `find` و `wc` و `which` و
`diff` و `stat` و `du` و `cd`، وصيغ `git` التي تقرأ فقط[^read-only-list]. هذه الأوامر تطّلع على
الملفات ولا تغيّرها.

**الوضع الذي تبدأ به الجلسة.** في Claude Code بالإصدار v2.1.283 أو أحدث، يكون الوضع التلقائي (auto)
هو وضع البداية المدمج لجلسات الطرفية التفاعلية وجلسات VS Code[^auto-default]. في الوضع التلقائي
يراجع نموذجٌ ثانٍ، هو المصنِّف (classifier)، الإجراءاتِ بدلًا منك[^classifier]. والمصنِّف برنامج يفرز
كل إجراء إلى مسموح أو ممنوع. وهو نموذج أيضًا، فقد يخطئ.

في هذه الوحدة تراجع كل إجراء بنفسك، لذلك تبدأ في الوضع اليدوي. يقبل سطر الأوامر الاسم `manual`
لهذا الوضع: `claude --permission-mode manual`[^manual-flag]. ويمكنك أيضًا أن تضغط `Shift+Tab` في
أي وقت لتغيّر وضع الأذونات في الجلسة التي أنت فيها[^shift-tab].

## جرّبها

تحتاج إلى حساب لدى Claude لتستخدم Claude Code: اشتراك Claude (Pro أو Max أو Team أو Enterprise)، أو
حساب Claude Console (وصول إلى الواجهة البرمجية API برصيد مدفوع مسبقًا، والواجهة البرمجية هي الطريق الذي تستدعي به برامجُك
أنت Claude)[^console]، أو وصول عبر مزوّد سحابي مدعوم، أي شركة تشغّل Claude على خوادمها[^account]. هذه خدمات مدفوعة، فاطّلع على السعر قبل
أن تشترك.

### التثبيت

على macOS أو Linux أو WSL (نظام Linux داخل Windows)، أمر التثبيت هو[^install]:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

وفي موجّه أوامر Windows (CMD) هو[^install-windows]:

```bat
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

حين ينتهي المثبّت، افتح نافذة طرفية جديدة وشغّل `claude --version`. التثبيت السليم يطبع رقم
إصدار[^version].

### مشروع صغير

أنشئ مجلدًا فيه ملف Python واحد وأودِعه (commit)، حتى يستطيع git أن يريك لاحقًا ما غيّره Claude:

```bash
mkdir tip-calc
cd tip-calc
git init
```

احفظ هذا باسم `tip.py`:

```python
"""A small tip calculator."""


def tip(total, percent):
    """Return the tip on a bill: percent of the total, rounded to cents."""
    return round(total * percent / 100, 2)


if __name__ == "__main__":
    print(tip(50, 15))
```

البرنامج يحسب البقشيش: نسبةً مئوية من الفاتورة. شغّله بالأمر `python3 tip.py`، فيطبع:

```text
7.5
```

ثم أودِعه:

```bash
git add tip.py
git commit -m "Add the tip calculator"
```

### جلستك الأولى

افتح الطرفية في أي مجلد مشروع وابدأ Claude Code[^start]. المشروع هنا هو `tip-calc`، وتبدأ في الوضع
اليدوي:

```bash
claude --permission-mode manual
```

يطلب منك Claude Code تسجيل الدخول في أول استخدام[^login]. اتّبع خطواته في المتصفح.

**اطلب منه أن يقرأ ويشرح.** اكتب:

```text
explain what tip.py does, line by line
```

أي: «اشرح ما يفعله tip.py سطرًا سطرًا». يقرأ Claude Code ملفات مشروعك حين يحتاج إليها، فلا داعي
لأن تلصقها له[^reads]. وقراءة الملفات داخل مجلد مشروعك لا تحتاج إلى موافقة[^reads-free]، لذلك يجيب
دون طلب إذن. قارن جوابه بالكود: هل يذكر أن `round(..., 2)` يُبقي رقمين بعد الفاصلة؟

**اطلب منه أن يعدّل الكود.** اكتب:

```text
add a function split(total, percent, people) to tip.py that returns what each person pays, tip included
```

أي: «أضف إلى tip.py دالة split تعيد ما يدفعه كل شخص، شاملًا البقشيش». يظهر طلب إذن للتعديل، يعرض ما يوشك Claude أن يفعله[^prompt]. اقرأه. إن كان التعديل يفعل ما طلبته ولا يمسّ إلا
`tip.py`، فاختر **Yes**. وإن فعل شيئًا آخر، فاختر **No**.

**اطلب منه أن يشغّل الملف.** اكتب:

```text
run tip.py
```

ليس `python3` من مجموعة أوامر القراءة فقط، لذلك يظهر طلب إذن قبل تشغيل الأمر. وافق عليه: فأنت تعرف ما
يفعله `tip.py`.

**ارفض مرة عن قصد.** اطلب شيئًا لا تريده، مثل `delete tip.py` (احذف tip.py). إن سألك Claude في المحادثة أولًا
هل أنت متأكد، فأجب بنعم ليظهر طلب الإذن. ثم اختر **No**. إن اخترت
**No** دون تعليق، يتوقف Claude Code عن العمل على طلبك[^deny]. أعد المحاولة، وقبل أن تجيب انتقل إلى **No**
واضغط `Tab` ليُفتح حقل للتعليق[^comment]، واكتب السبب. يرسل Claude Code تعليقك إلى Claude على أنه سبب الرفض، ويواصل Claude
العمل[^deny-comment].

للخروج اكتب `/exit`[^exit]. ثم شغّل `git diff` في الطرفية: يعرض كل سطر غيّره Claude منذ إيداعك. والدرس
التالي عن قراءته.

## أخطاء شائعة

**«يفعل Claude Code ما يشاء على حاسوبي».** في الوضع اليدوي يسألك قبل معظم التعديلات والأوامر والاتصال
بالشبكة[^manual]. ما يعمل قرارك أنت، فاقرأ كل طلب إذن.

**«القراءة آمنة، إذن كل شيء آمن».** القراءة وأوامر القراءة فقط تعمل دون سؤال. أما التعديلات وبقية
الأوامر فتسأل. والإجابة بـ **Yes** على تعديل أو أمر تغيّر ملفاتك.

**«Yes, and don't ask again مثل Yes تمامًا».** ليست كذلك. في تعديل الملفات تدوم الموافقة حتى نهاية
الجلسة[^edit-approval]. وفي أمر Bash تُحفظ قاعدةٌ تسري على الجلسات القادمة في أي مكان من ذلك
المستودع[^bash-approval]. لا تخترها إلا لأوامر كنت ستوافق عليها في كل مرة.

**«إن كتبتُ في طلبي "لا تحذف الملفات أبدًا" فلن يستطيع حذفها».** قواعد الأذونات يفرضها Claude Code لا
النموذج[^enforced]. كلماتك توجّه ما يحاول Claude فعله. أما ما يعمل فعلًا فتقرّره طلبات الإذن والقواعد.

**«الجلسة الجديدة تسألني عن كل شيء».** في الإصدارات الحديثة تبدأ الجلسة الجديدة في الوضع التلقائي،
حيث يقرّر المصنِّف بدلًا منك[^auto-default]. ابدأ بالأمر `claude --permission-mode manual`، أو بدّل
الوضع بـ `Shift+Tab`، حين تريد أن تراجع كل إجراء.

**«إذا بدأ فلا أستطيع إيقافه».** اضغط `Esc` لتوقف Claude فورًا[^esc]. وقبل أن يعدّل Claude ملفًا،
يحفظ نسخة من محتواه الحالي؛ اضغط `Esc` مرتين لترجع إلى حالة سابقة، أو اطلب من Claude أن يتراجع[^rewind].
لكن الترجيع لا يغطّي كل شيء: فهو لا يتتبّع الملفات التي غيّرتها أوامر Bash[^bash-untracked]. أودِع
عملك، ليستطيع git دائمًا أن يعيده.

## تمرينك

لا يمكن تشغيل Claude Code داخل اختبار، لذلك يدرّبك هذا التمرين على القرار الذي تتخذه عند كل طلب إذن.
افتح `exercise/starter/permission_check.py`. يصف الملف كل إجراء يطلبه Claude بقاموس، مثل
`{"tool": "Edit", "file": "tip.py"}` أو `{"tool": "Bash", "command": "python3 tip.py"}`.

اكتب دالتين.

تعيد `asks_first(action)` القيمة `True` حين يسألك الوضع اليدوي أولًا:

- `Read` و `Grep` و `Glob` (الأدوات التي تقرأ الملفات وتبحث فيها) لا تسأل أبدًا؛
- `Edit` و `Write` (الأدوات التي تغيّر الملفات) تسأل دائمًا؛
- `Bash` يسأل، إلا إذا كان الأمر أمرًا واحدًا بسيطًا (بلا `;` ولا `&` ولا `|` ولا `>` ولا `<` ولا
  علامة اقتباس مائلة ولا `$(` ولا سطر جديد) وبرنامجه من `READ_ONLY_COMMANDS`؛
- أي أداة أخرى تسأل: حين لا تكون متأكدًا، اسأل.

في أوامر الطرفية، يرسل `>` مخرجات الأمر إلى ملف، ويُدخل `<` ملفًا إلى الأمر؛ ويسمّى كلاهما إعادة توجيه
(redirection).

هذا نموذج مبسّط يسأل كلما لم يكن متأكدًا. أما Claude Code الحقيقي فينظر عن قرب أكثر: فهو مثلًا يفحص الملف الذي تشير إليه إعادة التوجيه (`>` أو `<`) كأن Claude يكتبه أو يقرؤه مباشرة[^redirect]، ويعدّ صيغ
`git` التي تقرأ فقط أوامرَ للقراءة فقط[^read-only-list]. يترك
التمرين هذه الحالات جانبًا.

وتعيد `answer(action, task_files, expected_commands)` ما ستجيب به:

- `"no prompt"` حين تكون `asks_first(action)` هي `False`؛
- مع `Edit` أو `Write`: `"yes"` حين يكون الملف من `task_files`، وإلا `"no"`؛
- مع `Bash`: `"yes"` حين يكون الأمر، بعد حذف المسافات حوله، من `expected_commands`، وإلا `"no"`؛
- مع أي أداة أخرى: `"no"`.

شغّل الاختبارات من مجلد البداية (`exercise/starter/`):

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تصبح دالتاك صحيحتين. يوجد حلّ في `exercise/solution/`؛ حاول بنفسك أولًا. ثم
جرّب الشيء الحقيقي: جلسة واحدة في الوضع اليدوي على `tip-calc`، توافق فيها على تعديل واحد وترفض إجراءً
واحدًا.

## اختبر نفسك

أجب عن الأسئلة في `quiz.json`. إن وجدتها صعبة، فاقرأ «الفكرة» مرة أخرى، والأخطاء الشائعة عن
**Yes, and don't ask again**.

[^what]: وثائق Claude Code، نظرة عامة (Overview).
[^loop]: وثائق Claude Code، كيف يعمل Claude Code (How Claude Code works).
[^tools]: وثائق Claude Code، كيف يعمل Claude Code (How Claude Code works).
[^manual]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^prompt]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^read-only]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^read-only-list]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^auto-default]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^classifier]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^manual-flag]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^shift-tab]: وثائق Claude Code، البدء السريع (Quickstart).
[^account]: وثائق Claude Code، البدء السريع (Quickstart).
[^install]: وثائق Claude Code، البدء السريع (Quickstart).
[^install-windows]: وثائق Claude Code، البدء السريع (Quickstart).
[^version]: وثائق Claude Code، البدء السريع (Quickstart).
[^start]: وثائق Claude Code، البدء السريع (Quickstart).
[^login]: وثائق Claude Code، البدء السريع (Quickstart).
[^reads]: وثائق Claude Code، البدء السريع (Quickstart).
[^deny]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^deny-comment]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^edit-approval]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^bash-approval]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^enforced]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^esc]: وثائق Claude Code، كيف يعمل Claude Code (How Claude Code works).
[^rewind]: وثائق Claude Code، كيف يعمل Claude Code (How Claude Code works).
[^bash-untracked]: وثائق Claude Code، نقاط الاستعادة (Checkpointing).
[^reads-free]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^harness]: وثائق Claude Code، كيف يعمل Claude Code (How Claude Code works).
[^first-change]: وثائق Claude Code، البدء السريع (Quickstart).
[^comment]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
[^exit]: وثائق Claude Code، البدء السريع (Quickstart).
[^console]: وثائق Claude Code، البدء السريع (Quickstart).
[^redirect]: وثائق Claude Code، إعداد الأذونات (Configure permissions).
