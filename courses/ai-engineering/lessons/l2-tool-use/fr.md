# Donner un outil à Claude

## Ce que vous saurez faire

- Définir un outil : son nom, une description qui dit quand l'utiliser, et un JSON Schema pour son entrée.
- Lire la demande d'outil de Claude, exécuter l'outil dans votre code, et lui renvoyer le résultat.
- Faire tourner la boucle d'outils : continuer tant que Claude demande des outils, s'arrêter quand il répond.

## L'idée

Claude ne peut pas chercher une commande dans la base de données de votre boutique : il n'a jamais vu ces
données. Votre code, lui, le peut. L'**utilisation d'outils** (*tool use*, aussi appelée appel de
fonctions, *function calling*) permet à Claude d'appeler des fonctions que vous définissez[^ov-what].
Vous décrivez un outil ; Claude décide quand l'appeler, d'après la demande de l'utilisateur et la
description de l'outil[^ov-what].

Le modèle n'exécute jamais rien lui-même. Il écrit une demande structurée, votre code exécute l'opération,
et le résultat revient dans la conversation[^hw-contract]. Claude ne voit jamais votre code : il ne voit
que la définition fournie et le résultat renvoyé[^hw-sees].

Une définition d'outil se place dans la liste `tools` de la requête[^dt-tools]. Elle a trois
parties[^dt-fields] :

- `name` : des lettres, des chiffres, `_` ou `-`, au plus 128 caractères[^dt-fields].
- `description` : ce que fait l'outil, quand l'utiliser et comment il se comporte.
- `input_schema` : un JSON Schema pour l'entrée de l'outil, comme les schémas de la leçon précédente.

```json
{
  "name": "lookup_order",
  "description": "Look up a customer's order by its order number and return its status. Use it when the user asks where an order is or whether it has shipped. It returns only the status and the days to delivery, not what the order contains.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {"type": "string", "description": "The order number, such as A-1042."}
    },
    "required": ["order_id"]
  }
}
```

La description compte plus que tout : le guide d'Anthropic en fait de loin le facteur le plus important
de la performance d'un outil[^dt-desc], et demande au moins trois ou quatre phrases[^dt-sentences].

Voici un **cycle** de l'échange d'outil, pour la question `Where is order A-1042?` :

1) Vous envoyez la question et la liste `tools`.
2) Claude répond avec la raison d'arrêt `tool_use` et un bloc `tool_use`. Le bloc contient un `id`, le
   nom de l'outil `name`, et un objet `input` pour lui[^hc-block]. Claude écrit souvent d'abord un court
   bloc de texte, comme "I'll look up that order."[^dt-comment]
3) Votre code exécute l'outil avec cette entrée.
4) Vous envoyez une nouvelle requête : toute la conversation jusqu'ici, la réponse de Claude en tour
   `assistant`, et un tour `user` avec un bloc `tool_result`. Son `tool_use_id` est l'`id` de l'appel
   auquel il répond, et son `content` est le résultat[^hc-result].
5) Claude lit le résultat et écrit sa réponse[^hc-continue].

Une réponse peut contenir un ou plusieurs blocs `tool_use`[^hc-block] : répondez à chacun. L'API Claude
n'a pas de rôle spécial `tool` : les appels d'outils voyagent dans des tours `assistant`, les résultats
dans des tours `user`[^hc-roles]. Deux règles d'ordre comptent. Les résultats doivent suivre
immédiatement le tour qui les a demandés, sans aucun message entre les deux. Et dans ce tour `user`, les
blocs `tool_result` viennent en premier, avant tout texte[^hc-order].

**La boucle d'outils** répète cet échange. Tant que la raison d'arrêt est `tool_use`, exécutez les outils
et poursuivez la conversation. Toute autre raison d'arrêt termine la boucle : Claude a répondu, ou s'est
arrêté pour une raison que votre code doit traiter[^hw-loop]. Un cycle, c'est une réponse qui demande des
outils, plus les résultats que votre code renvoie. Chaque cycle coûte une nouvelle requête, et chaque
requête renvoie tout l'historique[^stateless] : limitez donc le nombre de cycles.

Les outils coûtent des tokens. Les définitions d'outils comptent comme tokens d'entrée[^ov-price], et
l'API ajoute un prompt système qui active l'utilisation d'outils[^ov-enables] : 286 tokens sur Claude
Opus 5.5[^ov-prompt].

## Essayez

### Sans clé : un cycle, à la main

Le dossier `exercise/tests/` contient deux réponses d'exemple, qui ont la forme de vraies réponses sans
être des enregistrements de vrais appels : l'appel de Claude à `lookup_order`, puis sa réponse finale.
Elles jouent ici le rôle de Claude. Enregistrez ce code sous `one_round.py` dans le dossier de la leçon,
et lancez `python3 one_round.py` depuis ce dossier :

```python
"""One round of the tool exchange, offline: two sample replies stand in for Claude."""
import json
from pathlib import Path

folder = Path("exercise/tests")
replies = [json.loads((folder / name).read_text(encoding="utf-8"))
           for name in ("sample_tool_call.json", "sample_final_answer.json")]


def lookup_order(order_id):
    """Real code would ask the shop's database. This one knows a single order."""
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
reply = replies[0]  # the reply to request 1: Claude asks for the tool
print("stop_reason:", reply["stop_reason"])
messages.append({"role": "assistant", "content": reply["content"]})
results = []
for block in reply["content"]:
    if block["type"] == "tool_use":
        print("Claude calls", block["name"], "with", block["input"])
        output = lookup_order(**block["input"])
        results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(output)})
messages.append({"role": "user", "content": results})
print("request 2 sends", len(messages), "messages:", [m["role"] for m in messages])
reply = replies[1]  # the reply to request 2: Claude answers with the result
print("stop_reason:", reply["stop_reason"])
print("".join(block["text"] for block in reply["content"] if block["type"] == "text"))
```

`lookup_order(**block["input"])` passe les champs de l'entrée comme arguments nommés (*keyword
arguments*) : `{"order_id": "A-1042"}` devient `lookup_order(order_id="A-1042")`.
La deuxième requête envoie 3 messages : la question, l'appel de Claude, et le résultat.

### Avec votre propre clé (facultatif)

Ce code fait tourner la vraie boucle : il faut une clé, et les tokens consommés sont facturés. Préparez la
clé et le SDK comme dans la leçon « Votre premier appel à l'API ».

```python
import json

import anthropic

client = anthropic.Anthropic()
tools = [{
    "name": "lookup_order",
    "description": ("Look up a customer's order by its order number and return its status. "
                    "Use it when the user asks where an order is or whether it has shipped. "
                    "It returns only the status and the days to delivery, not what the order contains."),
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order number, such as A-1042."}},
        "required": ["order_id"],
    },
}]


def lookup_order(order_id):
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
for round_number in range(5):  # a limit, so the loop cannot run forever
    response = client.messages.create(model="claude-opus-5-5", max_tokens=1024, tools=tools, messages=messages)
    if response.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": response.content})
    results = []
    for block in response.content:
        if block.type == "tool_use":
            output = lookup_order(**block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
    messages.append({"role": "user", "content": results})
if response.stop_reason == "tool_use":
    print("Stopped: Claude still wanted tools after 5 rounds.")
print("stop_reason:", response.stop_reason)
print("".join(block.text for block in response.content if block.type == "text"))
```

Le SDK peut aussi faire tourner cette boucle pour vous, avec son Tool Runner[^hc-runner]. Écrivez d'abord
la boucle à la main, pour savoir ce qu'elle fait.

## Erreurs fréquentes

- **« Claude exécute ma fonction. »** Jamais. Il demande ; votre code exécute et rend compte[^hw-contract].
  C'est votre code qui décide de ce qu'un outil a le droit de faire.
- **Une description d'une ligne.** La description est le principal appui de Claude pour choisir un outil
  et remplir son entrée[^dt-desc]. Dites ce que fait l'outil, quand l'utiliser, et ce qu'il ne renvoie pas.
- **Oublier le tour `assistant`.** La requête suivante doit contenir la réponse de Claude, avec ses blocs
  `tool_use`, avant vos résultats. L'API est sans état : elle ne se souvient pas de l'appel[^stateless].
- **Du texte avant les résultats.** Dans le tour des résultats, les blocs `tool_result` viennent en
  premier. Du texte avant eux fait échouer la requête avec une erreur[^hc-400].
- **Ne répondre qu'au premier appel.** Une réponse peut contenir plusieurs blocs `tool_use`[^hc-block].
  Envoyez un résultat pour chacun, relié par son `tool_use_id`.
- **Faire aveuglément confiance à l'entrée.** Quand l'utilisateur omet une valeur obligatoire, Claude Opus a
  bien plus de chances de la demander[^ov-ask], mais Claude peut aussi en deviner une, comme un numéro de
  commande que l'utilisateur n'a jamais donné[^ov-guess]. Vérifiez
  l'entrée avant d'agir.
- **Faire confiance à ce que renvoie un outil.** Les pages web, les e-mails et tout contenu extérieur
  peuvent cacher des instructions destinées à Claude[^hc-untrusted2]. Traitez les résultats d'outils comme non fiables, et
  gardez ce contenu dans des blocs `tool_result`, pas dans votre prompt système ni dans votre propre
  texte[^hc-untrusted].
- **Forcer un outil avec `tool_choice`.** `tool_choice` est un champ facultatif de la requête qui peut
  obliger Claude à utiliser un outil[^dt-choice] : `auto` laisse Claude choisir, `any` l'oblige à appeler
  un outil, et `tool` l'oblige à appeler un outil précis. Sur Claude Opus 5.5, `any` et `tool` renvoient
  une erreur[^dt-forced]. Laissez `auto`, la valeur par défaut[^ov-auto], et écrivez
  une meilleure description ou un meilleur prompt.

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/tools.py` et écrivez quatre fonctions. Elles fonctionnent hors ligne : dans les
tests, un substitut (*stand-in*) joue le rôle de Claude, comme dans la leçon précédente.

- `define_tool(name, description, properties, required)` renvoie une définition d'outil. Levez
  `ValueError` pour un nom que l'API refuserait, une description vide, ou un champ obligatoire absent de
  `properties`.
- `tool_calls(response)` renvoie les appels d'outils de la réponse, dans l'ordre, sous forme de dicts avec
  `id`, `name` et `input`.
- `tool_results(response, functions)` exécute chaque appel et renvoie le message `user` avec un bloc
  `tool_result` par appel. `functions` associe le nom de chaque outil à la fonction Python qui l'exécute.
- `run_tool_loop(ask, question, tools, functions, max_rounds)` fait tourner la boucle :
  `ask(messages, tools)` remplace l'appel à l'API. Elle renvoie le texte de la réponse et toute la
  conversation, et lève `RuntimeError` si Claude appelle encore un outil après `max_rounds` cycles. Avec `max_rounds=3`,
  elle envoie donc au plus quatre requêtes : trois dont les réponses appellent des outils, et une quatrième
  dont la réponse doit être la réponse finale.

Dans cette leçon, chaque outil réussit. La leçon suivante traite des outils qui échouent.

### Lancer les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, comparez ensuite.

## Vérifiez vos acquis

Répondez au quiz de cette leçon. Si une question vous résiste, relisez les cinq étapes de l'échange
d'outil dans « L'idée ».

[^dt-sentences]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^ov-ask]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-400]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-choice]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-untrusted2]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^ov-what]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hw-contract]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^dt-tools]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-fields]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-desc]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-block]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-comment]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-result]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-continue]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-roles]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-order]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-loop]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^ov-price]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-prompt]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-enables]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-runner]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^ov-guess]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-untrusted]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-forced]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^ov-auto]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
