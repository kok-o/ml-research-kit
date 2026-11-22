# ML Research Kit

Скилл для исследовательских задач в Soup и других репозиториях обучения моделей.
Он помогает спланировать эксперимент, проверить пересечения с работой команды
и принять решение по сырым метрикам. Codex и Antigravity используют один
[SKILL.md](skills/ml-research/SKILL.md).

## Codex

Клонируйте репозиторий и выполните из его корня в PowerShell:

```powershell
$skill = (Get-Item -LiteralPath 'skills/ml-research').FullName
$skillsDir = Join-Path $env:USERPROFILE '.agents/skills'
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
New-Item -ItemType Junction -Path (Join-Path $skillsDir 'ml-research') -Target $skill
```

В macOS и Linux из корня репозитория:

```sh
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/ml-research" ~/.agents/skills/ml-research
```

Пользовательская установка доступна во всех рабочих копиях. После `git pull`
ссылка ведёт на обновлённые инструкции. Чтобы проверить автоматический выбор,
откройте чат в Soup и задайте исследовательский вопрос обычным языком, например
«Как сравнить два оптимизатора по времени до заданного validation loss?».
Для явного вызова используйте `$ml-research`.

## Antigravity

Из корня репозитория:

```sh
agy plugin validate --strict .
agy plugin install .
```

Плагин также загружает правила из `rules/AGENTS.md`. После обновления checkout
повторите установку, чтобы обновить копию Antigravity.

## Проверка радара PR

Радар использует Python 3.10+, Git с поддержкой `merge-tree --write-tree`
и авторизованный GitHub CLI. Он проверяет конфликты с `origin/main` и открытые
PR, которые затрагивают указанные пути. Пример из корня этого репозитория:

```sh
python skills/ml-research/scripts/team_radar.py --repo /path/to/worktree --paths src/train.py --fetch
python -m unittest discover -s tests -v
```
