const DAY = 86400000;
const fuels = ["regu_gas", "diesel_gas"];
const utc = day => new Date(day + "T00:00:00Z");
const iso = date => date.toISOString().slice(0, 10);
export const nextDay = day => iso(new Date(+utc(day) + DAY));
export const daysBetween = (start, end) => (+utc(end) - utc(start)) / DAY;

export function monthsAfter(day, months) {
  const origin = utc(day);
  const last = new Date(Date.UTC(origin.getUTCFullYear(), origin.getUTCMonth() + months + 1, 0));
  last.setUTCDate(Math.min(origin.getUTCDate(), last.getUTCDate()));
  return iso(last);
}

export function historyWithQuotes(snapshot, quotes) {
  const history = snapshot.dates.map((day, i) => ({
    day, regu_gas: snapshot.fuels.regu_gas.actual[i], diesel_gas: snapshot.fuels.diesel_gas.actual[i],
    source: snapshot.filled.includes(day) ? "Carried forward" : "Recorded",
  }));
  const limit = monthsAfter(history.at(-1).day, 3);
  for (const quote of quotes) {
    if (quote.day <= history.at(-1).day || quote.day > limit ||
        !fuels.every(f => Number.isFinite(quote[f]) && quote[f] > 0)) {
      throw new Error("Enter a later quote within the three-month window and a positive price for both fuels.");
    }
    for (let day = nextDay(history.at(-1).day); day < quote.day; day = nextDay(day)) {
      history.push({ ...history.at(-1), day, source: "Carried forward" });
    }
    history.push({ ...quote, source: "Added quote" });
  }
  return history;
}

function featureRow(history, fuel, other, day, origin) {
  const last = history.at(-1)[fuel];
  const date = utc(day);
  const weekday = (date.getUTCDay() + 6) % 7;
  let flatDays = 0;
  while (history.length - flatDays > 1 && history.at(-flatDays - 2)[fuel] === last) flatDays++;
  return {
    lag_1: last, lag_7: history.at(-7)[fuel], other_lag_1: history.at(-1)[other],
    roll_mean_7: history.slice(-7).reduce((sum, row) => sum + row[fuel], 0) / 7,
    day_index: daysBetween(origin, day), month: date.getUTCMonth() + 1, day_of_week: weekday,
    weekday_sin: Math.sin(2 * Math.PI * weekday / 7), weekday_cos: Math.cos(2 * Math.PI * weekday / 7),
    ten_day_boundary: Number([1, 11, 21].includes(date.getUTCDate())),
    last_change: last - history.at(-2)[fuel], flat_days: flatDays,
  };
}

function leaf(node, input, boosted) {
  while (Array.isArray(node)) {
    const [index, threshold, left, right] = node;
    const value = Math.fround(input[index]);
    // sklearn sends equality left. XGBoost uses strict float32 comparisons.
    const goLeft = boosted ? value < Math.fround(threshold) : value <= threshold;
    node = goLeft ? left : right;
  }
  return node;
}

function predict(name, model, row) {
  const input = model.features.map(key => row[key]);
  if (name === "Linear Regression") {
    return input.reduce((sum, value, i) =>
      sum + model.coefficients[i] * ((value - model.mean[i]) / model.scale[i]), model.intercept);
  }
  if (name === "Random Tree") return row.lag_1 + leaf(model.tree, input, false);
  if (name === "XGBoost") {
    const delta = model.trees.reduce((sum, tree) =>
      Math.fround(sum + Math.fround(leaf(tree, input, true))), Math.fround(model.base));
    return row.lag_1 + delta;
  }
  throw new Error("Unknown forecast model.");
}

export function forecastDays(history, end, bundle, name, limit) {
  const lastDay = history.at(-1).day;
  if (end < lastDay || end > limit || !Number.isFinite(daysBetween(lastDay, end))) {
    throw new Error("Choose a forecast date within the three-month window.");
  }
  const rows = [...history];
  for (let day = nextDay(lastDay); day <= end; day = nextDay(day)) {
    const prediction = { day, source: "Forecast" };
    // Both fuels read the same previous day, including when using the cross-fuel lag.
    for (const fuel of fuels) {
      const other = fuel === fuels[0] ? fuels[1] : fuels[0];
      const features = featureRow(rows, fuel, other, day, bundle.startDate);
      prediction[fuel] = predict(name, bundle.models[name][fuel], features);
      if (!Number.isFinite(prediction[fuel])) throw new Error("The model returned an invalid price.");
    }
    rows.push(prediction);
  }
  return rows.slice(history.length);
}
