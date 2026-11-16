import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { Status } from "../components/Status";

export default function Rankings() {
  const { data, error, loading } = useApi(() => api.rankings({ limit: 150 }));
  return (
    <section>
      <h1>Rankings</h1>
      <p className="muted">
        Z-scores vs. the draftable pool. The first load per season downloads from NBA.com and can take a few
        minutes.
      </p>
      <Status loading={loading} error={error} />
      {data && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th className="left">Player</th>
                {data.categories.map((c) => (
                  <th key={c.key}>{c.label}</th>
                ))}
                <th>Total</th>
                <th>Avail</th>
                <th>Adj</th>
              </tr>
            </thead>
            <tbody>
              {data.players.map((p, i) => (
                <tr key={p.PLAYER_ID}>
                  <td>{i + 1}</td>
                  <td className="left">{p.PLAYER_NAME}</td>
                  {data.categories.map((c) => {
                    const v = p[c.key] as number | null;
                    return (
                      <td key={c.key} className={v == null ? "" : v >= 0 ? "pos" : "neg"}>
                        {v == null ? "–" : v.toFixed(2)}
                      </td>
                    );
                  })}
                  <td>{p.TOTAL.toFixed(2)}</td>
                  <td>{p.AVAIL.toFixed(2)}</td>
                  <td className="strong">{p.ADJ_TOTAL.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
