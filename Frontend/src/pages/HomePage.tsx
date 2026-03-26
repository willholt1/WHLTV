import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div>
      <h1>WHLTV</h1>
      <p>Welcome to the app.</p>

      <p>
        <Link to="/rankings">View current rankings</Link>
      </p>
    </div>
  );
}