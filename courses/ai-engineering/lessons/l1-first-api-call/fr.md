# Votre premier appel à l'API

## Ce que vous saurez faire

- Appeler Claude depuis Python avec le SDK officiel, puis lire la réponse et le nombre de tokens consommés.
- Construire une conversation : un prompt système, puis des tours utilisateur et assistant.
- Choisir le modèle et `max_tokens` d'une requête, et traiter une réponse arrêtée faute de tokens.
- Lire une réponse en flux continu, morceau par morceau, au fur et à mesure qu'elle arrive.

## L'idée

Une API (interface de programmation) est une porte qu'un programme ouvre aux autres programmes. La porte
de Claude s'appelle la Messages API : votre code envoie une requête par Internet, et une réponse revient.

Vos appels utilisent une clé d'API : une chaîne secrète qui identifie votre compte, à garder pour vous.
On la range d'habitude dans une variable d'environnement de votre machine[^start-key]. Le SDK Python
officiel (une bibliothèque que vous installez) la lit dans `ANTHROPIC_API_KEY` sans que vous ayez à la lui
passer[^start-env]. Ce SDK est la façon dont Anthropic donne aux programmes Python accès à l'API
Claude[^sdk].

Une requête est un petit objet JSON. Voici les champs que vous utiliserez d'abord :

- `model` : le modèle qui répond. Si vous hésitez, la documentation d'Anthropic conseille de commencer par
  Claude Opus 5.5[^models-start], dont le nom dans l'API est `claude-opus-5-5`[^model-id]. Les noms de
  modèles changent : consultez la page des modèles avant de choisir.
- `max_tokens` : le nombre maximal de tokens à générer avant de s'arrêter[^max-tokens]. C'est un plafond,
  pas un objectif : le modèle peut s'arrêter avant[^max-early].
- `system` (facultatif) : le prompt système, qui sert à donner à Claude du contexte et des consignes,
  par exemple un objectif ou un rôle[^system].
- `messages` : la conversation jusqu'ici, du plus ancien au plus récent. Chaque tour a un `role`, `user`
  ou `assistant`, et un `content`. Les modèles sont entraînés sur des tours qui alternent entre
  utilisateur et assistant[^alternating].

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "system": "You are a patient tutor. Answer in two sentences.",
  "messages": [
    {"role": "user", "content": "What is a token?"}
  ]
}
```

L'API est sans état (*stateless*) : elle ne se souvient pas de vos appels précédents, donc vous envoyez
tout l'historique de la conversation à chaque fois[^stateless]. Pour poser une question de suivi, vous
ajoutez la réponse de Claude comme tour `assistant` et votre nouvelle question comme tour `user`, puis
vous renvoyez le tout. Le dernier tour doit être celui de l'utilisateur. Terminer par un tour assistant
(le *prefill*) n'est pas pris en charge sur Claude 4.6 et les modèles plus récents[^prefill]. Une telle
requête renvoie une erreur[^prefill-error].

Vous croiserez peut-être `temperature` dans d'anciens exemples : ce paramètre règle la part de hasard
dans la réponse[^temperature]. Sur Claude 4.7 et les modèles plus récents, `temperature`, `top_p` et
`top_k` ne sont pas pris en charge[^sampling], et toute valeur autre que la valeur par défaut fait échouer
la requête[^sampling-error]. Guidez plutôt la réponse avec votre prompt.

Voici une réponse, affichée en JSON. C'est un exemple qui a la forme d'une vraie réponse, pas
l'enregistrement d'un vrai appel : ses nombres de tokens sont donnés à titre d'illustration.

```json
{
  "id": "msg_sample_01",
  "type": "message",
  "role": "assistant",
  "model": "claude-opus-5-5",
  "content": [
    {
      "type": "text",
      "text": "A token is a small piece of text, such as a word or part of a word. Claude reads your prompt and writes its answer as tokens."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 41,
    "output_tokens": 28
  }
}
```

Trois parties comptent le plus :

- `content` est une liste de blocs, pas une seule chaîne. Un bloc `text` contient des mots de la réponse.
  Il existe d'autres sortes de blocs, par exemple les blocs de réflexion (*thinking*)[^thinking-blocks] :
  rassemblez donc les blocs de type `text` au lieu de supposer que le premier bloc est la réponse.
- `stop_reason` indique pourquoi Claude a cessé d'écrire[^stop-every]. `end_turn` signifie que Claude a
  terminé sa réponse naturellement[^stop-end]. `max_tokens` signifie qu'il a atteint la limite
  `max_tokens` de votre requête[^stop-max] : le texte est coupé, et la solution est d'augmenter
  `max_tokens` ou de poursuivre la réponse[^stop-max-do]. Une raison d'arrêt n'est pas une erreur : elle
  dit pourquoi une réponse réussie s'est terminée[^stop-not-error]. Il existe d'autres valeurs, que
  d'autres leçons présenteront.
- `usage` compte les tokens d'entrée (ce que vous avez envoyé) et les tokens de sortie (ce que Claude a
  écrit)[^usage]. Le nombre de tokens de sortie est le total retenu pour la facturation[^usage-billing].
  Comme vous renvoyez l'historique à chaque appel, le nombre de tokens d'entrée grandit avec la
  conversation.

Le streaming change la façon dont la réponse voyage, pas ce qu'elle dit. Avec `"stream": true`, l'API
envoie la réponse en morceaux, sous forme d'événements envoyés par le serveur (*server-sent
events*)[^stream-sse] : vous pouvez afficher le texte pendant que Claude écrit encore. Pour les requêtes
avec de grandes valeurs de `max_tokens`, le SDK exige le streaming pour éviter les délais d'attente
dépassés[^stream-timeout]. Le flux commence par un événement `message_start` qui contient un message au
contenu vide[^stream-start]. Chaque bloc de contenu arrive ensuite sous la forme d'un événement
`content_block_start`, d'un ou plusieurs événements `content_block_delta`, et d'un événement
`content_block_stop`[^stream-flow]. Chaque delta met à jour le bloc situé à un index donné[^stream-delta].
Les nombres de tokens de l'événement `message_delta` sont des totaux cumulés, pas des valeurs à
additionner[^stream-cumulative]. Un flux peut aussi contenir des événements `ping`[^stream-ping], et votre
code doit traiter sans planter les types d'événements qu'il ne connaît pas[^stream-unknown].

## Essayez

### Avec votre propre clé (facultatif)

Cette partie appelle la vraie API : elle demande une clé d'API, et les tokens consommés sont
facturés[^usage-billing]. Passez-la si vous n'avez pas de clé : la partie suivante et l'exercice
fonctionnent sans. Mettez la clé dans votre environnement, jamais dans votre code, et ne la mettez
jamais dans un commit.

```bash
export ANTHROPIC_API_KEY="your-key-here"
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
```

```python
import os

import anthropic

if "ANTHROPIC_API_KEY" not in os.environ:
    raise SystemExit("Set ANTHROPIC_API_KEY in your environment first.")

client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY dans l'environnement

history = [{"role": "user", "content": "What is a token?"}]
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
)
answer = "".join(block.text for block in message.content if block.type == "text")
print(answer)
print("stop_reason:", message.stop_reason)
print("tokens in:", message.usage.input_tokens, "out:", message.usage.output_tokens)

# Une question de suivi : renvoyer toute la conversation, avec la nouvelle question à la fin.
history += [
    {"role": "assistant", "content": answer},
    {"role": "user", "content": "And what is a context window?"},
]
with client.messages.stream(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # chaque morceau s'affiche dès qu'il arrive
print()
```

Votre réponse ne sera pas identique mot pour mot aux exemples ci-dessous, ses nombres de tokens non plus.

### Sans clé : lire une réponse d'exemple

Le dossier de la leçon contient l'exemple ci-dessus, une réponse coupée et un exemple de flux, dans
`exercise/tests/`. Depuis le dossier de la leçon, lancez :

```python
import json
from pathlib import Path

folder = Path("exercise/tests")
for name in ("sample_reply.json", "sample_cut_off.json"):
    reply = json.loads((folder / name).read_text(encoding="utf-8"))
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    print(name, "->", reply["stop_reason"], reply["usage"])
    print("  ", text)
```

La première réponse a utilisé 41 tokens d'entrée et 28 tokens de sortie, et elle s'est terminée par
`end_turn`. La seconde s'est terminée par `max_tokens` : Claude a écrit 16 tokens de sortie et s'est
arrêté au milieu d'une phrase, car il avait atteint la limite `max_tokens` de la requête. Son texte finit
par « that a model can », une phrase sans fin. Dans `sample_stream.json`, la même première réponse arrive
en 6 morceaux de texte.

## Erreurs fréquentes

- **Écrire la clé dans le code.** Le code se partage et finit dans des commits. Lisez plutôt la clé dans
  l'environnement[^start-env].
- **Croire que l'API se souvient.** Chaque appel est indépendant[^stateless]. Si vous n'envoyez que la
  nouvelle question, Claude n'a jamais vu la première.
- **Mettre le prompt système dans `messages`.** Les consignes valables dès le début vont dans le champ
  `system`, au premier niveau de la requête[^system-top].
- **Prendre `content[0]` pour la réponse.** La réponse, ce sont les blocs de texte, et le premier bloc peut
  être d'une autre sorte[^thinking-blocks].
- **Ignorer `stop_reason`.** Une réponse coupée par `max_tokens` ressemble à une réponse normale qui
  s'arrête au milieu d'une phrase. Vérifiez `stop_reason` avant de faire confiance au texte[^stop-every].
- **Additionner les nombres de tokens du flux.** Ceux de `message_delta` sont des totaux cumulés : gardez
  le dernier[^stream-cumulative].

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/first_call.py` et écrivez trois fonctions. Elles fonctionnent hors ligne, sur les
exemples de `exercise/tests/` :

- `build_request(model, max_tokens, turns, system=None)` renvoie le corps de la requête sous forme de
  dict. `turns` est une liste de paires `(role, text)`. N'ajoutez `system` que s'il y a un prompt système.
  Levez `ValueError` si `max_tokens` est inférieur à un ou n'est pas un entier, s'il n'y a aucun tour, si
  un rôle n'est ni `user` ni `assistant`, ou si le dernier tour n'est pas celui de l'utilisateur.
- `read_reply(response)` renvoie un dict avec `text` (tous les blocs de texte mis bout à bout),
  `stop_reason`, `input_tokens`, `output_tokens` et `cut_off`, qui vaut True quand la réponse s'est arrêtée
  à `max_tokens`.
- `join_stream(events)` renvoie le même dict à partir d'une liste d'événements de streaming.

### Lancer les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, comparez ensuite.

## Vérifiez vos acquis

Faites le quiz de cette leçon. Si une question vous résiste, relisez la partie « L'idée » sur les champs
de la requête, sur `stop_reason` ou sur le streaming.
