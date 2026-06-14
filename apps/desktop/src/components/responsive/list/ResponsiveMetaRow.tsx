import type { ReactNode } from "react";

export function ResponsiveMetaRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="responsive-meta-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
