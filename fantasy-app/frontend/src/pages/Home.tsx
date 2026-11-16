import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { Status } from "../components/Status";

export default function Home() {
  const { data, error, loading } = useApi(api.health);
  return (
    <section>
      <h1>Fantasy Basketball Tools</h1>
      <p>9-category rankings, draft board and roster check-ins, built on the fantasy-tools notebooks.</p>
      <Status loading={loading} error={error} />
      {data && (
        <p className="muted">
          API {data.status} · season {data.season}
        </p>
      )}
    </section>
  );
}
