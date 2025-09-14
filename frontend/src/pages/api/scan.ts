import type { NextApiRequest, NextApiResponse } from "next";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { domain } = req.body;
  if (!domain || typeof domain !== "string") {
    return res.status(400).json({ error: "domain required" });
  }

  try {
    const client = await pool.connect();
    await client.query(
      `INSERT INTO scan_queue (domain)
       SELECT $1
       WHERE NOT EXISTS (SELECT 1 FROM scan_queue WHERE domain = $1 AND processed = false)`,
      [domain]
    );
    client.release();
    return res.status(200).json({ status: "queued" });
  } catch (err) {
    console.error("API /api/scan error:", err);
    return res.status(500).json({ error: "db error" });
  }
}
