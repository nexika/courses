# Connecter un serveur MCP

## Ce que vous saurez faire

- Ajouter un serveur MCP à Claude Code avec `claude mcp add`, choisir son transport et sa portée,
  vérifier qu'il est connecté, et autoriser ou refuser ses outils avec des règles de permission.
- Lire un fichier `.mcp.json` : ce que chaque serveur lance ou contacte, et comment garder les secrets
  hors du fichier.
- Décider si vous faites confiance à un serveur avant de le connecter.

## L'idée

Dans la leçon « Ce qu'est MCP », l'hôte était un petit fichier Python. Ici, l'hôte est Claude Code. Vous lui
dites quels serveurs connecter ; il les lance ou les contacte, liste leurs outils et les propose à Claude.

**Ajouter un serveur**

`claude mcp add` ajoute un serveur. Un serveur **distant** se contacte par HTTP, à une URL. HTTP est le
transport recommandé pour les serveurs distants[^cc-http] :

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

Un serveur **local** tourne comme un programme sur votre ordinateur, en stdio. Il convient aux outils qui
ont besoin d'un accès direct à votre système ou à vos propres scripts[^cc-stdio]. Vous donnez la commande
qui le lance après `--` : tout ce qui précède `--` est pour Claude Code (`--transport`, `--env`,
`--scope`), et tout ce qui suit est passé au serveur tel quel[^cc-dashdash] :

```bash
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
```

Ici, `files` est le nom que vous donnez au serveur. `npx` est l'outil de Node.js pour exécuter un paquet,
et `-y` confirme qu'il peut installer ce paquet[^local-npx]. Node.js est un programme qui exécute du code
JavaScript. Ce serveur, le serveur de fichiers (*Filesystem server*), a besoin de Node.js[^local-node], et
les dossiers indiqués à la fin sont ceux qu'il a le droit d'utiliser[^local-dirs]. `--env NAME=value`
définit une variable d'environnement pour un serveur local[^cc-env-flag]. N'écrivez pas le nom du serveur juste après une paire `--env` :
Claude Code lirait le nom comme une autre paire et refuserait la commande[^cc-env-order].

Pour voir vos serveurs, lancez `claude mcp list` dans un terminal ; `claude mcp get <name>` en montre un,
et `claude mcp remove <name>` en retire un. Dans Claude Code, `/mcp` montre l'état de chaque
serveur[^cc-manage]. `claude mcp list` affiche un état à côté de chaque serveur, par exemple connecté,
authentification requise (vous devez d'abord vous connecter au service) ou échec de
connexion[^cc-status].

**Les portées : où le réglage est enregistré**

Chaque serveur est ajouté avec une **portée** (*scope*), qui décide où Claude Code le charge et qui
d'autre l'obtient[^cc-scopes] :

| Portée | Chargé dans | Partagé avec l'équipe | Enregistré dans |
|---|---|---|---|
| `local` (par défaut) | ce projet seulement | non | `~/.claude.json` |
| `project` | ce projet seulement | oui, par git | `.mcp.json` dans le dossier du projet |
| `user` | tous vos projets | non | `~/.claude.json` |

`~/.claude.json` est un fichier de votre dossier personnel, hors de votre projet. La portée local est
celle par défaut, et un serveur ajouté
en portée local reste privé[^cc-local]. (La portée dit où le réglage est enregistré : un serveur distant
peut avoir la portée local, et un serveur stdio la portée project.) Un serveur de portée project est écrit dans
`.mcp.json` à la racine du projet, pour que toute personne qui clone le projet (télécharge sa propre copie
avec git) ait les mêmes serveurs[^cc-project]. Choisissez la portée avec `--scope`, par exemple `--scope project`[^cc-scope-flag]. Voici un
`.mcp.json` avec deux serveurs (les parties `${...}` sont expliquées plus bas) :

```json
{
  "mcpServers": {
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${DOCS_DIR:-./docs}"]
    },
    "tickets": {
      "type": "http",
      "url": "https://tickets.example.com/mcp",
      "headers": {"Authorization": "Bearer ${TICKETS_TOKEN}"}
    }
  }
}
```

Une entrée avec une `command` est un serveur stdio local[^cc-notype] ; elle peut aussi avoir `env`, les
variables d'environnement passées au serveur[^cc-env-locations]. Une entrée avec une `url` doit aussi indiquer son
`type`, par exemple `http` : Claude Code lit une entrée sans `type` comme un serveur stdio local, donc une
`url` sans `type` est une erreur dans le fichier[^cc-notype].

Quand le même nom est défini dans plusieurs portées, Claude Code utilise une seule définition : local
d'abord, puis project, puis user. Il prend l'entrée entière dans cette portée et ne mélange pas les
champs de plusieurs portées[^cc-precedence].

**Les secrets restent hors du fichier**

Un serveur distant a souvent besoin d'un *jeton* secret (*token*) : ici une clé d'accès qui prouve qui
vous êtes, pas les tokens du modèle. Il peut être envoyé dans un *en-tête* (*header*), une ligne
d'informations en plus qui accompagne chaque requête HTTP, comme dans
`Authorization: Bearer <token>`[^cc-bearer]. Ne l'envoyez qu'à une adresse en `https://`. HTTPS est la
version chiffrée de HTTP, qui chiffre toute la communication entre un client et un serveur[^mdn-https].
Sur une adresse `http://` simple, rien n'est chiffré : d'autres sur le chemin réseau pourraient lire le
jeton.

`.mcp.json` est partagé par git[^cc-scopes] : toute personne qui peut lire le projet peut le lire. N'y
écrivez jamais de jeton secret. Écrivez plutôt `${NAME}`, et Claude Code y met la valeur de la variable
d'environnement `NAME` de votre machine ; `${NAME:-default}` utilise `default` quand `NAME` n'est pas
défini[^cc-env-syntax]. Cela permet aux équipes de partager un seul fichier tandis que chacun garde ses propres chemins et
clés[^cc-env-why]. Si une variable n'est pas définie et n'a pas de valeur par défaut, le fichier se charge
quand même, `claude mcp list` le signale, et le texte `${NAME}` est utilisé tel quel[^cc-env-unset].

**La confiance : ce que vous laissez entrer**

Connecter un serveur lui donne une place dans votre travail. Le guide d'Anthropic le dit clairement :
vérifiez que vous faites confiance à chaque serveur avant de le connecter, et sachez que les serveurs qui
vont chercher du contenu extérieur peuvent vous exposer à l'injection de prompt[^cc-verify], ces
instructions cachées vues dans la leçon sur l'utilisation d'outils[^hc-untrusted2]. Quatre questions
aident.

- **Qu'est-ce qui va tourner sur mon ordinateur ?** Un serveur local est un programme téléchargé et
  exécuté sur votre machine[^sec-local]. Sa commande s'exécute dès que l'hôte lance le serveur, ce qu'un hôte
  peut faire à chaque démarrage[^local-start], avant que Claude n'appelle le moindre outil : une demande de
  permission pour un appel d'outil arrive trop tard pour l'arrêter. Il tourne avec les droits de votre compte utilisateur : il peut
  faire sur les fichiers tout ce que vous pouvez faire[^local-perms]. Lisez la commande en entier. Un
  attaquant peut cacher une commande de démarrage malveillante dans la configuration d'un
  serveur[^sec-startup], et les commandes avec `sudo` (exécuter en
  administrateur), `rm -rf` (supprimer des fichiers et des dossiers entiers sans demander) ou un accès réseau méritent un examen plus
  attentif[^sec-patterns].
- **Qui l'a écrit, et à quoi a-t-il accès ?** La spécification traite les outils comme du code qui peut
  tout faire, et tient les descriptions du comportement des outils pour non fiables, sauf si le serveur
  est de confiance[^spec-safety]. Préférez des serveurs d'éditeurs que vous connaissez, et donnez à chacun
  le strict nécessaire : un dossier, pas tout votre dossier personnel ; un utilisateur de base de données
  en lecture seule (un compte de la base qui ne peut que lire), pour que les requêtes de Claude ne puissent pas modifier les données[^cc-readonly].
- **Apporte-t-il du contenu extérieur ?** Les pages web, les e-mails et tout autre contenu qui échappe à
  votre contrôle peuvent contenir des instructions destinées à Claude[^hc-untrusted2]. Traitez ce que
  renvoie un tel serveur comme des données, pas comme des ordres.
- **Qui l'a approuvé ?** Claude Code demande avant d'utiliser les serveurs du `.mcp.json` d'un projet dans
  une session interactive[^cc-approve]. Un projet peut aussi tenter de les approuver
  d'avance, avec des réglages comme `enabledMcpjsonServers` dans son `.claude/settings.json`, le fichier de
  réglages de Claude Code pour ce projet, commité dans git avec le reste. Claude Code ignore ces réglages
  tant que le dossier n'est pas de confiance[^cc-clone]. La première fois que vous
  lancez `claude` dans un dossier, il vous demande si vous lui faites confiance (la boîte de dialogue de
  confiance de l'espace de travail) ; une fois que vous acceptez, les approbations commitées dans le projet
  comptent[^cc-trust]. Lisez donc le `.mcp.json` et le `.claude/settings.json` d'un projet cloné avant de lui
  faire confiance. Mais dans les exécutions `claude -p` (Claude Code lancé par un script, sans
  personne pour répondre), les sessions Agent SDK (des programmes construits sur l'Agent SDK d'Anthropic, abordé dans un niveau
  ultérieur de ce cours) et les sessions cloud (Claude Code sur une machine distante), Claude Code charge les serveurs du projet sans
  demander[^cc-noprompt] : lisez le `.mcp.json` d'un projet avant d'y lancer Claude Code sans
  surveillance.

**Utiliser les outils d'un serveur**

Une fois le serveur connecté, Claude peut appeler ses outils comme n'importe quel autre outil, et vous
voyez une demande de permission pour eux comme pour les autres actions[^perm-prompts]. Claude Code nomme
chaque outil `mcp__<server>__<tool>`[^perm-mcp].

Les règles de permission, vues dans la leçon sur l'installation de Claude Code, sont de trois sortes. Une
règle `allow` permet à Claude d'utiliser un outil sans vous demander, une règle `ask` fait demander Claude
Code à chaque fois, et une règle `deny` empêche Claude d'utiliser l'outil[^perm-kinds]. Les règles de refus
sont examinées d'abord et l'emportent[^perm-order]. Les règles se trouvent dans les fichiers
`settings.json` de Claude Code, et `/permissions` les liste toutes[^perm-files] ; les règles pour tous vos
projets vont dans `~/.claude/settings.json`[^perm-user].

Une règle peut nommer les outils d'un serveur : `mcp__files` et `mcp__files__*` correspondent à tous les
outils du serveur `files`, et `mcp__files__read_file` à un seul outil[^perm-mcp]. Dans une règle `deny` ou
`ask`, un `*` dans le nom de l'outil remplace n'importe quel texte, donc `mcp__*` correspond à tous les
outils MCP[^perm-glob]. Dans une règle `allow`, un `*` dans un nom d'outil MCP ne peut venir qu'après
`mcp__<server>__`, comme dans `mcp__files__*` : une règle `allow` `mcp__*` est ignorée et n'approuve
rien[^perm-allow-glob]. Ce réglage permet à Claude d'utiliser tous les outils du serveur `files` sans
demander :

```json
{"permissions": {"allow": ["mcp__files__*"]}}
```

Et celui-ci refuse tous les outils MCP[^perm-deny] :

```json
{"permissions": {"deny": ["mcp__*"]}}
```

Une règle de refus arrête les appels d'outils de Claude. Elle n'arrête pas la commande d'un serveur local,
qui s'est déjà exécutée au démarrage du serveur.

## Essayez

### Sans Claude Code : lire un `.mcp.json`

`exercise/tests/sample_mcp.json` est un fichier de projet inventé avec cinq serveurs. Ce script ne lance
rien : il affiche ce que chaque serveur lancerait ou contacterait, avec les variables remplies depuis un
environnement fictif. Enregistrez-le sous `read_mcp_json.py` dans le dossier de la leçon et lancez
`python3 read_mcp_json.py` depuis ce dossier :

```python
"""Read a .mcp.json file and say what each server would run or reach. Nothing is started."""
import json
import re
from pathlib import Path

config = json.loads(Path("exercise/tests/sample_mcp.json").read_text(encoding="utf-8"))
environ = {"TICKETS_TOKEN": "tk-demo"}  # a pretend environment: only this one variable is set


def expand(text):
    """Replace ${VAR} and ${VAR:-default}; leave an unset variable with no default as written."""
    def one(match):
        name, default = match.group(1), match.group(2)
        return environ.get(name, default if default is not None else match.group(0))
    return re.sub(r"\$\{(\w+)(?::-([^}]*))?\}", one, text)


for name, entry in config["mcpServers"].items():
    if "command" in entry:
        line = " ".join(expand(word) for word in [entry["command"], *entry.get("args", [])])
        print(f"{name}: runs on your computer: {line}")
    else:
        kind = entry.get("type", "NO TYPE")
        print(f"{name}: connects to {expand(entry['url'])} ({kind})")
    for key, value in entry.get("headers", {}).items():
        print(f"    sends the header {key}: {expand(value)}")
```

Le motif `\$\{(\w+)(?::-([^}]*))?\}` trouve `${`, un nom, un `:-` facultatif suivi d'une valeur par
défaut, et `}`. `re.sub(pattern, one, text)` appelle la fonction `one` pour chaque `${...}` trouvé, et met à sa place ce
que `one` renvoie ; `match.group(0)` est le `${...}` entier, `match.group(1)` le nom de la variable et `match.group(2)` sa valeur par défaut,
ou `None`. Dans `[entry["command"], *entry.get("args", [])]`, le `*` place les éléments de la liste args
dans la nouvelle liste, après la commande.

La sortie montre que 2 des 5 serveurs exécutent une commande sur votre ordinateur. Lisez chaque ligne
comme le ferait un relecteur. `files` est un serveur connu, limité à un dossier. `crm` a son jeton écrit
dans le fichier, où toute personne qui a le projet peut le lire. `wiki` n'a pas de `type` : Claude Code ne
le connecterait pas. `helper` télécharge un script venu d'internet avec `curl` et l'exécute avec `sh` (un shell, comme Bash) : ne
le connectez pas tant que vous ne savez pas exactement ce que fait ce script.

### Avec Claude Code (facultatif)

Cette partie utilise un vrai serveur et Claude Code : il faut Node.js, et les requêtes de Claude sont
décomptées de votre abonnement Claude Code ou facturées sur votre clé d'API. Créez un petit dossier pour
le serveur, sans rien de privé dedans :

```bash
mkdir -p ~/mcp-sandbox
echo "Remember to water the plants." > ~/mcp-sandbox/note.txt
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
claude mcp list
```

Lancez `claude --permission-mode manual`, pour que Claude Code demande avant d'utiliser un outil, comme dans la
leçon sur l'installation de Claude Code. Tapez `/mcp` pour voir le serveur et ses outils, puis demandez :
`Use the files server to read note.txt in ~/mcp-sandbox.` Regardez quel outil Claude appelle (son nom
commence par `mcp__files__`), et lisez la demande de permission avant d'y répondre. Sans les mots « the
files server », Claude peut lire le fichier avec ses propres outils. Quand vous avez fini, retirez le serveur avec `claude mcp remove files`.

## Erreurs fréquentes

- **Écrire un jeton secret dans `.mcp.json`.** Le fichier est partagé par git. Utilisez `${NAME}` et gardez la
  valeur dans votre environnement[^cc-env-syntax].
- **Une `url` sans `type`.** Claude Code la lit comme un serveur stdio et signale une erreur de
  configuration[^cc-notype]. Ajoutez `"type": "http"`.
- **Oublier `--` avant la commande d'un serveur local.** Sans lui, Claude Code essaie de lire les options
  du serveur, comme `--port`, comme les siennes[^cc-nodash].
- **« La portée local veut dire un serveur local. »** La portée dit où le réglage est enregistré et qui le
  partage ; le transport dit comment Claude Code joint le serveur[^cc-scopes].
- **S'attendre à ce que les portées fusionnent.** L'entrée entière vient d'une seule portée : local, puis
  project, puis user[^cc-precedence].
- **« Il est dans une liste de serveurs, donc il est sûr. »** Vérifiez ce qu'il lance, qui l'a écrit et à
  quoi il a accès[^cc-verify]. Un serveur local a vos droits[^local-perms].
- **Donner à un serveur plus qu'il ne lui faut.** Un dossier, un utilisateur en lecture seule, seulement
  les outils dont vous vous servez. Un utilisateur de base de données en lecture seule, par exemple, ne peut
  pas modifier les données[^cc-readonly]. Refusez les outils dont vous ne voulez pas avec des
  règles de permission[^perm-mcp].
- **« Claude Code demande toujours avant de charger les serveurs d'un projet. »** Pas dans les exécutions
  `claude -p`, les sessions Agent SDK ni les sessions cloud[^cc-noprompt], ni une fois que vous faites confiance
  à un dossier dont les réglages commités les approuvent[^cc-trust].

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/mcp_setup.py` et écrivez six fonctions. Elles travaillent hors ligne sur de
simples valeurs Python ; rien ne lance Claude Code ni un serveur.

- `add_command(name, url=..., command=..., args=..., scope=..., env=...)` renvoie la commande
  `claude mcp add` sous forme de liste de mots, toujours avec `--transport` et `--scope` avant le nom :
  `--transport http` et l'URL pour un serveur distant, ou
  `--transport stdio`, les paires `--env` après le nom, `--` et la commande pour un serveur local. Elle
  lève `ValueError` pour une portée inconnue, pour `url` et `command` donnés ensemble ou aucun des deux,
  ou pour `env` avec une `url`.
- `expand(text, environ)` remplit `${NAME}` et `${NAME:-default}` et renvoie le texte et la liste des noms
  manquants. Un nom manquant sans valeur par défaut reste tel quel.
- `pick(local, project, user)` renvoie, pour chaque nom de serveur, la portée et l'entrée qu'utilise
  Claude Code.
- `tool_name(server, tool)` renvoie le nom que Claude Code donne à l'outil, et `rule_matches(rule, server,
  tool)` dit si une règle de permission comme `mcp__files` ou `mcp__*` lui correspond. Elle ne vérifie pas
  si la règle est une autorisation ou un refus. Le module standard `fnmatch` de Python compare un nom à un
  motif qui contient `*`.
- `review(config)` lit un `.mcp.json` et renvoie ce qu'il faut vérifier, sous forme de paires
  `(server, kind)` : `no-type`, `not-https` (une URL distante qui ne commence pas par `https://` ; une URL qui commence par `${`
  est ignorée, puisque sa valeur n'est connue que plus tard),
  `secret` (une valeur d'en-tête ou d'`env` dont le nom évoque un secret, écrite sans `${...}`), et
  `command` (une commande locale avec `sudo`, `rm -rf`, `curl` ou `wget` (tous deux téléchargent depuis internet),
  `&&`, `|` ou `;`).

`review` est un premier filtre, pas un contrôle de sécurité. Elle ne sait pas distinguer une commande
sûre d'une commande malveillante : elle montre seulement ce qu'une personne doit lire.

### Lancez les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, puis comparez.

## Vérifiez vos acquis

Faites le quiz de cette leçon. Si une question vous pose problème, relisez le tableau des portées et les
quatre questions de confiance.

[^cc-http]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-stdio]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-dashdash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^local-node]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-npx]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-dirs]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^cc-env-order]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-manage]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-status]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scopes]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-local]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-project]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-notype]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-precedence]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-syntax]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-why]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-unset]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-verify]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^hc-untrusted2]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^sec-local]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^local-perms]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^sec-startup]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^sec-patterns]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^spec-safety]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^cc-readonly]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-approve]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-clone]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-noprompt]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-nodash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-mcp]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-locations]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-bearer]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^mdn-https]: HTTPS, MDN Web Docs, <https://developer.mozilla.org/en-US/docs/Glossary/HTTPS>
[^local-start]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^perm-prompts]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-files]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scope-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-user]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-kinds]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-order]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-trust]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-allow-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-deny]: Configure permissions, <https://code.claude.com/docs/en/permissions>
