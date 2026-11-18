export const fuelNames = { regu_gas: "Regular gasoline", diesel_gas: "Diesel" };
export const styles = {
  actual: { name: "Actual price", color: "#283643", line: "solid" },
  xgboost_delta__sokundo: { name: "XGBoost", color: "#ce542d", line: "solid" },
  linear_regression_time_lags__kay: {
    name: "Linear Regression",
    color: "#7562be",
    line: "dashed",
  },
  random_tree__heng: { name: "Random Tree", color: "#128173", line: "dotted" },
  baseline: { name: "Yesterday’s price", color: "#77828c", line: "dashed" },
};
export const styleOf = (m) =>
  styles[m.id] ?? { name: m.name, color: "#46729a", line: "solid" };
export const num = (n, digits = 0) =>
  n == null
    ? "—"
    : n.toLocaleString("en-US", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
export const date = (iso, year = false) =>
  new Date(iso + "T00:00:00Z").toLocaleDateString("en-GB", {
    timeZone: "UTC",
    day: "numeric",
    month: "short",
    ...(year ? { year: "numeric" } : {}),
  });
