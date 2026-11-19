<script setup>
import { computed, onMounted, ref } from "vue";
import { CalendarDays, ChartSpline, Plus, Undo2 } from "lucide-vue-next";
import Plot from "./Plot.vue";
import { axisChart, line } from "./chart";
import { date, num, fuelNames, styles } from "./study";
import { daysBetween, forecastDays, historyWithQuotes, monthsAfter, nextDay } from "./forecast";

const props = defineProps({ snapshot: Object, fuelId: String, quotes: Array });
const emit = defineEmits(["update:quotes"]);
const seed = props.snapshot.dates.at(-1);
const limit = monthsAfter(seed, 3);
const history = computed(() => historyWithQuotes(props.snapshot, props.quotes));
const last = computed(() => history.value.at(-1));
const end = ref([monthsAfter(last.value.day, 1), limit].sort()[0]);
const model = ref("Random Tree");
const bundle = ref(null), loadError = ref(false);
const day = ref(nextDay(last.value.day)), regular = ref(""), diesel = ref("");
const daysLeft = computed(() => daysBetween(last.value.day, limit));
const minimum = computed(() => daysLeft.value ? nextDay(last.value.day) : limit);
const validEnd = computed(() => end.value >= minimum.value && end.value <= limit);
const forecast = computed(() => {
  if (!bundle.value || !validEnd.value) return [];
  return forecastDays(history.value, end.value, bundle.value, model.value, limit);
});
async function loadModels() {
  loadError.value = false;
  try {
    const response = await fetch(import.meta.env.BASE_URL + "study/forecast-models.json");
    if (!response.ok) throw Error();
    const data = await response.json();
    if (!data.models?.["Random Tree"] || !data.startDate) throw Error();
    bundle.value = data;
  } catch {
    loadError.value = true;
  }
}
onMounted(loadModels);
function addQuote() {
  const quote = { day: day.value, regu_gas: Number(regular.value), diesel_gas: Number(diesel.value) };
  if (quote.day <= last.value.day || quote.day > limit ||
      ![quote.regu_gas, quote.diesel_gas].every(v => Number.isFinite(v) && v > 0)) return;
  emit("update:quotes", [...props.quotes, quote]);
  if (!validEnd.value || end.value <= quote.day) end.value = [monthsAfter(quote.day, 1), limit].sort()[0];
  day.value = nextDay(quote.day);
  regular.value = diesel.value = "";
}
function undoQuote() {
  const quotes = props.quotes.slice(0, -1);
  day.value = nextDay(quotes.at(-1)?.day ?? seed);
  emit("update:quotes", quotes);
}
const color = "#b4512b";
const chart = computed(() => {
  const known = history.value.slice(Math.max(0, props.snapshot.dates.length - 28));
  const rows = known.concat(forecast.value);
  const fuel = props.fuelId;
  const prices = line("Price history", rows.map((r, i) => i < known.length ? r[fuel] : null), styles.actual, "end");
  const projected = line(model.value, rows.map((r,i) => i >= known.length - 1 ? r[fuel] : null),
    { color, line: "dashed" });
  if (forecast.value.length) {
    projected.markArea = { silent: true, itemStyle: { color: "#f6e1d755" },
      data: [[{ xAxis: last.value.day }, { xAxis: end.value }]] };
  }
  const option = axisChart(rows.map(r => r.day), [prices, projected]);
  option.tooltip.formatter = items => {
    const row = rows.find(r => r.day === items[0]?.axisValue);
    return row ? [date(row.day, true), row.source === "Forecast" ? model.value + " forecast" : row.source,
      num(row[fuel], 2) + " KHR/L"].join("\n") : "";
  };
  return option;
});
</script>

<template>
  <section class="panel forecast-panel">
    <div class="panel-head">
      <div>
        <div class="title-icon"><ChartSpline /><h2>Price forecast</h2></div>
        <p>{{ fuelNames[fuelId] }} · Daily · KHR/L</p>
      </div>
      <div class="controls">
        <label>Forecast model
          <select v-model="model">
            <option v-for="name in ['Random Tree', 'Linear Regression', 'XGBoost']" :key="name" :value="name">
              {{ name }}<template v-if="bundle?.models[name]?.[fuelId]?.author"> · {{ bundle.models[name][fuelId].author }}</template>
            </option>
          </select>
        </label>
        <label>Forecast through
          <input type="date" v-model="end" :min="minimum" :max="limit" :disabled="!daysLeft" required />
        </label>
      </div>
    </div>
    <p v-if="loadError" class="feedback" role="alert">Forecast models could not be loaded. <button @click="loadModels">Retry</button></p>
    <p v-else-if="!bundle" class="feedback" role="status">Loading fitted models…</p>
    <p v-else-if="!validEnd" class="feedback" role="alert">Choose an end date from {{ date(minimum, true) }} to {{ date(limit, true) }}.</p>
    <template v-else>
      <div class="forecast-summary" aria-live="polite">
        <template v-if="forecast.length">
          <strong>{{ num(forecast.at(-1)[fuelId], 2) }} <small>KHR/L</small></strong>
          <span>{{ date(end, true) }} estimate · {{ forecast.length }} forecast {{ forecast.length === 1 ? "day" : "days" }}</span>
        </template>
        <span v-else>Added observations reach the end of the three-month window.</span>
      </div>
      <Plot :option="chart" :label="fuelNames[fuelId] + ' price history and forecast'" />
      <div class="legend">
        <span class="actual"><i></i>Price history</span>
        <span class="actual"><i :style="{borderColor:color,borderTopStyle:'dashed'}"></i>{{ model }} forecast</span>
      </div>
    </template>
    <div class="chart-footer"><CalendarDays :size="15" /><span>Latest quote {{ date(last.day, true) }} · Forecast limit {{ date(limit, true) }}</span></div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <div><div class="title-icon"><Plus /><h2>Add price observations</h2></div>
        <p>Enter both posted prices to update the graph. Gaps carry the previous quote forward.</p></div>
    </div>
    <form v-if="daysLeft" class="quote-form controls" @submit.prevent="addQuote">
      <label>Quote date<input type="date" v-model="day" :min="nextDay(last.day)" :max="limit" required /></label>
      <label>Regular gasoline (KHR/L)<input type="number" v-model="regular" min="0.01" step="0.01" required /></label>
      <label>Diesel (KHR/L)<input type="number" v-model="diesel" min="0.01" step="0.01" required /></label>
      <button type="submit" class="add"><Plus :size="15" /> Add quote</button>
    </form>
    <div v-if="quotes.length" class="added">
      <span>{{ quotes.length }} added · Latest {{ date(last.day) }} · Regular {{ num(last.regu_gas, 2) }} · Diesel {{ num(last.diesel_gas, 2) }} KHR/L</span>
      <button @click="undoQuote"><Undo2 :size="14" /> Undo last quote</button>
    </div>
    <div class="chart-footer">Added quotes stay in this dashboard session. Beyond the latest quote, each predicted day supplies the inputs for the next. The study evaluated one-day forecasts.</div>
  </section>
</template>

<style scoped>
.controls { display: flex; flex-wrap: wrap; align-items: end; gap: 10px 14px; }
.controls label { display: grid; gap: 5px; font-size: 12px; font-weight: 550; color: var(--muted); }
.controls input, .controls select { font: inherit; font-size: 14px; color: var(--ink); background: white; padding: 8px 10px; border-radius: 6px; border: 1px solid #cfd6da; min-width: 0; min-height: 37px; }
.forecast-summary, .feedback { margin: 6px 24px 2px; }
.forecast-summary strong { display: block; font-size: 28px; letter-spacing: -.7px; }
.forecast-summary small { font-size: 14px; font-weight: 500; }
.forecast-summary span, .added { color: var(--muted); font-size: 13px; }
.quote-form { padding: 5px 24px 19px; }
.quote-form input[type=number] { width: 155px; }
.add, .added button { display: inline-flex; gap: 5px; align-items: center; border-radius: 6px; padding: 9px 12px; }
.add { background: #9b4426; color: white; min-height: 37px; }
.added { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 0 24px 12px; flex-wrap: wrap; }
.added button, .feedback button { color: #893e22; text-decoration: underline; }
@media(max-width:650px) {
  .forecast-summary,.feedback { margin: 5px 13px; }
  .controls { gap: 8px; }
  .quote-form, .added { padding: 6px 13px 14px; }
  .quote-form { display: grid; grid-template-columns: 1fr 1fr; }
  .quote-form label:first-child { grid-column: 1/-1; }
  .quote-form input[type=number] { width: 100%; }
  .add { justify-content: center; }
}
</style>
