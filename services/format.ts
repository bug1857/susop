export function formatValue(val: any, fallbackUndefined = "Not Available", fallbackNull = "Not Calculated"): string {
  if (val === undefined) return fallbackUndefined;
  if (val === null) return fallbackNull;
  if (typeof val === "number" && isNaN(val)) return fallbackUndefined;
  if (typeof val === "string" && val.trim() === "") return fallbackUndefined;
  return String(val);
}

export function formatMetric(val: any, formatType?: "percent" | "emissions" | "number", fallbackUndefined = "Not Available", fallbackNull = "Not Calculated"): string {
  if (val === undefined) return fallbackUndefined;
  if (val === null) return fallbackNull;
  if (typeof val === "number" && isNaN(val)) return fallbackUndefined;
  if (typeof val === "string" && val.trim() === "") return fallbackUndefined;

  const num = Number(val);
  if (isNaN(num)) return String(val);

  if (formatType === "percent") {
    return `${(num * 100).toFixed(0)}%`;
  }
  if (formatType === "emissions") {
    return `${num.toFixed(1)} t`;
  }
  return String(num);
}
