import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.R2_PLAYWRIGHT_PATH || "playwright-core");
const baseURL = process.env.R2_TEST_URL;
const username = process.env.R2_TEST_USERNAME;
const password = process.env.R2_TEST_PASSWORD;
const executablePath = process.env.R2_CHROMIUM || "/usr/bin/chromium";

if (!baseURL || !username || !password) throw new Error("missing test credentials");

const browser = await chromium.launch({ executablePath, headless: true, args: ["--no-sandbox"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
const page = await context.newPage();
const pageErrors = [];
page.on("pageerror", error => pageErrors.push(error.message));

async function api(path, options = {}) {
  return page.evaluate(async ({ path, options }) => {
    const response = await fetch(path, {
      ...options,
      headers: options.body && typeof options.body === "string"
        ? { "content-type": "application/json", ...(options.headers || {}) }
        : options.headers,
    });
    const text = await response.text();
    const body = text ? JSON.parse(text) : null;
    if (!response.ok) throw new Error(body?.error || `HTTP ${response.status}`);
    return body;
  }, { path, options });
}

async function upload(path, name, content, type, folderId = "root") {
  return page.evaluate(async ({ path, name, content, type, folderId }) => {
    const data = new FormData();
    data.append("folderId", folderId);
    data.append("file", new File([Array.isArray(content) ? new Uint8Array(content) : content], name, { type }));
    const response = await fetch(path, { method: "POST", body: data });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
    return body;
  }, { path, name, content, type, folderId });
}

async function refreshDrive() {
  await page.getByTitle("刷新").first().click();
  await page.locator(".drive-folder-group").waitFor();
}

async function moveModalInto(folderName, conflictPolicy = "cancel") {
  const modal = page.locator(".move-modal");
  await modal.locator(".move-folder", { hasText: folderName }).click();
  await modal.locator("#conflictPolicy").selectOption(conflictPolicy);
  await modal.getByRole("button", { name: "移动到此文件夹", exact: true }).click();
}

try {
  await page.goto(baseURL, { waitUntil: "networkidle" });
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);
  await page.locator("form.card button.primary").click();
  await page.getByRole("heading", { name: "我的网盘" }).waitFor();

  const prefix = `manage-${Date.now()}`;
  const folders = {};
  for (const suffix of ["A", "B", "C", "D"]) {
    folders[suffix] = await api("/api/drive/folders", {
      method: "POST", body: JSON.stringify({ name: `${prefix}-${suffix}`, parentId: "root" }),
    });
  }
  folders.A1 = await api("/api/drive/folders", {
    method: "POST", body: JSON.stringify({ name: `${prefix}-A1`, parentId: folders.A.id }),
  });
  const files = [];
  for (let index = 1; index <= 6; index += 1) {
    files.push(await upload("/api/upload", `${prefix}-${index}.txt`, `file-${index}`, "text/plain"));
  }
  await refreshDrive();

  const folderD = page.locator(`.drive-folder-group [data-item-id="${folders.D.id}"]`);
  const folderA = page.locator(`.drive-folder-group [data-item-id="${folders.A.id}"]`);
  await Promise.all([
    page.waitForResponse(response => response.url().includes("/api/items/reorder") && response.ok()),
    folderD.locator(".drag-handle").dragTo(folderA),
  ]);
  let listedFolders = await api("/api/drive/folders");
  let rootFolderIds = listedFolders.filter(item => item.parentId === "root").map(item => item.id);
  assert.ok(rootFolderIds.indexOf(folders.D.id) < rootFolderIds.indexOf(folders.A.id));

  const fileSix = page.locator(`.drive-file-group [data-item-id="${files[5].id}"]`);
  const fileOne = page.locator(`.drive-file-group [data-item-id="${files[0].id}"]`);
  await Promise.all([
    page.waitForResponse(response => response.url().includes("/api/items/reorder") && response.ok()),
    fileSix.locator(".drag-handle").dragTo(fileOne),
  ]);
  let rootFiles = await api("/api/drive/files?folderId=root");
  assert.ok(rootFiles.findIndex(item => item.id === files[5].id) < rootFiles.findIndex(item => item.id === files[0].id));

  await Promise.all([
    page.waitForResponse(response => response.url().includes("/api/items/reorder") && response.ok()),
    page.locator(`.drive-file-group [data-item-id="${files[5].id}"]`).getByTitle("下移").click(),
  ]);
  rootFiles = await api("/api/drive/files?folderId=root");
  assert.ok(rootFiles.findIndex(item => item.id === files[5].id) > rootFiles.findIndex(item => item.id === files[0].id));

  await page.locator(`.drive-file-group [data-item-id="${files[0].id}"]`).getByTitle("移动").click();
  await moveModalInto(`${prefix}-A`);
  await page.getByText(/移动完成：成功 1/).waitFor();
  assert.deepEqual((await api(`/api/drive/files?folderId=${folders.A.id}`)).map(item => item.id), [files[0].id]);

  await page.locator(`.drive-folder-group [data-item-id="${folders.C.id}"] .item-select`).click();
  await page.locator(`.drive-file-group [data-item-id="${files[1].id}"] .item-select`).click();
  await page.locator("#managementBar").getByRole("button", { name: "移动到", exact: true }).click();
  await moveModalInto(`${prefix}-B`);
  await page.getByText(/移动完成：成功 2/).waitFor();
  listedFolders = await api("/api/drive/folders");
  assert.equal(listedFolders.find(item => item.id === folders.C.id).parentId, folders.B.id);
  assert.deepEqual((await api(`/api/drive/files?folderId=${folders.B.id}`)).map(item => item.id), [files[1].id]);

  const conflictTarget = await upload("/api/upload", `${prefix}-conflict.txt`, "target", "text/plain", folders.A.id);
  const conflictSource = await upload("/api/upload", `${prefix}-conflict.txt`, "source", "text/plain");
  await refreshDrive();
  await page.locator(`.drive-file-group [data-item-id="${conflictSource.id}"]`).getByTitle("移动").click();
  await moveModalInto(`${prefix}-A`, "rename");
  await page.getByText(/移动完成：成功 1/).waitFor();
  const conflictRows = await api(`/api/drive/files?folderId=${folders.A.id}`);
  assert.ok(conflictRows.some(item => item.id === conflictTarget.id && item.name === `${prefix}-conflict.txt`));
  assert.ok(conflictRows.some(item => item.id === conflictSource.id && item.name === `${prefix}-conflict (1).txt`));

  await page.getByRole("button", { name: "我的图床", exact: true }).first().click();
  const imageA = await api("/api/image-host/folders", {
    method: "POST", body: JSON.stringify({ name: `${prefix}-images-A`, parentId: "root" }),
  });
  const imageB = await api("/api/image-host/folders", {
    method: "POST", body: JSON.stringify({ name: `${prefix}-images-B`, parentId: "root" }),
  });
  const pngBytes = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, ...Buffer.from("browser-move")];
  const image = await upload("/api/image-host/upload", `${prefix}.png`, pngBytes, "image/png");
  await page.getByTitle("刷新").first().click();
  await page.locator(`.image-folder-group [data-item-id="${imageA.id}"] .item-select`).click();
  await page.locator(`.image-file-group [data-item-id="${image.id}"] .image-select`).click();
  await page.locator("#imageSelectionBar").getByRole("button", { name: "移动到", exact: true }).click();
  await moveModalInto(`${prefix}-images-B`);
  await page.getByText(/移动完成：成功 2/).waitFor();
  const imageFolders = await api("/api/image-host/folders");
  assert.equal(imageFolders.find(item => item.id === imageA.id).parentId, imageB.id);
  assert.deepEqual((await api(`/api/image-host/files?folderId=${imageB.id}`)).map(item => item.id), [image.id]);

  await page.getByRole("button", { name: "我的网盘", exact: true }).first().click();
  await page.locator(".crumbs button").first().click();
  for (const width of [375, 390, 430]) {
    await page.setViewportSize({ width, height: 820 });
    await page.waitForTimeout(100);
    const dimensions = await page.evaluate(() => ({ body: document.body.scrollWidth, viewport: document.documentElement.clientWidth }));
    assert.ok(dimensions.body <= dimensions.viewport, `${width}px horizontal overflow: ${JSON.stringify(dimensions)}`);
    const row = page.locator(`.drive-folder-group [data-item-id="${folders.D.id}"]`);
    await row.getByTitle("下移").click();
    await page.getByText(/顺序已保存|已经在最下方/).waitFor();
    await row.getByTitle("移动").click();
    await page.locator(".move-modal").waitFor();
    await page.locator(".move-modal").getByRole("button", { name: "取消", exact: true }).click();
  }

  assert.deepEqual(pageErrors, []);
  console.log(JSON.stringify({
    desktopFolderDrag: true,
    desktopFileDrag: true,
    moveSingleFile: true,
    mixedBatchMove: true,
    conflictAutoRename: true,
    imageFolderAndFileMove: true,
    mobileViewports: [375, 390, 430],
    pageErrors: pageErrors.length,
  }));
} finally {
  await browser.close();
}
