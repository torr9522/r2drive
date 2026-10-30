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
const context = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
const page = await context.newPage();
const consoleErrors = [];
const pageErrors = [];
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("pageerror", error => pageErrors.push(error.message));

try {
  await page.goto(baseURL, { waitUntil: "networkidle" });
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);
  await page.locator("form.card button.primary").click();
  await page.getByRole("heading", { name: "我的网盘" }).waitFor();

  const scrollPrefix = await page.evaluate(async () => {
    const prefix = `scroll-${Date.now()}-`;
    for (let index = 0; index < 28; index += 1) {
      const response = await fetch("/api/drive/folders", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: `${prefix}${String(index).padStart(2, "0")}`, parentId: "root" }),
      });
      if (!response.ok && response.status !== 409) throw new Error(await response.text());
    }
    return prefix;
  });
  await Promise.all([
    page.waitForResponse(response => response.url().includes("/api/stats") && response.ok()),
    page.getByTitle("刷新").first().click(),
  ]);
  await page.getByText(`${scrollPrefix}27`, { exact: true }).waitFor();

  const search = page.locator("#search");
  await search.fill(scrollPrefix);
  await page.locator(".work").evaluate(node => { node.scrollTop = 650; });
  await search.focus();
  await page.evaluate(() => { window.__stableShell = document.querySelector(".shell"); });
  const large = Buffer.alloc(24 * 1024 * 1024, 0x61);
  await page.locator("#fileInput").setInputFiles({ name: "large-upload.bin", mimeType: "application/octet-stream", buffer: large });
  await search.focus();
  await page.waitForTimeout(250);
  const duringUpload = await page.evaluate(() => ({
    focused: document.activeElement?.id,
    sameShell: document.querySelector(".shell") === window.__stableShell,
    scrollTop: document.querySelector(".work")?.scrollTop || 0,
  }));
  assert.equal(duringUpload.focused, "search");
  assert.equal(duringUpload.sameShell, true);
  assert.ok(duringUpload.scrollTop > 100, `scroll reset during upload: ${duringUpload.scrollTop}`);
  await page.locator("#driveUploads .task span", { hasText: "上传完成" }).waitFor({ timeout: 60_000 });
  const afterUpload = await page.evaluate(() => ({
    focused: document.activeElement?.id,
    sameShell: document.querySelector(".shell") === window.__stableShell,
    scrollTop: document.querySelector(".work")?.scrollTop || 0,
  }));
  assert.deepEqual(afterUpload, { focused: "search", sameShell: true, scrollTop: afterUpload.scrollTop });
  assert.ok(afterUpload.scrollTop > 100, `scroll reset after upload: ${afterUpload.scrollTop}`);

  await search.fill("");
  const targets = await page.evaluate(async () => {
    const create = async name => {
      const response = await fetch("/api/drive/folders", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, parentId: "root" }),
      });
      return response.json();
    };
    return { source: await create(`queue-source-${Date.now()}`), other: await create(`queue-other-${Date.now()}`) };
  });
  await page.getByTitle("刷新").first().click();
  await page.getByText(targets.source.name, { exact: true }).click();
  await page.locator("#fileInput").setInputFiles([
    { name: "queue-large.bin", mimeType: "application/octet-stream", buffer: Buffer.alloc(12 * 1024 * 1024, 0x62) },
    { name: "queue-small.txt", mimeType: "text/plain", buffer: Buffer.from("queued") },
  ]);
  await page.getByRole("button", { name: "我的网盘", exact: true }).last().click();
  await page.getByText(targets.other.name, { exact: true }).click();
  const finalQueueTask = page.locator("#driveUploads .task", { hasText: "queue-small.txt" });
  await finalQueueTask.waitFor();
  await finalQueueTask.getByText("上传完成", { exact: true }).waitFor({ timeout: 60_000 });
  const frozenTarget = await page.evaluate(async sourceId => {
    const response = await fetch(`/api/drive/files?folderId=${encodeURIComponent(sourceId)}`);
    return response.json();
  }, targets.source.id);
  assert.deepEqual(frozenTarget.map(item => item.name).sort(), ["queue-large.bin", "queue-small.txt"]);

  await page.getByRole("button", { name: "我的图床", exact: true }).first().click();
  await page.locator("#imageFileInput").setInputFiles({
    name: "valid.png", mimeType: "image/png",
    buffer: Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.from("browser-test")]),
  });
  await page.locator("#imageUploads .task", { hasText: "valid.png" }).getByText(/上传完成/).waitFor({ timeout: 30_000 });
  await page.locator("#imageFileInput").setInputFiles({ name: "invalid.png", mimeType: "image/png", buffer: Buffer.from("invalid") });
  await page.locator("#appToast").getByText(/上传失败：不支持该图片格式/).waitFor({ timeout: 30_000 });

  for (const width of [375, 390, 430]) {
    await page.setViewportSize({ width, height: 820 });
    await page.waitForTimeout(100);
    const dimensions = await page.evaluate(() => ({
      body: document.body.scrollWidth,
      viewport: document.documentElement.clientWidth,
    }));
    assert.ok(dimensions.body <= dimensions.viewport, `${width}px horizontal overflow: ${JSON.stringify(dimensions)}`);
    await page.locator(".mobile-menu-button").click();
    await page.locator("#mobileDrawer.open").waitFor();
    await page.locator("#drawerBackdrop").click({ position: { x: width - 5, y: 20 } });
  }

  assert.deepEqual(pageErrors, []);
  console.log(JSON.stringify({
    desktopUploadScroll: duringUpload.scrollTop,
    desktopUploadFocus: duringUpload.focused,
    stableShellDuringAndAfterUpload: true,
    frozenQueueTargetFiles: frozenTarget.map(item => item.name).sort(),
    mobileViewports: [375, 390, 430],
    pageErrors: pageErrors.length,
    expectedHttpConsoleErrors: consoleErrors.length,
  }));
} finally {
  await browser.close();
}
