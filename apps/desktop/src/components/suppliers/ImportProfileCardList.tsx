import type { ImportProfile } from "@/lib/api";
import { ImportProfileCard } from "@/components/suppliers/ImportProfileCard";
import { ResponsiveDataCardList } from "@/components/responsive/list";

export function ImportProfileCardList({ profiles }: { profiles: ImportProfile[] }) {
  return (
    <ResponsiveDataCardList>
      {profiles.map((profile, index) => (
        <li key={profile.id}>
          <ImportProfileCard profile={profile} index={index} />
        </li>
      ))}
    </ResponsiveDataCardList>
  );
}
