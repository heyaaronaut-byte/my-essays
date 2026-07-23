/**
 * gdrive-to-github.gs
 *
 * Watches a Google Drive folder. Any Google Doc that is new or has been
 * edited since the last run gets exported as plain text and pushed to
 * your GitHub repo as a markdown essay file. A GitHub Action (separate
 * file) then rebuilds the site.
 *
 * ONE-TIME SETUP
 * 1. Go to script.google.com -> New project. Paste this whole file in.
 * 2. Project Settings (gear icon) -> Script Properties -> add:
 *      DRIVE_FOLDER_ID   = the ID from your Drive folder's URL
 *      GITHUB_TOKEN      = a GitHub personal access token (repo contents write)
 *      GITHUB_REPO       = e.g. "yourusername/my-essays"
 *      GITHUB_BRANCH     = "main"
 * 3. Run `syncEssays` once manually (you'll be asked to authorize).
 * 4. Triggers (clock icon) -> Add Trigger -> function: syncEssays,
 *    type: Time-driven, Minutes timer, every 15 minutes.
 *
 * That's it. Write a Doc in the folder, wait up to 15 min, check the site.
 */

function syncEssays() {
  const props = PropertiesService.getScriptProperties();
  const folderId = props.getProperty('DRIVE_FOLDER_ID');
  const githubToken = props.getProperty('GITHUB_TOKEN');
  const githubRepo = props.getProperty('GITHUB_REPO');
  const githubBranch = props.getProperty('GITHUB_BRANCH') || 'main';

  const folder = DriveApp.getFolderById(folderId);
  const files = folder.getFilesByType(MimeType.GOOGLE_DOCS);

  while (files.hasNext()) {
    const file = files.next();
    const docId = file.getId();
    const lastUpdated = file.getLastUpdated().getTime();
    const storedKey = 'doc_' + docId;
    const storedTimestamp = props.getProperty(storedKey);

    if (storedTimestamp && Number(storedTimestamp) >= lastUpdated) {
      continue; // no changes since last sync
    }

    try {
      publishDoc(file, docId, githubToken, githubRepo, githubBranch);
      props.setProperty(storedKey, String(lastUpdated));
      Logger.log('Published: ' + file.getName());
    } catch (err) {
      Logger.log('Failed to publish ' + file.getName() + ': ' + err);
    }
  }
}

function publishDoc(file, docId, token, repo, branch) {
  const title = file.getName();
  const doc = DocumentApp.openById(docId);
  const bodyText = doc.getBody().getText().trim();

  const dateStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMMM yyyy');
  const slug = slugify(title);
  const path = 'essays/' + slug + '.md';

  const markdown = 'title: ' + title + '\n' +
                    'date: ' + dateStr + '\n\n' +
                    bodyText;

  pushToGithub(token, repo, branch, path, markdown, 'Publish/update: ' + title);
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

function pushToGithub(token, repo, branch, path, content, message) {
  const apiUrl = 'https://api.github.com/repos/' + repo + '/contents/' + path;
  const headers = {
    Authorization: 'token ' + token,
    Accept: 'application/vnd.github+json'
  };

  // Check if file already exists, to get its sha (required for updates)
  let sha = null;
  const getResp = UrlFetchApp.fetch(apiUrl + '?ref=' + branch, {
    headers: headers,
    muteHttpExceptions: true
  });
  if (getResp.getResponseCode() === 200) {
    sha = JSON.parse(getResp.getContentText()).sha;
  }

  const payload = {
    message: message,
    content: Utilities.base64Encode(content, Utilities.Charset.UTF_8),
    branch: branch
  };
  if (sha) payload.sha = sha;

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: 'put',
    headers: headers,
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const code = putResp.getResponseCode();
  if (code !== 200 && code !== 201) {
    throw new Error('GitHub API error ' + code + ': ' + putResp.getContentText());
  }
}
