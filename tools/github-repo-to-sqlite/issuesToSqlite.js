/*globals Bun*/
import { Database } from "bun:sqlite";

const [issuesPath, releasesPath, dbPath = "githubrepo.db"] = Bun.argv.slice(2);

async function readJSON(path) {
  const file = Bun.file(path);
  return await file.json();
}

const issues = await readJSON(issuesPath),
  releases = await readJSON(releasesPath);

const db = new Database(dbPath, { create: true });

db.run(`
  CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    avatar_url TEXT
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author_id INTEGER NOT NULL,
    state TEXT NOT NULL,
    is_locked BOOLEAN NOT NULL,
    comment_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    closed_at TEXT,
    milestone_id INTEGER,
    repository_id INTEGER
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS label (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    description TEXT
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    closed_at TEXT,
    state TEXT NOT NULL,
    due_on TEXT
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS issue_reaction (
    issue_id INTEGER NOT NULL,
    reaction TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (issue_id, reaction),
    FOREIGN KEY (issue_id) REFERENCES issue(id)
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS issue_label (
    issue_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    PRIMARY KEY (issue_id, label_id),
    FOREIGN KEY (issue_id) REFERENCES issue(id),
    FOREIGN KEY (label_id) REFERENCES label(id)
  )
`);

db.run(`
  CREATE TABLE IF NOT EXISTS release (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT,
    tarball_url TEXT,
    zipball_url TEXT,
    body TEXT,
    target_commitish TEXT,
    draft BOOLEAN NOT NULL,
    prerelease BOOLEAN NOT NULL
  )
`);

const INSERT_USER = db.prepare(
  "INSERT INTO user (id, username, avatar_url) VALUES (?, ?, ?)",
);
function insertUser(id, username, avatar_url) {
  INSERT_USER.run(id, username, avatar_url);
}

const INSERT_LABEL = db.prepare(`
    INSERT INTO label (id, name, color, description)
    VALUES (?, ?, ?, ?)
  `);
function insertLabel(id, name, color, description) {
  INSERT_LABEL.run(id, name, color, description);
}

const INSERT_MILESTONE = db.prepare(`
    INSERT INTO milestone (id, title, description, created_at, updated_at, closed_at, state, due_on)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
function insertMilestone(
  id,
  title,
  description,
  created_at,
  updated_at,
  closed_at,
  state,
  due_on,
) {
  INSERT_MILESTONE.run(
    id,
    title,
    description,
    created_at,
    updated_at,
    closed_at,
    state,
    due_on,
  );
}

const INSERT_ISSUE = db.prepare(`
    INSERT INTO issue (id, number, title, body, author_id, state, is_locked, comment_count, created_at, updated_at, closed_at, milestone_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
function insertIssue(
  id,
  number,
  title,
  body,
  author_id,
  state,
  is_locked,
  comment_count,
  created_at,
  updated_at,
  closed_at,
  milestone_id,
) {
  INSERT_ISSUE.run(
    id,
    number,
    title,
    body,
    author_id,
    state,
    is_locked,
    comment_count,
    created_at,
    updated_at,
    closed_at,
    milestone_id,
  );
}

const INSERT_REACTION = db.prepare(`
    INSERT INTO issue_reaction (issue_id, reaction, count)
    VALUES (?, ?, ?)
  `);
function insertIssueReaction(issue_id, reaction, count) {
  INSERT_REACTION.run(issue_id, reaction, count);
}

const INSERT_ISSUE_LABEL = db.prepare(`
    INSERT INTO issue_label (issue_id, label_id)
    VALUES (?, ?)
  `);
function insertIssueLabel(issue_id, label_id) {
  INSERT_ISSUE_LABEL.run(issue_id, label_id);
}

const INSERT_RELEASE = db.prepare(`
    INSERT INTO release (id, tag_name, name, created_at, published_at, tarball_url, zipball_url, body, target_commitish, draft, prerelease)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
function insertRelease(
  id,
  tag_name,
  name,
  created_at,
  published_at,
  tarball_url,
  zipball_url,
  body,
  target_commitish,
  draft,
  prerelease,
) {
  INSERT_RELEASE.run(
    id,
    tag_name,
    name,
    created_at,
    published_at,
    tarball_url,
    zipball_url,
    body,
    target_commitish,
    draft,
    prerelease,
  );
}

const users = {},
  labels = {},
  milestones = {};

function addUser({ id, login, avatar_url }) {
  users[login] = { id, username: login, avatar_url };
}

function addLabel({ id, name, color, descripton }) {
  if (labels[id] === undefined) {
    labels[id] = { id, name, color, descripton };
    insertLabel(id, name, color, descripton);
  }
}

function addMilestone({
  id,
  title,
  description,
  created_at,
  updated_at,
  closed_at,
  state,
  due_on,
}) {
  milestones[id] = {
    id,
    title,
    description,
    created_at,
    updated_at,
    closed_at,
    state,
    due_on,
  };
}

console.log("Inserting issues");
let count = 0;
for (const issue of issues) {
  const {
    id,
    number,
    title,
    body,
    user: author,
    labels,
    state,
    locked,
    comments,
    created_at,
    updated_at,
    closed_at,
    milestone,
    reactions,
    assignees,
  } = issue;

  if (count % 100 == 0) {
    console.log(`Inserted ${count} issues`);
  }

  if (milestone) {
    addMilestone(milestone);
  }

  addUser(author);
  assignees.forEach((user) => addUser(user));
  labels.forEach((label) => {
    addLabel(label);
    insertIssueLabel(id, label.id);
  });

  for (const [reaction, count] of Object.entries(reactions)) {
    if (count > 0 && reaction !== "total_count") {
      insertIssueReaction(id, reaction, count);
    }
  }

  try {
    insertIssue(
      id,
      number,
      title,
      body,
      author.id,
      state,
      locked,
      comments,
      created_at,
      updated_at,
      closed_at,
      milestone?.id,
    );
  } catch (err) {
    console.error(
      {
        id,
        number,
        title,
        body,
        author_id: author.id,
        state,
        locked,
        comments,
        created_at,
        updated_at,
        closed_at,
        milestone,
      },
      err,
    );
  }

  count += 1;
}

db.run(`CREATE VIRTUAL TABLE IF NOT EXISTS issue_fts USING fts5(id, title)`);

db.run(`
INSERT INTO issue_fts (id, title)
SELECT id, title FROM issue
`);

console.log("Inserting users");
for (const user of Object.values(users)) {
  const { id, username, avatar_url } = user;
  insertUser(id, username, avatar_url);
}

console.log("Inserting milestones");
for (const milestone of Object.values(milestones)) {
  const {
    id,
    title,
    description,
    created_at,
    updated_at,
    closed_at,
    state,
    due_on,
  } = milestone;

  insertMilestone(
    id,
    title,
    description,
    created_at,
    updated_at,
    closed_at,
    state,
    due_on,
  );
}

console.log("Inserting releases");
for (const release of releases) {
  const {
    id,
    tag_name,
    name,
    created_at,
    published_at,
    tarball_url,
    zipball_url,
    body,
    target_commitish,
    draft,
    prerelease,
  } = release;
  insertRelease(
    id,
    tag_name,
    name,
    created_at,
    published_at,
    tarball_url,
    zipball_url,
    body,
    target_commitish,
    draft,
    prerelease,
  );
}

console.log("done!");
db.close();
