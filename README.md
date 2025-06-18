# Github Repo Explorer (Gloodata Extension)

 A Python extension for [Gloodata](https://gloodata.com/) that lets you explore GitHub repositories stored in a local SQLite database. Designed for LLM-based interactions: query repo metadata, commits, and file trees through natural language, no UI needed.

[🎥 Watch Youtube Demo](https://www.youtube.com/watch?v=EV5E5gR5oKM)

![Extension Preview](https://raw.githubusercontent.com/gloodata/extension-github-repo-explorer/refs/heads/main/resources/ext-preview.webp)


## Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/)
- [Gloodata](https://gloodata.com/download/)

Check that you are in a recent version of `uv`:

```bash
uv self update
```

### Project Setup

First you need to generate the `githubrepo.db` file using the scripts in `tools/github-repo-to-sqlite`.

Feel free to change the exported repository, here we are going to export the [facebook/react](https://github.com/facebook/react) repo:

```sh
cd tools/github-repo-to-sqlite
# get your token here https://github.com/settings/tokens
export GIHUB_TOKEN="YOUR TOKEN HERE"
bun run dumpRepo.js facebook react react-issues.json react-releases.json
bun run issuesToSqlite.js react-issues.json react-releases.json ../../githubrepo.db
```

[GitHub docs: Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Run

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

## Adding New Visualizations

1. Define new SQL queries in `queries.sql`
2. Create tool functions in `src/toolbox.py` using the `@tb.tool` decorator
3. Specify visualization types and parameters in the return dictionary

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainers.
