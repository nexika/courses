# Obtenir un JSON fiable

## Ce que vous saurez faire

- Décrire les données voulues avec un JSON Schema : les champs, leurs types, et ceux qui sont obligatoires.
- Demander à Claude un JSON qui suit ce schéma, avec `output_config.format`.
- Vérifier chaque réponse avant que votre code ne l'utilise, et décider quand redemander et quand s'arrêter.

## L'idée

Votre code ne sait pas lire une phrase aimable. Si une application de support demande à Claude de trier
le message d'un client, elle a besoin de trois champs fiables : une catégorie, une priorité et un court
résumé. Sans aide, Claude peut écrire un JSON mal formé, ou un JSON auquel manque un champ obligatoire, et
votre application casse[^so-without].

Un **JSON Schema** décrit la forme des données attendues. Le schéma lui-même est écrit en JSON : ce sont
des données, pas un programme[^js-data]. Voici le schéma d'un ticket de support :

```json
{
  "type": "object",
  "properties": {
    "category": {"type": "string", "enum": ["bug", "billing", "question"]},
    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
    "summary": {"type": "string"}
  },
  "required": ["category", "priority", "summary"],
  "additionalProperties": false
}
```

Lisez-le de haut en bas. La valeur est un objet (un objet JSON, comme un dict Python). `properties` liste
ses champs et le schéma de chacun. `type` nomme le genre de valeur : `string`, `integer`, `number`,
`boolean`, `array`, `object` ou `null`. `enum` liste les seules valeurs permises. `minimum` et `maximum`
bornent un nombre. Deux règles surprennent. En JSON Schema, un champ listé dans `properties` n'est pas
obligatoire tant que vous ne le nommez pas dans `required`[^js-required]. Et les champs en trop sont
acceptés tant que vous ne mettez pas `additionalProperties` à `false`[^js-additional].

Les **sorties structurées** (*structured outputs*) sont la fonctionnalité de l'API Claude qui oblige
Claude à suivre un schéma[^so-intro]. Vous placez le schéma dans la requête, dans `output_config.format`,
avec `type` à `json_schema`[^so-send]. Claude écrit alors un JSON valide conforme à votre schéma, dans le
bloc de texte de la réponse[^so-read]. Le mécanisme transforme votre schéma en grammaire, un ensemble de
règles qui limite ce que Claude peut écrire ensuite[^so-grammar].

La fonctionnalité n'accepte pas n'importe quel schéma. Chaque objet doit mettre `additionalProperties` à
`false`[^so-supported]. Les contraintes numériques comme `minimum` et `maximum` ne sont pas prises en
charge, et une requête qui utilise une fonctionnalité non prise en charge échoue avec une
erreur[^so-unsupported]. Vous gardez donc deux versions : le schéma envoyé, sans `minimum` ni `maximum`,
et le schéma complet, que votre code vérifie. La plupart des *helpers* des SDK font de même : ils envoient
à Claude un schéma simplifié, et un *helper* qui vérifie les réponses applique quand même toutes les
règles de votre schéma complet[^so-sdk].

Alors pourquoi vérifier ? Parce que « suit le schéma » a des exceptions :

- **Un refus.** Claude peut décliner une requête. La réponse a alors la raison d'arrêt `refusal`, et sa
  sortie peut ne pas respecter votre schéma[^so-refusal]. Un refus est une réponse normale et réussie, pas
  une erreur[^stop-refusal]. Renvoyer la même requête n'est pas la solution documentée : une requête
  refusée par Claude Opus 5.5 peut généralement être servie en réessayant sur un autre modèle
  Claude[^refusal-fallback].
- **Une réponse coupée.** Si la réponse atteint `max_tokens`, le JSON peut être incomplet. La solution
  documentée est de réessayer avec un `max_tokens` plus élevé[^so-max].
- **Les majuscules des valeurs d'`enum`.** Claude peut renvoyer `"Bug"` quand votre schéma dit `"bug"` :
  la casse des valeurs d'enum n'est pas garantie[^so-enum-case]. La documentation conseille de comparer
  les valeurs d'enum sans tenir compte de la casse[^so-enum].
- **Les règles que l'API ne vérifie pas,** comme `minimum` et `maximum` ci-dessus, et celles qu'un schéma
  ne sait pas exprimer, comme « la date doit être dans le futur ». Seul votre code les vérifie.

Une réponse qui enfreint l'une de vos règles peut être redemandée. Chaque nouvelle requête coûte des
tokens : fixez une limite, puis arrêtez-vous et signalez le problème. Les sorties structurées ont aussi un
petit coût : Claude reçoit un prompt système supplémentaire qui explique le format, donc votre nombre de
tokens d'entrée augmente légèrement[^so-cost].

## Essayez

### Avec votre propre clé (facultatif)

Ce code appelle la vraie API : il faut une clé, et les tokens consommés sont facturés. Préparez la clé et
le SDK comme dans la leçon « Votre premier appel à l'API ». Le schéma envoyé ici n'a ni `minimum` ni
`maximum` ; une description (`description`) indique la plage à Claude à la place.

```python
import json

import anthropic

SENT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["bug", "billing", "question"]},
        "priority": {"type": "integer", "description": "1 = low, 2 = normal, 3 = urgent"},
        "summary": {"type": "string"},
    },
    "required": ["category", "priority", "summary"],
    "additionalProperties": False,
}

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Sort this support message: I was charged twice in March."}],
    output_config={"format": {"type": "json_schema", "schema": SENT_SCHEMA}},
)
print("stop_reason:", response.stop_reason)
text = "".join(block.text for block in response.content if block.type == "text")
print(json.loads(text) if response.stop_reason == "end_turn" else text)
```

Ce code suit l'exemple « JSON Schema brut » du guide des sorties structurées d'Anthropic[^so-raw]. Votre
réponse sera différente des exemples ci-dessous.

### Sans clé : lire six réponses d'exemple

Le dossier `exercise/tests/` contient six réponses d'exemple à la requête du ticket. Elles ont la forme
de vraies réponses, mais ce ne sont pas des enregistrements de vrais appels. L'une d'elles,
`sample_not_json.json`, montre ce que peut renvoyer une requête sans `output_config` : du JSON précédé
d'une phrase. Enregistrez ce code sous `read_samples.py` dans le dossier de la leçon, et lancez
`python3 read_samples.py` depuis ce dossier :

```python
"""Read six sample replies and say which ones your code could use. No network, no key."""
import json
from pathlib import Path

CATEGORIES = ("bug", "billing", "question")
folder = Path("exercise/tests")

for path in sorted(folder.glob("sample_*.json")):
    reply = json.loads(path.read_text(encoding="utf-8"))
    if reply["stop_reason"] != "end_turn":
        print(f"{path.name}: not usable, stop_reason is {reply['stop_reason']}")
        continue
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    try:
        ticket = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"{path.name}: not usable, not JSON ({error})")
        continue
    problems = []
    if str(ticket.get("category")).lower() not in CATEGORIES:
        problems.append("unknown category")
    priority = ticket.get("priority")
    if type(priority) is not int or not 1 <= priority <= 3:
        problems.append("priority must be a whole number from 1 to 3")
    if not isinstance(ticket.get("summary"), str):
        problems.append("no summary")
    print(f"{path.name}: " + ("not usable, " + ", ".join(problems) if problems else "usable"))
```

Seules 2 des 6 réponses d'exemple sont utilisables. `sample_enum_case.json` passe parce que la
vérification de la catégorie ignore la casse. `sample_out_of_range.json` est un JSON valide avec tous les
champs, mais il met la priorité à 5 : rien dans le schéma envoyé à l'API ne l'a empêché, seule votre
vérification le détecte. Deux réponses se sont arrêtées trop tôt, l'une avec `max_tokens` et l'autre avec
`refusal`, et une n'est pas du JSON du tout.

## Erreurs fréquentes

- **« Avec les sorties structurées, je ne vérifie plus rien. »** Un refus ou une réponse coupée peut ne
  pas respecter le schéma[^so-refusal] [^so-max], et les contraintes numériques ne sont pas envoyées à
  l'API[^so-unsupported]. Vérifiez chaque réponse.
- **Envoyer `minimum` ou `maximum` dans le schéma.** La requête échoue[^so-unsupported]. Gardez le schéma
  complet dans votre code et envoyez le schéma simplifié.
- **Oublier `required`.** Sans lui, tous les champs sont facultatifs[^js-required], et votre code tombe
  plus tard sur une clé absente.
- **Comparer les valeurs d'enum à l'identique.** `"Bug"` peut revenir à la place de
  `"bug"`[^so-enum-case]. Comparez sans tenir compte de la casse, puis reprenez l'orthographe du schéma.
- **Prendre `True` pour un nombre.** En Python, `bool` est un sous-type de `int`[^py-bool] :
  `isinstance(True, int)` vaut donc `True`. Une vérification d'entier doit écarter les booléens.
- **Demander le raisonnement de Claude dans un champ.** Un champ qui demande la réflexion du modèle ou son
  raisonnement pas à pas peut provoquer un refus. Demandez plutôt une courte explication[^so-reasoning].
- **Réessayer sans limite.** Chaque tentative coûte des tokens. Arrêtez-vous après quelques essais, et ne
  renvoyez pas telle quelle une requête refusée : la solution documentée est un autre
  modèle[^refusal-fallback].

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/structured.py`. Il vous fournit `TYPES` (ce que chaque type JSON Schema accepte
en Python), l'exception `ReplyError` (une erreur que votre code lève, avec une raison `reason`), et
`use_schema_spelling()`, qui remet les valeurs d'enum dans l'orthographe du schéma. Écrivez trois
fonctions :

- `validate(value, schema)` renvoie la liste des problèmes, vide si la valeur est valide. Elle prend en
  charge `type`, `enum` (sans tenir compte de la casse), `minimum`, `maximum`, `properties`, `required`,
  `additionalProperties: false` et `items` (le schéma de chaque élément d'un tableau). Signalez chaque
  problème, en commençant par son emplacement, par exemple `$.priority` (`$` désigne la valeur entière).
- `parse_reply(response, schema)` renvoie la valeur vérifiée, ou lève `ReplyError` avec la raison
  `refusal`, `cut_off`, `not_json` ou `invalid`.
- `ask_until_valid(ask, schema, max_tokens, attempts)` appelle `ask(max_tokens)` jusqu'à obtenir une
  réponse valide. Dans les tests, `ask` est un substitut (*stand-in*) : une fonction qui joue le rôle de
  l'API et renvoie des réponses d'exemple, donc aucun appel n'est facturé. Elle s'arrête tout de suite sur
  un refus, double `max_tokens` après une réponse coupée (doubler est un choix de ce cours ; la
  documentation dit seulement de l'augmenter), et lève `ReplyError` avec la raison `gave_up` après la
  dernière tentative.

Le schéma complet du ticket se trouve dans `exercise/tests/ticket_schema.json`.

### Lancer les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, comparez ensuite.

## Vérifiez vos acquis

Répondez au quiz de cette leçon. Si une question vous résiste, relisez la liste des exceptions dans
« L'idée » : le refus, la réponse coupée, la casse des enums, et les règles que l'API ne vérifie pas.

[^so-without]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^js-data]: What is a schema? (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/about>
[^js-required]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^js-additional]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^so-intro]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-send]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-read]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-grammar]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-supported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-unsupported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-sdk]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-refusal]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^stop-refusal]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^refusal-fallback]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^so-max]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum-case]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-cost]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-raw]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^py-bool]: Built-in Types (Python documentation), <https://docs.python.org/3/library/stdtypes.html>
[^so-reasoning]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
