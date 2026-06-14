import type { ImportProfile } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { parserLabel } from "@/components/suppliers/parserLabels";
import {
  ResponsiveDataCard,
  ResponsiveMetaGrid,
  ResponsiveMetaRow,
} from "@/components/responsive/list";

export function ImportProfileCard({
  profile,
  index,
}: {
  profile: ImportProfile;
  index: number;
}) {
  return (
    <ResponsiveDataCard index={index}>
      <h3 className="text-sm font-medium">{profile.name}</h3>
      <ResponsiveMetaGrid>
        <ResponsiveMetaRow label="Formato">{parserLabel(profile.parser_key)}</ResponsiveMetaRow>
        <ResponsiveMetaRow label="Por defecto">
          {profile.is_default ? (
            <Badge variant="success">Sí</Badge>
          ) : (
            <span className="text-muted-foreground">—</span>
          )}
        </ResponsiveMetaRow>
      </ResponsiveMetaGrid>
    </ResponsiveDataCard>
  );
}
