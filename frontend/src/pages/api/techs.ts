// frontend/src/pages/api/techs.ts
import type { NextApiRequest, NextApiResponse } from "next";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const client = await pool.connect();

    const agg = await client.query(`
      SELECT t.name, COALESCE(t.category, 'Other') as category, count(*) as cnt
      FROM website_technologies wt
      JOIN technologies t ON t.id = wt.technology_id
      GROUP BY t.name, t.category
      ORDER BY cnt DESC
      LIMIT 200
    `);

    const domainsRes = await client.query(`
      SELECT w.domain, w.company_name, w.hosting, array_remove(array_agg(t.name), NULL) as techs
      FROM websites w
      LEFT JOIN website_technologies wt ON wt.website_id = w.id
      LEFT JOIN technologies t ON t.id = wt.technology_id
      GROUP BY w.id, w.domain, w.company_name, w.hosting
      ORDER BY w.domain
      LIMIT 2000
    `);

    client.release();

    res.status(200).json({
      techs: agg.rows,
      domains: domainsRes.rows.map((d: any) => ({
        domain: d.domain,
        company: d.company_name,
        hosting: d.hosting,
        techs: d.techs,
      })),
    });
  } catch (err) {
    console.error("API /api/techs error:", err);
    res.status(500).json({ error: "db error" });
  }
}
