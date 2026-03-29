import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import { RankingsPage } from "./features/rankings/pages/RankingsPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { VetosPage } from "./features/vetos/pages/vetosPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "rankings", element: <RankingsPage /> },
      { path: "vetos", element: <VetosPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
