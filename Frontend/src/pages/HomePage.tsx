import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div className="p-8 bg-black text-white">
      <h1>WHLTV</h1>
      <p>Welcome to the app.</p>

      <p>
        <Link to="/rankings">View current rankings</Link>
      </p>
    </div>
  );
}