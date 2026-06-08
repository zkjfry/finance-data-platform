import { createHashRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CompanyDetailPage } from "./pages/CompanyDetailPage";
import { CompanySearchPage } from "./pages/CompanySearchPage";
import { DashboardPage } from "./pages/DashboardPage";
import { MarketsPage } from "./pages/MarketsPage";
import { NewsPage } from "./pages/NewsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SearchPage } from "./pages/SearchPage";

const router = createHashRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "markets",
        element: <MarketsPage />,
      },
      {
        path: "companies",
        element: <CompanySearchPage />,
      },
      {
        path: "companies/:ticker",
        element: <CompanyDetailPage />,
      },
      {
        path: "news",
        element: <NewsPage />,
      },
      {
        path: "reports",
        element: <ReportsPage />,
      },
      {
        path: "search",
        element: <SearchPage />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}