export function restoreVariantSheetFocus(
  event: Event,
  trigger: HTMLElement | null | undefined,
): void {
  event.preventDefault();
  if (trigger?.isConnected) {
    trigger.focus();
  }
}
