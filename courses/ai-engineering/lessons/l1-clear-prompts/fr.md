# Écrire des prompts clairs

## Ce que vous saurez faire

- Transformer une demande vague en un prompt qui énonce la tâche directement et donne à Claude le contexte qui lui manque.
- Ajouter des exemples et dire précisément quelle forme la réponse doit avoir.
- Séparer les parties d'un prompt avec des balises XML, et omettre celles dont vous n'avez pas besoin.

## L'idée

Un *prompt* est le texte que vous envoyez au modèle : vos instructions, plus tout ce dont le modèle a
besoin pour les suivre. Dans la leçon précédente, vous en avez envoyé un via l'API. Cette leçon porte
sur ce qu'on met dedans.

Claude ne voit que le prompt. Il ne connaît ni votre produit, ni vos utilisateurs, ni ce que votre
code fera de sa réponse. Le guide d'Anthropic vous invite à voir Claude comme un employé brillant mais
nouveau, à qui manque le contexte de vos normes et de vos façons de travailler[^employee]. Il propose
aussi un test valable pour tout prompt : montrez-le à un collègue qui connaît mal la tâche et
demandez-lui de le suivre ; s'il est perdu, Claude le sera aussi[^golden].

Voici un prompt vague :

```text
Sort this ticket: "I was charged twice this month."
```

Autrement dit : « Trie ce ticket : "On m'a débité deux fois ce mois-ci." ». Le trier dans quoi ?
Quelles réponses sont permises ? Faut-il un mot, une phrase, ou un paragraphe qui explique le
raisonnement ? Claude doit deviner. Les prédictions du modèle ont une part de hasard[^random] : deux appels
peuvent donc deviner différemment.

Voici la même demande, écrite clairement :

```text
<task>
Classify the support ticket below into exactly one category: billing, bug or feature_request.
</task>

<context>
We sell a photo-editing app. Each ticket goes to the team that owns its category, so a wrong category makes the customer wait for the wrong team.
</context>

<examples>
<example>
Ticket: The export button does nothing since the last update.
Category: bug
</example>
<example>
Ticket: Could you add a dark mode?
Category: feature_request
</example>
</examples>

<output_format>
Reply with the category name only, in lowercase, with nothing before or after it.
</output_format>

<ticket>
I was charged twice this month.
</ticket>
```

Ce prompt demande à Claude de classer le ticket dans une seule catégorie parmi trois : facturation
(billing), bug ou demande de fonctionnalité (feature_request). Il explique que l'entreprise vend
une application de retouche photo et qu'une mauvaise catégorie envoie le client vers la mauvaise
équipe, donne deux exemples, et demande le seul nom de la catégorie, en minuscules.

Il fait cinq choses. Chacune vient du guide de *prompting* d'Anthropic.

**Énoncez la tâche directement.** Claude répond bien à des instructions claires et explicites[^clear].
Nommez l'action et les réponses que vous acceptez : « classe dans une seule catégorie : billing, bug
ou feature_request », pas « trie ça ».

**Donnez le contexte qui manque à Claude.** Expliquer la raison d'une instruction peut aider Claude à
comprendre vos objectifs et à donner des réponses plus ciblées[^context]. Ici, le contexte dit qui est
l'entreprise et ce que coûte une mauvaise catégorie. Claude ne peut connaître ni l'un ni l'autre si
vous ne l'écrivez pas.

**Montrez des exemples.** Les exemples sont l'un des moyens les plus fiables d'orienter le format, le
ton et la structure des réponses de Claude[^examples]. Le guide en recommande trois à cinq[^count], et
les veut variés : ils doivent couvrir les cas limites (entrées inhabituelles ou à la frontière entre deux catégories) et varier assez pour que Claude ne retienne pas
des motifs que vous n'avez pas voulus[^diverse]. Le prompt ci-dessus n'en a que deux, pour rester
court. Un vrai classifieur (un programme qui range des entrées dans des catégories fixes) en ajouterait, dont un cas difficile comme une demande de remboursement
causée par un bug.

**Précisez le format de sortie.** Soyez précis sur le format et les contraintes que vous voulez[^format].
Votre code comparera la réponse de Claude à une liste de catégories : `billing` correspond,
`This looks like a billing issue.` ne correspond pas. Dites ce qu'il faut faire plutôt que seulement
ce qu'il ne faut pas faire[^positive] : « réponds seulement avec le nom de la catégorie » marche mieux
que « n'explique pas ».

**Séparez les parties avec des balises XML.** Les balises XML aident Claude à lire un prompt qui mêle
instructions, contexte, exemples et entrées variables sans confondre une partie avec une
autre[^xml]. Une balise est un nom entre chevrons, `<context>`, fermé par le même nom précédé d'une
barre oblique, `</context>`. Les exemples vont dans des balises `<example>`, toutes dans une seule
balise `<examples>`, pour que Claude les distingue des instructions[^example-tags]. Le ticket est une
entrée variable : il change à chaque appel, donc il a sa propre balise, et les mots du client ne se
mêlent jamais à vos instructions.

XML est une façon de baliser un texte avec des balises comme celles-ci. Votre prompt n'a pas besoin
d'être du XML valide, et il n'existe pas de liste fixe de noms de balises : un nom cohérent et
descriptif comme `<ticket>` suffit[^tag-names].

Un prompt clair rend une bonne réponse plus probable. Il ne la garantit pas : Claude peut encore
choisir la mauvaise catégorie. Et tous les problèmes ne se règlent pas en changeant le prompt : la latence ou le
coût, par exemple, s'améliorent parfois plus facilement en choisissant un autre modèle[^not-always]. La leçon suivante montre comment
tester un prompt face à des réponses attendues, pour savoir si une modification a aidé.

## Essayez

Ce script construit les deux prompts et les affiche. Il n'utilise que la bibliothèque standard et ne
fait aucun appel réseau. Enregistrez-le sous `try_prompt.py` et lancez `python3 try_prompt.py`.

```python
"""Print a vague prompt and a clear one built from tagged parts."""


def tag(name, text):
    return f"<{name}>\n{text.strip()}\n</{name}>"


vague = 'Sort this ticket: "I was charged twice this month."'

examples = [
    "Ticket: The export button does nothing since the last update.\nCategory: bug",
    "Ticket: Could you add a dark mode?\nCategory: feature_request",
]
clear = "\n\n".join([
    tag("task", "Classify the support ticket below into exactly one category: billing, bug or feature_request."),
    tag("context", "We sell a photo-editing app. Each ticket goes to the team that owns its category, "
                   "so a wrong category makes the customer wait for the wrong team."),
    tag("examples", "\n".join(tag("example", example) for example in examples)),
    tag("output_format", "Reply with the category name only, in lowercase, with nothing before or after it."),
    tag("ticket", "I was charged twice this month."),
])

print("--- vague ---")
print(vague)
print()
print("--- clear ---")
print(clear)
```

La sortie, ce sont les deux prompts de « L'idée ». Changez une partie, par exemple supprimez la ligne
`output_format`, et regardez ce que Claude ne saurait plus.

Les prompts sont ici en anglais pour que le code soit le même dans toutes les langues du cours. Claude
fonctionne bien dans beaucoup d'autres langues[^languages] : vous pouvez écrire vos propres prompts en
français.

### Envoyez-le à Claude

Si vous avez une clé d'API depuis la leçon précédente, vous pouvez envoyer les deux prompts et
comparer les réponses. Ajoutez ces lignes à la fin de `try_prompt.py`. Cette partie passe par le
réseau et coûte un peu ; elle est facultative.

```python
import anthropic

MODEL = "..."  # l'identifiant du modèle utilisé dans la leçon précédente
client = anthropic.Anthropic()
for prompt in (vague, clear):
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    # la réponse peut commencer par d'autres blocs, comme la réflexion (thinking) : on affiche le premier bloc de texte
    print(next(block.text for block in message.content if block.type == "text"))
    print("---")
```

Lancez-le plusieurs fois. Demandez-vous si votre code pourrait utiliser la réponse au prompt vague.

## Erreurs fréquentes

**« Claude sait ce que je veux dire. »** Il ne sait que ce qui est dans le prompt. Si un nouveau
collègue avait besoin de poser une question, écrivez la réponse dans le prompt.

**« Un prompt plus long est un meilleur prompt. »** La longueur n'est pas le but. Chaque partie doit
apprendre à Claude quelque chose dont il a besoin. Une balise `<context>` vide, ou une section qui dit
« aucun », ajoute du bruit et aucune information. Omettez-la.

**« Dire à Claude ce qu'il ne doit pas faire suffit. »** « N'explique pas » laisse la forme de la
réponse ouverte. Dites plutôt ce que la réponse doit être[^positive].

**« Mes exemples se ressemblent tous, donc ils sont cohérents. »** Des exemples qui partagent tous un
hasard, comme la même longueur ou la même catégorie, peuvent apprendre ce hasard à Claude[^diverse].
Variez-les exprès.

**« Les balises XML sont des commandes spéciales à apprendre. »** Il n'y a pas de liste à retenir :
utilisez des noms de balises cohérents et descriptifs dans tous vos prompts[^tag-names]. `<ticket>`
convient parce qu'il dit ce qu'il contient.

**« Les balises rendent l'entrée sûre. »** Les balises montrent à Claude où l'entrée commence et où
elle finit. Ne comptez pas sur elles seules pour empêcher un texte dans l'entrée d'agir comme une
instruction. Le cours y reviendra en traitant l'injection de prompt.

## Votre exercice

Ouvrez `exercise/starter/prompt_builder.py` et écrivez
`build_prompt(task, context, examples, output_format, input_text)`.
Elle renvoie une seule chaîne :

- chaque partie, sans les espaces autour, dans sa propre balise, dans cet ordre : `<task>`,
  `<context>`, `<examples>`, `<output_format>`, et en dernier `<input>` ;
- chaque exemple dans sa propre balise `<example>`, toutes dans `<examples>` ;
- l'entrée variable (comme le ticket) dans `<input>`, en dernier, pour qu'elle ne se mêle pas à vos instructions ;
- une balise seule sur sa ligne avant et après son contenu, et une ligne vide entre deux parties ;
- une partie vide ou faite seulement d'espaces, ou un exemple vide, entièrement omis ;
- une tâche vide refusée avec une `ValueError`, car un prompt sans tâche ne demande rien.

Lancez les tests depuis le dossier de départ :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que votre fonction n'est pas juste. Une solution se trouve dans `exercise/solution/` ;
essayez d'abord par vous-même.

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles sont difficiles, relisez « L'idée » et regardez ce que
chacune des cinq parties du prompt clair apporte à Claude.

[^employee]: Anthropic, Prompting best practices.
[^golden]: Anthropic, Prompting best practices.
[^clear]: Anthropic, Prompting best practices.
[^context]: Anthropic, Prompting best practices.
[^examples]: Anthropic, Prompting best practices.
[^count]: Anthropic, Prompting best practices.
[^diverse]: Anthropic, Prompting best practices.
[^format]: Anthropic, Prompting best practices.
[^positive]: Anthropic, Prompting best practices.
[^xml]: Anthropic, Prompting best practices.
[^example-tags]: Anthropic, Prompting best practices.
[^tag-names]: Anthropic, Prompting best practices.
[^not-always]: Anthropic, Prompt engineering overview.
[^random]: Anthropic, Glossary, « Temperature ».
[^languages]: Anthropic, Multilingual support.
