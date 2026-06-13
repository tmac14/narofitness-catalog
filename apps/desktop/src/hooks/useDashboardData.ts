import { useCallback, useEffect, useState } from "react";
import {
  flattenCategories,
  listCatalogs,
  listCategories,
  listJobs,
  listMasters,
  listPriceLists,
  type CatalogListItem,
  type JobOut,
} from "@/lib/api";
import { buildKpiSnapshot, recentCatalogs, recentPriceLists } from "@/lib/dashboardData";

export type PriceListRow = {
  id: string;
  source_filename: string;
  imported_at: string;
  supplier_id: string;
};

export type DashboardLoadErrors = {
  products?: boolean;
  catalogs?: boolean;
  priceLists?: boolean;
  categories?: boolean;
  jobs?: boolean;
};

export type DashboardData = {
  kpis: ReturnType<typeof buildKpiSnapshot>;
  priceLists: PriceListRow[];
  recentPriceLists: PriceListRow[];
  catalogs: CatalogListItem[];
  recentCatalogs: CatalogListItem[];
  recentJobs: JobOut[];
  loading: boolean;
  errors: DashboardLoadErrors;
  refresh: () => void;
};

const INITIAL_KPIS = buildKpiSnapshot({
  productsTotal: null,
  catalogsCount: null,
  priceListsCount: null,
  categoriesCount: null,
});

export function useDashboardData(): DashboardData {
  const [kpis, setKpis] = useState(INITIAL_KPIS);
  const [priceLists, setPriceLists] = useState<PriceListRow[]>([]);
  const [catalogs, setCatalogs] = useState<CatalogListItem[]>([]);
  const [recentJobs, setRecentJobs] = useState<JobOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<DashboardLoadErrors>({});

  const load = useCallback(() => {
    setLoading(true);
    setErrors({});

    let productsTotal: number | null = null;
    let catalogsCount: number | null = null;
    let priceListsCount: number | null = null;
    let categoriesCount: number | null = null;
    const nextErrors: DashboardLoadErrors = {};

    const tasks = [
      listMasters({ page: 1, page_size: 1 })
        .then((res) => {
          productsTotal = res.total;
        })
        .catch(() => {
          nextErrors.products = true;
        }),
      listCatalogs()
        .then((res) => {
          catalogsCount = res.items.length;
          setCatalogs(res.items);
        })
        .catch(() => {
          nextErrors.catalogs = true;
          setCatalogs([]);
        }),
      listPriceLists()
        .then((res) => {
          priceListsCount = res.length;
          setPriceLists(res);
        })
        .catch(() => {
          nextErrors.priceLists = true;
          setPriceLists([]);
        }),
      listCategories()
        .then((res) => {
          categoriesCount = flattenCategories(res).length;
        })
        .catch(() => {
          nextErrors.categories = true;
        }),
      listJobs({ limit: 5 })
        .then((res) => {
          setRecentJobs(res.items);
        })
        .catch(() => {
          nextErrors.jobs = true;
          setRecentJobs([]);
        }),
    ];

    void Promise.all(tasks).finally(() => {
      setKpis(
        buildKpiSnapshot({
          productsTotal,
          catalogsCount,
          priceListsCount,
          categoriesCount,
        }),
      );
      setErrors(nextErrors);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return {
    kpis,
    priceLists,
    recentPriceLists: recentPriceLists(priceLists),
    catalogs,
    recentCatalogs: recentCatalogs(catalogs),
    recentJobs,
    loading,
    errors,
    refresh: load,
  };
}
