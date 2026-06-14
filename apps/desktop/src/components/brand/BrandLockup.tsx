import { cn } from "@/lib/utils";

type BrandLockupProps = {
  className?: string;
};

export function BrandLockup({ className }: BrandLockupProps) {
  return (
    <div className={cn("brand-lockup", className)}>
      <p className="brand-lockup__title" aria-label="NaroCatalog by Narofitness">
        <span className="brand-lockup__title-naro">NARO</span>
        <span className="brand-lockup__title-catalog">CATALOG</span>
        <span className="brand-lockup__byline">
          <span className="brand-lockup__byline-sep" aria-hidden="true">
            {" "}
            —{" "}
          </span>
          <span className="brand-lockup__byline-by">by</span>
          <span className="brand-lockup__byline-brand"> NAROFITNESS</span>
        </span>
      </p>
    </div>
  );
}
