import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DataTableScroll } from "@/components/ui/data-table";
import { cn } from "@/lib/utils";

export type CatalogLineItem = {
  id: string;
  sku: string;
  name: string;
  markup_percent: string | null;
  final_price_override: string | null;
  final_price: string | null;
  sort_order: number;
};

type SortableRowProps = {
  item: CatalogLineItem;
  defaultMarkup: string;
  onRemove: (id: string) => void;
  onMarkupBlur: (id: string, value: string) => void;
  onPriceBlur: (id: string, value: string) => void;
};

function SortableLineRow({
  item,
  defaultMarkup,
  disabled,
  disabledReason,
  onRemove,
  onMarkupBlur,
  onPriceBlur,
}: SortableRowProps & { disabled?: boolean; disabledReason?: string }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <TableRow
      ref={setNodeRef}
      style={style}
      className={cn(isDragging && "relative z-10 bg-muted/80 shadow-sm")}
      data-state={isDragging ? "selected" : undefined}
    >
      <TableCell className="w-10 p-2">
        <button
          type="button"
          disabled={disabled}
          title={disabled ? disabledReason : undefined}
          className="flex h-8 w-8 cursor-grab items-center justify-center rounded-md text-muted-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring active:cursor-grabbing disabled:cursor-not-allowed disabled:opacity-40"
          aria-label={
            disabled && disabledReason
              ? `${disabledReason} — ${item.name}`
              : `Reordenar ${item.name}`
          }
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
      </TableCell>
      <TableCell className="w-[120px] truncate font-mono text-xs">{item.sku}</TableCell>
      <TableCell className="max-w-[200px] truncate" title={item.name}>
        {item.name}
      </TableCell>
      <TableCell className="w-[88px]">
        <Input
          type="number"
          className="h-8 w-16"
          placeholder={defaultMarkup}
          defaultValue={item.markup_percent ?? ""}
          onBlur={(e) => onMarkupBlur(item.id, e.target.value)}
        />
      </TableCell>
      <TableCell className="w-[96px]">
        <Input
          type="number"
          step="0.01"
          className="h-8 w-20"
          defaultValue={item.final_price_override ?? ""}
          onBlur={(e) => onPriceBlur(item.id, e.target.value)}
        />
      </TableCell>
      <TableCell className="w-[88px] font-medium tabular-nums">{item.final_price ?? "—"}</TableCell>
      <TableCell className="w-10 p-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0"
          aria-label={`Eliminar ${item.name}`}
          onClick={() => onRemove(item.id)}
        >
          ×
        </Button>
      </TableCell>
    </TableRow>
  );
}

type Props = {
  items: CatalogLineItem[];
  defaultMarkup: string;
  disabled?: boolean;
  /** Shown on grip handles when reorder is temporarily disabled (e.g. while saving). */
  disabledReason?: string;
  onReorder: (items: CatalogLineItem[]) => void;
  onRemove: (id: string) => void;
  onMarkupBlur: (id: string, value: string) => void;
  onPriceBlur: (id: string, value: string) => void;
};

export function SortableCatalogLines({
  items,
  defaultMarkup,
  disabled = false,
  disabledReason,
  onReorder,
  onRemove,
  onMarkupBlur,
  onPriceBlur,
}: Props) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  function handleDragEnd(event: DragEndEvent) {
    if (disabled) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = items.findIndex((i) => i.id === active.id);
    const newIndex = items.findIndex((i) => i.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const next = [...items];
    const [moved] = next.splice(oldIndex, 1);
    next.splice(newIndex, 0, moved);
    onReorder(next);
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div aria-busy={disabled || undefined} aria-label={disabled ? disabledReason : undefined}>
        <DataTableScroll stickyHeader>
          <table className="w-full caption-bottom text-sm table-fixed">
            <TableHeader>
              <TableRow>
                <TableHead className="w-10" />
                <TableHead className="w-[120px]">SKU</TableHead>
                <TableHead>Nombre</TableHead>
                <TableHead className="w-[88px]">Margen %</TableHead>
                <TableHead className="w-[96px]">Precio fijo</TableHead>
                <TableHead className="w-[88px]">Precio</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="min-h-[8rem] h-32 text-center text-muted-foreground"
                    >
                      No hay líneas en esta página
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item) => (
                    <SortableLineRow
                      key={item.id}
                      item={item}
                      defaultMarkup={defaultMarkup}
                      disabled={disabled}
                      disabledReason={disabledReason}
                      onRemove={onRemove}
                      onMarkupBlur={onMarkupBlur}
                      onPriceBlur={onPriceBlur}
                    />
                  ))
                )}
              </TableBody>
            </SortableContext>
          </table>
        </DataTableScroll>
      </div>
    </DndContext>
  );
}
