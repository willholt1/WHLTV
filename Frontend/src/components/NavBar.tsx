import { Link } from "react-router-dom";

export function NavBar() {
  return (
    <nav className="bg-slate-800 border-b border-slate-700">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <span className="text-white font-semibold text-lg">
          WHLTV
        </span>

        <div className="flex gap-6 text-sm">
          <Link
            to="/"
            className="hover:text-white transition-colors"
          >
            Home
          </Link>

          <Link
            to="/rankings"
            className="hover:text-blue-400 transition-colors"
          >
            Rankings
          </Link>
        </div>
      </div>
    </nav>
  );
}