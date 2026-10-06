# Les tokens, la fenêtre de contexte et le coût

## Ce que vous saurez faire

- Expliquer ce qu'est un token, et pourquoi on compte des tokens plutôt que des mots.
- Dire ce qui remplit la fenêtre de contexte d'une requête, et vérifier qu'une requête laisse de la place pour la réponse.
- Lire les nombres de tokens qu'indique une réponse, et estimer le coût d'un appel et d'une charge de travail entière.

## L'idée

Un modèle ne lit ni des mots ni des lettres. Il lit des **tokens**. Le glossaire d'Anthropic les
décrit comme les plus petites unités d'un modèle de langage : un token peut correspondre à un mot, à
un morceau de mot, à un caractère, voire à un octet[^tokens]. Un mot courant tient parfois en un seul
token ; un mot rare, un nom propre ou une ligne de code est souvent découpé en plusieurs.

La quantité de texte que contient un token dépend du texte. Pour Claude, un token représente environ
3,5 caractères de texte anglais, et ce chiffre varie selon la langue[^chars]. Si vous écrivez en
français ou en arabe, ne supposez pas le ratio de l'anglais : mesurez votre propre texte.

Le nombre dépend aussi du modèle. Le tokenizer, la partie qui découpe le texte en tokens, peut changer
d'un modèle à l'autre : les modèles Claude 4.7 et suivants en utilisent un plus récent, et le même
texte y donne environ 30 % de tokens de plus que sur les modèles antérieurs[^tokenizer]. Un nombre de
tokens est toujours un nombre pour un modèle donné.

**La fenêtre de contexte** est tout le texte auquel le modèle peut se référer pendant qu'il génère
une réponse, y compris cette réponse elle-même[^window]. Voyez-la comme la mémoire de travail du
modèle pour une requête. Ce n'est pas ce que le modèle a appris pendant son entraînement : c'est ce
que vous envoyez maintenant, plus ce qu'il écrit en retour.

Tout ce qui est dans la requête compte : le prompt système (les instructions que vous donnez au modèle
avant la conversation), chaque message et les éventuelles définitions d'outils[^everything]. La
réponse que Claude écrit compte aussi[^output]. Entrée et sortie se partagent la même fenêtre.

La fenêtre a une taille, mesurée en tokens. Beaucoup de modèles actuels, dont Claude Opus 5.5 et
Claude Sonnet 5.5, ont une fenêtre de contexte d'un million de tokens (notée 1M)[^sizes-1m].
D'autres, comme Claude Sonnet 4.5, ont 200K tokens[^sizes-200k]. Si l'entrée seule dépasse la
fenêtre, l'API refuse la requête avec une erreur 400[^too-long]. Une fenêtre plus grande ne garantit
pas de meilleures réponses pour autant : plus le nombre de tokens augmente, plus la précision et le
rappel se dégradent, ce qu'Anthropic appelle le *context rot*[^rot].

**Tokens d'entrée et tokens de sortie.** Les tokens d'entrée sont tout ce que vous envoyez. Les
tokens de sortie sont ce que Claude écrit. Vous ne pouvez pas connaître d'avance la longueur de la
réponse, mais vous pouvez la plafonner : `max_tokens` est le nombre maximal de tokens à générer avant
de s'arrêter, et le modèle peut s'arrêter avant[^max-tokens].

**L'usage.** Inutile de deviner ce qu'un appel a consommé : chaque réponse l'indique dans son champ
`usage`[^usage]. `input_tokens` est le nombre de tokens d'entrée utilisés[^usage-in], et
`output_tokens` le nombre de tokens de sortie utilisés[^usage-out]. Dans une réponse, cela ressemble
à ceci :

```json
"usage": {"input_tokens": 12, "output_tokens": 6}
```

**Le coût.** Anthropic facture séparément les tokens d'entrée et les tokens de sortie, en dollars
américains[^usd], par million de tokens, noté MTok[^mtok]. Un appel coûte donc :

```text
cost = input_tokens × input price / 1,000,000  +  output_tokens × output price / 1,000,000
```

Les prix changent. Le jour où cette leçon a été vérifiée, la page des tarifs indiquait ces prix, en
dollars par MTok :

| Modèle | Entrée | Sortie |
|---|---|---|
| Claude Opus 5.5[^price-opus] | 4 | 20 |
| Claude Sonnet 5.5[^price-sonnet] | 2 | 10 |
| Claude Haiku 4.5[^price-haiku] | 1 | 5 |

Le prix d'un token n'augmente pas avec la taille de la requête : une très grosse requête est facturée
au même prix par token qu'une petite[^flat].

Un exemple chiffré.
Sur Claude Sonnet 5.5, un appel qui envoie 2 000 tokens d'entrée et reçoit 500 tokens de sortie coûte 0,009 $.
Les 500 tokens de sortie coûtent à eux seuls 0,005 $ : un cinquième des tokens, mais plus de la moitié du coût.
Une charge de travail, ce sont beaucoup d'appels : 10 000 appels de ce type par jour coûtent 90 $ par jour.
Les mêmes appels sur Claude Haiku 4.5 coûtent 45 $ par jour.
C'est ainsi que l'on compare des modèles avant de choisir : mêmes nombres de tokens, prix différents.

## Essayez

### Compter les tokens avant d'envoyer

L'API peut compter les tokens d'une requête avant que vous ne l'envoyiez[^count]. Vous configurerez
une clé d'API dans les leçons suivantes ; si vous en avez déjà une, ce code compte les tokens d'entrée
d'une courte requête (il faut `pip install anthropic`) :

```python
import anthropic

client = anthropic.Anthropic()  # lit votre clé dans la variable d'environnement ANTHROPIC_API_KEY
count = client.messages.count_tokens(
    model="claude-sonnet-5-5",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "How many tokens is this sentence?"}],
)
print(count.input_tokens)
```

Ce nombre est une estimation[^estimate], et il ne couvre que l'entrée : la sortie n'existe pas encore.
Le comptage est gratuit, mais il a ses propres limites de débit[^count-free]. Les nombres exacts que
vous payez sont ceux du champ `usage` de la vraie réponse.

### Estimer le coût d'un appel

Ce programme tourne sans clé et sans réseau. Il prend l'`usage` d'une réponse et la table des prix,
et affiche le coût d'un appel et celui de nombreux appels :

```python
import json

# Dollars américains par million de tokens (MTok), recopiés de la page des tarifs d'Anthropic.
# Les prix changent : relisez la page avant de vous y fier.
PRICES = {
    "claude-opus-5-5": {"input": 4, "output": 20},
    "claude-sonnet-5-5": {"input": 2, "output": 10},
    "claude-haiku-4-5": {"input": 1, "output": 5},
}

# La partie usage d'une réponse, sous la forme que donne l'API (les nombres sont un exemple).
response = json.loads('{"usage": {"input_tokens": 2000, "output_tokens": 500}}')
usage = response["usage"]


def call_cost(usage, price):
    """Dollars for one call: each kind of token at its own price, per million tokens."""
    return (usage["input_tokens"] * price["input"] + usage["output_tokens"] * price["output"]) / 1_000_000


for model, price in PRICES.items():
    one = call_cost(usage, price)
    print(f"{model}: one call ${one:.4f}, 10,000 calls ${one * 10_000:.2f}")

# Une estimation grossière, pour du texte anglais seulement : environ 3,5 caractères par token.
text = "x" * 7000  # tient lieu de 7 000 caractères de texte anglais
print("rough guess:", round(len(text) / 3.5), "tokens")
```

Enregistrez-le sous `estimate.py` et lancez `python3 estimate.py` :

```text
claude-opus-5-5: one call $0.0180, 10,000 calls $180.00
claude-sonnet-5-5: one call $0.0090, 10,000 calls $90.00
claude-haiku-4-5: one call $0.0045, 10,000 calls $45.00
rough guess: 2000 tokens
```

La dernière ligne est une estimation grossière : 7 000 caractères de texte anglais font environ 2 000 tokens.
Servez-vous-en pour avoir un ordre de grandeur, jamais pour remplir un budget au token près. Changez
les nombres de l'`usage` et voyez combien les tokens de sortie font plus bouger le coût que les tokens
d'entrée.

## Erreurs fréquentes

- **« Un token, c'est un mot. »** Un token peut être un mot, un morceau de mot, un caractère ou un
  octet[^tokens]. Comptez des tokens, pas des mots.
- **« La fenêtre de contexte, c'est mon prompt. »** La réponse est aussi dans la fenêtre[^output]. Une
  requête dont l'entrée remplit presque la fenêtre laisse peu de place à la réponse.
- **« L'entrée et la sortie coûtent pareil. »** Dans la table des prix ci-dessus, un token de sortie
  coûte cinq fois plus cher qu'un token d'entrée[^price-opus][^price-sonnet][^price-haiku]. Les
  longues réponses sont souvent la partie chère.
- **« Un nombre mesuré sur un modèle vaut pour un autre. »** Le tokenizer change d'un modèle à
  l'autre, et le même texte peut donner environ 30 % de tokens de plus sur les modèles récents[^tokenizer].
  Recomptez pour le modèle que vous allez utiliser.
- **« `count_tokens` me donne la facture. »** C'est une estimation de l'entrée[^estimate]. Le champ
  `usage` de la réponse indique ce qui a vraiment été consommé[^usage].
- **« Ces prix sont fixes. »** Ils changent : relisez la page des tarifs avant de prévoir un budget.
  Certaines options les modifient aussi : par exemple, la Batch API accorde une remise de 50 % sur les
  tokens d'entrée et de sortie[^batch]. D'autres leçons reviendront sur le coût.

## Votre exercice

Ouvrez `exercise/starter/cost.py` et écrivez cinq petites fonctions. Les prix sont en dollars par
million de tokens, comme `{"input": 2, "output": 10}` ; l'usage est l'`usage` d'une réponse, comme
`{"input_tokens": 2000, "output_tokens": 500}`.

- `call_cost(usage, price)` : le coût d'un appel, en dollars.
- `workload_cost(usage, price, calls)` : le coût de `calls` appels avec cet usage.
- `total_usage(responses)` : la somme des `usage` d'une liste de réponses enregistrées.
- `leaves_room(input_tokens, max_tokens, context_window)` : `True` quand l'entrée plus la plus longue
  réponse que vous autorisez tiennent dans la fenêtre.
- `rough_tokens(text, chars_per_token=3.5)` : l'estimation grossière de « Essayez », arrondie à un
  nombre entier.

Refusez un nombre négatif avec une `ValueError`. Le fichier `prices.json` voisin contient la table des
prix de cette leçon ; `python3 cost.py` l'utilise une fois vos fonctions écrites.

Lancez les tests depuis le dossier de départ :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que vos fonctions ne sont pas justes. Une solution se trouve dans
`exercise/solution/` ; essayez d'abord seul.

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles vous semblent difficiles, relisez « L'idée » et
refaites l'exemple chiffré à la main : tokens d'entrée et tokens de sortie, chacun à son prix par
million.

[^tokens]: Anthropic, Glossary.
[^chars]: Anthropic, Glossary.
[^tokenizer]: Anthropic, Token counting.
[^window]: Anthropic, Context windows.
[^everything]: Anthropic, Context windows.
[^output]: Anthropic, Context windows.
[^sizes-1m]: Anthropic, Context windows.
[^sizes-200k]: Anthropic, Context windows.
[^too-long]: Anthropic, Context windows.
[^rot]: Anthropic, Context windows.
[^max-tokens]: Anthropic, Create a Message (référence de l'API).
[^usage]: Anthropic, Context windows.
[^usage-in]: SDK Python d'Anthropic, types/usage.py.
[^usage-out]: SDK Python d'Anthropic, types/usage.py.
[^usd]: Anthropic, Pricing.
[^mtok]: Anthropic, Pricing.
[^price-opus]: Anthropic, Pricing.
[^price-sonnet]: Anthropic, Pricing.
[^price-haiku]: Anthropic, Pricing.
[^flat]: Anthropic, Pricing.
[^count]: Anthropic, Token counting.
[^estimate]: Anthropic, Token counting.
[^count-free]: Anthropic, Token counting.
[^batch]: Anthropic, Pricing.
