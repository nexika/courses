# Installer Claude Code et approuver ses actions

## Ce que vous saurez faire

- Installer Claude Code et ouvrir une session dans le dossier d'un projet.
- Demander à Claude Code de lire et d'expliquer du code, puis de le modifier.
- Repérer les actions pour lesquelles Claude Code vous demande votre accord, et approuver ou refuser chacune.

## L'idée

Claude Code est un assistant de programmation fondé sur l'IA, qui vous aide à créer des fonctionnalités,
corriger des bugs et automatiser des tâches de développement[^what]. Vous lui parlez dans votre
terminal. Le cours s'en sert dans chaque module : cette première leçon porte donc sur la façon de
travailler avec lui sans risque.

Cette leçon suppose acquis ce qu'enseigne le cours externe du Niveau 0 : ouvrir un terminal, passer
d'un dossier à l'autre, lancer un fichier Python, et utiliser git pour faire un *commit* et lire un
*diff* (les lignes qui ont changé entre deux versions d'un fichier).

**Ce qui se passe quand vous demandez quelque chose.** Quand vous confiez une tâche à Claude, il passe
par trois phases : rassembler le contexte, agir, puis vérifier le résultat[^loop]. Il le fait avec
des outils. Sans outils, Claude ne peut que répondre par du texte ; avec des outils, il peut lire
votre code, modifier des fichiers, lancer des commandes, chercher sur le web et interagir avec des
services externes[^tools].

Un exemple. Vous tapez :

```text
add a function that splits the bill between people
```

Autrement dit : « ajoute une fonction qui partage l'addition entre plusieurs personnes ». Claude lit
vos fichiers pour trouver où l'addition est calculée (rassembler le contexte). Il modifie un fichier
pour ajouter la fonction (agir). Il peut lancer le fichier pour voir s'il fonctionne (vérifier).
Chacune de ces étapes est une action sur votre ordinateur.

**Qui décide de ce qui s'exécute.** Certaines actions sont sans danger : lire un fichier ne change
rien. D'autres modifient vos fichiers ou lancent des programmes. Claude Code a des modes de permission
qui fixent les actions qu'il fait sans vous demander. En mode Manual, Claude Code s'arrête et vous
demande avant la plupart des actions qui modifient des fichiers, lancent des commandes shell ou
accèdent au réseau[^manual]. Une commande shell est une commande tapée dans le terminal, comme
`python3 tip.py`.

Quand il demande, vous voyez une demande de permission. Elle montre ce que Claude s'apprête à faire,
suivi de vos options[^prompt]. On y trouve en général **Yes** (oui), **No** (non) et
**Yes, and don't ask again** (oui, et ne plus demander), qui approuve aussi les actions suivantes du
même genre ; combien de temps, cela dépend de l'action[^bash-approval]. Lisez la demande avant de
répondre : c'est le moment où vous décidez.

Toutes les commandes ne demandent pas. Claude Code reconnaît un ensemble intégré de commandes Bash
comme étant en lecture seule, et les lance sans demande de permission, quel que soit le
mode[^read-only]. Bash est le programme qui exécute les commandes shell. L'ensemble comprend `ls`,
`cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, et
les formes de `git` qui ne font que lire[^read-only-list]. Ces commandes consultent des fichiers sans
les modifier.

**Le mode de départ d'une session.** Avec Claude Code v2.1.283 ou plus récent, le mode auto est le
mode de permission de départ intégré pour les sessions interactives dans le terminal et dans
VS Code[^auto-default]. En mode auto, un second modèle, le classifieur, examine les actions à votre
place[^classifier]. Un classifieur est un programme qui range chaque action dans « autorisée » ou
« bloquée ». C'est lui aussi un modèle : il peut se tromper.

Dans ce module, vous vérifiez chaque action vous-même : vous partez donc en mode Manual. La ligne de
commande accepte le nom `manual` pour ce mode : `claude --permission-mode manual`[^manual-flag]. Vous
pouvez aussi appuyer sur `Shift+Tab` à tout moment pour changer le mode de permission de la session
en cours[^shift-tab].

## Essayez

Il vous faut un compte Claude pour utiliser Claude Code : un abonnement Claude (Pro, Max, Team ou
Enterprise), un compte Claude Console, ou un accès via un fournisseur cloud pris en charge[^account].
Ces services sont payants : regardez le prix avant de vous inscrire.

### Installation

Sous macOS, Linux ou WSL (Linux dans Windows), la commande d'installation est[^install] :

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Dans l'invite de commandes de Windows (CMD), c'est[^install-windows] :

```bash
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Quand l'installation est terminée, ouvrez une nouvelle fenêtre de terminal et lancez
`claude --version`. Une installation qui fonctionne affiche un numéro de version[^version].

### Un petit projet

Créez un dossier avec un seul fichier Python et faites-en un *commit*, pour que git puisse vous
montrer plus tard ce que Claude a changé :

```bash
mkdir tip-calc
cd tip-calc
git init
```

Enregistrez ceci sous le nom `tip.py` :

```python
"""A small tip calculator."""


def tip(total, percent):
    """Return the tip on a bill: percent of the total, rounded to cents."""
    return round(total * percent / 100, 2)


if __name__ == "__main__":
    print(tip(50, 15))
```

Le programme calcule le pourboire : un pourcentage de l'addition. Lancez-le avec `python3 tip.py`. Il
affiche :

```text
7.5
```

Puis faites le *commit* :

```bash
git add tip.py
git commit -m "Add the tip calculator"
```

### Votre première session

Ouvrez votre terminal dans le dossier d'un projet et lancez Claude Code[^start]. Ici le projet est
`tip-calc`, et vous partez en mode Manual :

```bash
claude --permission-mode manual
```

Claude Code vous demande de vous connecter à la première utilisation[^login]. Suivez les étapes dans
le navigateur.

**Demandez-lui de lire et d'expliquer.** Tapez :

```text
explain what tip.py does, line by line
```

C'est-à-dire : « explique ce que fait tip.py, ligne par ligne ». Claude Code lit les fichiers du
projet quand il en a besoin ; inutile de les coller vous-même[^reads]. Lire des fichiers dans le
dossier du projet ne demande pas d'accord[^reads-free] : il répond donc sans demande de permission.
Comparez sa réponse au code : dit-il que `round(..., 2)` garde deux décimales ?

**Demandez-lui de modifier le code.** Tapez :

```text
add a function split(total, percent, people) to tip.py that returns what each person pays, tip included
```

C'est-à-dire : « ajoute à tip.py une fonction split qui renvoie ce que paie chaque personne,
pourboire compris ». Une demande de permission apparaît pour la modification. Elle montre les lignes
que Claude veut ajouter (`+`) et supprimer (`-`). Lisez-les. Si la modification fait ce que vous avez
demandé et ne touche que `tip.py`, choisissez **Yes**. Si elle fait autre chose, choisissez **No**.

**Demandez-lui de lancer le fichier.** Tapez :

```text
run tip.py
```

`python3` ne fait pas partie des commandes en lecture seule : une demande apparaît donc avant que la
commande s'exécute. Approuvez-la : vous savez ce que fait `tip.py`.

**Refusez une fois, exprès.** Demandez quelque chose que vous ne voulez pas, comme `delete tip.py`
(supprime tip.py), et choisissez **No**. Si vous choisissez **No** sans commentaire, Claude Code
arrête le tour en cours[^deny]. Recommencez et, avant de répondre, placez-vous sur **No** et appuyez
sur `Tab` pour écrire une raison. Claude Code transmet votre commentaire à Claude comme raison du
refus, et Claude continue son travail[^deny-comment].

Pour sortir, tapez `/exit`. Puis lancez `git diff` dans le terminal : il montre chaque ligne que
Claude a changée depuis votre *commit*. La leçon suivante explique comment le lire.

## Erreurs fréquentes

**« Claude Code fait ce qu'il veut sur mon ordinateur. »** En mode Manual, il demande avant la
plupart des modifications, des commandes et des accès au réseau[^manual]. Ce qui s'exécute dépend de
vous : lisez chaque demande.

**« Lire est sans danger, donc tout est sans danger. »** La lecture et les commandes en lecture seule
passent sans demande. Les modifications et les autres commandes demandent. Un **Yes** à une
modification ou à une commande change vos fichiers.

**« Yes, and don't ask again, c'est pareil que Yes. »** Non. Pour une modification de fichier,
l'accord dure jusqu'à la fin de la session[^edit-approval]. Pour une commande Bash, une règle est
enregistrée et s'applique aux sessions futures partout dans ce dépôt[^bash-approval]. Ne le
choisissez que pour des commandes que vous approuveriez à chaque fois.

**« Si j'écris "ne supprime jamais de fichier" dans ma demande, il ne pourra pas en supprimer. »** Les
règles de permission sont appliquées par Claude Code, pas par le modèle[^enforced]. Vos mots orientent
ce que Claude essaie de faire. Ce qui s'exécute, ce sont les demandes de permission et les règles qui
en décident.

**« Une nouvelle session me demande tout. »** Sur les versions récentes, une nouvelle session démarre
en mode auto, où un classifieur décide à votre place[^auto-default]. Lancez
`claude --permission-mode manual`, ou changez de mode avec `Shift+Tab`, quand vous voulez vérifier
chaque action.

**« Une fois lancé, je ne peux plus l'arrêter. »** Appuyez sur `Esc` pour arrêter Claude
immédiatement[^esc]. Avant de modifier un fichier, Claude en garde une copie ; appuyez deux fois sur
`Esc` pour revenir à un état antérieur, ou demandez à Claude d'annuler[^rewind]. Ce retour en arrière
ne couvre pas tout : il ne suit pas les fichiers modifiés par des commandes Bash[^bash-untracked].
Faites des *commits* : git pourra toujours vous rendre votre travail.

## Votre exercice

On ne peut pas lancer Claude Code dans un test : cet exercice entraîne donc la décision que vous
prenez à chaque demande. Ouvrez `exercise/starter/permission_check.py`. Chaque action que Claude
demande à faire y est décrite par un dictionnaire, par exemple `{"tool": "Edit", "file": "tip.py"}` ou
`{"tool": "Bash", "command": "python3 tip.py"}`.

Écrivez deux fonctions.

`asks_first(action)` renvoie `True` quand le mode Manual vous demanderait d'abord :

- `Read`, `Grep` et `Glob` (les outils qui lisent et cherchent dans les fichiers) ne demandent jamais ;
- `Edit` et `Write` (les outils qui modifient les fichiers) demandent toujours ;
- `Bash` demande, sauf si la commande est une seule commande simple (sans `;`, `&`, `|`, `>`, `<`,
  accent grave, `$(` ni retour à la ligne) dont le programme est dans `READ_ONLY_COMMANDS` ;
- tout autre outil demande : dans le doute, on demande.

C'est un modèle simplifié, qui demande dès qu'il a un doute. Le vrai Claude Code regarde de plus près :
par exemple, il vérifie où pointe une redirection (`>` ou `<`), et il traite les formes de `git` en
lecture seule comme telles. L'exercice laisse ces cas de côté.

`answer(action, task_files, expected_commands)` renvoie votre réponse :

- `"no prompt"` quand `asks_first(action)` vaut `False` ;
- pour `Edit` ou `Write` : `"yes"` si le fichier fait partie de `task_files`, sinon `"no"` ;
- pour `Bash` : `"yes"` si la commande, sans les espaces autour, fait partie de `expected_commands`,
  sinon `"no"` ;
- pour tout autre outil : `"no"`.

Lancez les tests depuis le dossier de départ :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Ils échouent tant que vos fonctions ne sont pas justes. Une solution se trouve dans
`exercise/solution/` ; essayez d'abord seul. Passez ensuite au vrai : une session en mode Manual sur
`tip-calc`, où vous approuvez une modification et refusez une action.

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles vous semblent difficiles, relisez « L'idée », ainsi
que les erreurs fréquentes sur **Yes, and don't ask again**.

[^what]: Documentation de Claude Code, Overview.
[^loop]: Documentation de Claude Code, How Claude Code works.
[^tools]: Documentation de Claude Code, How Claude Code works.
[^manual]: Documentation de Claude Code, Choose a permission mode.
[^prompt]: Documentation de Claude Code, Configure permissions.
[^read-only]: Documentation de Claude Code, Configure permissions.
[^read-only-list]: Documentation de Claude Code, Configure permissions.
[^auto-default]: Documentation de Claude Code, Choose a permission mode.
[^classifier]: Documentation de Claude Code, Choose a permission mode.
[^manual-flag]: Documentation de Claude Code, Choose a permission mode.
[^shift-tab]: Documentation de Claude Code, Quickstart.
[^account]: Documentation de Claude Code, Quickstart.
[^install]: Documentation de Claude Code, Quickstart.
[^install-windows]: Documentation de Claude Code, Quickstart.
[^version]: Documentation de Claude Code, Quickstart.
[^start]: Documentation de Claude Code, Quickstart.
[^login]: Documentation de Claude Code, Quickstart.
[^reads]: Documentation de Claude Code, Quickstart.
[^deny]: Documentation de Claude Code, Configure permissions.
[^deny-comment]: Documentation de Claude Code, Configure permissions.
[^edit-approval]: Documentation de Claude Code, Configure permissions.
[^bash-approval]: Documentation de Claude Code, Configure permissions.
[^enforced]: Documentation de Claude Code, Configure permissions.
[^esc]: Documentation de Claude Code, How Claude Code works.
[^rewind]: Documentation de Claude Code, How Claude Code works.
[^bash-untracked]: Documentation de Claude Code, Checkpointing.
[^reads-free]: Documentation de Claude Code, Configure permissions.
