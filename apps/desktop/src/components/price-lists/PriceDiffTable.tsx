import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  priceDiffTableRowClass,
  type PriceDiffRow,
} from "@/components/price-lists/priceDiffLabels";

export function PriceDiffTable({ items }: { items: PriceDiffRow[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Referencia</TableHead>
          <TableHead>Nombre</TableHead>
          <TableHead>Precio A</TableHead>
          <TableHead>Precio B</TableHead>
          <TableHead>Diferencia</TableHead>
          <TableHead>Diferencia %</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((row) => (
          <TableRow key={row.sku} className={priceDiffTableRowClass(row.change_type)}>
            <TableCell>{row.sku}</TableCell>
            <TableCell>{row.name}</TableCell>
            <TableCell>{row.price_a ?? "—"}</TableCell>
            <TableCell>{row.price_b ?? "—"}</TableCell>
            <TableCell>{row.delta_abs ?? "—"}</TableCell>
            <TableCell>{row.delta_pct != null ? `${row.delta_pct}%` : "—"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
