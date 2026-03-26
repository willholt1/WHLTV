import { Link } from "react-router-dom";

export function NavBar() {
  return (
    <nav style={{ marginBottom: "1rem" }}>
      <Link to="/">Home</Link>
      {" | "}
      <Link to="/rankings">Rankings</Link>
    </nav>
  );
}