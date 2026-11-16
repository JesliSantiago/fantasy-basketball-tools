import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { Status } from "../components/Status";

export default function Draft() {
  const { data, error, loading } = useApi(api.draft);
  return (
    <section>
      <h1>Draft board</h1>
      <Status loading={loading} error={error} />
      {data && (
        <div className="columns">
          <div>
            <h2>My team ({data.mine.length})</h2>
            <ul>
              {data.mine.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </div>
          <div>
            <h2>Taken ({data.taken.length})</h2>
            <ul>
              {data.taken.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
