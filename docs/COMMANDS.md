# Command reference

| Intent | Examples |
|---|---|
| Help | help, what can you do |
| Time | what time is it, tell me the time |
| Date | what is today's date, what day is it |
| Add note | remember <text>, save note <text> |
| List notes | show my notes, list notes |
| Search notes | search notes for <text> |
| Delete note | delete note <id> (confirmation required) |
| Add task | add task <text>, remind me to <text> |
| List tasks | show my tasks, list tasks |
| Complete task | complete task <id>, finish task <id> |
| Completed tasks | show completed tasks |
| Calculator | calculate <expression> |
| Open URL | open <http-or-https-url> (confirmation required) |
| Teach alias | teach "phrase" as help/time/date/note.list/task.list |
| Exit | exit, quit, goodbye |

Aliases are exact phrase mappings to a small allowlist of parameter-free intents. They cannot inject arguments or register arbitrary code.
