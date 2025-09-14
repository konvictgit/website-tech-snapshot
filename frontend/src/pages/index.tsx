// frontend/src/pages/index.tsx
import React from "react";
import useSWR from "swr";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type ApiTech = { name: string; category: string; cnt: string };
type ApiDomain = {
  domain: string;
  techs: string[];
  company?: string;
  hosting?: string;
};
type ApiResponse = { techs?: ApiTech[]; domains?: ApiDomain[]; error?: string };

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Home() {
  const { data, error, mutate } = useSWR<ApiResponse>("/api/techs", fetcher);
  const [query, setQuery] = React.useState("");
  const [scanning, setScanning] = React.useState(false);
  const [status, setStatus] = React.useState<string | null>(null);
  const [pendingDomain, setPendingDomain] = React.useState<string | null>(null);

  if (error) return <div>Error loading data</div>;
  if (!data) return <div>Loading...</div>;

  const techs = (data.techs || []).map((t) => ({
    name: t.name,
    category: t.category || "Other",
    count: Number(t.cnt),
  }));

  const domains = data.domains || [];
  const filtered = domains.filter(
    (d) =>
      d.domain.toLowerCase().includes(query.toLowerCase()) ||
      (d.company || "").toLowerCase().includes(query.toLowerCase())
  );

  const handleScan = async () => {
    if (!query) return;
    setScanning(true);
    setPendingDomain(query);
    setStatus("Queuing scan...");

    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ domain: query }),
      });
      const json = await res.json();

      if (json.status === "queued") {
        setStatus(`Domain "${query}" queued for scanning ✅`);
        setTimeout(() => mutate(), 5000);
      } else {
        setStatus(`Scan failed: ${json.error || "unknown error"}`);
        setPendingDomain(null);
      }
    } catch {
      setStatus("Error while queuing scan ❌");
      setPendingDomain(null);
    } finally {
      setScanning(false);
    }
  };

  const pendingStillMissing =
    pendingDomain &&
    !domains.some(
      (d) => d.domain.toLowerCase() === pendingDomain.toLowerCase()
    );

  return (
    <div style={{ padding: 24, fontFamily: "Inter, sans-serif" }}>
      <h1 style={{ marginBottom: 12 }}>Mini MixRank — Tech Overview</h1>

      {/* Search + Scan */}
      <div style={{ marginBottom: 18, display: "flex", gap: 8 }}>
        <input
          placeholder="Search domains or companies..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            padding: 8,
            flex: 1,
            border: "1px solid #ccc",
            borderRadius: 4,
          }}
        />
        <button
          onClick={handleScan}
          disabled={scanning || !query}
          style={{
            padding: "8px 16px",
            background: "#111827",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: scanning ? "wait" : "pointer",
          }}
        >
          {scanning ? "Scanning..." : "Scan"}
        </button>
      </div>
      {status && <p>{status}</p>}

      {/* Chart */}
      <div style={{ height: 360 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={techs}>
            <XAxis dataKey="name" hide />
            <YAxis />
            <Tooltip
              formatter={(value: any, name: any, props: any) => [
                value,
                props.payload.name,
              ]}
            />
            <Bar dataKey="count" fill="#111827" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Domains Table */}
      <h2 style={{ marginTop: 24 }}>Domains</h2>
      {filtered.length === 0 && !pendingStillMissing ? (
        <p>No domains match your search.</p>
      ) : (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            marginTop: 8,
            fontSize: 14,
          }}
        >
          <thead>
            <tr style={{ background: "#f9fafb" }}>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #ddd",
                  padding: "10px 12px",
                  width: 50,
                }}
              >
                #
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #ddd",
                  padding: "10px 12px",
                }}
              >
                Domain
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #ddd",
                  padding: "10px 12px",
                }}
              >
                Company
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #ddd",
                  padding: "10px 12px",
                }}
              >
                Hosting
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #ddd",
                  padding: "10px 12px",
                }}
              >
                Technologies
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d, idx) => (
              <tr
                key={d.domain}
                style={{
                  background: idx % 2 === 0 ? "#fff" : "#f8f8f8",
                }}
              >
                <td style={{ padding: "8px 12px", fontWeight: 500 }}>
                  {idx + 1}
                </td>
                <td style={{ padding: "8px 12px" }}>{d.domain}</td>
                <td style={{ padding: "8px 12px" }}>{d.company || "-"}</td>
                <td style={{ padding: "8px 12px" }}>{d.hosting || "-"}</td>
                <td style={{ padding: "8px 12px" }}>
                  {(d.techs || []).join(", ")}
                </td>
              </tr>
            ))}
            {pendingStillMissing && (
              <tr style={{ background: "#fff" }}>
                <td style={{ padding: "8px 12px", fontWeight: 500 }}>•</td>
                <td style={{ padding: "8px 12px" }}>{pendingDomain}</td>
                <td style={{ padding: "8px 12px", color: "gray" }}>
                  ⏳ Scanning...
                </td>
                <td style={{ padding: "8px 12px", color: "gray" }}>
                  ⏳ Scanning...
                </td>
                <td style={{ padding: "8px 12px", color: "gray" }}>
                  ⏳ Scanning...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
