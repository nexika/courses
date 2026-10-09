# راجع ما غيّره Claude

## ما الذي ستتمكن من فعله

- قراءة الفروق (diff): أيّ الملفات تغيّرت، وأيّ الأسطر أُضيفت وأيّها حُذفت.
- تشغيل الاختبارات بنفسك، والتأكد من أنها ما زالت تختبر ما كانت تختبره من قبل.
- رصد التغييرات التي تستحق نظرة أدقّ قبل قبولها: ملفات خارج المهمة، واختبارات تغيّرت أو حُذفت،
  واختبارات أُوقف تشغيلها.

## الفكرة

في الدرس السابق وافقت على كل إجراء أو رفضته. أما هذا الدرس فعن النتيجة: التغيير الذي يتركه Claude في
ملفاتك.

يتوقّف Claude حين يبدو العمل منتهيًا[^looks-done]. لكن أن يبدو العمل منتهيًا شيء، وأن يكون صحيحًا شيء
آخر. يسمّي دليل Anthropic خطأً شائعًا: أن يقدّم Claude تنفيذًا يبدو مقنعًا لكنه لا يعالج الحالات
الحدّية[^trust-gap]. والحالة الحدّية (edge case) مُدخلٌ غير معتاد، مثل فاتورة يتقاسمها صفر من
الأشخاص. وعلاج الدليل صريح: وفّر دائمًا وسيلة للتحقق (اختبارات، سكربتات، لقطات شاشة)؛ وما لا تستطيع
التحقق منه فلا تُطلقه[^verify].

لذلك تفعل شيئين قبل أن تقبل أي تغيير: تقرأ الفروق، وتشغّل الاختبارات.

**الفروق.** تعرض الفروق ما تغيّر بين نسختين من الملف. يعرض `git diff` التغييرات بين شجرة العمل
والفهرس[^git-diff]. شجرة العمل (working tree) هي ملفاتك كما هي الآن؛ والفهرس (index)، ويسمّى أيضًا
منطقة التجهيز (staging area)، هو المكان الذي يضع فيه `git add` محتوى إيداعك (commit)
التالي[^git-add]. إن لم تشغّل `git add` منذ آخر إيداع، فإن `git diff` يعرض كل تغيير في الملفات التي يتتبّعها git
أصلًا. أما الملف الجديد الذي أنشأه Claude فلا يظهر فيه: يسرد `git status` المسارات التي لا يتتبّعها
Git[^git-status]، فشغّله هو أيضًا. وداخل Claude Code يتيح لك الأمر `/diff` أن تطّلع على التغييرات في شجرة العمل دون أن تغادر
الجلسة[^slash-diff].

هذا جزء من فروق. كانت المهمة المعطاة لـ Claude: «اجعل `test_split_needs_people` ينجح». يتحقّق هذا
الاختبار من أن `split` ترفض فاتورة يتقاسمها صفر من الأشخاص.

```diff
--- a/tip.py
+++ b/tip.py
@@ -3,4 +3,6 @@
 
 
 def split(total, percent, people):
-    return round((total + tip(total, percent)) / people, 2)
+    if people < 1:
+        raise ValueError("people must be at least 1")
+    return round(total / people + tip(total, percent), 2)
```

اقرأها من الأعلى:

- يسمّي `--- a/tip.py` و `+++ b/tip.py` النسخة القديمة من الملف والنسخة الجديدة. والملف الذي أُنشئ أو
  حُذف يظهر في أحد طرفيه `/dev/null`[^dev-null]. ويبدأ `git diff` أيضًا كل ملف بسطر مثل
  `diff --git a/tip.py b/tip.py`[^git-header].
- السطر الذي يبدأ بـ `@@` يفتح مقطع تغيير (hunk): يأتي بعده مقطع أو أكثر، وكل مقطع يعرض موضعًا واحدًا
  يختلف فيه الملفان[^hunks]. والأرقام بين علامتي `@@` تحدّد الأسطر التي يغطّيها المقطع في الملف
  القديم وفي الجديد[^hunk-header].
- ثم يبدأ كل سطر بحرف واحد: `-` لسطر حُذف، و `+` لسطر أُضيف، ومسافة لسطر لم يتغيّر[^plus-minus].

يفعل هذا التغيير شيئين. السطران اللذان يبدآن بـ `+` ويرفعان `ValueError` هما ما طلبته المهمة. لكن
السطر الأخير تغيّر أيضًا: كان الكود القديم يقسم الفاتورة كلها، مع البقشيش، على عدد الأشخاص؛ أما الجديد
فيقسم المبلغ وحده ثم يضيف البقشيش كاملًا إلى حصة كل شخص. لم يطلب أحد ذلك. ومثل هذا التغيير لا تجده إلا
بالقراءة.

**الاختبارات.** الاختبارات وسيلتك للتحقق، لكن التغيير قد يطال الاختبارات نفسها. وهذا أول الملف الثاني في الفروق نفسها:

```diff
--- a/test_tip.py
+++ b/test_tip.py
@@ -1,6 +1,6 @@
 class TipTest(unittest.TestCase):
     def test_split(self):
-        self.assertEqual(split(100, 10, 4), 27.5)
+        self.assertEqual(split(100, 10, 4), 35.0)
```

كان `test_split` ينصّ على أن يدفع كل شخص 27.5. كسر الكود الجديد ذلك، فعُدّل الاختبار ليطابقه: صار كل شخص يدفع 35.0.
كل الاختبارات تنجح، والكود خاطئ: أربعة أشخاص يدفع كلٌّ منهم هذا المبلغ يعني أنهم يدفعون معًا 140.0،
بينما الفاتورة مع البقشيش 110.0. والتأكيد (assertion) سطرٌ يتحقّق من نتيجة، مثل `assertEqual`؛ فإذا
تغيّر، تغيّر معه ما نقول إن الكود يجب أن يفعله. اسأل لماذا تغيّر.

**ما الذي تبحث عنه.** قبل أن تقبل تغييرًا، تحقّق من:

- **ملفات خارج المهمة.** لكل ملف في الفروق سبب يجب أن يبرّر وجوده.
- **اختبارات تغيّرت أو حُذفت.** سطر يبدأ بـ `-` في ملف اختبار قد يحذف تحققًا. اقرأه.
- **اختبارات أُوقف تشغيلها.** وضعُ `@unittest.skip` فوق اختبار يتخطّاه: فلا يعود يعمل[^skip].
- **أخطاء أُخفيت بدل أن تُصلح.** يطلب الدليل من Claude أن يعالج السبب الجذري لا أن يكتم
  الخطأ[^root-cause]. وكتلة `try` و `except` جديدة تبتلع خطأً (تلتقطه وتمضي كأن شيئًا لم يحدث) تستحق سؤالًا.

ثم شغّل الاختبارات بنفسك واقرأ مخرجاتها. وإن سألت Claude هل تنجح الاختبارات، فاطلب منه أن يُظهر الدليل
بدل أن يؤكد النجاح: مخرجات الاختبارات، والأمر الذي شغّله وما أعاده[^evidence].

**إن كان التغيير خاطئًا.** أخبر Claude بما هو خاطئ، أو تخلّص من التغيير. يستعيد `git restore` ملفات
شجرة العمل من مصدر استعادة[^git-restore]: فالأمر `git restore tip.py` يعيد نسخة `tip.py` التي يحفظها
git (نسخة الفهرس[^restore-index]، وهي آخر إيداع لك إن لم تشغّل `git add` بعده).

## جرّبها

### اعرض الفروق

يبني هذا السكربت الفروق السابقة بالوحدة `difflib` في Python، فترى الصيغة دون جلسة ولا مستودع. والفروق
الموحّدة طريقة مختصرة لعرض الأسطر التي تغيّرت فقط ومعها بضعة أسطر من السياق[^difflib]، ويستخدم
`git diff` العلامات نفسها: `+` و `-` والمسافة.

احفظه باسم `see_the_diff.py` وشغّله بالأمر `python3 see_the_diff.py`:


```python
"""Show what a change did to two files, in the same format as git diff."""
import difflib

before = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    return round((total + tip(total, percent)) / people, 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 27.5)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

# The task was: "make test_split_needs_people pass". This is the change that came back.
after = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    if people < 1:
        raise ValueError("people must be at least 1")
    return round(total / people + tip(total, percent), 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 35.0)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

for name in before:
    lines = difflib.unified_diff(
        before[name].splitlines(keepends=True),
        after[name].splitlines(keepends=True),
        fromfile=f"a/{name}",
        tofile=f"b/{name}",
    )
    print("".join(lines))
```

يطبع السكربت جزأي الفروق من «الفكرة»، مع بضعة أسطر لم تتغيّر بعد التأكيد. والآن عدّل `after` بنفسك:
أعد سطر `return` القديم في `tip.py`، والقيمة القديمة في `test_tip.py`. شغّل السكربت مرة أخرى. لن يبقى
إلا ما احتاجته المهمة من أسطر.

### اقرأ نتيجة تشغيل الاختبارات

ستشغّل الاختبارات بنفسك، فعليك أن تعرف كيف تقرأ نتيجتها. احفظ هذا باسم `test_run.py` في مجلد فارغ،
وشغّل فيه `python3 -m unittest`:

```python
import unittest


class ReadTheRun(unittest.TestCase):
    def test_passes(self):
        self.assertEqual(1 + 1, 2)

    @unittest.skip("not ready")
    def test_skipped(self):
        self.assertEqual(1 + 1, 3)

    def test_fails(self):
        self.assertEqual(2 + 2, 5)


if __name__ == "__main__":
    unittest.main()
```

يطبع شيئًا كهذا (سيختلف المسار والتوقيت عندك):

```text
F.s
======================================================================
FAIL: test_fails (test_run.ReadTheRun.test_fails)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../test_run.py", line 13, in test_fails
    self.assertEqual(2 + 2, 5)
AssertionError: 4 != 5

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=1, skipped=1)
```

اقرأها من الأعلى. في السطر الأول حرف لكل اختبار: `.` لاختبار نجح، و `F` لاختبار فشل، و `s` لاختبار
تُخطّي. ثم يعرض كل فشلٍ اسمَ الاختبار، والسطر الذي فشل، والسبب: هنا `4 != 5`. والسطر الأخير يلخّص
التشغيل كله.

احذف الآن `test_fails` وشغّل من جديد:

```text
.s
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK (skipped=1)
```

النتيجة `OK`، لكن اختبارًا لم يعمل أصلًا. تعني `OK` أن أي اختبار جرى تشغيله لم يفشل؛ ولا تعني أن كل
الاختبارات جرى تشغيلها. اقرأ السطر الأخير حتى نهايته.

وفي مشروعك أنت، بعد الجلسة، شغّل `git diff` (أو `/diff` داخل Claude Code)، ثم `python3 -m unittest`،
واقرأ الاثنين قبل أن تودِع.

## أخطاء شائعة

**«الاختبارات تنجح، إذن التغيير صحيح».** تنجح الاختبارات حين يطابق الكود الاختبارات. فإن تغيّرت
الاختبارات أيضًا، فاقرأ كيف تغيّرت. في المثال تنجح كل الاختبارات والكود خاطئ.

**«قال Claude إن الاختبارات تنجح».** الجملة ليست تشغيلًا للاختبارات. اطلب المخرجات، أو شغّل الاختبارات
بنفسك[^evidence].

**«أسطر `+` وحدها هي المهمة».** أسطر `-` تُريك ما اختفى. وحذفُ تأكيد أو تحقق تغييرٌ في سلوك البرنامج.

**«كثرة التغييرات تعني عملًا أكثر».** الملف الذي يقع خارج المهمة سؤالٌ لا مكافأة. اسأل لماذا تغيّر، أو
ارفضه.

**«قبول التعديلات تلقائيًا يعني أنني أتخطّى المراجعة».** تقترح الوثائق وضع `acceptEdits`، وهو وضع يوافق على تعديل الملفات دون أن يسألك، لمن يريد أن
يراجع التغييرات في محرّره أو عبر `git diff` بعد حدوثها، بدل الموافقة على كل تعديل في
لحظته[^accept-edits]. المراجعة تنتقل إلى وقت آخر، لكنها لا تختفي.

**«أستطيع دائمًا أن أرجع».** النسخ التي يحفظها Claude قبل كل تعديل، ويعيدك إليها الضغط على `Esc` مرتين (وتسمّى نقاط الاستعادة، checkpoints)، لا تتتبّع إلا التغييرات التي تجري عبر أدوات
تعديل الملفات لدى Claude؛ أما ما تغيّره أوامر الطرفية فلا تلتقطه، وهي ليست بديلًا عن git[^not-git].
أودِع قبل الجلسة، فتستطيع دائمًا أن تعود إلى تلك النقطة.

**«أداة المراجعة تغني عن مراجعتي».** في Claude Code أمرٌ اسمه `/code-review` يراجع الفروق الحالية بحثًا عن الأخطاء في وكيل فرعي (subagent) جديد، أي نسخة ثانية من Claude تعمل وحدها[^code-review]. هو مفيد، لكنه يعتمد على نموذج أيضًا: قد يفوته شيء. ولا يعرف ما الذي قصدتَ
أن تطلبه. أنت تعرف.

## تمرينك

افتح `exercise/starter/diff_review.py`. ستكتب دالتين تقرآن النص الذي يطبعه `git diff`.

### ما الذي ستبنيه

تعيد `parse_diff(text)` قاموسًا فيه مدخل لكل ملف، بالترتيب الذي تظهر به الملفات. يربط كل مدخل مسار
الملف (دون البادئة `a/` أو `b/`) بقاموس فيه:

- `"status"`: القيمة `"added"` حين يكون الطرف القديم `/dev/null`، و `"deleted"` حين يكون الطرف الجديد
  `/dev/null`، و `"modified"` في غير ذلك؛
- `"added"`: الأسطر المضافة، دون علامة `+` في أولها؛
- `"removed"`: الأسطر المحذوفة، دون علامة `-` في أولها.

أسطر الترويسة (`diff --git` و `index` و `---` و `+++` و `@@`) ليست من المحتوى. انتبه: السطر المحذوف
الذي يبدأ نصه بـ `--` يُطبع هكذا `---`، فيبدو كأنه ترويسة. استعن بسطر `@@`: فهو يعطي لكل طرف موضع بداية
المقطع وعدد أسطره، بالشكل `-start,count +start,count`. وإن كان المقطع سطرًا واحدًا، لا يظهر إلا رقم سطر
البداية[^hunk-one]: فيكون العدد واحدًا. عُدّ الأسطر وأنت تقرؤها، فتعرف دائمًا متى ينتهي المقطع.

وتعيد `red_flags(text, task_files)` قائمة من الأزواج `(path, reason)`، بترتيب الملفات، ولكل ملف بهذا
الترتيب من الأسباب:

- `"outside the task"`: المسار ليس في `task_files`؛
- `"test deleted"`: حُذف ملف اختبار؛
- `"assertion changed"`: سطر محذوف في ملف اختبار يحتوي على `assert`؛
- `"test skipped"`: سطر مضاف يحتوي على `unittest.skip` أو `skipTest(` أو `mark.skip`.

ملف الاختبار هو الملف الذي يبدأ اسمه بـ `test_` أو ينتهي بـ `_test.py`.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تصبح دالتاك صحيحتين. يوجد حلّ في `exercise/solution/`؛ حاول بنفسك أولًا. ثم
جرّبها على تغيير حقيقي: بعد جلسة مع Claude Code، شغّل `git diff > change.diff` ومرّر نص `change.diff`
إلى `red_flags`. العلامة سببٌ للقراءة المتأنية. وغياب العلامات لا يعني أن التغيير صحيح: اقرأ الفروق على
أي حال.

## اختبر نفسك

أجب عن الأسئلة في `quiz.json`. إن وجدتها صعبة، فاقرأ الفروق في «الفكرة» مرة أخرى، سطرًا سطرًا.

[^looks-done]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^trust-gap]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^verify]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^git-diff]: وثائق Git، الأمر git-diff.
[^slash-diff]: وثائق Claude Code، الوضع التفاعلي (Interactive mode).
[^dev-null]: وثائق Git، الأمر git-diff.
[^git-header]: وثائق Git، الأمر git-diff.
[^hunks]: دليل GNU diffutils، الوصف المفصّل للصيغة الموحّدة (Detailed Description of Unified Format).
[^hunk-header]: دليل GNU diffutils، الوصف المفصّل للصيغة الموحّدة (Detailed Description of Unified Format).
[^plus-minus]: وثائق Git، الأمر git-diff.
[^root-cause]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^evidence]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^git-restore]: وثائق Git، الأمر git-restore.
[^difflib]: وثائق Python، الوحدة difflib.
[^accept-edits]: وثائق Claude Code، اختيار وضع الأذونات (Choose a permission mode).
[^not-git]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^code-review]: وثائق Claude Code، أفضل الممارسات (Best practices for Claude Code).
[^git-add]: وثائق Git، الأمر git-add.
[^skip]: وثائق Python، الوحدة unittest.
[^hunk-one]: دليل GNU diffutils، الوصف المفصّل للصيغة الموحّدة (Detailed Description of Unified Format).
[^git-status]: وثائق Git، الأمر git-status.
[^restore-index]: وثائق Git، الأمر git-restore.
