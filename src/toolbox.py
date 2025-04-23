import os
from enum import Enum
from datetime import date
from glootil import Toolbox, DynEnum, date_to_data_tag
from state import SQLiteState as State

db_path = os.environ.get("EXTENSION_DB_PATH", "./githubrepo.db")

tb = Toolbox(
    "gd-github-repo-explorer",
    "GitHub Repository Explorer",
    "Explore issues and releases for a GitHub repository",
    state=State(db_path),
)


@tb.enum(icon="toggle")
class Status(Enum):
    """Issue status"""

    open = "Open"
    closed = "Closed"


@tb.enum(icon="user")
class Label(DynEnum):
    """Issue label"""

    @staticmethod
    async def load(state: State):
        return await state.query_to_tuple("select_labels", {}, id=None, name="?")


@tb.enum(icon="user")
class User(DynEnum):
    """Github id and username"""

    @staticmethod
    async def search(state: State, query: str = "", limit: int = 100):
        return await state.query_to_tuple(
            "search_users",
            dict(query=query, limit=limit),
            id=None,
            username="?",
        )


@tb.enum(icon="flag")
class Milestone(DynEnum):
    """Repository milestone"""

    @staticmethod
    async def search(state: State, query: str = "", limit: int = 100):
        return await state.query_to_tuple(
            "search_milestones", dict(query=query, limit=limit), id=None, title="?"
        )


@tb.enum(icon="error")
class Issue(DynEnum):
    """Repository issue number and title"""

    @staticmethod
    async def search(state: State, query: str = "", limit: int = 100):
        return await state.query_to_tuple(
            "search_issues", dict(query=query, limit=limit), id=None, title="?"
        )


@tb.tool(
    name="Show Issues as Table",
    manual_update=True,
    args=dict(
        start="From", end="To", status="Status", author="Author", milestone="Milestone"
    ),
    examples=[
        "Show issues for the last year",
        "Show open issues for the last 5 years",
        "show closed issues since 2010",
    ],
)
async def issues_table(
    state: State,
    start: date | None,
    end: date | None,
    status: Status | None,
    author: User | None,
    milestone: Milestone | None,
):
    """Show issues in a table with filters"""

    tuples = await state.query_to_tuple(
        "select_issues",
        dict(start=start, end=end, status=status, author=author, milestone=milestone),
        id=None,
        title="?",
        state="open",
        author_id=None,
        author_name="?",
        milestone_id=None,
        milestone_title="?",
        is_locked=0,
        comment_count=0,
        created_at=None,
        updated_at=None,
        closed_at=None,
    )

    rows = []
    for t in tuples:
        (
            id,
            title,
            state_str,
            author_id,
            author_name,
            milestone_id,
            milestone_title,
            is_locked,
            comment_count,
            created_at,
            updated_at,
            closed_at,
        ) = t
        locked_label = "Yes" if is_locked else "No"
        issue_tag = Issue(id, title).to_data_tag()
        author_tag = User(author_id, author_name).to_data_tag() if author_id else None
        milestone_tag = (
            Milestone(milestone_id, milestone_title).to_data_tag()
            if milestone_id
            else None
        )
        status_tag = None
        if state_str == "open":
            status_tag = Status.open.to_data_tag()
        elif state_str == "closed":
            status_tag = Status.closed.to_data_tag()

        row = (
            issue_tag,
            status_tag,
            author_tag,
            milestone_tag,
            locked_label,
            comment_count,
            date_to_data_tag(created_at),
            date_to_data_tag(updated_at),
            date_to_data_tag(closed_at),
        )
        rows.append(row)

    return {
        "type": "Table",
        "columns": [
            {"id": "title", "label": "Issue"},
            {"id": "state", "label": "State"},
            {"id": "author", "label": "Author"},
            {"id": "milestone", "label": "Milestone"},
            {"id": "is_locked", "label": "Locked", "visible": False},
            {"id": "comment_count", "label": "Comments"},
            {"id": "created_at", "label": "Created"},
            {"id": "updated_at", "label": "Updated"},
            {"id": "closed_at", "label": "Closed"},
        ],
        "rows": rows,
    }


@tb.tool(name="Show Labels", examples=["Show labels", "Show issue labels"])
async def show_labels(state: State):
    """Show all labels in the repository"""

    tuples = await state.query_to_tuple(
        "select_labels", {}, id=None, name="?", color="?", description=""
    )
    rows = []
    for id, name, color, desc in tuples:
        rows.append((Label(id, name).to_data_tag(), color, desc or ""))

    return {
        "type": "Table",
        "columns": [
            {"id": "name", "label": "Name"},
            {"id": "color", "label": "Color"},
            {"id": "description", "label": "Description"},
        ],
        "rows": rows,
    }


@tb.tool(name="Show Users", examples=["Show project contributors", "Show users"])
async def show_users(state: State):
    """Show a list of users related to the project"""

    tuples = await state.query_to_tuple(
        "select_all_users", {}, id=None, username="?", avatar_url=None
    )
    rows = []
    for id, username, avatar_url in tuples:
        rows.append((User(id, username).to_data_tag(), avatar_url))

    return {
        "type": "Table",
        "columns": [
            {"id": "username", "label": "Name"},
            {"id": "avatar_url", "label": "Avatar URL", "visible": False},
        ],
        "rows": rows,
    }


@tb.tool(
    name="Show Issue",
    ui_prefix="Show",
    args=dict(issue="Issue"),
    examples=["Show first issue", "Show issue #123"],
)
async def show_issue(state: State, issue: Issue | None):
    """Show details for an issue"""
    if not issue:
        return "No issue selected"

    row = await state.query("select_issue_by_id", dict(id=issue.name))
    return f"""
# [{row.get("number", "?")}] {row.get("title", "?")}

- State: {row.get("state", "?")}
- Author: {row.get("author_name", "?")}
- Milestone: {row.get("milestone_title", "?")}
- Locked: {row.get("is_locked", "?")}
- Comments: {row.get("comment_count", "?")}
- Created: {row.get("created_at", "?")}
- Updated: {row.get("updated_at", "?")}
- Closed: {row.get("closed_at", "?")}

{row.get("body", "")}
    """


@tb.tool(name="Issues Activity by Day")
async def issues_activity_by_day(state: State):
    """Show open/close issue count activity by day"""
    rows = await state.query_to_tuple(
        "select_activity_by_day", {}, date=None, closed=0, created=0
    )
    return {
        "type": "Series",
        "title": "Issues Activity by Day",
        "xCol": "date",
        "valCols": ["closed", "created"],
        "xAxisType": "time",
        "cols": [
            ["date", "Day"],
            ["closed", "Closed"],
            ["created", "Created"],
        ],
        "rows": rows,
    }


@tb.tool(
    name="Issue Count by Label", examples=["Show label usage", "Show issues by label"]
)
async def issue_count_by_label(state: State):
    """Show number of issues with each label"""
    rows = await state.query_to_tuple(
        "select_issue_count_by_label", {}, label="?", count=0
    )

    return {
        "type": "Series",
        "title": "Issue Count by Label",
        "xCol": "label",
        "valCols": ["count"],
        "cols": [
            ["label", "Label"],
            ["count", "Count"],
        ],
        "rows": rows,
    }


@tb.tool(name="Show Milestone", ui_prefix="Show", args=dict(milestone="Milestone"))
async def show_milestone(state: State, milestone: Milestone | None):
    """Show details for a milestone"""
    if not milestone:
        return "No milestone selected"

    row = await state.query("select_milestone_by_id", dict(id=milestone.name))

    return f"""
# {row.get("title", "?")}

- State: {row.get("state", "?")}
- Created: {row.get("created_at", "?")}
- Updated: {row.get("updated_at", "?")}
- Closed: {row.get("closed_at", "?")}
- Due On: {row.get("due_on", "?")}

{row.get("description", "")}
    """
