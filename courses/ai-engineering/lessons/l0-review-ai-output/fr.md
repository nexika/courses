# Vérifier ce que Claude a modifié

## Ce que vous saurez faire

- Lire un *diff* : voir quels fichiers ont changé, et quelles lignes ont été ajoutées ou supprimées.
- Lancer les tests vous-même, et vérifier qu'ils testent toujours ce qu'ils testaient avant.
- Repérer les modifications à regarder de près avant de les accepter : fichiers hors de la tâche,
  tests modifiés ou supprimés, tests désactivés.

## L'idée

Dans la leçon précédente, vous avez approuvé ou refusé chaque action. Cette leçon porte sur le
résultat : la modification que Claude laisse dans vos fichiers.

Claude s'arrête quand le travail a l'air terminé[^looks-done]. Avoir l'air terminé et être juste, ce
n'est pas pareil. Le guide d'Anthropic décrit un échec fréquent : Claude produit une implémentation qui
paraît plausible mais ne gère pas les cas limites[^trust-gap]. Un cas limite est une entrée
inhabituelle, comme une addition partagée entre zéro personne. Le remède du guide est net : fournissez
toujours un moyen de vérifier (tests, scripts, captures d'écran) ; si vous ne pouvez pas vérifier, ne
livrez pas[^verify].

Avant d'accepter une modification, vous faites donc deux choses : lire le *diff*, et lancer les tests.

**Le diff.** Un *diff* montre ce qui a changé entre deux versions d'un fichier. `git diff` montre les
changements entre l'arbre de travail et l'index[^git-diff]. L'arbre de travail (*working tree*), ce
sont vos fichiers tels qu'ils sont maintenant ; l'index, aussi appelé zone de préparation (*staging
area*), est l'endroit où `git add` place le contenu de votre prochain *commit*[^git-add]. Si vous
n'avez pas lancé `git add` depuis votre dernier *commit*, `git diff` montre tout ce qui a changé depuis
ce *commit*. Dans Claude Code, la commande `/diff` permet de parcourir les changements de l'arbre de
travail sans quitter la session[^slash-diff].

Voici une partie d'un *diff*. La tâche donnée à Claude était « fais passer
`test_split_needs_people` » : ce test vérifie que `split` refuse une addition partagée entre zéro
personne.

```diff
--- a/tip.py
+++ b/tip.py
@@ -3,4 +3,6 @@
 
 
 def split(total, percent, people):
-    return round((total + tip(total, percent)) / people, 2)
+    if people < 1:
+        raise ValueError("people must be at least 1")
+    return round(total / people + tip(total, percent), 2)
```

Lisez-le depuis le haut :

- `--- a/tip.py` et `+++ b/tip.py` désignent l'ancienne et la nouvelle version du fichier. Un fichier
  créé ou supprimé affiche `/dev/null` d'un côté[^dev-null]. La sortie de `git diff` commence aussi
  chaque fichier par une ligne comme `diff --git a/tip.py b/tip.py`[^git-header].
- Une ligne qui commence par `@@` ouvre un bloc de modifications (*hunk*) : il en vient un ou
  plusieurs, et chacun montre un endroit où les fichiers diffèrent[^hunks]. Les nombres entre les
  marques `@@` indiquent quelles lignes de l'ancien et du nouveau fichier le bloc couvre[^hunk-header].
- Chaque ligne commence ensuite par un caractère : `-` pour une ligne supprimée, `+` pour une ligne
  ajoutée, et une espace pour une ligne inchangée[^plus-minus].

Cette modification fait deux choses. Les deux lignes `+` qui lèvent `ValueError` sont ce que la tâche
demandait. Mais la dernière ligne a changé aussi : l'ancien code divisait toute l'addition, pourboire
compris, par le nombre de personnes ; le nouveau divise seulement le montant, puis ajoute le pourboire
entier à chaque part. Personne ne l'a demandé. C'est le genre de changement qu'on ne trouve qu'en
lisant.

**Les tests.** Les tests sont votre vérification, mais une modification peut aussi toucher les tests.
Voici la suite du même *diff* :

```diff
--- a/test_tip.py
+++ b/test_tip.py
@@ -1,6 +1,6 @@
 class TipTest(unittest.TestCase):
     def test_split(self):
-        self.assertEqual(split(100, 10, 4), 27.5)
+        self.assertEqual(split(100, 10, 4), 35.0)
```

`test_split` disait que chaque personne payait 27.5. Le nouveau code a cassé cela, et le test a été
modifié pour suivre : chaque personne paie désormais 35.0. Tous les tests passent, et le code est
faux : si quatre personnes paient chacune ce montant, ensemble elles paient 140.0, alors que
l'addition avec le pourboire fait 110.0. Une assertion (une ligne qui vérifie un résultat, comme
`assertEqual`) qui change, c'est ce que le code doit faire qui change. Demandez pourquoi.

**Ce qu'il faut regarder.** Avant d'accepter une modification, vérifiez :

- **Les fichiers hors de la tâche.** Chaque fichier du *diff* doit avoir une raison d'y être.
- **Les tests modifiés ou supprimés.** Une ligne `-` dans un fichier de test peut retirer une
  vérification. Lisez-la.
- **Les tests désactivés.** `@unittest.skip` au-dessus d'un test le fait sauter : il ne s'exécute
  plus[^skip].
- **Les erreurs cachées au lieu d'être corrigées.** Le guide demande à Claude de traiter la cause
  profonde, pas d'étouffer l'erreur[^root-cause]. Un nouveau `try` et `except` qui avale une erreur
  mérite une question.

Lancez ensuite les tests vous-même et lisez leur sortie. Si vous demandez à Claude si les tests
passent, faites-lui montrer des preuves plutôt qu'affirmer la réussite : la sortie des tests, la
commande lancée et ce qu'elle a renvoyé[^evidence].

**Si la modification est fausse.** Dites à Claude ce qui ne va pas, ou jetez la modification.
`git restore` restaure des fichiers de l'arbre de travail à partir d'une source[^git-restore] :
`git restore tip.py` remet la version de `tip.py` que git connaît (celle de l'index, qui est votre
dernier *commit* si vous n'avez pas lancé `git add` depuis).

## Essayez

Ce script construit le *diff* ci-dessus avec le module `difflib` de Python : vous voyez le format sans
session ni dépôt. Les *diffs* unifiés sont une façon compacte de ne montrer que les lignes modifiées,
avec quelques lignes de contexte[^difflib], et `git diff` utilise les mêmes marques `+`, `-` et
espace.

Enregistrez-le sous le nom `see_the_diff.py` et lancez `python3 see_the_diff.py` :


```python
"""Show what a change did to two files, in the same format as git diff."""
import difflib

before = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    return round((total + tip(total, percent)) / people, 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 27.5)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

# The task was: "make test_split_needs_people pass". This is the change that came back.
after = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    if people < 1:
        raise ValueError("people must be at least 1")
    return round(total / people + tip(total, percent), 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 35.0)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

for name in before:
    lines = difflib.unified_diff(
        before[name].splitlines(keepends=True),
        after[name].splitlines(keepends=True),
        fromfile=f"a/{name}",
        tofile=f"b/{name}",
    )
    print("".join(lines))
```

Il affiche les deux parties du *diff* de « L'idée », avec quelques lignes inchangées après
l'assertion. Modifiez maintenant `after` vous-même : remettez l'ancienne ligne `return` dans `tip.py`,
et l'ancienne valeur dans `test_tip.py`. Relancez le script. Il ne reste que les lignes dont la tâche
avait besoin.

Dans votre propre projet, après une session, lancez `git diff` (ou `/diff` dans Claude Code), puis
`python3 -m unittest`, et lisez les deux avant de faire le *commit*.

## Erreurs fréquentes

**« Les tests passent, donc la modification est juste. »** Les tests passent quand le code correspond
aux tests. Si les tests ont changé aussi, lisez comment. Dans l'exemple, tous les tests passent et le
code est faux.

**« Claude a dit que les tests passent. »** Une phrase n'est pas une exécution des tests. Demandez la
sortie, ou lancez les tests vous-même[^evidence].

**« Seules les lignes `+` comptent. »** Les lignes `-` montrent ce qui a disparu. Une assertion ou
une vérification supprimée change le comportement.

**« Plus de modifications, c'est plus de travail fait. »** Un fichier hors de la tâche est une
question, pas un bonus. Demandez pourquoi il a changé, ou refusez-le.

**« Accepter les modifications automatiquement, c'est sauter la revue. »** La documentation conseille
le mode `acceptEdits` quand vous voulez relire les changements dans votre éditeur ou avec `git diff`
après coup, plutôt que d'approuver chaque modification sur le moment[^accept-edits]. La revue se
déplace ; elle ne disparaît pas.

**« Je pourrai toujours revenir en arrière. »** Les points de restauration (*checkpoints*) ne suivent
que les changements faits avec les outils d'édition de fichiers de Claude ; les changements faits par
des commandes shell ne sont pas capturés, et ils ne remplacent pas git[^not-git]. Faites un *commit*
avant la session : vous pourrez toujours revenir à ce point.

**« Un outil de revue remplace ma revue. »** Claude Code a une commande `/code-review` qui vérifie le
*diff* en cours pour y trouver des bugs de correction[^code-review]. Elle est utile, et c'est aussi un
modèle : elle peut rater des choses. Elle ne sait pas ce que vous vouliez demander. Vous, si.

## Votre exercice

Ouvrez `exercise/starter/diff_review.py`. Vous écrivez deux fonctions qui lisent le texte qu'affiche
`git diff`.

### Ce qu'il faut construire

`parse_diff(text)` renvoie un dictionnaire avec une entrée par fichier, dans l'ordre où les fichiers
apparaissent. Chaque entrée associe le chemin du fichier (sans le préfixe `a/` ou `b/`) à un
dictionnaire :

- `"status"` : `"added"` quand l'ancien côté est `/dev/null`, `"deleted"` quand le nouveau côté est
  `/dev/null`, sinon `"modified"` ;
- `"added"` : les lignes ajoutées, sans leur `+` initial ;
- `"removed"` : les lignes supprimées, sans leur `-` initial.

Les lignes d'en-tête (`diff --git`, `index`, `---`, `+++`, `@@`) ne sont pas du contenu. Attention :
une ligne supprimée dont le texte commence par `--` s'affiche `---`, et ressemble donc à un en-tête.
Servez-vous de la ligne `@@` : elle donne, pour chaque côté, où le bloc commence et combien de lignes
il compte, sous la forme `-start,count +start,count`. Si un bloc ne contient qu'une ligne, seul son
numéro de ligne de départ apparaît[^hunk-one] : le nombre vaut alors un. Comptez les lignes en les
lisant, et vous savez toujours où le bloc se termine.

`red_flags(text, task_files)` renvoie une liste de paires `(path, reason)`, dans l'ordre des
fichiers, et pour chaque fichier dans cet ordre de raisons :

- `"outside the task"` : le chemin n'est pas dans `task_files` ;
- `"test deleted"` : un fichier de test a été supprimé ;
- `"assertion changed"` : une ligne supprimée d'un fichier de test contient `assert` ;
- `"test skipped"` : une ligne ajoutée contient `unittest.skip`, `skipTest(` ou `mark.skip`.

Un fichier de test est un fichier dont le nom commence par `test_` ou se termine par `_test.py`.

### Lancer les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que vos fonctions ne sont pas justes. Une solution se trouve dans
`exercise/solution/` ; essayez d'abord seul. Servez-vous-en ensuite sur une vraie modification : après
une session Claude Code, lancez `git diff > change.diff` et passez le texte de `change.diff` à
`red_flags`. Un signal est une raison de lire de près. L'absence de signal ne veut pas dire que la
modification est juste : lisez le *diff* quand même.

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles vous semblent difficiles, relisez les deux *diffs* de
« L'idée », ligne par ligne.

[^looks-done]: Documentation de Claude Code, Best practices for Claude Code.
[^trust-gap]: Documentation de Claude Code, Best practices for Claude Code.
[^verify]: Documentation de Claude Code, Best practices for Claude Code.
[^git-diff]: Documentation de Git, git-diff.
[^slash-diff]: Documentation de Claude Code, Interactive mode.
[^dev-null]: Documentation de Git, git-diff.
[^git-header]: Documentation de Git, git-diff.
[^hunks]: Manuel de GNU diffutils, Detailed Description of Unified Format.
[^hunk-header]: Manuel de GNU diffutils, Detailed Description of Unified Format.
[^plus-minus]: Documentation de Git, git-diff.
[^root-cause]: Documentation de Claude Code, Best practices for Claude Code.
[^evidence]: Documentation de Claude Code, Best practices for Claude Code.
[^git-restore]: Documentation de Git, git-restore.
[^difflib]: Documentation de Python, difflib.
[^accept-edits]: Documentation de Claude Code, Choose a permission mode.
[^not-git]: Documentation de Claude Code, Best practices for Claude Code.
[^code-review]: Documentation de Claude Code, Commands.
[^git-add]: Documentation de Git, git-add.
[^skip]: Documentation de Python, unittest.
[^hunk-one]: Manuel de GNU diffutils, Detailed Description of Unified Format.
