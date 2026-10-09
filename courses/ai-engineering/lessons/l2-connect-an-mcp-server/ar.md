# اربط خادم MCP

## ما الذي ستتمكن من فعله

- تضيف خادم MCP إلى Claude Code بالأمر `claude mcp add`، وتختار ناقله ونطاقه، وتتحقق من أنه اتصل، وتسمح
  بأدواته أو تمنعها بقواعد الأذونات.
- تقرأ ملف `.mcp.json`: ما يشغّله كل خادم أو يصل إليه، وكيف تُبقي الأسرار خارجه.
- تقرّر هل تثق بخادم قبل أن تربطه.

## الفكرة

في درس "ما هو MCP" كان المضيف ملف Python صغيرًا. أما الآن فالمضيف هو Claude Code. تخبره بالخوادم التي يتصل
بها، فيشغّلها أو يصل إليها، ويسرد أدواتها ويعرضها على Claude.

**إضافة خادم**

الأمر `claude mcp add` يضيف خادمًا. الخادم **البعيد** يُوصَل إليه عبر HTTP، على رابط (URL). و HTTP هو
الناقل الموصى به للخوادم البعيدة[^cc-http]:

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

أما الخادم **المحلي** فيعمل برنامجًا على حاسوبك، عبر stdio. ويناسب الأدوات التي تحتاج إلى وصول مباشر
إلى نظامك أو إلى سكربتاتك الخاصة[^cc-stdio]. تكتب الأمر الذي يشغّله بعد `--`: كل ما قبل `--` موجّه إلى
Claude Code (`--transport` و`--env` و`--scope`)، وكل ما بعده يُمرَّر إلى الخادم كما هو[^cc-dashdash]:

```bash
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
```

هنا `files` هو الاسم الذي تعطيه للخادم. و `npx` أداة Node.js لتشغيل حزمة، و`-y` تؤكد أنه يجوز لها تثبيت
الحزمة[^local-npx]. و Node.js برنامج يشغّل كود JavaScript. وهذا الخادم، خادم الملفات (Filesystem
server)، يحتاج إلى Node.js[^local-node]، والمجلدات التي تكتبها في آخر الأمر هي التي يجوز له
استخدامها[^local-dirs]. و`--env NAME=value` تضبط متغير بيئة لخادم محلي[^cc-env-flag]. لا تكتب اسم الخادم مباشرة بعد زوج
`--env`: سيقرأ Claude Code الاسم على أنه زوج آخر ويرفض الأمر[^cc-env-order].

لترى خوادمك، شغّل `claude mcp list` في الطرفية؛ و`claude mcp get <name>` تعرض خادمًا واحدًا، و`claude mcp
remove <name>` تحذفه. وداخل Claude Code، يعرض `/mcp` حالة كل خادم[^cc-manage]. ويعرض `claude mcp list`
حالةً بجانب كل خادم، مثل: متصل، أو يحتاج إلى مصادقة (عليك أن تسجّل الدخول إلى الخدمة أولًا)، أو فشل
الاتصال[^cc-status].

**النطاقات: أين يُحفظ الإعداد**

يُضاف كل خادم في **نطاق (scope)**، يقرّر أين يحمّله Claude Code ومن يحصل عليه غيرك[^cc-scopes]:

| النطاق | يُحمَّل في | يُشارَك مع فريقك | يُحفظ في |
|---|---|---|---|
| `local` (الافتراضي) | هذا المشروع وحده | لا | `~/.claude.json` |
| `project` | هذا المشروع وحده | نعم، عبر git | `.mcp.json` في مجلد المشروع |
| `user` | كل مشاريعك | لا | `~/.claude.json` |

`~/.claude.json` ملف في مجلدك الرئيسي (home)، خارج مشروعك. النطاق local هو الافتراضي، والخادم الذي تضيفه
بالنطاق local يبقى خاصًا بك[^cc-local]. (النطاق يخص مكان حفظ الإعداد: قد يكون للخادم البعيد نطاق local،
وقد يكون لخادم stdio نطاق project.) أما خادم النطاق project فيُكتب في `.mcp.json` في جذر المشروع، ليحصل كل من
يستنسخ المشروع (أي ينزّل نسخته الخاصة منه بـ git) على الخوادم نفسها[^cc-project]. اختر النطاق بـ `--scope`، مثلًا `--scope project`[^cc-scope-flag]. هذا ملف
`.mcp.json` فيه خادمان (أجزاء `${...}` مشروحة أدناه):

```json
{
  "mcpServers": {
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${DOCS_DIR:-./docs}"]
    },
    "tickets": {
      "type": "http",
      "url": "https://tickets.example.com/mcp",
      "headers": {"Authorization": "Bearer ${TICKETS_TOKEN}"}
    }
  }
}
```

المدخل الذي فيه `command` خادم stdio محلي[^cc-notype]، وقد يحمل أيضًا `env`، وهي متغيرات البيئة التي
تُمرَّر إلى الخادم[^cc-env-locations]. أما المدخل الذي فيه `url` فيجب أن يذكر نوعه `type` أيضًا، مثل
`http`: فـ Claude Code يقرأ المدخل الذي لا `type` له على أنه خادم stdio محلي، لذلك يكون `url` دون `type`
خطأً في الملف[^cc-notype].

وحين يُعرَّف الاسم نفسه في أكثر من نطاق، يستخدم Claude Code تعريفًا واحدًا: local أولًا، ثم project، ثم
user. ويأخذ المدخل كله من ذلك النطاق، ولا يخلط حقولًا من نطاقات عدة[^cc-precedence].

**الأسرار تبقى خارج الملف**

كثيرًا ما يحتاج الخادم البعيد إلى *رمز سري* (token): وهو هنا مفتاح وصول يثبت هويتك، لا رموز النموذج. ويمكن أن يُرسَل
في *ترويسة* (header)، وهي سطر من المعلومات الإضافية يرافق كل طلب HTTP، كما في
`Authorization: Bearer <token>`[^cc-bearer]. ولا ترسله إلا إلى عنوان يبدأ بـ `https://`. فـ HTTPS هو النسخة
المشفّرة من HTTP، وهو يشفّر كل الاتصال بين العميل والخادم[^mdn-https]. أما على عنوان `http://` عادي فلا شيء مشفّر،
فيستطيع آخرون على طريق الشبكة أن يقرؤوا الرمز.

يُشارَك `.mcp.json` عبر git[^cc-scopes]، فيستطيع قراءته كل من يقرأ المشروع. لا تكتب فيه رمزًا سريًا أبدًا. اكتب
`${NAME}` بدلًا منه، فيضع Claude Code مكانه قيمة متغيّر البيئة `NAME` من جهازك؛ و`${NAME:-default}` تستخدم
`default` حين لا يكون `NAME` مضبوطًا[^cc-env-syntax]. وهذا يتيح للفرق أن تتشارك ملفًا واحدًا، بينما يحتفظ كل
شخص بمساراته ومفاتيحه[^cc-env-why]. وإذا لم يكن المتغير مضبوطًا ولا قيمة افتراضية له، يُحمَّل الملف رغم
ذلك، ويحذّر منه `claude mcp list`، ويُستخدم النص `${NAME}` كما هو[^cc-env-unset].

**الثقة: ما الذي تُدخله**

حين تربط خادمًا، فإنك تُدخله في عملك. ودليل Anthropic يقولها صراحة: تحقّق من أنك تثق بكل خادم قبل أن تربطه، واعلم
أن الخوادم التي تجلب محتوى من الخارج قد تعرّضك لخطر حقن الموجّهات (prompt injection)[^cc-verify]، وهي
التعليمات المخفية التي قابلتها في درس استخدام الأدوات[^hc-untrusted2]. وتساعدك أربعة أسئلة.

- **ما الذي سيعمل على حاسوبي؟** الخادم المحلي برنامج يُنزَّل ويُشغَّل على جهازك[^sec-local]. ويعمل أمره بمجرد أن يشغّل المضيفُ الخادمَ، وقد
  يفعل المضيف ذلك كلما بدأ[^local-start]، قبل أن يستدعي Claude أي أداة: فطلب الإذن لاستدعاء أداة يأتي بعد فوات
  الأوان لإيقافه. وهو يعمل
  بصلاحيات حساب المستخدم الخاص بك، فيستطيع أن يفعل بالملفات كل ما تستطيع أنت فعله[^local-perms]. اقرأ
  الأمر كاملًا. فقد يخفي مهاجم أمر بدء ضارًا في إعدادات خادم[^sec-startup]، والأوامر التي فيها `sudo` (تشغيل بصلاحيات
  المسؤول) أو `rm -rf` (حذف ملفات ومجلدات كاملة دون سؤال) أو وصول إلى الشبكة تستحق نظرة أدق[^sec-patterns].
- **من كتبه، وإلى ماذا يصل؟** تعامل المواصفة الأدوات على أنها كود قد يفعل أي شيء، وتعدّ أوصاف سلوك
  الأدوات غير موثوقة ما لم يكن الخادم موثوقًا[^spec-safety]. فضّل الخوادم من ناشرين تعرفهم، وأعطِ كلًّا
  منها أقل ما يحتاج: مجلدًا واحدًا لا مجلدك الرئيسي كله، ومستخدم قاعدة بيانات للقراءة فقط (حساب في قاعدة البيانات لا يستطيع إلا القراءة)، حتى لا تستطيع
  الاستعلامات التي يشغّلها Claude تغيير البيانات[^cc-readonly].
- **هل يجلب محتوى من الخارج؟** صفحات الويب والبريد وغيرها من المحتوى الخارج عن سيطرتك قد تحمل تعليمات
  موجّهة إلى Claude[^hc-untrusted2]. تعامل مع ما يعيده مثل هذا الخادم على أنه بيانات، لا أوامر.
- **من وافق عليه؟** يسأل Claude Code قبل أن يستخدم خوادم `.mcp.json` في مشروع ما خلال جلسة
  تفاعلية[^cc-approve]، وقد يحاول المشروع أيضًا أن يوافق عليها مسبقًا، بإعدادات مثل
  `enabledMcpjsonServers` في ملفه `.claude/settings.json`، وهو ملف إعدادات Claude Code الخاص بذلك المشروع،
  المُضاف إلى git مع بقية الملفات. ويتجاهل Claude Code هذه الإعدادات ما دام المجلد غير موثوق[^cc-clone]. وحين تشغّل `claude` في مجلد أول مرة، يسألك هل تثق به (نافذة الثقة بمساحة العمل)؛
  فإذا قبلت، صارت الموافقات المُضافة إلى git في المشروع معتمدة[^cc-trust]. لذلك اقرأ `.mcp.json` و`.claude/settings.json`
  في المشروع المستنسَخ قبل أن تثق به. لكنه في
  تشغيلات `claude -p` (حين يُشغَّل Claude Code من سكربت، ولا أحد يجيب عن الأسئلة)، وجلسات Agent SDK (برامج مبنية على Agent SDK من Anthropic، في
  مستوى لاحق من هذا المقرر)، والجلسات السحابية (Claude Code يعمل على جهاز بعيد)، يحمّل Claude Code خوادم المشروع دون أن يسأل[^cc-noprompt]: فاقرأ `.mcp.json` في المشروع قبل أن تشغّل عليه
  Claude Code دون إشراف.

**استخدام أدوات الخادم**

حين يتصل الخادم، يستطيع Claude أن يستدعي أدواته كأي أداة أخرى، وترى طلب إذن لها كما للأفعال
الأخرى[^perm-prompts]. ويسمّي Claude Code كل أداة `mcp__<server>__<tool>`[^perm-mcp].

وقواعد الأذونات، التي قابلتها في درس إعداد Claude Code، ثلاثة أنواع. قاعدة السماح `allow` تتيح لـ Claude أن
يستخدم أداة دون أن يسألك، وقاعدة السؤال `ask` تجعل Claude Code يسألك في كل مرة، وقاعدة المنع `deny` تمنع
Claude من استخدام الأداة[^perm-kinds]. وقواعد المنع تُفحص أولًا وتغلب[^perm-order]. وتوجد القواعد في ملفات
`settings.json` الخاصة بـ Claude Code، ويسردها كلها الأمر `/permissions`[^perm-files]؛ والقواعد التي تخص كل
مشاريعك توضع في `~/.claude/settings.json`[^perm-user].

وتستطيع القاعدة أن تسمّي أدوات خادم: `mcp__files` و`mcp__files__*` تطابقان كل أدوات الخادم `files`، و
`mcp__files__read_file` تطابق أداة واحدة[^perm-mcp]. وفي قاعدة المنع أو السؤال، تعني `*` في اسم الأداة أي نص،
فتطابق `mcp__*` كل أدوات MCP[^perm-glob]. أما في قاعدة السماح، فلا تأتي `*` في اسم أداة MCP إلا بعد
`mcp__<server>__`، كما في `mcp__files__*`: فقاعدة السماح `mcp__*` تُتخطّى ولا توافق على شيء[^perm-allow-glob].
هذا الإعداد يتيح لـ Claude أن يستخدم كل أدوات الخادم `files` دون أن يسأل:

```json
{"permissions": {"allow": ["mcp__files__*"]}}
```

وهذا يمنع كل أدوات MCP[^perm-deny]:

```json
{"permissions": {"deny": ["mcp__*"]}}
```

قاعدة المنع توقف استدعاءات Claude للأدوات. لكنها لا توقف أمر الخادم المحلي نفسه، الذي عمل بالفعل حين بدأ
الخادم.

## جرّبها

### دون Claude Code: اقرأ `.mcp.json`

الملف `exercise/tests/sample_mcp.json` ملف مشروع مختلَق فيه خمسة خوادم. هذا السكربت لا يشغّل شيئًا: يطبع
ما سيشغّله كل خادم أو يصل إليه، مع ملء المتغيرات من بيئة مُتخيَّلة. احفظه باسم `read_mcp_json.py` في مجلد
الدرس، وشغّل `python3 read_mcp_json.py` من ذلك المجلد:

```python
"""Read a .mcp.json file and say what each server would run or reach. Nothing is started."""
import json
import re
from pathlib import Path

config = json.loads(Path("exercise/tests/sample_mcp.json").read_text(encoding="utf-8"))
environ = {"TICKETS_TOKEN": "tk-demo"}  # a pretend environment: only this one variable is set


def expand(text):
    """Replace ${VAR} and ${VAR:-default}; leave an unset variable with no default as written."""
    def one(match):
        name, default = match.group(1), match.group(2)
        return environ.get(name, default if default is not None else match.group(0))
    return re.sub(r"\$\{(\w+)(?::-([^}]*))?\}", one, text)


for name, entry in config["mcpServers"].items():
    if "command" in entry:
        line = " ".join(expand(word) for word in [entry["command"], *entry.get("args", [])])
        print(f"{name}: runs on your computer: {line}")
    else:
        kind = entry.get("type", "NO TYPE")
        print(f"{name}: connects to {expand(entry['url'])} ({kind})")
    for key, value in entry.get("headers", {}).items():
        print(f"    sends the header {key}: {expand(value)}")
```

يجد النمط `\$\{(\w+)(?::-([^}]*))?\}` العلامة `${`، ثم اسمًا، ثم `:-` مع قيمة افتراضية إن وُجدت، ثم `}`.
تستدعي `re.sub(pattern, one, text)` الدالة `one` لكل `${...}` تجدها، وتضع مكانه ما تعيده `one`؛ و
`match.group(0)` هو `${...}` كله، و`match.group(1)` هو اسم المتغيّر، و`match.group(2)` قيمته الافتراضية، أو `None`.
وفي `[entry["command"], *entry.get("args", [])]` تضع `*` عناصر قائمة args في القائمة الجديدة، بعد الأمر.

يُظهر الخرج أن 2 من الخوادم الخمسة تشغّل أمرًا على حاسوبك. اقرأ كل سطر كما يقرؤه مراجع. `files` خادم
معروف محصور في مجلد واحد. و`crm` رمزه السري مكتوب في الملف، حيث يقرؤه كل من لديه المشروع. و`wiki` لا
`type` له، فلن يتصل به Claude Code. و`helper` يُنزّل سكربتًا من الإنترنت بـ `curl` ويشغّله بـ `sh` (برنامج يشغّل أوامر الطرفية، مثل Bash): لا
تربطه حتى تعرف بالضبط ما يفعله ذلك السكربت.

### مع Claude Code (اختياري)

هذا الجزء يستخدم خادمًا حقيقيًا و Claude Code، فهو يحتاج إلى Node.js، والطلبات التي يرسلها Claude تُحسب من
اشتراكك في Claude Code أو تُحتسب على مفتاح API الخاص بك. أنشئ مجلدًا صغيرًا يستخدمه الخادم، لا شيء خاص
فيه:

```bash
mkdir -p ~/mcp-sandbox
echo "Remember to water the plants." > ~/mcp-sandbox/note.txt
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
claude mcp list
```

شغّل `claude --permission-mode manual`، ليسألك Claude Code قبل أن يستخدم أداة، كما في درس إعداد Claude Code. واكتب
`/mcp` لترى الخادم وأدواته، ثم اسأل: `Use the files server to read note.txt in ~/mcp-sandbox.` راقب
الأداة التي يستدعيها Claude (يبدأ اسمها بـ `mcp__files__`)، واقرأ طلب الإذن قبل أن تجيب عنه. ودون عبارة
"the files server"، قد يقرأ Claude الملف بأدواته الخاصة بدلًا من ذلك. وحين تنتهي، احذف الخادم بالأمر
`claude mcp remove files`.

## أخطاء شائعة

- **كتابة رمز سري في `.mcp.json`.** الملف يُشارَك عبر git. استخدم `${NAME}` واحفظ القيمة في
  بيئتك[^cc-env-syntax].
- **`url` دون `type`.** يقرؤه Claude Code على أنه خادم stdio ويبلّغ عن خطأ في الإعداد[^cc-notype]. أضف
  `"type": "http"`.
- **نسيان `--` قبل أمر الخادم المحلي.** دونها يحاول Claude Code أن يقرأ خيارات الخادم، مثل `--port`، على
  أنها خياراته هو[^cc-nodash].
- **"النطاق local يعني خادمًا محليًا."** النطاق يقول أين يُحفظ الإعداد ومن يتشاركه، والناقل يقول كيف يصل
  Claude Code إلى الخادم[^cc-scopes].
- **توقّع دمج النطاقات.** المدخل كله يأتي من نطاق واحد: local، ثم project، ثم user[^cc-precedence].
- **"إنه في قائمة خوادم، إذن هو آمن."** افحص ما يشغّله، ومن كتبه، وإلى ماذا يصل[^cc-verify]. الخادم المحلي
  يملك صلاحياتك[^local-perms].
- **إعطاء الخادم أكثر مما يحتاج.** مجلد واحد، ومستخدم للقراءة فقط، والأدوات التي تستخدمها
  فقط. فمستخدم قاعدة البيانات للقراءة فقط، مثلًا، لا يستطيع تغيير البيانات[^cc-readonly]. وامنع الأدوات التي لا تريدها بقواعد الأذونات[^perm-mcp].
- **"يسأل Claude Code دائمًا قبل تحميل خوادم المشروع."** ليس في تشغيلات `claude -p`، ولا في جلسات Agent
  SDK، ولا في الجلسات السحابية[^cc-noprompt]، ولا بعد أن تثق بمجلد توافق عليها
  إعداداته المُضافة إلى git[^cc-trust].

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/mcp_setup.py` واكتب ست دوال. تعمل دون اتصال على قيم Python عادية، ولا يشغّل شيء
Claude Code أو خادمًا.

- `add_command(name, url=..., command=..., args=..., scope=..., env=...)` تعيد الأمر `claude mcp add`
  قائمةً من الكلمات، وفيها دائمًا `--transport` و`--scope` قبل الاسم: `--transport http` والرابط لخادم بعيد، أو `--transport stdio` وأزواج `--env` بعد
  الاسم ثم `--` والأمر لخادم محلي. وترفع `ValueError` لنطاق غير معروف، أو حين يُعطى `url` و`command`
  معًا أو لا يُعطى أيٌّ منهما، أو حين يأتي `env` مع `url`.
- `expand(text, environ)` تملأ `${NAME}` و`${NAME:-default}` وتعيد النص وقائمةً بالأسماء الناقصة. والاسم الناقص
  الذي لا قيمة افتراضية له يبقى كما كُتب.
- `pick(local, project, user)` تعيد لكل اسم خادم النطاقَ والمدخلَ اللذين يستخدمهما Claude Code.
- `tool_name(server, tool)` تعيد الاسم الذي يعطيه Claude Code للأداة، و`rule_matches(rule, server, tool)`
  تقول هل تطابقها قاعدة أذونات مثل `mcp__files` أو `mcp__*`. ولا تفحص هل القاعدة قاعدة سماح
  أم منع. والوحدة القياسية `fnmatch` في Python تقارن اسمًا بنمط فيه `*`.
- `review(config)` تقرأ `.mcp.json` وتعيد ما يجب فحصه، أزواجًا `(server, kind)`: `no-type`، و`not-https`
  (رابط بعيد لا يبدأ بـ `https://`؛ ويُتخطّى الرابط الذي يبدأ بـ `${` لأن قيمته لا تُعرف إلا لاحقًا)، و`secret` (قيمة في الترويسات (headers) أو في `env` يدل اسمها على سرّ،
  مكتوبة دون `${...}`)، و`command` (أمر محلي فيه `sudo` أو `rm -rf` أو `curl` أو `wget` (كلاهما يُنزّل من الإنترنت) أو `&&` أو `|`
  أو `;`).

`review` مصفاة أولى، لا فحص أمني. لا تستطيع أن تميّز أمرًا آمنًا من أمر ضار: إنها تشير فقط إلى ما يجب أن
يقرأه شخص.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. يوجد حل في `exercise/solution/`: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إذا صعب عليك سؤال، فاقرأ جدول النطاقات وأسئلة الثقة الأربعة من جديد.

[^cc-http]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-stdio]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-dashdash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^local-node]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-npx]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-dirs]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^cc-env-order]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-manage]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-status]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scopes]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-local]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-project]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-notype]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-precedence]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-syntax]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-why]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-unset]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-verify]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^hc-untrusted2]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^sec-local]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^local-perms]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^sec-startup]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^sec-patterns]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^spec-safety]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^cc-readonly]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-approve]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-clone]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-noprompt]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-nodash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-mcp]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-locations]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-bearer]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^mdn-https]: HTTPS, MDN Web Docs, <https://developer.mozilla.org/en-US/docs/Glossary/HTTPS>
[^local-start]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^perm-prompts]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-files]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scope-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-user]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-kinds]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-order]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-trust]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-allow-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-deny]: Configure permissions, <https://code.claude.com/docs/en/permissions>
