# Github Repo Explorer (Gloodata Extension)

A Python extension for [Gloodata](https://gloodata.com/) to explore a github repository from a sqlite database.

![Extension Preview](https://raw.githubusercontent.com/gloodata/extension-github-repo-explorer/refs/heads/main/resources/ext-preview.webp)

# Setup

First you need to generate the `githubrepo.db` file using the scripts in `tools/github-repo-to-sqlite`.

Feel free to change the exported repository, here we are going to export the [facebook/react](https://github.com/facebook/react) repo:

```sh
cd tools/github-repo-to-sqlite
# get your token here https://github.com/settings/tokens
export GIHUB_TOKEN="YOUR TOKEN HERE"
bun run dumpRepo.js facebook react react-issues.json react-releases.json
bun run issuesToSqlite.js react-issues.json react-releases.json ../../githubrepo.db
```

# Run

Check that you are in a recent version of `uv`:

```bash
uv self update
```

```sh
uv run src/main.py
```

Available environment variables and their defaults:

- `EXTENSION_PORT`: `9876`
- `EXTENSION_HOST`: `localhost`
- `EXTENSION_DB_PATH`: `./githubrepo.db`

For example, to change the port:

```sh
EXTENSION_PORT=6677 uv run src/main.py
```

# Adding New Visualizations

1. Define new SQL queries in `queries.sql`
2. Create tool functions in `src/toolbox.py` using the `@tb.tool` decorator
3. Specify visualization types and parameters in the return dictionary

# License

This project is open source and available under the [MIT License](LICENSE).

# Support

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainers.
