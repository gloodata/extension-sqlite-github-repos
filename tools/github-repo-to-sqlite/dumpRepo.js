/* globals Bun */
// https://github.com/octokit/core.js#readme
import { Octokit } from "octokit";

const [
  owner = "facebook",
  repo = "react",
  issuesPath = "issues.json",
  releasesPath = "releases.json",
] = Bun.argv.slice(2);

const octokit = new Octokit({
  //auth: 'YOUR-TOKEN'
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

await writeJSON(issuesPath, await getIssues(owner, repo));
await writeJSON(releasesPath, await getReleases(owner, repo));
