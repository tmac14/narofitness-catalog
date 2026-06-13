import { useEffect, useRef, useState } from "react";

interface DelayedLoadingOptions {
  delayMs?: number;
  minShowMs?: number;
}

export function useDelayedLoading(
  isLoading: boolean,
  { delayMs = 300, minShowMs = 400 }: DelayedLoadingOptions = {},
) {
  const [showSkeleton, setShowSkeleton] = useState(false);
  const shownAtRef = useRef<number | null>(null);

  useEffect(() => {
    let delayTimer: ReturnType<typeof setTimeout> | undefined;
    let hideTimer: ReturnType<typeof setTimeout> | undefined;

    if (isLoading) {
      delayTimer = setTimeout(() => {
        shownAtRef.current = Date.now();
        setShowSkeleton(true);
      }, delayMs);
    } else if (shownAtRef.current !== null) {
      const elapsed = Date.now() - shownAtRef.current;
      const remaining = Math.max(0, minShowMs - elapsed);
      hideTimer = setTimeout(() => {
        shownAtRef.current = null;
        setShowSkeleton(false);
      }, remaining);
    } else {
      setShowSkeleton(false);
    }

    return () => {
      if (delayTimer) clearTimeout(delayTimer);
      if (hideTimer) clearTimeout(hideTimer);
    };
  }, [isLoading, delayMs, minShowMs]);

  return showSkeleton;
}
