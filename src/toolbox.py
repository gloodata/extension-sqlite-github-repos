import os
from enum import Enum
from datetime import datetime, date
from glootil import Toolbox, DynEnum, date_to_data_tag, ContextActionInfo
from state import SQLiteState as State
import httpx

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
    name="Show Issues",
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
        number=-1,
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
            number,
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
            number,
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
            {"id": "number", "label": "#"},
            {"id": "issue", "label": "Issue"},
            {"id": "state", "label": "State"},
            {"id": "author", "label": "Author"},
            {"id": "milestone", "label": "Milestone", "visible": False},
            {"id": "is_locked", "label": "Locked", "visible": False},
            {"id": "comment_count", "label": "Comments"},
            {"id": "created_at", "label": "Created"},
            {"id": "updated_at", "label": "Updated", "visible": False},
            {"id": "closed_at", "label": "Closed", "visible": False},
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


@tb.tool(name="Show User", examples=["user info for mofeiZ", "Show user @eps1lon"])
async def show_user(user: User | None):
    """Show details for a user"""
    if not user:
        return "No user selected"

    async with httpx.AsyncClient() as client:
        url = f"https://api.github.com/users/{user.value}"
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()

            html_url = data.get("html_url")

            user_type = data.get("type")
            name = data.get("name")
            company = data.get("company")
            blog = data.get("blog")
            location = data.get("location")
            email = data.get("email") or ""
            bio = data.get("bio") or ""
            followers = data.get("followers")
            following = data.get("following")
            created_at = format_date(data.get("created_at"))
            public_repos = data.get("public_repos")
            public_gists = data.get("public_gists")

            return {
                "type": "InfoBox",
                "columns": [
                    {"id": "user_type", "label": "Type"},
                    {"id": "name", "label": "Name"},
                    {"id": "company", "label": "Company"},
                    {"id": "blog", "label": "Blog"},
                    {"id": "location", "label": "Location"},
                    {"id": "email", "label": "Email"},
                    {"id": "bio", "label": "Bio"},
                    {"id": "followers", "label": "Followers"},
                    {"id": "following", "label": "Following"},
                    {"id": "created_at", "label": "Created At"},
                    {"id": "public_repos", "label": "Public Repos"},
                    {"id": "public_gists", "label": "Public Gists"},
                ],
                "row": [
                    user_type,
                    url_tag_value(name, html_url),
                    company,
                    url_tag_value(blog, blog),
                    location,
                    email,
                    bio,
                    followers,
                    following,
                    created_at,
                    public_repos,
                    public_gists,
                ],
            }
        else:
            return f"Error: {response.status_code} - {response.text}"


@tb.context_action(tool=show_user, target=User)
def show_user_for_user(ctx: ContextActionInfo):
    return {"args": {"user": ctx.value.get("label")}}


@tb.context_action(tool=issues_table, target=User)
def show_issues_for_user(ctx: ContextActionInfo):
    return {"args": {"author": ctx.value.get("label")}}


@tb.context_action(tool=issues_table, target=Status)
def show_issues_for_status(ctx: ContextActionInfo):
    return {"args": {"status": ctx.value.get("label")}}


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

    locked_label = "Yes" if row.get("is_locked") else "No"
    author_name = row.get("author_name", "?")

    return f"""
# [{row.get("number", "?")}] {row.get("title", "?")}

- State: {row.get("state", "?")}
- Author: [@{author_name}](https://github.com/{author_name})
- Milestone: {row.get("milestone_title", "?")}
- Locked: {locked_label}
- Comments: {row.get("comment_count", "?")}
- Created: {format_date_row(row, "created_at")}
- Updated: {format_date_row(row, "updated_at")}
- Closed: {format_date_row(row, "closed_at", "No")}

{row.get("body", "")}
    """


@tb.context_action(tool=show_issue, target=Issue)
def show_issue_for_issue(ctx: ContextActionInfo):
    return {"args": {"issue": ctx.value.get("label")}}


@tb.tool(name="Issues Activity by Day")
async def issues_activity_by_day(state: State, user: User | None):
    """Show open/close issue count activity by day"""
    user_id = user.name if user else None
    rows = await state.query_to_tuple(
        "select_activity_by_day", {"user_id": user_id}, date=None, closed=0, created=0
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


@tb.context_action(tool=issues_activity_by_day, target=User)
def show_issues_activity_for_user(ctx: ContextActionInfo):
    return {"args": {"user": ctx.value.get("label")}}


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


def format_date_row(row, name, default="?"):
    iso_date = row.get(name)
    return format_date(iso_date, default)


def format_date(iso_date, default="?"):
    if iso_date:
        return datetime.fromisoformat(iso_date).strftime("%Y-%m-%d %H:%M")
    else:
        return default


def url_tag_value(value, url):
    return ["link", {"url": url, "label": value}]


@tb.tool(name="Show Milestone", ui_prefix="Show", args=dict(milestone="Milestone"))
async def show_milestone(state: State, milestone: Milestone | None):
    """Show details for a milestone"""
    if not milestone:
        return "No milestone selected"

    row = await state.query("select_milestone_by_id", dict(id=milestone.name))

    return f"""
# {row.get("title", "?")}

- State: {row.get("state", "?")}
- Created: {format_date_row(row, "created_at")}
- Updated: {format_date_row(row, "updated_at")}
- Closed: {format_date_row(row, "closed_at", "No")}
- Due On: {format_date_row(row, "due_on", "Not Due")}

{row.get("description", "")}
    """
