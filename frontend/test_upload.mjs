import { writeFileSync, unlinkSync } from "node:fs";

const API = process.env.API_URL || "http://localhost:8000/api/v1/upload";

// Minimal valid MP4 (ftyp + moov box, ~28 bytes)
const FAKE_MP4 = Buffer.from(
  "0000001c667479706d703432000000006d7034326d70343169736f6d" +
  "000000086d6f6f7600000000",
  "hex"
);

const VIDEO = "test_video.mp4";
const LOG = "test_log.txt";

writeFileSync(VIDEO, FAKE_MP4);
writeFileSync(LOG, "DJI Flight Log - fake test data\nTimestamp: 2026-01-01T00:00:00Z\n");

async function run() {
  console.log(`POST ${API}`);

  const form = new FormData();
  form.append("name", "Test Flight");
  form.append("video", new Blob([FAKE_MP4], { type: "video/mp4" }), VIDEO);
  form.append("log", new Blob(["DJI Flight Log - fake test data\n"], { type: "text/plain" }), LOG);

  try {
    const res = await fetch(API, { method: "POST", body: form });
    console.log(`Status: ${res.status}`);

    const body = await res.text();
    try {
      console.log("Response:", JSON.stringify(JSON.parse(body), null, 2));
    } catch {
      console.log("Response:", body);
    }
  } catch (err) {
    console.error("Request failed:", err.message);
  } finally {
    unlinkSync(VIDEO);
    unlinkSync(LOG);
  }
}

run();
