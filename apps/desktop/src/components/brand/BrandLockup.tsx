import { APP_BRAND_LOGOS } from "@/lib/appAssets";
import { cn } from "@/lib/utils";

type BrandLockupProps = {
  className?: string;
};

export function BrandLockup({ className }: BrandLockupProps) {
  return (
    <div className={cn("brand-lockup", className)}>
      <img
        src={APP_BRAND_LOGOS.catalogGrid}
        alt=""
        aria-hidden="true"
        className="brand-lockup__mark"
        width={36}
        height={36}
        decoding="async"
        fetchPriority="high"
      />
      <div className="brand-lockup__text">
        <p className="brand-lockup__title" aria-label="NaroCatalog">
          <span className="brand-lockup__title-naro">NARO</span>
          <span className="brand-lockup__title-catalog">CATALOG</span>
        </p>
        <p className="brand-lockup__subtitle" aria-label="by Narofitness">
          <span className="brand-lockup__subtitle-by">by</span>
          <span className="brand-lockup__subtitle-brand">NAROFITNESS</span>
        </p>
      </div>
    </div>
  );
}
