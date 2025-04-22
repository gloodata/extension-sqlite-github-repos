-- name: select_issues(start, end, status, author, milestone)
SELECT
  issue.id AS id,
  issue.number AS number,
  issue.title AS title,
  issue.body AS body,
  issue.state AS state,
  issue.is_locked AS is_locked,
  issue.comment_count AS comment_count,
  issue.created_at AS created_at,
  issue.updated_at AS updated_at,
  issue.closed_at AS closed_at,

  issue.author_id AS author_id,
  user.username AS author_name,

  issue.milestone_id AS milestone_id,
  milestone.title AS milestone_title
FROM
    issue
LEFT JOIN
    user ON issue.author_id = user.id
LEFT JOIN
    milestone ON issue.milestone_id = milestone.id
WHERE
    (:status IS NULL OR issue.state = :status) AND
    (:author IS NULL OR issue.author_id = :author) AND
    (:milestone IS NULL OR issue.milestone_id = :milestone) AND
    (:start IS NULL OR issue.created_at > :start) AND
    (:end IS NULL OR issue.updated_at < :end)
ORDER BY created_at DESC

-- name: select_issue_by_id(id)^
SELECT
  issue.id AS id,
  issue.number AS number,
  issue.title AS title,
  issue.body AS body,
  issue.state AS state,
  issue.is_locked AS is_locked,
  issue.comment_count AS comment_count,
  issue.created_at AS created_at,
  issue.updated_at AS updated_at,
  issue.closed_at AS closed_at,

  issue.author_id AS author_id,
  user.username AS author_name,

  issue.milestone_id AS milestone_id,
  milestone.title AS milestone_title
FROM
    issue
LEFT JOIN
    user ON issue.author_id = user.id
LEFT JOIN
    milestone ON issue.milestone_id = milestone.id
WHERE
    issue.id = :id

-- name: search_issues(query, limit)
SELECT id, title
FROM issue
WHERE id IN (
    SELECT id
    FROM issue_fts
    WHERE title MATCH :query
)
ORDER BY id
LIMIT :limit

-- name: select_all_users()
SELECT id, username, avatar_url
FROM user
ORDER BY username

-- name: search_users(query, limit)
SELECT id, username
FROM user
WHERE username LIKE '%' || :query || '%' COLLATE NOCASE
ORDER BY username
LIMIT :limit

-- name: search_milestones(query, limit)
SELECT id, title
FROM milestone
WHERE title LIKE '%' || :query || '%' COLLATE NOCASE
ORDER BY title
LIMIT :limit

-- name: select_labels()
SELECT id, name, color, description
FROM label
ORDER BY name

-- name: select_activity_by_day()
SELECT
    date,
    SUM(closed_count) AS closed,
    SUM(created_count) AS created
FROM (
    SELECT
        DATE(closed_at) AS date,
        COUNT(*) AS closed_count,
        0 AS created_count
    FROM
        issue
    WHERE
        closed_at IS NOT NULL
    GROUP BY
        DATE(closed_at)

    UNION ALL

    SELECT
        DATE(created_at) AS date,
        0 AS closed_count,
        COUNT(*) AS created_count
    FROM
        issue
    GROUP BY
        DATE(created_at)
) AS counts
GROUP BY
    date
ORDER BY
    date

-- name: select_issue_count_by_label()
SELECT
    l.name AS label,
    COUNT(il.issue_id) AS count
FROM
    issue_label il
JOIN
    label l ON il.label_id = l.id
GROUP BY
    l.id, l.name
ORDER BY
    count DESC
