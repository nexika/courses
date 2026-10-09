# Quand un outil échoue

## Ce que vous saurez faire

- Signaler l'échec d'un outil à Claude dans un `tool_result` avec `is_error`, au lieu de planter ou d'inventer un résultat.
- Écrire des messages d'erreur qui disent à Claude ce qui n'a pas marché et quoi essayer ensuite.
- Vérifier l'entrée de Claude avant d'exécuter un outil, et répondre à chaque appel, même quand la plupart échouent.

## L'idée

Les outils échouent. Un service est en panne, un numéro de commande n'existe pas, ou Claude appelle un
outil avec une entrée qui ne convient pas. Votre code a trois mauvaises options et une bonne.

- **Planter.** Votre programme s'arrête, et l'utilisateur n'obtient rien. Attraper l'erreur sans envoyer
  de résultat ne vaut pas mieux : chaque bloc `tool_use` a besoin de son `tool_result` juste
  après[^hc-follow], sinon la requête suivante échoue[^hc-missing].
- **Envoyer quelque chose d'inutile,** comme un résultat vide ou `"failed"`. Claude n'a rien sur quoi
  s'appuyer.
- **Inventer un résultat,** comme un statut par défaut. Claude ne voit que le résultat renvoyé, pas la
  façon dont vous l'avez obtenu[^hw-sees] : il ne peut pas distinguer un résultat inventé d'un vrai.
- **Signaler l'échec.** Envoyez un `tool_result` dont le `content` dit ce qui s'est passé, avec
  `"is_error": true`[^hc-exec]. Claude intègre alors l'erreur dans sa réponse, par exemple en disant à
  l'utilisateur que le service n'est pas disponible[^hc-exec-claude].

`is_error` est un champ facultatif du bloc `tool_result` : mettez-le à `true` quand l'exécution de l'outil
s'est terminée par une erreur[^hc-is-error]. Voici une recherche qui a échoué :

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_sample_02",
      "content": "No order A-999. Ask the user to check the number: order numbers are A- followed by four digits.",
      "is_error": true
    }
  ]
}
```

Le message s'adresse à Claude. Le guide d'Anthropic demande des messages d'erreur instructifs : au lieu
d'un `"failed"` générique, dites ce qui n'a pas marché et ce que Claude devrait essayer ensuite. Cela
donne à Claude le contexte nécessaire pour se rattraper ou s'adapter sans deviner[^hc-instructive].
Pensez à qui le lit ensuite : Claude peut le répéter à l'utilisateur[^hc-exec-claude]. Retirez donc ce
qu'aucun des deux ne doit voir : traces d'exécution (*stack trace*, la liste des appels que Python affiche
quand une erreur n'est pas attrapée), adresses de serveurs ou mots de passe.

Les échecs sont de deux sortes :

- **L'outil a tourné et a échoué :** la commande n'existe pas, ou le service a mis trop de temps.
  Signalez ce qui s'est passé.
- **L'appel de Claude était faux :** un champ obligatoire manque, un champ a le mauvais type, un champ n'est
  pas permis, ou le nom de l'outil n'existe pas. Vérifiez l'entrée avec l'`input_schema` de l'outil avant d'exécuter quoi que ce
  soit, et signalez les problèmes. Claude réessaiera alors l'outil en complétant l'information
  manquante[^hc-invalid] : si une demande d'outil est invalide ou incomplète, Claude réessaie de 2 à 3 fois
  avec des corrections avant de s'excuser auprès de l'utilisateur[^hc-retries]. Pendant le développement,
  un appel faux signifie le plus souvent que la `description` de l'outil manque de détails[^hc-desc]. S'il
  vous faut des entrées toujours conformes au schéma, l'API propose l'utilisation stricte des outils
  (*strict tool use*), avec `strict: true` dans la définition de l'outil[^hc-strict]. Même alors, l'outil
  lui-même peut échouer : les résultats d'erreur restent nécessaires.

Chaque nouvelle tentative coûte un tour, et la limite de tours de la leçon précédente s'applique toujours.

## Essayez

Le dossier `exercise/tests/` contient une réponse d'exemple avec quatre appels d'outils. Elle a la forme
d'une vraie réponse sans être l'enregistrement d'un vrai appel, et une vraie réponse réunit rarement
autant d'erreurs à la fois. Un appel est correct. Un autre demande une commande qui n'existe pas. Le
troisième envoie un champ nommé `order` au lieu de `order_id`. Le dernier appelle `track_parcel`, un
outil qui n'existe pas. Enregistrez ce code sous `four_calls.py` dans le dossier de la leçon, et lancez
`python3 four_calls.py` depuis ce dossier :

```python
"""Four tool calls, three failures: every call still gets a tool_result. No network, no key."""
import json
from pathlib import Path

reply = json.loads(Path("exercise/tests/sample_four_calls.json").read_text(encoding="utf-8"))
ORDERS = {"A-1042": "shipped"}


def lookup_order(order_id):
    if order_id not in ORDERS:
        raise LookupError(f"No order {order_id}. Ask the user to check the number: order numbers are A- followed by four digits.")
    return {"order_id": order_id, "status": ORDERS[order_id]}


FUNCTIONS = {"lookup_order": lookup_order}
results = []
for block in reply["content"]:
    if block["type"] != "tool_use":
        continue
    result = {"type": "tool_result", "tool_use_id": block["id"]}
    if block["name"] not in FUNCTIONS:
        result.update(content=f"Unknown tool '{block['name']}'. Available tools: lookup_order.", is_error=True)
    else:
        try:
            result["content"] = json.dumps(FUNCTIONS[block["name"]](**block["input"]))
        except LookupError as error:
            result.update(content=str(error), is_error=True)
        except TypeError:  # the input's fields do not fit the function
            result.update(content="Invalid input for lookup_order: it takes one field, order_id. "
                                  "Call it again with a corrected input.", is_error=True)
    results.append(result)
    print(json.dumps(result))
print(sum(1 for r in results if r.get("is_error")), "of", len(results), "results have is_error set")
```

Chaque appel reçoit un `tool_result`, dans l'ordre, et 3 des 4 résultats portent `is_error`. Rien n'a planté, rien n'a été inventé. Attraper
`TypeError` est un raccourci ici : c'est ce que Python lève quand les champs de l'entrée ne conviennent pas
à la fonction. Votre exercice vérifie l'entrée avec le schéma avant d'exécuter l'outil, ce qui donne à
Claude un message plus précis.

## Erreurs fréquentes

- **Laisser filer l'exception.** La boucle s'arrête, et le bloc `tool_use` n'obtient jamais son
  `tool_result`[^hc-missing]. Attrapez l'échec et signalez-le.
- **Renvoyer une erreur comme un résultat normal.** Sans `is_error`, le texte `No order A-999` ressemble à
  une donnée. Mettez `"is_error": true`[^hc-is-error].
- **Des messages génériques.** `"failed"` ne donne rien à Claude. Dites ce qui n'a pas marché et quoi
  essayer ensuite[^hc-instructive].
- **Envoyer l'exception brute.** Une trace d'exécution peut contenir des chemins de fichiers, des adresses
  ou des secrets, et Claude peut répéter l'erreur à l'utilisateur[^hc-exec-claude]. Nommez le type
  d'échec ; gardez les détails dans vos journaux
  (*logs* : ce que votre programme note pour vous, par exemple dans un fichier).
- **Exécuter l'outil sur une entrée non vérifiée.** Vérifiez d'abord les champs obligatoires, les champs
  non permis et les types. Un appel faux est signalé pour que Claude le corrige[^hc-invalid].
- **Sauter les appels après le premier échec.** Chaque bloc `tool_use` a besoin de son propre
  `tool_result`[^hc-missing]. Répondez à tous.

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/errors.py`. Il vous fournit `JSON_TYPES` et `ToolError`, une exception que vos
outils lèvent quand ils échouent d'une façon qu'ils savent expliquer. Écrivez trois fonctions :

- `check_input(tool, args)` renvoie les problèmes de l'entrée envoyée par Claude : champs obligatoires
  manquants, valeurs du mauvais type, et, quand le schéma met `additionalProperties` à `false`, champs
  qu'il ne liste pas. Comme l'a montré la leçon sur le JSON, un schéma sans ce réglage accepte les champs
  en trop.
- `run_one(call, tools, functions)` exécute un appel et renvoie toujours un bloc `tool_result`. Signalez
  un outil inconnu en listant les vrais ; signalez une entrée fausse sans exécuter l'outil ; transmettez
  à Claude le message d'une `ToolError` ; et pour toute autre exception, nommez l'outil et le type
  d'exception, mais pas son message.
- `tool_results(response, tools, functions)` renvoie le message `user` avec un résultat par appel, dans
  l'ordre. Elle ne lève jamais d'exception.

### Lancer les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, comparez ensuite.

## Vérifiez vos acquis

Répondez au quiz de cette leçon. Si une question vous résiste, relisez les quatre options au début de
« L'idée ».

[^hc-missing]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec-claude]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-is-error]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-instructive]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-invalid]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-retries]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-desc]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-follow]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hc-strict]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
