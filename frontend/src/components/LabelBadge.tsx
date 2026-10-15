import type { Label } from "@/lib/api";
import { LABEL_STYLE, LABEL_TEXT } from "@/lib/labels";

export default function LabelBadge({ label }: { label: Label }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${LABEL_STYLE[label]}`}>
      {LABEL_TEXT[label]}
    </span>
  );
}
