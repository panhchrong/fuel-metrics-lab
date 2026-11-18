import { date, num, styleOf, styles } from "./study";

export function axisChart(dates, series, zero = false) {
  return {
    animation: false,
    textStyle: { fontFamily: "Inter, Arial, sans-serif" },
    grid: { top: 34, bottom: 31, left: 54, right: 18 },
    tooltip: {
      trigger: "axis",
      renderMode: "richText",
      confine: true,
      backgroundColor: "#fff",
      valueFormatter: (v) => (v == null ? "—" : num(v, 2)),
    },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "#cfd5d6" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#64717c",
        formatter: (d) => date(d),
        hideOverlap: true,
        margin: 12,
      },
    },
    yAxis: {
      type: "value",
      scale: !zero,
      splitNumber: 4,
      axisLabel: { color: "#64717c", formatter: (v) => num(v) },
      splitLine: { lineStyle: { type: "dashed", color: "#dfe4e6" } },
    },
    series,
  };
}

export function line(name, data, style, step = false) {
  return {
    name,
    data,
    type: "line",
    step,
    symbol: "none",
    itemStyle: { color: style.color },
    lineStyle: { color: style.color, width: 2.4, type: style.line },
    emphasis: { disabled: true },
  };
}

export function priceChart(snapshot, fuel, full, errors, selected) {
  const split = snapshot.dates.indexOf(snapshot.testStart);
  const start = full ? 0 : Math.max(0, split - 35);
  const dates = snapshot.dates.slice(start);
  const offset = split - start;
  const actual = fuel.actual.slice(start);
  const testIndex = new Map(fuel.dates.map((d, i) => [d, i]));
  const observed = line(
    errors ? "Price-change day" : "Actual price",
    errors ? dates.map(() => null) : actual,
    styles.actual,
    "end",
  );
  observed.markArea = {
    silent: true,
    itemStyle: { color: "rgba(239,121,69,.065)" },
    data: [[{ xAxis: snapshot.testStart }, { xAxis: dates.at(-1) }]],
  };
  observed.markLine = {
    silent: true,
    symbol: "none",
    lineStyle: { color: "#c26b47", type: "dashed", width: 1.3 },
    label: {
      position: "insideEndBottom",
      rotate: 0,
      formatter: "Backtest begins",
      color: "#9e482b",
      backgroundColor: "#ffecdf",
      padding: [4, 6],
      borderRadius: 3,
    },
    data: [{ xAxis: snapshot.testStart }],
  };
  if (errors)
    observed.markPoint = {
      symbol: "diamond",
      symbolSize: 9,
      label: { show: false },
      itemStyle: { color: "#33404c" },
      data: fuel.dates.flatMap((d, i) =>
        fuel.changed[i] ? [{ coord: [d, 0] }] : [],
      ),
    };
  const series = [observed];
  for (const m of fuel.models.filter((m) => selected.includes(m.id))) {
    const values = dates.map((d, i) => {
      const j = testIndex.get(d);
      if (j === undefined)
        return !errors && i === offset - 1 ? actual[i] : null;
      return errors ? Math.abs(m.values[j] - actual[i]) : m.values[j];
    });
    const s = line(styleOf(m).name, values, styleOf(m));
    s.z = m.id === "baseline" ? 2 : 4;
    series.push(s);
  }
  const option = axisChart(dates, series, errors);
  // The anchor joins the paths visually; it is an observation, never a forecast.
  option.tooltip.formatter = (items) => {
    const d = items[0]?.axisValue;
    if (!d) return "";
    const j = testIndex.get(d);
    const rows = [date(d, true)];
    if (!errors) rows.push("Actual price   " + num(actual[dates.indexOf(d)]));
    if (snapshot.filled.includes(d)) rows.push("Forward-filled price");
    if (j !== undefined) {
      if (errors) rows.push(fuel.changed[j] ? "Price-change day" : "Flat day");
      for (const m of fuel.models.filter((m) => selected.includes(m.id))) {
        rows.push(
          styleOf(m).name +
            "   " +
            num(
              errors
                ? Math.abs(m.values[j] - actual[dates.indexOf(d)])
                : m.values[j],
              2,
            ),
        );
      }
    }
    return rows.join("\n");
  };
  return option;
}
