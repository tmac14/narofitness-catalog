import { useStatusBar } from "@/context/useStatusBar";
import { useDashboardData } from "@/hooks/useDashboardData";
import {
  buildRecentMovements,
  generalStatusSummary,
  getActionableRecommendations,
  getDashboardEmptyState,
  getPrimaryDashboardAction,
  shouldShowDashboardSidebar,
  shouldShowProcessModule,
  shouldShowSystemAlert,
} from "@/lib/dashboardData";
import { DashboardSkeleton } from "@/components/LoadingPage";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { DashboardHero } from "@/components/dashboard/DashboardHero";
import { DashboardKpiGrid } from "@/components/dashboard/DashboardKpiGrid";
import { DashboardOnboardingCard } from "@/components/dashboard/DashboardOnboardingCard";
import { DashboardRecentMovements } from "@/components/dashboard/DashboardRecentMovements";
import { DashboardRecentCatalogs } from "@/components/dashboard/DashboardRecentCatalogs";
import { DashboardProcessModule } from "@/components/dashboard/DashboardProcessModule";
import { DashboardSystemAlert } from "@/components/dashboard/DashboardSystemAlert";
import { DashboardRecommendations } from "@/components/dashboard/DashboardRecommendations";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const { health, activeJobs, recentTerminalJob, jobsError, setPanelOpen } = useStatusBar();
  const { kpis, recentPriceLists, recentCatalogs, catalogs, recentJobs, loading, errors, refresh } =
    useDashboardData();

  const showSkeleton = useDelayedLoading(loading);
  const connected = health.connected;
  const hasCatalogs = kpis.catalogs != null && kpis.catalogs > 0;
  const hasPriceLists = kpis.priceLists != null && kpis.priceLists > 0;

  const statusSummary = generalStatusSummary({ connected, hasPriceLists, hasCatalogs });
  const { primary, secondary } = getPrimaryDashboardAction({ hasCatalogs });
  const emptyState = getDashboardEmptyState({ hasCatalogs, catalogsError: errors.catalogs });

  const recommendations = getActionableRecommendations({
    catalogs,
    hasCatalogs,
    priceListsCount: kpis.priceLists,
  });

  const showSystemAlert = shouldShowSystemAlert({
    connected: health.connected,
    pdfEngine: health.pdfEngine,
    pdfEngineError: health.pdfEngineError,
    jobsError,
  });

  const showProcessModule = shouldShowProcessModule({
    activeJobsCount: activeJobs.length,
    recentTerminalFailed: recentTerminalJob?.status === "failed",
  });

  const showSidebar = shouldShowDashboardSidebar({
    recommendations,
    showSystemAlert,
    showProcessModule,
  });

  const movements = buildRecentMovements({
    priceLists: recentPriceLists,
    jobs: recentJobs,
    catalogs: recentCatalogs,
  });

  const openProcesses = () => setPanelOpen(true);

  if (showSkeleton) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="dashboard-page">
      <DashboardHero
        statusSummary={statusSummary}
        connected={connected}
        primaryAction={primary}
        secondaryAction={secondary}
      />

      <DashboardKpiGrid kpis={kpis} errors={errors} />

      <div className={cn("dashboard-layout", showSidebar && "dashboard-layout--with-sidebar")}>
        <div className="dashboard-layout__main">
          {emptyState ? (
            <DashboardOnboardingCard emptyState={emptyState} />
          ) : (
            <div className="dashboard-overview builder-panel space-y-6 p-4 sm:p-5">
              <DashboardRecentCatalogs
                catalogs={recentCatalogs}
                error={errors.catalogs}
                onRetry={refresh}
              />
              <DashboardRecentMovements
                movements={movements}
                priceListsError={errors.priceLists}
                jobsError={errors.jobs}
              />
            </div>
          )}
        </div>

        {showSidebar ? (
          <aside className="dashboard-layout__sidebar space-y-5">
            {showProcessModule ? <DashboardProcessModule onOpenProcesses={openProcesses} /> : null}
            {showSystemAlert ? (
              <DashboardSystemAlert
                health={health}
                jobsError={jobsError}
                onOpenProcesses={openProcesses}
              />
            ) : null}
            <DashboardRecommendations items={recommendations} />
          </aside>
        ) : null}
      </div>
    </div>
  );
}
