# من الخطة إلى الإيداع

## ما الذي ستتمكن من فعله

- استخدام وضع التخطيط (plan mode) ليستكشف Claude الكود ويقترح خطة قبل أن يغيّر أي شيء.
- إعطاء Claude وسيلة تحقق يستطيع تشغيلها، ثم الموافقة على الخطة وتركه ينفّذ التغيير.
- مراجعة النتيجة وإيداع (commit) تغيير واحد برسالة تقول ما الذي يفعله.

## الفكرة

في الدرسين الأولين وافقت على الإجراءات واحدًا واحدًا، وقرأت الفروق التي تركتها. هذا الدرس يرتّبها
خطواتٍ لتغيير كامل واحد.

ترك Claude يقفز مباشرة إلى كتابة الكود قد ينتج كودًا يحلّ المشكلة الخطأ[^wrong-problem]. ويعطي دليل
Anthropic العلاج: افصل البحث والتخطيط عن التنفيذ[^separate]. وسير العمل الذي يوصي به أربع
مراحل[^phases]: **الاستكشاف**، ثم **التخطيط**، ثم **التنفيذ**، ثم **الإيداع**.

**وضع التخطيط.** يطلب وضع التخطيط من Claude أن يبحث ويقترح تغييرات دون أن يجريها. يقرأ Claude الملفات،
ويشغّل أوامر الطرفية ليستكشف، ويكتب خطة، لكنه لا يعدّل الكود المصدري[^plan-mode]. تدخله بالضغط على
`Shift+Tab` (حتى يُظهر شريط الحالة `⏸ plan mode on`)، أو ببدء الجلسة بالأمر
`claude --permission-mode plan`[^start-plan]، أو بوضع `/plan` قبل طلب واحد[^enter-plan].

حين تجهز الخطة، يعرضها Claude ويسألك كيف يتابع. يهمّنا هنا جوابان:

- **Yes, manually approve edits**: توافق على الخطة، وتراجع كل تعديل على حدة[^approve-manual].
- **No, keep planning**: تبقى في وضع التخطيط وتقول لـ Claude ما الذي يجب تغييره[^keep-planning].

الموافقة على الخطة تُخرجك من وضع التخطيط، فيبدأ Claude التعديل[^approve-exits]. ويمكنك أيضًا أن تضغط
`Ctrl+G` لتفتح الخطة في محرّر النصوص وتعدّلها بنفسك قبل أن يتابع Claude[^ctrl-g].

**وسيلة تحقق يستطيع Claude تشغيلها.** قبل أن ينفّذ Claude أي شيء، أعطه طريقة يعرف بها متى ينتهي:
اختبارات، أو بناء، أو لقطة شاشة للمقارنة[^check]. ومثال الدليل يقولها صراحة: اكتب اختبارًا فاشلًا يُظهر
المشكلة، ثم أصلحها[^failing-test]. والاختبار الفاشل اختبارٌ يصف ما تريده ويفشل اليوم، لأن الكود لا يفعله
بعد.

**تغيير واحد، إيداع واحد.** الإيداع يسجّل المحتوى الحالي للفهرس (index) مع رسالة تصف
التغييرات[^git-commit]. أودِع تغييرًا واحدًا في كل مرة، برسالة تقول ما الذي تغيّر ولماذا. فإن ساء
التغيير التالي، استطعت دائمًا أن تعود إلى هذا.

هذه الحلقة كاملة على مثال واحد. تريد أن ترفض `tip` النسبة المئوية السالبة.

- **استكشف وخطّط** في وضع التخطيط: «اقرأ tip.py و test_tip.py؛ أريد أن ترفض tip() النسبة السالبة.
  ضع خطة».
- **راجع الخطة.** هل تغيّر `tip.py` وحده؟ هل تقول أي خطأ ترفعه؟ إن لم تفعل، فأجب بـ
  **No, keep planning** وقل ما الذي يجب تغييره.
- **نفّذ**: وافق بـ **Yes, manually approve edits**، واقرأ كل تعديل، واطلب من Claude تشغيل الاختبارات.
- **راجع**: اقرأ `git diff` ومخرجات الاختبارات، كما في الدرس السابق.
- **أودِع**: اطلب من Claude أن يودِع برسالة وصفية[^commit-step]، واقرأ أمر `git commit` في طلب الإذن،
  ثم وافق عليه.

**متى لا تخطّط.** وضع التخطيط مفيد، لكن له كلفة[^overhead]. إن استطعت وصف الفروق بجملة واحدة، فتخطَّ
الخطة[^one-sentence]. والتغيير السابق بهذا الصغر: نخطّط له هنا للتدرّب على الخطوات فقط. يكون التخطيط
أنفع حين لا تكون متأكدًا من الطريقة، أو حين يمسّ التغيير عدة ملفات، أو حين لا تعرف الكود
جيدًا[^planning-useful].

## جرّبها

استخدم المشروع `tip-calc` من الدرس الأول. ابدأ Claude Code في الوضع اليدوي (Manual)، كما فعلت من قبل.

### اكتب وسيلة التحقق أولًا

احفظ هذا باسم `test_tip.py` بجانب `tip.py`:

```python
import unittest

from tip import tip


class TipTest(unittest.TestCase):
    def test_tip(self):
        self.assertEqual(tip(50, 15), 7.5)

    def test_a_negative_percent_is_refused(self):
        with self.assertRaises(ValueError):
            tip(50, -5)


if __name__ == "__main__":
    unittest.main()
```

شغّل `python3 -m unittest` في المجلد `tip-calc`. يفشل الاختبار الجديد، لأن `tip` لا ترفض النسبة السالبة
بعد:

```text
F.
======================================================================
FAIL: test_a_negative_percent_is_refused (test_tip.TipTest.test_a_negative_percent_is_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tip-calc/test_tip.py", line 11, in test_a_negative_percent_is_refused
    with self.assertRaises(ValueError):
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 2 tests in 0.000s

FAILED (failures=1)
```

قد تختلف الأسطر قليلًا باختلاف إصدار Python لديك. أودِع الاختبار، حتى لا تُظهر الفروق لاحقًا إلا تغيير
Claude:

```bash
git add test_tip.py
git commit -m "Test that tip refuses a negative percent"
```

### خطّط

في Claude Code اضغط `Shift+Tab` حتى يُظهر شريط الحالة `⏸ plan mode on`، ثم اكتب:

```text
read tip.py and test_tip.py. test_a_negative_percent_is_refused fails. Plan the smallest change to tip.py that makes it pass. Do not change the tests.
```

أي: «اقرأ tip.py و test_tip.py. الاختبار test_a_negative_percent_is_refused يفشل. خطّط لأصغر تغيير في
tip.py يجعله ينجح. لا تغيّر الاختبارات». اقرأ الخطة. إن مسّت ملفًا غير `tip.py`، أو غيّرت اختبارًا،
فاختر **No, keep planning** وقل ذلك.

### نفّذ وتحقّق

اختر **Yes, manually approve edits**. اقرأ التعديل في طلب الإذن قبل أن توافق عليه. ثم اكتب:

```text
run python3 -m unittest and show me the output
```

أي: «شغّل `python3 -m unittest` وأرني المخرجات». وافق على الأمر. يجب أن ينجح الاختباران. اقرأ المخرجات
بنفسك: فهي دليلك.

### راجع وأودِع

شغّل `git diff` في طرفية أخرى، أو `/diff` داخل Claude Code. يجب ألّا يتغيّر إلا `tip.py`، وفقط ليرفض
النسبة السالبة. ثم اكتب:

```text
commit this change with a descriptive message
```

أي: «أودِع هذا التغيير برسالة وصفية». يعرض طلب الإذن أمر `git commit` ورسالته. وافق عليه إن كانت
الرسالة تقول ما الذي تغيّر. ثم شغّل `git log --oneline` لترى إيداعيك: الاختبار، ثم الإصلاح.

## أخطاء شائعة

**«وضع التخطيط يجعل التغيير آمنًا».** يمنع وضع التخطيط Claude من تعديل الكود المصدري ما دام
يخطّط[^plan-mode]. لكن الخطة نفسها قد تكون خاطئة. اقرأها، وصحّح مسار Claude بمجرد أن تلاحظ أنه
انحرف[^course-correct].

**«خطّط أولًا دائمًا».** للتخطيط كلفة[^overhead]. والتغيير الذي تصفه بجملة واحدة لا يحتاج
إليه[^one-sentence].

**«الموافقة على الخطة موافقة على كل تعديل».** ليس مع **Yes, manually approve edits**: فما زلت تراجع كل
تعديل[^approve-manual]. أما خيار الموافقة الآخر فيبدأ الوضع التلقائي (auto)[^approve-auto]، حيث يراجع
المصنِّف (classifier) التعديلاتِ بدلًا منك؛ فلا تختره إلا إن كنت ستراجع الفروق بعد ذلك.

**«كتب Claude اختبارات، إذن التغيير مُختبَر».** الاختبارات التي تُكتب بعد الكود قد تختبر ما يفعله الكود
لا ما أردته أنت. اكتب وسيلة التحقق أو اقرأها قبل التنفيذ، وانظر في تغييرات الاختبارات داخل الفروق.

**«يكفي إيداع واحد في آخر اليوم».** الإيداع الذي يخلط عدة تغييرات صعبُ المراجعة وصعبُ التراجع عنه.
أودِع كل تغيير وحده، بعد أن تنجح اختباراته وتقرأ فروقه.

**«أودع Claude، إذن السجلّ سليم».** اقرأ رسالة الإيداع في طلب الإذن. يجب أن تقول ما الذي تغيّر. وإن لم
تفعل، فأجب بـ **No** وقل كيف ينبغي أن تكون الرسالة.

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/bill.py`. تقسم دالته `split_bill(total_cents, tip_percent, people)` فاتورةً،
مع البقشيش، بين عدة أشخاص بالسنتات الكاملة. العمل بالسنتات (أعداد صحيحة) يجنّبك مفاجآت التقريب في
الأعداد العشرية: يجب أن يساوي مجموع الحصص الفاتورة مع بقشيشها بالضبط. وتذكر سلسلة التوثيق (docstring)
القواعد: يُقرَّب البقشيش إلى أقرب سنت (ونصف السنت يُقرَّب إلى الأعلى)، والسنتات التي لا تنقسم بالتساوي
تذهب واحدًا واحدًا إلى أوائل الأشخاص، والمدخلات الخاطئة ترفع `ValueError`. والاختبارات في
`exercise/tests/` هي وسيلة التحقق.

انقل هذا التغيير من الخطة إلى الإيداع مع Claude Code:

- انسخ `exercise/starter/bill.py` و `exercise/tests/test_bill.py` إلى مجلد جديد، وشغّل فيه `git init`،
  وأودِع الملفين.
- شغّل `python3 -m unittest` وانظر كيف تفشل الاختبارات.
- في وضع التخطيط، اطلب من Claude أن يقرأ الملفين ويخطّط لتنفيذ `split_bill` بحيث تنجح الاختبارات دون
  تغييرها. راجع الخطة. واطلب منه مواصلة التخطيط إن كان أي شيء غير واضح.
- وافق بـ **Yes, manually approve edits**. وراجع كل تعديل.
- اجعل Claude يشغّل الاختبارات ويريك المخرجات. واقرأ `git diff`: يجب ألّا يتغيّر إلا `bill.py`.
- اطلب من Claude أن يودِع برسالة وصفية، وتحقّق من الرسالة قبل أن توافق.

### شغّل الاختبارات

لتتحقّق من نتيجتك باختبارات الدورة، شغّلها من مجلد البداية:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تصبح `split_bill` صحيحة. يوجد حلّ في `exercise/solution/`؛ لا تنظر إليه إلا بعد
إيداعك أنت. الاختبارات تفحص الكود لا الطريق الذي سلكته: الخطة والمراجعة والإيداع لك أنت أن تتدرّب
عليها. ويجب أن ينتهي `git log` لديك بإيداع واحد لا يغيّر إلا `bill.py`.

## اختبر نفسك

أجب عن الأسئلة في `quiz.json`. إن وجدتها صعبة، فاقرأ الخطوات الخمس في «الفكرة» مرة أخرى.

[^wrong-problem]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^separate]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^phases]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^plan-mode]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^start-plan]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^enter-plan]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^approve-manual]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^keep-planning]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^approve-exits]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^ctrl-g]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^check]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^failing-test]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^git-commit]: وثائق Git، الأمر git-commit.
[^commit-step]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^overhead]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^one-sentence]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^planning-useful]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^course-correct]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^approve-auto]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
