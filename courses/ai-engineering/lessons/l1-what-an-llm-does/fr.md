# Ce que fait un LLM

## Ce que vous saurez faire

- Expliquer avec des mots simples ce que fait un grand modèle de langage quand il écrit une réponse.
- Dire ce qu'il ne sait pas faire : connaître ce qui s'est passé après la fin de ses données
  d'entraînement, et avoir toujours raison.
- Dire ce que ces limites impliquent pour les logiciels que vous construisez avec lui.

Cette leçon suppose le Niveau 0 acquis : vous savez utiliser un terminal et lancer un petit programme Python.

## L'idée

Un grand modèle de langage (LLM, pour *large language model*) est un programme entraîné sur une très
grande quantité de texte. Anthropic décrit les LLM ainsi : ces modèles sont « entraînés sur de vastes
quantités de données textuelles et peuvent générer un texte semblable à celui d'un humain »[^llm].

Sa compétence de base est un petit pas, répété. À partir du texte déjà écrit, il devine ce qui vient
ensuite. Quand un modèle comme celui sur lequel repose Claude est entraîné pour la première fois (on parle
de *pré-entraînement*, ou *pretraining*), il apprend « à prédire le mot suivant, à partir du contexte qui
le précède dans le document »[^pretraining].

Pour être exact, le modèle ne travaille pas avec des mots mais avec des *tokens*. Un token est un morceau
de texte : un mot entier, une partie de mot, un caractère, voire un octet[^tokens]. La prochaine leçon
porte sur les tokens. Dans celle-ci, « le mot suivant » suffit.

Prenez le début d'une phrase : « Il était une ... ». Vous avez sans doute pensé à « fois ». Vous ne
l'avez cherché nulle part : vous avez déjà lu et entendu cette tournure bien des fois. Un modèle de langage
fait quelque chose de semblable, à une échelle immense. Il écrit toute une réponse en prédisant un
morceau, en l'ajoutant au texte, puis en prédisant le morceau suivant.

Claude est plus qu'un simple prédicteur brut : Anthropic précise qu'il « a déjà été affiné (*fine-tuned*)
pour être un assistant utile »[^finetune]. L'affinage (*fine-tuning*) est un entraînement supplémentaire
d'un modèle déjà pré-entraîné. Il est nécessaire : Anthropic note que les modèles seulement pré-entraînés
« ne sont pas naturellement doués pour répondre aux questions ou suivre des instructions », et l'affinage
est l'un des moyens de les améliorer[^pretrained]. Cet entraînement supplémentaire ne change pas le mécanisme de base : la réponse est toujours produite à partir
des motifs que le modèle a appris. Deux limites en découlent.

**Première limite : aucune connaissance en temps réel.** Un modèle apprend à partir de données collectées
jusqu'à une certaine date : sa *date limite des données d'entraînement* (*training data cutoff*). La page
de présentation des modèles d'Anthropic indique cette date pour chaque modèle actuel[^models]. Elle donne
juin 2026 pour Claude Fable 5.1, Claude Opus 5.5 et Claude Sonnet 5.5, et juillet 2025 pour Claude Haiku 4.5[^models].
Sur tout ce qui s'est passé après cette date, le modèle n'a lu aucun texte : il n'a aucun motif sur
lequel s'appuyer.

La même page donne aussi une *date limite des connaissances fiables* (*reliable knowledge cutoff*), qui
peut être plus ancienne : février 2025 pour Claude Haiku 4.5[^reliable]. Ne comptez donc pas sur un modèle
pour bien connaître les derniers mois avant sa date limite des données d'entraînement.

Le modèle ne peut travailler avec des faits plus récents que si vous les lui donnez. Vous pouvez coller
un document dans le *prompt* (le texte que vous envoyez au modèle). Votre code peut aller chercher les documents utiles et les transmettre avec
la question ; le glossaire d'Anthropic explique que cela « permet au modèle d'accéder à des informations
au-delà de ses données d'entraînement et de les utiliser »[^rag]. Vous pouvez aussi lui donner un outil,
comme la recherche web, qui permet à Claude de « répondre aux questions avec des informations à jour,
au-delà de sa date limite de connaissances »[^websearch].

**Seconde limite : des erreurs affirmées avec assurance.** Un motif fréquent n'est pas un fait vrai.
Anthropic prévient que même les modèles les plus avancés « peuvent parfois générer un texte factuellement
faux ou incohérent avec le contexte fourni », et appelle cela une *hallucination*[^halluc]. Une réponse
fausse peut sortir aussi fluide et aussi assurée qu'une réponse juste : le ton n'est pas une preuve.

**Pourquoi c'est important pour vous, ingénieur.** Traitez ce qu'écrit un modèle comme un brouillon à
vérifier, pas comme le résultat d'une requête dans une base de données. Mettez dans le *prompt* les faits
dont il a besoin, et demandez-lui de s'en tenir à eux : Anthropic suggère de « demander explicitement à
Claude de n'utiliser que les informations des documents fournis et non ses connaissances générales »[^halluc-docs].
Laissez-le dire qu'il ne sait pas ; le même guide conseille de « donner explicitement à Claude la
permission d'admettre son incertitude »[^halluc-idk]. Et gardez une étape de vérification dans votre code
ou votre façon de travailler : ces techniques réduisent les hallucinations, mais « ne les éliminent pas
entièrement »[^halluc-limit].

## Essayez

Voici un prédicteur du mot suivant assez petit pour être lu d'une traite. Il apprend à partir d'un petit
*corpus* (le texte sur lequel il est entraîné) : quelques messages d'une discussion d'équipe. Il compte
quel mot vient juste après quel autre, puis prédit le mot qui est venu ensuite le plus souvent.

Les messages sont en anglais, car le code est le même dans toutes les langues du cours. Enregistrez ce
fichier sous le nom `predict.py` et lancez `python3 predict.py` (il faut Python 3.10 ou plus récent, pour
`pairwise`) :

```python
from collections import Counter
from itertools import pairwise

corpus = """
the team meeting is on monday .
remember the meeting is on monday .
the meeting is on monday as usual .
news the meeting moved and is on friday now .
"""

words = corpus.lower().split()
pairs = Counter(pairwise(words))  # (mot, mot suivant) -> nombre de fois


def predict(word):
    followers = {b: n for (a, b), n in pairs.items() if a == word}
    if not followers:
        return None  # jamais vu : aucun motif à suivre
    return max(followers, key=followers.get)  # en cas d'égalité : le premier vu


print("after 'on':", {b: n for (a, b), n in pairs.items() if a == "on"})

sentence = ["meeting"]
for _ in range(4):
    sentence.append(predict(sentence[-1]))
print(" ".join(sentence))

print("after 'tuesday':", predict("tuesday"))
```

Vous devriez voir :

```
after 'on': {'monday': 3, 'friday': 1}
meeting is on monday .
after 'tuesday': None
```

Regardez ce qui s'est passé. Dans ce corpus, `monday` suit `on` 3 fois, et `friday`, 1 fois seulement.
Alors, en partant de `meeting`, le prédicteur écrit « meeting is on monday . », un mot après l'autre. La
phrase est fluide, et elle est fausse : le dernier message dit que la réunion a été déplacée au vendredi.
Le prédicteur n'a rien vérifié. Il a suivi le motif le plus fréquent.

Remarquez deux autres choses. D'abord, le point est ici un « mot » : le prédicteur a donc aussi appris où
finissent les phrases. Ensuite, il n'a rien à dire sur `tuesday`, parce que ce mot n'est pas dans son
corpus. Imaginez maintenant que le dernier message ait été envoyé après la collecte du corpus : le
prédicteur ne saurait même pas que le vendredi est possible. C'est une date limite des données
d'entraînement en miniature.

Un vrai LLM est bien plus capable que cela : il apprend sur énormément plus de texte et utilise bien plus
de contexte que le seul mot précédent[^pretraining]. Mais la leçon reste valable. Il écrit ce que ses
motifs rendent probable, et probable ne veut pas dire vrai.

## Erreurs fréquentes

- **« Le modèle va chercher la réponse. »** Il ne consulte pas un stock de faits. Il prédit le morceau de
  texte suivant à partir de ce qui précède[^pretraining]. Pour qu'il s'appuie sur des faits, donnez-lui
  les faits[^rag].
- **« Il a l'air sûr de lui, donc il a raison. »** Un texte fluide et assuré peut être factuellement
  faux[^halluc]. Vérifiez ce qui compte, quel que soit le ton.
- **« Il connaît l'actualité du jour. »** Sans documents ni outils, il n'a aucune information au-delà de
  sa date limite des données d'entraînement[^websearch]. Interrogez-le sur une version, un prix ou un
  événement récent, et il risque de répondre à partir de motifs plus anciens.
- **« Une température à zéro le rend exact. »** La température est un réglage qui « contrôle le caractère
  aléatoire des prédictions d'un modèle »[^temperature-def] : à quel point le choix du mot suivant est
  aléatoire. Les températures basses donnent des sorties « qui s'en tiennent aux formulations et aux
  réponses les plus probables »[^temperature]. Le plus probable, c'est exactement ce que choisit toujours
  notre petit prédicteur, et il a quand même répondu lundi. Et « même avec une température réglée à 0, les
  résultats ne seront pas entièrement déterministes »[^temperature-zero] : la même question peut recevoir
  des réponses différentes.
- **« Quelques astuces de prompt suppriment les hallucinations. »** Elles les réduisent ; le guide vous
  conseille de « toujours valider les informations critiques, surtout pour les décisions à fort
  enjeu »[^halluc-validate].

## Votre exercice

Construisez le prédicteur vous-même, sous forme de deux fonctions que vous pouvez tester. Le fichier de
départ est `exercise/starter/predictor.py`. Écrivez :

- `build_counts(text)` : mettez le texte en minuscules, découpez-le sur les espaces, et renvoyez un
  dictionnaire qui associe à chaque mot un dictionnaire des mots venus juste après lui, avec leur nombre.
- `next_word(counts, word)` : renvoyez le mot qui est venu le plus souvent après `word` (comparez en
  minuscules). En cas d'égalité, renvoyez le premier dans l'ordre alphabétique. Si rien n'a jamais suivi
  `word`, renvoyez `None`.

Depuis le dossier de la leçon, allez dans le dossier de départ et lancez les tests :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que vos deux fonctions ne marchent pas. Un des tests enchaîne vos prédictions à partir
de `meeting`, comme dans la partie Essayez. Quand tout passe, comparez votre code avec `exercise/solution/predictor.py`.

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles vous semblent difficiles, relisez les deux limites dans
L'idée et la fin de la partie Essayez.

[^llm]: Anthropic, Glossary, « LLM ».
[^pretraining]: Anthropic, Glossary, « Pretraining ».
[^pretrained]: Anthropic, Glossary, « Pretraining ».
[^tokens]: Anthropic, Glossary, « Tokens ».
[^finetune]: Anthropic, Glossary, « Fine-tuning ».
[^rag]: Anthropic, Glossary, « RAG (Retrieval augmented generation) ».
[^temperature]: Anthropic, Glossary, « Temperature ».
[^temperature-def]: Anthropic, Glossary, « Temperature ».
[^temperature-zero]: Anthropic, Glossary, « Temperature ».
[^models]: Anthropic, Models overview.
[^reliable]: Anthropic, Models overview.
[^websearch]: Anthropic, Web search tool.
[^halluc]: Anthropic, Reduce hallucinations.
[^halluc-docs]: Anthropic, Reduce hallucinations, « External knowledge restriction ».
[^halluc-idk]: Anthropic, Reduce hallucinations, « Allow Claude to say I don't know ».
[^halluc-limit]: Anthropic, Reduce hallucinations.
[^halluc-validate]: Anthropic, Reduce hallucinations.
