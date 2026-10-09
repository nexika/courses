# ما هو MCP

## ما الذي ستتمكن من فعله

- تشرح الغرض من MCP، وما يفعله كلٌّ من المضيف (host) والعميل (client) والخادم (server).
- تميّز بين الأدوات والموارد (resources) وقوالب الموجّهات (prompts)، وتقول من يقرّر متى يُستخدم كلٌّ منها.
- تتابع الرسائل بين العميل والخادم، وتقول كيف ينقلها الناقلان، وتحوّل أدوات الخادم ونتائجه إلى تعريفات
  الأدوات وكتل `tool_result` التي تعلّمتها في الدرسين السابقين.

## الفكرة

في الدروس السابقة كتبت كل أداة بنفسك: تعريفها، والدالة التي تشغّلها، والكود الذي يعيد نتيجتها. تخيّل
الآن عشرة تطبيقات يريد كلٌّ منها الوصول إلى طلبيات متجرك. سيكتب كلٌّ منها هذا الكود من جديد.

**MCP** (اختصار Model Context Protocol، أي بروتوكول سياق النموذج) معيار مفتوح المصدر لربط تطبيقات الذكاء
الاصطناعي بالأنظمة الخارجية[^intro-what]. و*البروتوكول* مجموعة قواعد متفق عليها لطريقة تخاطب برنامجين. و*المعيار*
طريقة واحدة متفق عليها لعمل شيء ما. و*مفتوح المصدر* يعني أن نصّه وكوده منشوران، ويحق لأي شخص أن يستخدمهما. ويشبّهه توثيقه بمنفذ USB-C: طريقة واحدة موحّدة لوصل
الأشياء[^intro-usb]. فيستطيع المتجر أن يكتب البحث عن الطلبيات مرة واحدة، على شكل خادم MCP، ويستخدمه كل
تطبيق يدعم MCP.

**المضيف والعميل والخادم**

يسمّي MCP ثلاثة أطراف[^arch-roles]:

- **المضيف (host)** هو تطبيق الذكاء الاصطناعي، مثل Claude Code أو Claude Desktop، تطبيق Anthropic لسطح المكتب. يتصل بخادم واحد أو
  أكثر[^arch-participants].
- **العميل (client)** هو الجزء من المضيف الذي يحتفظ بالاتصال بخادم واحد. ينشئ المضيف عميلًا واحدًا لكل
  خادم[^arch-participants].
- **الخادم (server)** برنامج يقدّم السياق للعملاء[^arch-roles]. قد يعمل على حاسوبك أو
  على جهاز آخر: كلمة "خادم" تسمّي الدور لا المكان[^arch-where].

فإذا اتصل Claude Code بخادمين، ففيه عميلان. والنموذج ليس طرفًا في MCP. الخادم لا يكلّم Claude أبدًا:
إنه يكلّم العميل، والمضيف هو الذي يقرّر ما يصل إلى النموذج. يحدّد MCP طريقة تبادل السياق فقط، ولا يقول
كيف يستخدم التطبيق النموذج[^arch-scope].

**الأدوات والموارد وقوالب الموجّهات**

يستطيع الخادم أن يقدّم ثلاثة أنواع من الأشياء، ولكلٍّ منها صاحب مختلف، هو من يقرّر متى
يُستخدم[^sc-table]:

| النوع | ما هو | من يقرّر |
|---|---|---|
| **الأدوات (tools)** | دوال يستطيع النموذج استدعاءها، مثل `lookup_order` التي كتبتها | النموذج |
| **الموارد (resources)** | بيانات تُقرأ لتكون سياقًا، مثل ملف أو مخطط قاعدة بيانات (جداولها وأعمدتها) | التطبيق |
| **قوالب الموجّهات (prompts)** | تعليمات جاهزة لمهمة ما، فيها فراغات تملؤها[^sc-params] | المستخدم |

ويضرب التوثيق مثالًا: خادم لقاعدة بيانات قد يقدّم أدوات للاستعلام منها، ومورِدًا فيه مخططها، وقالب موجّه
فيه أمثلة على استخدام الأدوات[^arch-db]. وفي Claude Code تظهر قوالب موجّهات الخادم أوامرَ تكتبها، مثل
`/servername:promptname`[^cc-prompts].

ولكل نوع *طرائقه* (methods) الخاصة، وهي عمليات مسمّاة يستطيع العميل أن يطلب من الخادم تشغيلها. `tools/list` تجد الأدوات و`tools/call` تشغّل
واحدة منها[^sc-tools-ops]. و`resources/list` تسرد الموارد و`resources/read` تقرأ
واحدًا منها[^sc-resources-ops]. و`prompts/list` تسرد قوالب الموجّهات و`prompts/get` تجلب واحدًا منها[^sc-prompts-ops].

**الرسائل**

يتبادل العملاء والخوادم رسائل **JSON-RPC 2.0**[^arch-jsonrpc]. و JSON-RPC صيغة صغيرة لتطلب من برنامج آخر
أن يشغّل طريقة (method). يذكر الطلب الإصدار، `"2.0"`، والطريقة `method` المطلوب
تشغيلها[^jsonrpc-request]. ويحمل أيضًا معرّفًا `id`، ويكرّر الجواب هذا المعرّف، فتعرف عن أي طلب
يجيب[^jsonrpc-id]. (والرسالة التي لا معرّف `id` لها *إشعار* (notification): لا يجيب عنه الطرف
الآخر[^jsonrpc-notify].) وفي الجواب `result` إذا نجح الاستدعاء، أو `error` إذا لم
ينجح[^jsonrpc-response].

هنا يسأل العميل خادم المتجر عن أدواته، فيجيب الخادم:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
```

```json
{"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "tools": [
  {"name": "lookup_order",
   "description": "Look up a customer's order by its order number and return its status.",
   "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}
]}}
```

للأداة اسم `name` ووصف `description` و`inputSchema`، وهو مخطط JSON Schema لمُدخلاتها[^spec-tool]. إنها
تشبه تعريفات الأدوات التي كتبتها، مع فرق واحد في التهجئة: تسمّي Claude API المخطط
`input_schema`[^dt-fields]. ولتشغيل الأداة، يرسل العميل `tools/call` مع اسم الأداة `name` ومعاملاتها
`arguments`[^spec-call]. وتحمل النتيجة قائمة `content` قد تجمع عدة عناصر من أنواع
مختلفة[^spec-content]. وقد تحمل أيضًا `isError`، وسنعود إليه أدناه. أما `"resultType": "complete"` فتعني
أن النتيجة نهائية[^rt-complete]. وقد يجيب الخادم بدلًا من ذلك بأنه يحتاج إلى مُدخلات إضافية قبل أن يُكمل
الاستدعاء[^spec-input]، وهذا ما لا يستخدمه هذا الدرس.

الإصدار الحالي من MCP *عديم الحالة* (stateless). فكما هي الحال في Messages API التي قابلتها في الدروس
السابقة[^stateless]، لا يحتاج الخادم إلى تذكّر الطلبات السابقة. لذلك يحمل كل طلب ما يحتاجه الخادم، ومنه إصدار البروتوكول، في حقل
`_meta`، فيستطيع الخادم أن يعالج كل طلب وحده[^arch-stateless]. والأمثلة هنا تحذف `_meta`، كما تفعل أمثلة الطلبات في
صفحة الأدوات من *مواصفة* MCP، أي الوثيقة الرسمية التي تضع قواعد البروتوكول[^spec-meta]. أما الطلب
الحقيقي فيجب أن يتضمّنه. وكانت
الإصدارات الأقدم تبدأ بمصافحة `initialize`، وهي تبادل افتتاحي يُنشئ *جلسة* (اتصالًا يتذكّر ما سبق)[^spec-older]، لذلك ستصادفها
في الأدلة والخوادم الأقدم.

تنتقل الرسائل عبر **ناقل (transport)**. مع **stdio**، يشغّل العميلُ الخادمَ على حاسوبك برنامجًا مستقلًا،
ويتبادلان رسالة في كل سطر عبر مدخله ومخرجه القياسيين (stdin و stdout: القناتان اللتان يقرأ منهما البرنامج
ويطبع فيهما). ومع **Streamable HTTP**، تُرسَل كل رسالة إلى الخادم في طلب HTTP POST، وهو نوع الطلب الذي
يرسل به برنامج بيانات إلى عنوان على الويب[^spec-transports]. و HTTP هو بروتوكول الويب، الذي تستخدمه متصفحات
الويب وواجهات الويب البرمجية. والخادم المحلي على
stdio يخدم في العادة عميلًا واحدًا، أما الخادم البعيد على HTTP فيخدم في العادة عملاء كثيرين[^arch-local].

**ما يفعله المضيف بالأدوات**

يجمع المضيف أدوات كل خوادمه في قائمة واحدة يستطيع النموذج استخدامها[^arch-registry]. وحين يستدعي
النموذج إحداها، يرسل المضيف الاستدعاء إلى الخادم الصحيح، ويعيد النتيجة إلى النموذج[^arch-route]. فالنموذج
ما زال يرى تعريف أداة وكتلة `tool_result`، كما في الدروس السابقة.

قد يقدّم خادمان أداةً اسمها `search` لكلٍّ منهما. وتطلب المواصفة من العملاء أن يميّزوا بينهما، مثلًا
بوضع اسم الخادم قبل اسم الأداة[^spec-collide]. ويجب أيضًا أن تناسب الأسماءُ الواجهةَ: يسمح MCP بالنقطة في
اسم الأداة[^spec-names]، أما اسم أداة Claude فلا يحمل إلا أحرفًا لاتينية وأرقامًا و`_`
و`-`[^dt-fields].

والفشل هنا أيضًا نوعان. **خطأ البروتوكول (protocol error)**، مثل أداة غير معروفة، يعود في شكل `error` من
JSON-RPC برقم خطأ، مثل `-32602`[^spec-errors]، وهو رقم JSON-RPC للمعاملات غير الصالحة[^jsonrpc-codes]: فاسم الأداة
أحد معاملات `tools/call`. أما **خطأ تنفيذ الأداة (tool execution error)**، مثل طلبية غير موجودة، فيعود في شكل
نتيجة عادية فيها `isError` مضبوطة على true، ويحمل معلومات يستطيع النموذج أن يصحّح بها
نفسه[^spec-errors-exec]. وتطلب المواصفة من العملاء أن يمرّروا أخطاء تنفيذ الأداة إلى النموذج. أما أخطاء البروتوكول فيجوز تمريرها
أيضًا، لكنها أقل قدرة على مساعدته في تصحيح نفسه[^spec-errors-model]. وفي الحالتين، تحتاج كل كتلة `tool_use`
إلى نتيجتها `tool_result` بعدها مباشرة[^hc-follow]، وإلا فشل الطلب التالي الذي ترسله إلى
Claude[^hc-missing]. وفي هذا المقرر يحوّل المضيف النوعين كليهما إلى
`tool_result` مع `is_error`، كما في الدرس السابق[^hc-is-error].

## جرّبها

هذا الملف يؤدي الأدوار الثلاثة، دون شبكة ودون مكتبة MCP. `shop_server` يقوم مقام الخادم، و`send` هو
العميل، والباقي هو المضيف. وكتلة `tool_use` نموذجية تقوم مقام Claude. احفظه باسم `host_and_server.py`
وشغّل `python3 host_and_server.py`:

```python
"""A host, its client and a server in one file. No network, no key, no MCP library."""
import json

ORDERS = {"A-1042": "shipped"}


def shop_server(message):
    """Stands in for an MCP server: it reads one JSON-RPC request and returns the response."""
    reply = {"jsonrpc": "2.0", "id": message["id"]}
    if message["method"] == "tools/list":
        reply["result"] = {"resultType": "complete", "tools": [{
            "name": "lookup_order",
            "description": "Look up a customer's order by its order number and return its status.",
            "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                            "required": ["order_id"]}}]}
    elif message["method"] == "tools/call" and message["params"]["name"] == "lookup_order":
        order_id = message["params"]["arguments"]["order_id"]
        found = order_id in ORDERS
        text = f"Order {order_id}: {ORDERS[order_id]}." if found else f"No order {order_id}."
        reply["result"] = {"resultType": "complete", "content": [{"type": "text", "text": text}],
                           "isError": not found}
    elif message["method"] == "tools/call":
        reply["error"] = {"code": -32602, "message": "Unknown tool: " + message["params"]["name"]}
    else:
        reply["error"] = {"code": -32601, "message": "Method not found"}
    return reply


next_id = 0


def send(method, params):
    """The client: it numbers each request, sends it to its one server, and returns the response."""
    global next_id  # next_id lives outside the function: this line lets send change it
    next_id += 1
    message = {"jsonrpc": "2.0", "id": next_id, "method": method, "params": params}
    print("client ->", json.dumps(message))
    response = shop_server(message)
    print("server ->", json.dumps(response))
    return response


# 1. The client asks the server which tools it has.
listing = send("tools/list", {})
# 2. The host turns them into tool definitions for the Claude API.
tools = [{"name": "shop__" + tool["name"], "description": tool["description"],
          "input_schema": tool["inputSchema"]} for tool in listing["result"]["tools"]]
print("tools for Claude:", [tool["name"] for tool in tools])
# 3. Claude asks for the tool. This sample tool_use block stands in for Claude's reply.
use = {"type": "tool_use", "id": "toolu_sample_01", "name": "shop__lookup_order", "input": {"order_id": "A-1042"}}
# 4. The host sends the call to the server, then turns the answer into a tool_result for Claude.
answer = send("tools/call", {"name": use["name"].removeprefix("shop__"),  # "shop__lookup_order" -> "lookup_order"
                             "arguments": use["input"]})
result = {"type": "tool_result", "tool_use_id": use["id"],
          "content": "\n".join(item["text"] for item in answer["result"]["content"] if item["type"] == "text")}
if answer["result"]["isError"]:
    result["is_error"] = True
print("tool_result for Claude:", json.dumps(result))
```

يعرض الخرج كل رسالة. يرى Claude أداة واحدة، `shop__lookup_order`، ولا يرى أي رسالة JSON-RPC.
غيّر رقم الطلبية في `use` إلى `A-999` وشغّله من جديد: يجيب الخادم مع `isError` مضبوطة على true، وتحصل
`tool_result` على `is_error`. ويستدعي هذا العرض الأداة دون أن يسأل أحدًا: أما المضيف الحقيقي فيجب أن يحصل
على موافقة المستخدم أولًا[^spec-consent].

الخادم الحقيقي برنامج مستقل، والمضيف الحقيقي يكلّمه عبر ناقل. ودرس "اربط خادم MCP" يربط خادمًا حقيقيًا
بـ Claude Code.

## أخطاء شائعة

- **"MCP يحلّ محلّ استخدام الأدوات."** لا. ما زال النموذج يرى تعريفات الأدوات ونتائجها[^arch-route]. يوحّد
  MCP الطريقة التي يحصل بها التطبيق على الأدوات والبيانات من الخوادم.
- **"الخادم يكلّم Claude."** الخادم يكلّم عميلًا داخل المضيف، والمضيف يقرّر ما يراه
  النموذج[^arch-scope].
- **"الخادم جهاز بعيد."** الخادم برنامج، أينما عمل[^arch-where]. وخادم stdio يعمل على حاسوبك نفسه، ويشغّله
  العميل[^spec-transports].
- **"الموارد وقوالب الموجّهات أدوات أيضًا."** النموذج يقرّر متى يستدعي أداة. أما الموارد فيقرّر التطبيق
  أيّها يستخدم، وقالب الموجّه يختاره المستخدم[^sc-table].
- **"كل فشل خطأ JSON-RPC."** الأداة غير المعروفة خطأ بروتوكول. أما الأداة التي عملت وفشلت فتعيد نتيجة
  فيها `isError`، وينبغي أن يراها النموذج ليصحّح نفسه[^spec-errors-model].
- **"ما يقوله الخادم عن أدواته صحيح."** تعدّ المواصفة الأدوات تنفيذًا لأي كود كان (arbitrary code execution)، أي أن الأداة قد تشغّل أي كود على
  الجهاز الذي يعمل عليه الخادم. وتقول إن أوصاف سلوك
  الأدوات غير موثوقة ما لم يكن الخادم موثوقًا[^spec-safety]. ويجب أن يحصل المضيف على موافقة المستخدم قبل
  أن يستدعي أي أداة[^spec-consent]. وسيعود درس ربط الخادم إلى مسألة الثقة.

## تمرينك

### ما الذي ستبنيه

افتح `exercise/starter/mcp_host.py` واكتب جانب المضيف من MCP، في أربع دوال. تستخدم الاختبارات أجوبة
خادم نموذجية من `exercise/tests/`، ولا يشغّل شيء خادمًا حقيقيًا.

- `request(request_id, method, params)` تعيد طلب JSON-RPC.
- `claude_tools(server, listing, routes)` تحوّل جواب الخادم عن `tools/list` إلى تعريفات أدوات لـ Claude.
  يصير كل اسم: اسم الخادم (الاسم الذي أعطاه المضيف للخادم)، ثم `__`، ثم اسم الأداة، مع وضع `_` مكان كل حرف ترفضه الواجهة. وتملأ
  `routes`، وهو قاموس يربط كل اسم جديد بخادمه وباسمه في MCP، ثم تعيد التعريفات مع `routes`. وترفع `ValueError` لجواب خطأ، أو لاسم
  أطول من اللازم، أو لاسم مأخوذ من قبل.
- `call_request(request_id, tool_use, routes)` تحوّل كتلة `tool_use` من Claude إلى اسم الخادم وطلب
  `tools/call`. وترفع `KeyError` لأداة لا يملكها أي خادم.
- `tool_result(tool_use_id, sent, response)` تحوّل جواب الخادم عن الطلب `sent` إلى كتلة `tool_result`. ترفع `ValueError` للجواب الذي لا
  يطابق معرّفه `id`، وتبلّغ عن خطأ البروتوكول مع `is_error`، وتحتفظ بـ `isError` من خطأ تنفيذ الأداة. وعناصر المحتوى التي ليست نصًا، مثل الصور، تصير ملاحظة قصيرة مثل
  `[image not shown]`.

### شغّل الاختبارات

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

تفشل الاختبارات حتى تعمل دوالك. يوجد حل في `exercise/solution/`: حاول أولًا، ثم قارن.

## اختبر نفسك

أجب عن اختبار هذا الدرس. إذا صعب عليك سؤال، فاقرأ "المضيف والعميل والخادم" وجدول الأدوات والموارد وقوالب
الموجّهات من جديد.

[^intro-what]: What is the Model Context Protocol (MCP)?, <https://modelcontextprotocol.io/docs/getting-started/intro>
[^intro-usb]: What is the Model Context Protocol (MCP)?, <https://modelcontextprotocol.io/docs/getting-started/intro>
[^arch-roles]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-participants]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-where]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-scope]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^sc-table]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-db]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^cc-prompts]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^sc-tools-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^sc-resources-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^sc-prompts-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-jsonrpc]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^jsonrpc-request]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^jsonrpc-id]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^jsonrpc-response]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^spec-tool]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^dt-fields]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^spec-call]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-content]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^sc-params]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-stateless]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^spec-meta]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-older]: MCP specification: Transports, <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports>
[^spec-transports]: MCP specification: Transports, <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports>
[^arch-local]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-registry]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-route]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^spec-collide]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-names]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors-exec]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors-model]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^hc-is-error]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^spec-safety]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^spec-consent]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^spec-input]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^jsonrpc-codes]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^hc-follow]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^rt-complete]: MCP specification: Schema Reference, <https://modelcontextprotocol.io/specification/2026-07-28/schema>
[^jsonrpc-notify]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^hc-missing]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
