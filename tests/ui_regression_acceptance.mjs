import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.R2_PLAYWRIGHT_PATH || "playwright-core");

const baseURL = process.env.R2_TEST_URL;
const username = process.env.R2_TEST_USERNAME;
const password = process.env.R2_TEST_PASSWORD;
const executablePath = process.env.R2_CHROMIUM || "/usr/bin/chromium";
const browserName = process.env.R2_BROWSER || "chromium";

if (!baseURL || !username || !password) throw new Error("missing test credentials");

if (!new Set(["chromium", "webkit"]).has(browserName)) throw new Error(`unsupported browser: ${browserName}`);
const browserType = browserName === "webkit" ? webkit : chromium;
const launchOptions = browserName === "chromium"
  ? { executablePath, headless: true, args: ["--no-sandbox"] }
  : { headless: true };
const browser = await browserType.launch(launchOptions);
const context = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
if (browserName === "chromium") {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: baseURL });
}
const page = await context.newPage();
const pageErrors = [];
page.on("pageerror", error => pageErrors.push(error.message));

const prefix = `ui-regression-${Date.now()}`;
let fixture;

async function api(path, options = {}) {
  return page.evaluate(async ({ path, options }) => {
    const response = await fetch(path, {
      ...options,
      headers: { "content-type": "application/json", ...(options.headers || {}) },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || `${response.status} ${path}`);
    return body;
  }, { path, options });
}

async function createFolder(name, parentId = "root") {
  return api("/api/drive/folders", {
    method: "POST",
    body: JSON.stringify({ name, parentId }),
  });
}

async function upload(name, folderId, text = name) {
  return page.evaluate(async ({ name, folderId, text }) => {
    const form = new FormData();
    form.append("folderId", folderId);
    form.append("file", new File([text], name, { type: "text/plain" }));
    const response = await fetch("/api/upload", { method: "POST", body: form });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `upload failed: ${response.status}`);
    return body;
  }, { name, folderId, text });
}

async function openFolder(name) {
  const row = page.locator('.drive-folder-group > [data-item-id]', { hasText: name });
  const id = await row.getAttribute("data-item-id");
  await page.evaluate(() => { window.__previousFolderShell = document.querySelector(".shell"); });
  await Promise.all([
    page.waitForResponse(response => response.url().includes(`/api/drive/files?folderId=${encodeURIComponent(id)}`) && response.ok()),
    row.locator("button.name").click(),
  ]);
  await page.waitForFunction(folderId => (
    S.folder === folderId
    && Boolean(document.querySelector(".drive-empty"))
    && document.querySelector(".shell") !== window.__previousFolderShell
  ), id);
}

async function emptyState() {
  return page.evaluate(() => {
    const folder = document.querySelector(".drive-empty");
    const search = document.querySelector(".search-empty");
    return {
      folderHidden: folder.hidden,
      folderDisplay: getComputedStyle(folder).display,
      searchHidden: search.hidden,
      searchDisplay: getComputedStyle(search).display,
    };
  });
}

try {
  await page.goto(baseURL, { waitUntil: "networkidle" });
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);
  await page.locator("form.card button.primary").click();
  await page.getByRole("heading", { name: "我的网盘" }).waitFor();

  const rootFile = await upload(`${prefix}-root.txt`, "root");
  const empty = await createFolder(`${prefix}-empty`);
  const filesOnly = await createFolder(`${prefix}-files-only`);
  const foldersOnly = await createFolder(`${prefix}-folders-only`);
  const mixed = await createFolder(`${prefix}-mixed`);
  const nested = await createFolder(`${prefix}-nested`, foldersOnly.id);
  const mixedChild = await createFolder(`${prefix}-mixed-child`, mixed.id);
  const fileOnlyFile = await upload(`${prefix}-file.txt`, filesOnly.id);
  const mixedFile = await upload(`${prefix}-mixed.txt`, mixed.id);
  fixture = { rootFile, empty, filesOnly, foldersOnly, mixed, nested, mixedChild, fileOnlyFile, mixedFile };

  await Promise.all([
    page.waitForResponse(response => response.url().includes("/api/drive/files?folderId=root") && response.ok()),
    page.getByTitle("刷新").first().click(),
  ]);
  await page.locator('.drive-file-group > [data-item-id]', { hasText: rootFile.name }).waitFor();
  assert.deepEqual(await emptyState(), {
    folderHidden: true, folderDisplay: "none", searchHidden: true, searchDisplay: "none",
  });

  await openFolder(filesOnly.name);
  assert.equal((await emptyState()).folderDisplay, "none");
  await page.locator(".crumbs button").first().click();
  await openFolder(foldersOnly.name);
  assert.equal((await emptyState()).folderDisplay, "none");
  await page.locator(".crumbs button").first().click();
  await openFolder(mixed.name);
  assert.equal((await emptyState()).folderDisplay, "none");
  await page.locator("#search").fill("no-such-item");
  assert.deepEqual(await emptyState(), {
    folderHidden: true, folderDisplay: "none", searchHidden: false, searchDisplay: "grid",
  });
  await page.locator("#search").fill("");
  await page.locator(".crumbs button").first().click();
  await openFolder(empty.name);
  assert.deepEqual(await emptyState(), {
    folderHidden: false, folderDisplay: "grid", searchHidden: true, searchDisplay: "none",
  });

  await page.locator(".crumbs button").first().click();
  const desktopFileRow = page.locator('.drive-file-group > [data-item-id]', { hasText: rootFile.name });
  await desktopFileRow.getByTitle("分享直链").click();
  await page.locator("#appToast").getByText("直链已复制", { exact: true }).waitFor();
  if (browserName === "chromium") {
    assert.match(await page.evaluate(() => navigator.clipboard.readText()), /\/public\//);
  }
  await desktopFileRow.getByTitle("分享页").click();
  await page.locator("#appToast").getByText("分享页链接已复制", { exact: true }).waitFor();
  if (browserName === "chromium") {
    assert.match(await page.evaluate(() => navigator.clipboard.readText()), /\/share\//);
  }

  for (const width of [375, 390, 430]) {
    await page.setViewportSize({ width, height: 820 });
    const fileRow = page.locator('.drive-file-group > [data-item-id]', { hasText: rootFile.name });
    await fileRow.locator(".mobile-drive-more-button").click();
    const sheet = page.locator(".drive-more-sheet.open");
    await sheet.waitFor();
    assert.ok((await sheet.getByRole("button", { name: /复制直链/ }).count()) === 1);
    assert.ok((await sheet.getByRole("button", { name: /复制分享页链接/ }).count()) === 1);
    await sheet.getByRole("button", { name: /复制分享页链接/ }).click();
    await page.locator("#appToast").getByText("分享页链接已复制", { exact: true }).waitFor();

    const folderRow = page.locator('.drive-folder-group > [data-item-id]', { hasText: mixed.name });
    await folderRow.locator(".mobile-drive-more-button").click();
    await page.locator(".drive-more-sheet.open").getByRole("button", { name: /复制文件夹分享链接/ }).click();
    await page.locator("#appToast").getByText("文件夹分享链接已复制", { exact: true }).waitFor();
    if (browserName === "chromium") {
      assert.match(await page.evaluate(() => navigator.clipboard.readText()), /\/share\/folder\//);
    }
    const dimensions = await page.evaluate(() => ({
      body: document.body.scrollWidth,
      viewport: document.documentElement.clientWidth,
    }));
    assert.ok(dimensions.body <= dimensions.viewport, `${width}px horizontal overflow`);
  }

  const sharedFolder = await api(`/api/drive/folders/${mixed.id}/public`, {
    method: "PATCH", body: JSON.stringify({ isPublic: true }),
  });
  const sharedFile = await api(`/api/drive/files/${mixedFile.id}/public`, {
    method: "PATCH", body: JSON.stringify({ isPublic: true }),
  });
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(new URL(sharedFolder.shareUrl, baseURL).href, { waitUntil: "networkidle" });
  const button = page.locator(".download-button", { hasText: "下载" });
  await button.waitFor();
  assert.equal(await button.count(), 1);
  assert.equal(await page.locator(".share-file-info", { hasText: mixedFile.name }).count(), 1);
  const downloads = [];
  page.on("download", item => downloads.push(item));
  const downloadPromise = page.waitForEvent("download");
  await button.click();
  const download = await downloadPromise;
  await download.cancel();
  await page.waitForTimeout(250);
  assert.equal(downloads.length, 1);

  await page.setViewportSize({ width: 375, height: 820 });
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(await page.locator(".download-button", { hasText: "下载" }).count(), 1);
  const shareDimensions = await page.evaluate(() => ({
    body: document.body.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }));
  assert.ok(shareDimensions.body <= shareDimensions.viewport, "folder share mobile overflow");

  await page.goto(new URL(sharedFile.shareUrl, baseURL).href, { waitUntil: "networkidle" });
  assert.equal(await page.getByRole("link", { name: "下载文件", exact: true }).count(), 1);
  assert.equal(await page.locator(".download-button").count(), 0);
  assert.deepEqual(pageErrors, []);

  console.log(JSON.stringify({
    emptyStates: ["root", "files-only", "folders-only", "mixed", "empty", "search-no-results"],
    browser: browserName,
    desktopSharing: true,
    mobileSharingViewports: [375, 390, 430],
    folderShareDownloads: downloads.length,
    singleFileShareUnchanged: true,
    pageErrors: pageErrors.length,
  }));
} finally {
  if (fixture) {
    await page.goto(baseURL, { waitUntil: "domcontentloaded" }).catch(() => {});
    await page.evaluate(async ({ fixture }) => {
      const remove = async (path, method = "DELETE") => fetch(path, { method });
      for (const file of [fixture.rootFile, fixture.fileOnlyFile, fixture.mixedFile]) {
        await remove(`/api/drive/files/${encodeURIComponent(file.id)}`);
      }
      for (const folder of [fixture.nested, fixture.mixedChild, fixture.empty, fixture.filesOnly, fixture.foldersOnly, fixture.mixed]) {
        await remove(`/api/drive/folders/${encodeURIComponent(folder.id)}`);
      }
    }, { fixture }).catch(() => {});
  }
  await browser.close();
}
