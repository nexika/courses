# Ce qu'est MCP

## Ce que vous saurez faire

- Expliquer à quoi sert MCP, et ce que font l'hôte, le client et le serveur.
- Distinguer les outils, les ressources et les prompts, et dire qui décide quand chacun sert.
- Suivre les messages entre un client et un serveur, dire comment les deux transports les acheminent, et
  transformer les outils et les résultats d'un serveur en définitions d'outils et en blocs `tool_result`,
  comme dans les deux leçons précédentes.

## L'idée

Dans les leçons précédentes, vous avez écrit chaque outil vous-même : sa définition, la fonction qui
l'exécute, et le code qui renvoie son résultat. Imaginez maintenant dix applications qui veulent toutes
accéder aux commandes de votre boutique. Chacune réécrirait ce code.

**MCP** (*Model Context Protocol*, protocole de contexte de modèle) est un standard open source pour
connecter les applications d'IA à des systèmes externes[^intro-what]. Un *protocole* est un ensemble de
règles convenues sur la façon dont deux programmes se parlent. Un *standard* est une façon convenue de
faire une chose. *Open source* veut dire que son texte et son code sont publics et que chacun peut les
utiliser. Sa propre documentation le compare à
un port USB-C : une seule façon standard de brancher les choses[^intro-usb]. Une boutique peut écrire sa
recherche de commandes une fois, sous forme de serveur MCP, et toute application qui parle MCP peut
l'utiliser.

**Hôte, client, serveur**

MCP nomme trois participants[^arch-roles] :

- L'**hôte** (*host*) est l'application d'IA, comme Claude Code ou Claude Desktop, l'application de bureau d'Anthropic. Il se connecte à un ou
  plusieurs serveurs[^arch-participants].
- Un **client** est la partie de l'hôte qui garde la connexion avec un serveur. L'hôte crée un client par
  serveur[^arch-participants].
- Un **serveur** est un programme qui fournit du contexte aux
  clients[^arch-roles]. Il peut tourner sur votre ordinateur ou sur une autre machine : « serveur » désigne
  le rôle, pas le lieu[^arch-where].

Claude Code connecté à deux serveurs contient donc deux clients. Le modèle n'est pas un participant. Le
serveur ne parle jamais à Claude : il parle au client, et c'est l'hôte qui décide de ce qui arrive au
modèle. MCP définit seulement comment le contexte s'échange ; il ne dit pas comment l'application utilise
le modèle[^arch-scope].

**Outils, ressources et prompts**

Un serveur peut offrir trois sortes de choses, et pour chacune, c'est quelqu'un de différent qui décide
quand elle sert[^sc-table] :

| Sorte | Ce que c'est | Qui décide |
|---|---|---|
| **Outils** (*tools*) | Des fonctions que le modèle peut appeler, comme votre `lookup_order` | Le modèle |
| **Ressources** (*resources*) | Des données à lire comme contexte, par exemple un fichier ou le schéma d'une base (ses tables et leurs colonnes) | L'application |
| **Prompts** | Des instructions toutes prêtes pour une tâche, avec des trous à remplir[^sc-params] | L'utilisateur |

La documentation donne un exemple : un serveur pour une base de données peut offrir des outils pour
l'interroger, une ressource qui contient son schéma, et un prompt avec des exemples d'utilisation des
outils[^arch-db]. Dans Claude Code, les prompts d'un serveur apparaissent comme des commandes à taper, par
exemple `/servername:promptname`[^cc-prompts].

Chaque sorte a ses *méthodes*, des opérations nommées qu'un client peut demander à un serveur d'exécuter. `tools/list` trouve les outils et `tools/call` en exécute
un[^sc-tools-ops]. `resources/list` liste les ressources et `resources/read` en lit
une[^sc-resources-ops]. `prompts/list` liste les prompts et `prompts/get` en récupère un[^sc-prompts-ops].

**Les messages**

Clients et serveurs échangent des messages **JSON-RPC 2.0**[^arch-jsonrpc]. JSON-RPC est un petit format
pour demander à un autre programme d'exécuter une méthode. Une requête indique la version, `"2.0"`, et la
méthode `method` à exécuter[^jsonrpc-request]. Elle porte aussi un `id`, que la réponse reprend : vous
savez ainsi à quelle requête elle répond[^jsonrpc-id]. (Un message sans `id` est une *notification* :
l'autre côté n'y répond pas[^jsonrpc-notify].) La réponse contient un `result` quand l'appel a
réussi, ou une `error` quand il a échoué[^jsonrpc-response].

Ici, le client demande ses outils au serveur d'une boutique, et le serveur répond :

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

Un outil a un `name`, une `description` et un `inputSchema`, un JSON Schema pour son entrée[^spec-tool]. Il
ressemble aux définitions d'outils que vous avez écrites, à une orthographe près : l'API Claude appelle le
schéma `input_schema`[^dt-fields]. Pour exécuter l'outil, le client envoie `tools/call` avec le nom de
l'outil `name` et ses `arguments`[^spec-call]. Le résultat contient une liste `content`, qui peut mêler
plusieurs éléments de types différents[^spec-content]. Il peut aussi contenir `isError`, dont on reparle
plus bas. `"resultType": "complete"` marque un résultat terminé[^rt-complete]. Un serveur peut, à la place, répondre qu'il lui
faut d'autres informations avant de terminer l'appel[^spec-input] ; cette leçon n'utilise pas ce cas.

La version actuelle de MCP est *sans état* (*stateless*) : comme pour l'API Messages vue dans les leçons
précédentes[^stateless], le serveur n'a pas à se souvenir des requêtes précédentes. Chaque requête porte donc ce dont le
serveur a besoin, dont la version du protocole, dans un champ `_meta`, et le serveur peut traiter chaque
requête isolément[^arch-stateless]. Les exemples ici omettent `_meta`, comme les exemples de requêtes de la page
sur les outils de la *spécification* MCP, le document officiel qui fixe les règles du protocole[^spec-meta]. Une
vraie requête doit l'inclure. Les versions plus anciennes commençaient par une poignée de main
`initialize`, un échange d'ouverture qui créait une
*session* (une connexion qui se souvient de ce qui précède)[^spec-older] : vous la croiserez encore dans des
guides et des serveurs plus anciens.

Les messages circulent par un **transport**. Avec **stdio**, le client lance le serveur comme un programme
sur votre ordinateur, et ils échangent un message par ligne sur son entrée et sa sortie standard (stdin et
stdout : les flux où un programme lit et écrit). Avec **Streamable HTTP**, chaque message est envoyé au
serveur dans une requête HTTP POST, le type de requête qu'un programme utilise pour envoyer des données à
une adresse web[^spec-transports]. HTTP est le protocole du web, celui des navigateurs et des API web. Un serveur local en stdio sert en général un seul client ; un serveur distant en
HTTP en sert en général beaucoup[^arch-local].

**Ce que l'hôte fait des outils**

L'hôte rassemble les outils de tous ses serveurs en une seule liste que le modèle peut
utiliser[^arch-registry]. Quand le modèle en appelle un, l'hôte envoie l'appel au bon serveur et renvoie le
résultat au modèle[^arch-route]. Le modèle voit toujours une définition d'outil et un `tool_result`, comme
dans les leçons précédentes.

Deux serveurs peuvent chacun offrir un outil nommé `search`. La spécification demande aux clients de les
distinguer, par exemple en plaçant un nom de serveur devant le nom de l'outil[^spec-collide]. Les noms
doivent aussi convenir à l'API : MCP autorise un point dans un nom d'outil[^spec-names], mais un nom d'outil
Claude ne peut contenir que des lettres, des chiffres, `_` et `-`[^dt-fields].

Là aussi, les échecs sont de deux sortes. Une **erreur de protocole** (*protocol error*), comme un outil
inconnu, revient sous forme d'`error` JSON-RPC avec un code numérique, par exemple `-32602`[^spec-errors], le
code JSON-RPC des paramètres invalides[^jsonrpc-codes] : le nom de l'outil est l'un des
paramètres de `tools/call`. Une **erreur d'exécution d'outil** (*tool
execution error*), comme une commande qui n'existe pas, revient sous forme de résultat normal avec
`isError` à true, et contient un retour dont le modèle peut se servir pour se corriger[^spec-errors-exec].
La spécification demande aux clients de transmettre les erreurs d'exécution d'outil au modèle. Les
erreurs de protocole peuvent l'être aussi, mais elles ont moins de chances de l'aider à se
rattraper[^spec-errors-model]. Dans tous les cas, chaque bloc `tool_use` a besoin de son
`tool_result` juste après lui[^hc-follow], sinon la prochaine requête que vous envoyez à
Claude échoue[^hc-missing]. Dans ce cours, l'hôte transforme les deux sortes en `tool_result` avec
`is_error`, comme dans la leçon précédente[^hc-is-error].

## Essayez

Ce fichier joue les trois rôles, sans réseau et sans bibliothèque MCP. `shop_server` tient lieu de
serveur, `send` est le client, et le reste est l'hôte. Un bloc `tool_use` d'exemple tient lieu de Claude.
Enregistrez-le sous `host_and_server.py` et lancez `python3 host_and_server.py` :

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

La sortie montre chaque message. Claude voit un seul outil, `shop__lookup_order`, et ne voit jamais de
message JSON-RPC. Remplacez le numéro de commande dans `use` par `A-999` et relancez : le serveur répond
avec `isError` à true, et le `tool_result` reçoit `is_error`. Cette démo appelle aussi l'outil sans demander à personne : un
vrai hôte doit d'abord obtenir l'accord de l'utilisateur[^spec-consent].

Un vrai serveur est un programme à part, et un vrai hôte lui parle par un transport. La leçon « Connecter
un serveur MCP » en connecte un à Claude Code.

## Erreurs fréquentes

- **« MCP remplace l'utilisation d'outils. »** Non. Le modèle voit toujours des définitions d'outils et
  des résultats d'outils[^arch-route]. MCP standardise la façon dont l'application obtient outils et
  données auprès des serveurs.
- **« Le serveur parle à Claude. »** Le serveur parle à un client dans l'hôte. C'est l'hôte qui décide de
  ce que le modèle voit[^arch-scope].
- **« Un serveur est une machine distante. »** Un serveur est un programme, où qu'il
  tourne[^arch-where]. Un serveur stdio tourne sur votre propre ordinateur, lancé par le
  client[^spec-transports].
- **« Les ressources et les prompts sont aussi des outils. »** Le modèle décide quand appeler un outil.
  L'application décide quelles ressources utiliser, et l'utilisateur choisit un prompt[^sc-table].
- **« Tout échec est une erreur JSON-RPC. »** Un outil inconnu est une erreur de protocole. Un outil qui
  s'est exécuté et a échoué renvoie un résultat avec `isError`, que le modèle devrait voir pour se
  corriger[^spec-errors-model].
- **« Ce qu'un serveur dit de ses outils est vrai. »** La spécification présente les outils comme de
  l'exécution de code arbitraire : un outil peut exécuter n'importe quel code sur la machine où tourne le
  serveur. Elle dit que les descriptions du comportement des outils ne sont pas
  fiables, sauf si le serveur l'est[^spec-safety]. L'hôte doit obtenir l'accord de l'utilisateur avant
  d'appeler un outil[^spec-consent]. La leçon sur la connexion d'un serveur revient sur la confiance.

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/mcp_host.py` et écrivez le côté hôte de MCP, en quatre fonctions. Les tests
utilisent des réponses de serveur d'exemple, dans `exercise/tests/` ; aucun vrai serveur ne tourne.

- `request(request_id, method, params)` renvoie une requête JSON-RPC.
- `claude_tools(server, listing, routes)` transforme la réponse d'un serveur à `tools/list` en définitions
  d'outils pour Claude, et les renvoie avec `routes`. Chaque nom devient le nom du serveur (celui que l'hôte lui a donné), `__`, puis le nom de l'outil, chaque
  caractère refusé par l'API étant remplacé par `_`. Elle remplit `routes`, un dictionnaire qui associe chaque nouveau nom
  à son serveur et à son nom MCP. Elle lève `ValueError` pour une réponse d'erreur, un nom trop long ou un
  nom déjà pris.
- `call_request(request_id, tool_use, routes)` transforme le bloc `tool_use` de Claude en nom de serveur et
  en requête `tools/call`. Elle lève `KeyError` pour un outil qu'aucun serveur ne possède.
- `tool_result(tool_use_id, sent, response)` transforme la réponse du serveur à la requête `sent` en bloc
  `tool_result`. Elle
  lève `ValueError` pour une réponse dont l'`id` ne correspond pas, signale une erreur de protocole avec `is_error`, et
  garde l'`isError` d'une erreur d'exécution d'outil. Les éléments de contenu qui ne sont pas du texte,
  comme les images, deviennent une courte note comme `[image not shown]`.

### Lancez les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, puis comparez.

## Vérifiez vos acquis

Faites le quiz de cette leçon. Si une question vous pose problème, relisez « Hôte, client, serveur » et le
tableau des outils, ressources et prompts.

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
