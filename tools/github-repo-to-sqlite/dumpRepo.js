/* globals Bun */
// https://github.com/octokit/core.js#readme
import { Octokit } from "octokit";

const [
  owner = "facebook",
  repo = "react",
  issuesPath = "issues.json",
  releasesPath = "releases.json",
] = Bun.argv.slice(2);

const octokitOpts = {};
if (process.env.GITHUB_TOKEN) {
  octokitOpts.auth = process.env.GITHUB_TOKEN;
} else {
  console.warn(
    "GITHUB_TOKEN environment variable not set, you may get rate limited",
  );
}

const octokit = new Octokit(octokitOpts);

octokit.hook.after("request", async (response, options) => {
  console.log(`${options.method} ${options.url}: ${response.status}`);
});

async function getIssues(owner, repo, per_page = 500) {
  return await octokit.paginate(octokit.rest.issues.listForRepo, {
    owner,
    repo,
    state: "all",
    per_page,
  });
}

async function getReleases(owner, repo, per_page = 100) {
  return await octokit.paginate(octokit.rest.repos.listReleases, {
    owner,
    repo,
    per_page,
  });
}

async function writeJSON(path, data) {
  return await Bun.write(path, JSON.stringify(data));
}

console.log("Fetching releases");
await writeJSON(releasesPath, await getReleases(owner, repo));
console.log("Fetching issues");
await writeJSON(issuesPath, await getIssues(owner, repo));
