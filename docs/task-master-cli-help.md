Usage: task-master [options] [command]

Claude Task Master CLI

Options:
  -V, --version                    output the version number
  -h, --help                       Display help information

Commands:
  dev                              Run the dev.js script
  parse-prd [options]              Parse a PRD file and generate tasks
  update [options]                 Update multiple tasks with ID >= "from"
                                   based on new information or implementation
                                   changes
  update-task [options]            Update a single specific task by ID with new
                                   information (use --id parameter)
  update-subtask [options]         Update a subtask by appending additional
                                   timestamped information
  generate [options]               Generate task files from tasks.json
  set-status [options]             Set the status of a task
  list [options]                   List all tasks
  expand [options]                 Break down tasks into detailed subtasks
  analyze-complexity [options]     Analyze tasks and generate expansion
                                   recommendations
  clear-subtasks [options]         Clear subtasks from specified tasks
  add-task [options]               Add a new task using AI or manual input
  next [options]                   Show the next task to work on based on
                                   dependencies and status
  show [options]                   Display detailed information about a
                                   specific task
  add-dependency [options]         Add a dependency to a task
  remove-dependency [options]      Remove a dependency from a task
  validate-dependencies [options]  Identify invalid dependencies without fixing
                                   them
  fix-dependencies [options]       Fix invalid dependencies automatically
  complexity-report [options]      Display the complexity analysis report
  add-subtask [options]            Add a subtask to an existing task
  remove-subtask [options]         Remove a subtask from its parent task
  remove-task [options]            Remove one or more tasks or subtasks
                                   permanently
  init [options]                   Initialize a new project with Task Master
                                   structure
  help [command]                   display help for command

---
Usage: task-master update-task [options]

Update a single specific task by ID with new information (use --id parameter)

Options:
  -f, --file <file>    Path to the tasks file (default: "tasks/tasks.json")
  -i, --id <id>        Task ID to update (required)
  -p, --prompt <text>  Prompt explaining the changes or new context (required)
  -r, --research       Use Perplexity AI for research-backed task updates
  -h, --help           Display help information

---
Usage: task-master generate [options]

Generate task files from tasks.json

Options:
  -f, --file <file>   Path to the tasks file (default: "tasks/tasks.json")
  -o, --output <dir>  Output directory (default: "tasks")
  -h, --help          Display help information
  __