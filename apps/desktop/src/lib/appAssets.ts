const publicBase = import.meta.env.BASE_URL;

function publicAsset(path: string): string {
  const normalized = path.replace(/^\//, "");
  return `${publicBase}${normalized}`;
}

export const APP_ICONS = {
  mark: publicAsset("icons/app-mark.png"),
} as const;

export const APP_BRAND_LOGOS = {
  fullLockup: publicAsset("brand/logos/01_full_lockup_narocatalog_by_narofitness_initial.png"),
  oneLineLockup: publicAsset("brand/logos/02_one_line_lockup_narocatalog_white_green.png"),
  markMinimal: publicAsset("brand/logos/03_nr_mark_minimal_flat_white_green.png"),
  shieldMetalFrame: publicAsset(
    "brand/logos/04_nr_shield_original_logo_with_metal_gym_frame.png",
  ),
  dynamicRing: publicAsset("brand/logos/05_nr_dynamic_ring_mark.png"),
  futuristic3d: publicAsset("brand/logos/06_nr_futuristic_3d_mark.png"),
  wordmark3d: publicAsset("brand/logos/07_narofitness_3d_strong_wordmark_exploration.png"),
  armoredShield: publicAsset("brand/logos/08_armored_shield_catalog_cards_and_dumbbell.png"),
  catalogGrid: publicAsset("brand/logos/09_catalog_grid_equipment_tiles_nr.png"),
  circularTechDial: publicAsset("brand/logos/10_circular_tech_dial_gym_catalog_mark.png"),
  horizontalBlueprint: publicAsset("brand/logos/11_horizontal_equipment_blueprint_tag_nr.png"),
  roundedCard: publicAsset("brand/logos/12_rounded_catalog_card_dumbbell_nr.png"),
  documentShield: publicAsset("brand/logos/13_document_shield_dumbbell_nr.png"),
  stackedCard: publicAsset("brand/logos/14_stacked_catalog_card_dumbbell_badge_nr.png"),
  hexPlate: publicAsset("brand/logos/15_hex_plate_dumbbell_interface_nr.png"),
  hexMachine: publicAsset("brand/logos/16_hex_machine_catalog_cards_nr.png"),
  layeredCard: publicAsset("brand/logos/17_layered_catalog_card_barbell_nr.png"),
} as const;
