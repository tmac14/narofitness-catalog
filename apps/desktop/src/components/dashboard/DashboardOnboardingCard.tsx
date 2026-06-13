import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";
import type { DashboardEmptyState } from "@/lib/dashboardData";
import { Button } from "@/components/ui/button";

type DashboardOnboardingCardProps = {
  emptyState: DashboardEmptyState;
};

export function DashboardOnboardingCard({ emptyState }: DashboardOnboardingCardProps) {
  return (
    <section
      className="dashboard-onboarding rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8"
      aria-labelledby="dashboard-onboarding-title"
    >
      <div className="mx-auto max-w-lg text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-primary">
          <BookOpen className="h-6 w-6" aria-hidden="true" />
        </div>
        <h2 id="dashboard-onboarding-title" className="text-lg font-semibold text-foreground">
          {emptyState.title}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {emptyState.description}
        </p>
        <Button asChild className="mt-5" size="sm">
          <Link to={emptyState.actionTo}>{emptyState.actionLabel}</Link>
        </Button>
      </div>
    </section>
  );
}
