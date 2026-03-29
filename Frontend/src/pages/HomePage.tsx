import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold text-white">WHLTV</h1>

      <p className="text-slate-400 max-w-xl">CS stats and visualisations</p>

      <Link
        to="/rankings"
        className="inline-block bg-blue-600 hover:bg-blue-700 transition px-5 py-2.5 rounded-md text-sm font-medium text-white"
      >
        View Rankings
      </Link>

      <Link
        to="/vetos"
        className="inline-block bg-blue-600 hover:bg-blue-700 transition px-5 py-2.5 rounded-md text-sm font-medium text-white"
      >
        View Vetos
      </Link>
    </div>
  );
}
