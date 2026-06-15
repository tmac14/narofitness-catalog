import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import ImportPage from "@/pages/ImportPage";
import SourceDocumentIntakePage from "@/pages/SourceDocumentIntakePage";
import AdaptationStudioPage from "@/pages/AdaptationStudioPage";
import ProductsPage from "@/pages/ProductsPage";
import ProductDetailPage from "@/pages/ProductDetailPage";
import CatalogsPage from "@/pages/CatalogsPage";
import CatalogEditorPage from "@/pages/CatalogEditorPage";
import CategoriesPage from "@/pages/CategoriesPage";
import PriceListsPage from "@/pages/PriceListsPage";
import SettingsPage from "@/pages/SettingsPage";
import SuppliersPage from "@/pages/SuppliersPage";
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/suppliers" element={<SuppliersPage />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="/catalog-from-pdf" element={<SourceDocumentIntakePage />} />
        <Route path="/adaptations/:projectId" element={<AdaptationStudioPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/products/:id" element={<ProductDetailPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/catalogs" element={<CatalogsPage />} />
        <Route path="/catalogs/:id" element={<CatalogEditorPage />} />
        <Route path="/price-lists" element={<PriceListsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
