import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import { RankingsPage } from "./features/rankings/pages/RankingsPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "rankings", element: <RankingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);