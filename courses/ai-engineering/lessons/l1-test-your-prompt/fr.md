# Tester votre prompt

## Ce que vous saurez faire

- Écrire un petit ensemble de cas de test pour un prompt, chacun avec une entrée et la réponse attendue.
- Noter les réponses du modèle avec du code : une correspondance exacte d'abord, puis un évaluateur plus
  tolérant.
- Lancer tous les cas, indiquer le taux de réussite et lire les cas en échec pour décider quoi corriger.

## L'idée

Dans la leçon précédente, vous avez écrit un prompt clair. Comment savoir s'il fonctionne ? La plupart des
gens l'essaient une fois, voient une bonne réponse et passent à autre chose. Cette réponse prouve très
peu. Elle vous renseigne sur une entrée, lors d'une exécution. Vos utilisateurs enverront des entrées que
vous n'avez jamais essayées. Et le même prompt peut répondre autrement à l'exécution suivante.
La *température* est un réglage qui fixe la part de hasard dans une réponse. La référence de l'API indique
que, même avec une température de 0.0, les résultats ne seront pas entièrement déterministes[^nondet] : le même prompt peut donner une autre réponse.
Sur les modèles récents, vous ne pouvez même pas la baisser : les modèles sortis après Claude Opus 4.6 ne
permettent pas de régler la température[^temperature].

Traitez donc un prompt comme du code : testez-le. Le guide d'Anthropic explique que construire une
application fondée sur un LLM (grand modèle de langage) commence par définir clairement vos critères de réussite, puis par concevoir
des évaluations qui mesurent les performances par rapport à ces critères[^cycle]. Sa présentation de
l'ingénierie de prompt suppose que vous avez déjà un moyen de tester votre prompt sur ces critères en le faisant
tourner, pas en devinant, avant de chercher à l'améliorer[^before].

Le test d'un prompt s'appelle une *évaluation*, ou *eval*. Une première évaluation a trois parties :

- **Les cas.** Des entrées, chacune avec la réponse attendue (on parle aussi de *réponse de référence*).
  Choisissez-les à l'image de votre trafic réel : le guide recommande de concevoir des évaluations qui
  ressemblent au mélange d'entrées que vos utilisateurs envoient vraiment, et ajoute de ne pas oublier les *cas limites* (*edge
  cases*)[^taskspecific]. Un cas limite est une entrée rare ou inhabituelle, à la frontière de ce que votre
  prompt doit traiter. Mettez ces entrées difficiles, pas seulement les faciles.
- **Un évaluateur.** Du code qui compare la réponse du modèle à la réponse attendue et dit réussite ou
  échec. Le guide recommande de formuler les questions de façon à permettre une notation automatique[^automate].
  Il présente la notation par le code comme la plus rapide et la plus fiable, tout en notant qu'elle manque
  de nuance : elle ne saisit pas les subtilités de sens des jugements complexes[^codegrade].
- **Le taux de réussite.** La part des cas réussis : le nombre de cas réussis divisé par le nombre total de
  cas.

Voici un petit exemple. Le prompt demande au modèle de classer un avis produit comme positif, négatif ou
mitigé. Un des cas est l'avis « Great screen, terrible battery. » avec la réponse attendue « mixed ». Si
le modèle répond « mixed », le cas réussit.

L'évaluateur le plus simple est la *correspondance exacte* : la réponse doit être exactement la chaîne
attendue. Il est strict. Il refuse « Mixed » et « mixed. », alors qu'une personne accepterait les deux. Un
évaluateur *tolérant* nettoie les deux chaînes avant de les comparer. Le guide décrit les évaluations par
correspondance exacte comme vérifiant si la sortie correspond à une réponse correcte définie à l'avance,
généralement après normalisation des espaces et de la casse[^exact] : espaces, tabulations et retours à la ligne
traités de la même façon, majuscules et minuscules confondues. Dans le guide, la « correspondance
exacte » inclut donc souvent ce nettoyage ; cette leçon donne un nom à chacune des deux étapes pour que vous
voyiez la différence. L'évaluateur tolérant de cette leçon ignore aussi un point final.

La tolérance a ses limites. Un évaluateur qui accepte toute réponse *contenant* le mot « positive »
accepterait aussi « not positive ». Un évaluateur trop permissif vous donne un taux de réussite élevé qui
ne veut rien dire. Une vérification « contient » n'est pas toujours une erreur : le guide cite la
*correspondance de chaîne* (*string match*), qui vérifie qu'une expression clé figure dans la
sortie[^stringmatch]. Elle peut convenir à une réponse longue qui doit mentionner une expression clé. Pour
des étiquettes courtes comme positive ou not positive, elle est risquée.

Beaucoup de cas simples valent mieux que quelques cas parfaits : le guide indique que davantage de
questions notées automatiquement, chacune un peu moins informative, valent mieux que moins de questions
notées à la main avec soin[^volume]. Commencez petit, et ajoutez un cas
chaque fois que vous découvrez un nouvel échec.

## Essayez

Enregistrez ce code dans `try_eval.py` et lancez `python3 try_eval.py`. Le modèle est ici un *substitut*
(*stand-in*) : une fonction qui renvoie des réponses inventées, dans le style des réponses d'un modèle. Il
ne demande ni réseau ni clé, et donne le même résultat à chaque exécution : vous voyez exactement ce que
fait chaque évaluateur.

```python
"""Test a prompt on ten cases with two graders. No network: the model is a stand-in."""

PROMPT = (
    "Classify the sentiment of this product review as positive, negative or mixed. "
    "Answer with one word.\n\nReview: {review}"
)

CASES = [
    {"input": "Arrived on time and works perfectly.", "expected": "positive"},
    {"input": "Broke after two days.", "expected": "negative"},
    {"input": "Great screen, terrible battery.", "expected": "mixed"},
    {"input": "Exactly what I ordered.", "expected": "positive"},
    {"input": "The worst purchase I have made.", "expected": "negative"},
    {"input": "Fast delivery, but the box was damaged.", "expected": "mixed"},
    {"input": "I love it.", "expected": "positive"},
    {"input": "Oh great, it stopped working again.", "expected": "negative"},
    {"input": "Not bad at all.", "expected": "positive"},
    {"input": "It does the job, but I expected more.", "expected": "mixed"},
]

# Made-up answers in the style of a model's replies, so this example gives the same result on every run.
CANNED = {
    "Arrived on time and works perfectly.": "positive",
    "Broke after two days.": "negative",
    "Great screen, terrible battery.": "mixed",
    "Exactly what I ordered.": "Positive",
    "The worst purchase I have made.": "negative.",
    "Fast delivery, but the box was damaged.": "Mixed\n",
    "I love it.": "positive",
    "Oh great, it stopped working again.": "positive",
    "Not bad at all.": " POSITIVE ",
    "It does the job, but I expected more.": "The sentiment is mixed.",
}


def stand_in_model(review):
    """Plays the model. A real one would receive PROMPT.format(review=review)."""
    return CANNED[review]


def exact_match(output, expected):
    return output == expected


def normalized_match(output, expected):
    def clean(text):
        return " ".join(text.split()).lower().rstrip(".")

    return clean(output) == clean(expected)


def run_eval(cases, model, grader):
    failures = []
    for case in cases:
        output = model(case["input"])
        if not grader(output, case["expected"]):
            failures.append({**case, "output": output})
    passed = len(cases) - len(failures)
    return passed / len(cases), failures


if __name__ == "__main__":
    for name, grader in [("exact match", exact_match), ("normalized match", normalized_match)]:
        rate, failures = run_eval(CASES, stand_in_model, grader)
        print(f"{name}: {len(CASES) - len(failures)} of {len(CASES)} passed, pass rate {rate:.0%}")
        for failure in failures:
            print(f"  FAIL {failure['input']!r}: expected {failure['expected']!r}, got {failure['output']!r}")
```

Il affiche :

```text
exact match: 4 of 10 passed, pass rate 40%
  FAIL 'Exactly what I ordered.': expected 'positive', got 'Positive'
  FAIL 'The worst purchase I have made.': expected 'negative', got 'negative.'
  FAIL 'Fast delivery, but the box was damaged.': expected 'mixed', got 'Mixed\n'
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'Not bad at all.': expected 'positive', got ' POSITIVE '
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
normalized match: 8 of 10 passed, pass rate 80%
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
```

### Lire les résultats

Avec la correspondance exacte, 4 cas sur 10 réussissent, soit un taux de réussite de 40 %. La plupart de
ces échecs ne sont pas de mauvaises réponses : « Positive » et « negative. » portent la bonne étiquette,
sous une forme un peu différente.

Avec l'évaluateur tolérant, 8 cas sur 10 réussissent, soit un taux de réussite de 80 %. Les deux échecs
restants sont réels, et ce sont deux problèmes différents :

- « Oh great, it stopped working again. » est sarcastique, et le modèle s'est trompé d'étiquette.
  L'exemple d'évaluation d'Anthropic classe lui-même le sarcasme parmi les cas limites[^sarcasm]. La
  correction se fait dans le prompt, par exemple une phrase sur le sarcasme, puis vous relancez
  l'évaluation.
- « The sentiment is mixed. » porte la bonne étiquette, mais le prompt demandait un seul mot. Rendez le
  prompt plus strict sur le format avant de rendre l'évaluateur plus permissif.

Regardez le premier cas seul : une réponse parfaite. Si vous n'aviez essayé que celui-là, vous n'auriez vu
aucun problème.

### Brancher un vrai modèle

Le SDK Python officiel donne accès à l'API Claude depuis Python[^sdk]. Si vous avez une clé d'API, vous
pouvez remplacer le substitut par un vrai appel. Le nom de modèle ci-dessous est l'un des identifiants d'API listés dans la
présentation des modèles d'Anthropic ; les noms de modèles changent, vérifiez donc cette liste avant de
lancer le code[^model]. Comme dans votre premier appel à l'API, le code prend le bloc de texte de la
réponse, pas `content[0]`, et laisse de la marge dans `max_tokens`.

Collez tout le bloc à la fin de `try_eval.py`. Ce fichier contient déjà `CASES`, `run_eval` et
`normalized_match` ; le bloc apporte le reste : `import anthropic`, `client`, `PROMPT` et `ask_claude`,
puis lance l'évaluation et affiche le taux de réussite et les cas en échec.

```python
import anthropic

client = anthropic.Anthropic()  # reads your key from the ANTHROPIC_API_KEY environment variable

PROMPT = (
    "Classify the sentiment of this product review as positive, negative or mixed. "
    "Answer with one word.\n\nReview: {review}"
)


def ask_claude(review):
    message = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT.format(review=review)}],
    )
    return next(block.text for block in message.content if block.type == "text")


if __name__ == "__main__":
    rate, failures = run_eval(CASES, ask_claude, normalized_match)
    print(f"claude: {len(CASES) - len(failures)} of {len(CASES)} passed, pass rate {rate:.0%}")
    for failure in failures:
        print(f"  FAIL {failure['input']!r}: expected {failure['expected']!r}, got {failure['output']!r}")
```

Lancez-le plusieurs fois. Avec un vrai modèle, le taux de réussite peut varier d'une exécution à l'autre :
une raison de plus de ne pas se fier à une seule réponse.

## Erreurs fréquentes

- **« Ça a marché quand je l'ai essayé. »** Une entrée, une exécution. Testez un ensemble de cas et
  regardez le taux de réussite.
- **Uniquement des cas faciles.** Si tous les cas sont évidents, un taux de réussite élevé ne vous apprend
  rien. Ajoutez les entrées qui vous inquiètent : sarcasme, avis mitigés, textes très courts ou très longs.
- **Modifier les réponses attendues jusqu'à ce que les tests passent.** La réponse attendue, c'est ce dont
  vous avez besoin, décidé avant de voir la sortie. Ne la changez que si vous découvrez qu'elle était
  fausse.
- **Un évaluateur trop strict ou trop permissif.** Trop strict, les écarts de format ressemblent à de
  mauvaises réponses. Trop permissif, de mauvaises réponses passent. Lisez aussi quelques cas réussis, pas
  seulement les échecs.
- **Ne donner que le chiffre.** Le taux de réussite dit combien de fois ; les cas en échec disent pourquoi.
- **Croire que la correspondance exacte suffit à toutes les tâches.** Elle convient aux réponses courtes et
  tranchées, comme des étiquettes. Pour les réponses qui demandent du jugement, des leçons ultérieures
  utilisent un modèle comme évaluateur : le guide décrit la notation par un LLM comme rapide et souple,
  capable de passer à l'échelle et adaptée aux jugements complexes, et ajoute : testez d'abord sa
  fiabilité, puis passez à l'échelle[^llmgrade]. Passer à l'échelle, c'est ici l'utiliser sur beaucoup plus de cas.

## Votre exercice

Ouvrez `exercise/starter/evaluate.py`. Il contient quelques cas, un modèle substitut et trois fonctions à
écrire :

- `exact_match(output, expected)` : vrai seulement si les deux chaînes sont identiques.
- `normalized_match(output, expected)` : vrai si elles sont égales une fois ignorés les majuscules et
  minuscules, les espaces en trop, et un point ou un point d'exclamation final. « not positive » doit
  toujours échouer face à « positive ». L'évaluateur d'« Essayez » n'ignore que le point ; le vôtre ignore
  aussi un « ! » final.
- `run_eval(cases, model, grader)` : interrogez le modèle une fois par cas, dans l'ordre, notez chaque
  réponse avec `grader(output, expected)` et renvoyez une paire : le taux de réussite (cas réussis divisés
  par le nombre total de cas) et la liste des cas en échec. Chaque cas en échec est un dictionnaire avec
  `input`, `expected`, `output` et `error`
  (`error` vaut `None` quand le modèle a répondu).

Deux règles de plus, parce que les vraies évaluations les rencontrent :

- Une liste de cas vide lève `ValueError`. Un taux de réussite calculé sur aucun cas ne veut rien dire.
- Si le modèle lève une exception (une erreur Python) sur un cas, ce cas échoue avec `output` à `None` et `error` contenant le
  message, puis l'exécution continue avec le cas suivant. Un vrai appel d'API peut échouer ; un seul échec
  ne doit pas arrêter toute l'évaluation.

En Python, `try` et `except` permettent d'attraper cette erreur. Le code dans `try` s'exécute ; s'il lève
une erreur, Python saute à `except`, et `exc` est l'erreur. `str(exc)` est son message :

```python
try:
    output = model(case["input"])  # l'appel qui peut échouer
    error = None
except Exception as exc:
    output, error = None, str(exc)  # pas de réponse, on garde le message
```

Lancez les tests depuis le dossier de départ :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que vos fonctions ne sont pas écrites. Quand ils passent, lancez `python3 evaluate.py`
pour voir le taux de réussite de chaque évaluateur, puis essayez vos propres cas. Pour essayer un vrai modèle, ne collez rien dans `evaluate.py` : les tests
l'importent, et ils auraient alors besoin d'`anthropic` et d'une clé. Créez `real_eval.py` à côté, commencez-le
par `from evaluate import CASES, run_eval, normalized_match`, collez sous cette ligne tout le bloc de
« Brancher un vrai modèle », et lancez `python3 real_eval.py` (il faut votre clé d'API).
Une solution complète se trouve dans `exercise/solution/` : ouvrez-la après avoir essayé.

## Vérifiez vos acquis

Répondez au quiz de cette leçon. S'il vous semble difficile, relisez « L'idée », puis comparez les deux
sorties d'« Essayez » cas par cas.

[^nondet]: Create a Message (Claude API reference), <https://platform.claude.com/docs/en/api/messages/create>
[^temperature]: Create a Message (Claude API reference), <https://platform.claude.com/docs/en/api/messages/create>
[^cycle]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^before]: Prompt engineering overview (Claude Platform Docs), <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview>
[^taskspecific]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^automate]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^codegrade]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^exact]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^stringmatch]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^volume]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^sarcasm]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
[^sdk]: anthropics/anthropic-sdk-python (README), <https://github.com/anthropics/anthropic-sdk-python>
[^model]: Models overview (Claude Platform Docs), <https://platform.claude.com/docs/en/about-claude/models/overview>
[^llmgrade]: Define success criteria and build evaluations (Claude Platform Docs), <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests>
