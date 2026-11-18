<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import {
  Fuel,
  LayoutDashboard,
  Route,
  ChartNoAxesCombined,
  MapPin,
  CalendarDays,
  FlaskConical,
  Trophy,
  Activity,
  TrendingDown,
  ChartSpline,
  ChevronDown,
  Droplet,
  Table2,
  ArrowDown,
  CircleHelp,
} from "lucide-vue-next";
import Plot from "./Plot.vue";
import Analysis from "./Analysis.vue";
import Forecast from "./Forecast.vue";
import Method from "./Method.vue";
import { date, num, fuelNames, styleOf, styles } from "./study";
import { priceChart } from "./chart";

const pages = [
  { name: "Model comparison", icon: LayoutDashboard },
  { name: "Forecast", icon: ChartSpline },
  { name: "Methodology", icon: Route },
  { name: "Data analysis", icon: ChartNoAxesCombined },
];
function pageFromHash() {
  return pages.find(p => "#" + p.name.toLowerCase().replaceAll(" ", "-") === location.hash)?.name ?? pages[0].name;
}
function syncTab() {
  tab.value = pageFromHash();
}
function openPage(name) {
  window.location.hash = name.toLowerCase().replaceAll(" ", "-");
}
const tab = ref(pageFromHash()),
  fuelId = ref("regu_gas"),
  snapshot = ref(null),
  loadError = ref(false);
const quotes = ref([]);
const mode = ref("Price"),
  full = ref(false),
  selected = ref([]),
  sort = ref("RMSE");
const fuel = computed(() => snapshot.value.fuels[fuelId.value]);
const trained = computed(() =>
  fuel.value.models.filter((m) => m.id !== "baseline"),
);
const best = computed(() => trained.value[0]);
const baseline = computed(() =>
  fuel.value.models.find((m) => m.id === "baseline"),
);
const gain = computed(() =>
  best.value && baseline.value
    ? 100 * (1 - best.value.scores.RMSE / baseline.value.scores.RMSE)
    : null,
);
const ranked = computed(() =>
  [...fuel.value.models].sort(
    (a, b) => a.scores[sort.value] - b.scores[sort.value],
  ),
);
const changed = computed(() => fuel.value.changed.filter(Boolean).length);
const chart = computed(() =>
  priceChart(
    snapshot.value,
    fuel.value,
    full.value,
    mode.value === "Daily error",
    selected.value,
  ),
);
const last = computed(() => snapshot.value.dates.at(-1));
const missing = computed(() =>
  Object.keys(styles).filter(
    (id) =>
      !["actual", "baseline"].includes(id) &&
      !trained.value.some((m) => m.id === id),
  ),
);
function setFuel(id) {
  fuelId.value = id;
  selected.value = trained.value.map((m) => m.id);
}
function toggle(id) {
  selected.value = selected.value.includes(id)
    ? selected.value.filter((v) => v !== id)
    : [...selected.value, id];
}
function spark(values) {
  const min = Math.min(...values),
    range = Math.max(...values) - min || 1;
  return values
    .map(
      (v, i) =>
        (i ? "L" : "M") +
        ((i * 108) / (values.length - 1)).toFixed(1) +
        "," +
        (29 - (v - min) * 24).toFixed(1),
    )
    .join(" ");
}
async function load() {
  loadError.value = false;
  try {
    const r = await fetch(import.meta.env.BASE_URL + "study/backtest.json");
    if (!r.ok) throw Error();
    const data = await r.json();
    if (
      !data.dates?.length ||
      !data.fuels?.regu_gas?.models ||
      !data.fuels?.diesel_gas?.models
    )
      throw Error();
    snapshot.value = data;
    setFuel(fuelId.value);
  } catch {
    snapshot.value = null;
    loadError.value = true;
  }
}
onMounted(load);
onMounted(() => window.addEventListener("hashchange", syncTab));
onBeforeUnmount(() => window.removeEventListener("hashchange", syncTab));
</script>
<template>
  <header class="mast">
    <div class="shell mast-inner">
      <div class="brand">
        <span class="brand-mark"><Fuel :size="23" /></span>Fuel<span>Lab</span>
      </div>
      <nav aria-label="Study pages">
        <button
          v-for="p in pages"
          :key="p.name"
          :aria-current="tab === p.name ? 'page' : undefined"
          :class="{ active: tab === p.name }"
          @click="openPage(p.name)"
        >
          <component :is="p.icon" :size="16" />{{ p.name }}
        </button>
      </nav>
      <span class="location"><MapPin :size="15" /> Cambodia</span>
    </div>
  </header>
  <main class="shell" v-if="snapshot">
    <div class="intro">
      <div>
        <div class="eyebrow">
          <span class="status-dot"></span> FUEL PRICE STUDY
        </div>
        <h1>{{ tab }}</h1>
        <p>
          {{
            tab === "Model comparison"
              ? "One-day-ahead predictions for Cambodia’s retail fuel prices."
              : tab === "Forecast"
                ? "Extend daily prices up to three months with the fitted notebook models."
                : tab === "Methodology"
                ? "Follow the evidence from daily prices to model selection."
                : "Explore the notebook’s price revisions, feature selection and forecast errors."
          }}
        </p>
      </div>
      <div class="fuel-control">
        <label for="fuel-select">Fuel type</label>
        <div>
          <Droplet :size="16" /><select
            id="fuel-select"
            :value="fuelId"
            @change="setFuel($event.target.value)"
          >
            <option v-for="(name, id) in fuelNames" :value="id">
              {{ name }}
            </option></select
          ><ChevronDown :size="14" />
        </div>
      </div>
    </div>
    <div
      v-if="(tab === 'Model comparison' || tab === 'Methodology') && (missing.length || snapshot.skipped.length)"
      class="notice"
      role="status"
    >
      Incomplete comparison.
      <span v-if="missing.length"
        >Unavailable for {{ fuelNames[fuelId] }}:
        {{ missing.map((id) => styles[id].name).join(", ") }}.</span
      >
      <div v-for="s in snapshot.skipped">{{ s.file }} — {{ s.reason }}</div>
    </div>
    <template v-if="tab === 'Model comparison'">
      <div class="metrics">
        <div class="metric winner">
          <div class="metric-label"><Trophy :size="16" /> Leading model</div>
          <strong>{{ best ? styleOf(best).name : "Unavailable" }}</strong
          ><small
            >Lowest model RMSE
            <span v-if="best" class="author">· {{ best.author }}</span></small
          ><Trophy class="watermark" :size="74" :stroke-width="1" />
        </div>
        <div class="metric">
          <div class="metric-label"><Activity :size="16" /> Test RMSE</div>
          <strong>{{ num(best?.scores.RMSE, 2) }} <em>KHR/L</em></strong
          ><small
            >{{ best ? styleOf(best).name : "No model" }} ·
            {{ snapshot.testDays }} test days</small
          ><svg
            v-if="best"
            class="spark"
            viewBox="0 0 111 34"
            aria-label="Daily absolute errors"
          >
            <path
              :d="
                spark(
                  best.values.map((v, i) =>
                    Math.abs(
                      v - fuel.actual[snapshot.dates.indexOf(fuel.dates[i])],
                    ),
                  ),
                )
              "
            />
          </svg>
        </div>
        <div class="metric">
          <div class="metric-label">
            <TrendingDown :size="16" /> RMSE vs. baseline
          </div>
          <strong
            >{{ num(gain === null ? null : Math.abs(gain), 2)
            }}<em
              >% {{ gain === null ? "" : gain >= 0 ? "lower" : "higher" }}</em
            ></strong
          ><small
            >Yesterday’s price ·
            {{ num(baseline?.scores.RMSE, 2) }} KHR/L</small
          >
        </div>
      </div>
      <section class="panel price-panel">
        <div class="panel-head">
          <div>
            <div class="title-icon">
              <ChartSpline :size="20" />
              <h2>Price trajectory</h2>
            </div>
            <p>
              {{ fuelNames[fuelId] }} <span>·</span> {{ snapshot.units }}
              <span>·</span> Daily
            </p>
          </div>
          <div class="segmented">
            <button
              v-for="v in ['Price', 'Daily error']"
              :aria-pressed="mode === v"
              @click="mode = v"
            >
              {{ v }}
            </button>
          </div>
        </div>
        <div class="chart-meta">
          <span
            >{{ mode === "Price" ? "RETAIL PRICE" : "ABSOLUTE ERROR" }} ·
            KHR/L</span
          ><label
            ><select aria-label="History range" v-model="full">
              <option :value="false">Recent history</option>
              <option :value="true">Full history</option>
            </select></label
          >
        </div>
        <Plot :option="chart" :label="fuelNames[fuelId] + ' ' + mode" />
        <div class="legend">
          <span class="actual"
            ><i v-if="mode === 'Price'"></i><b v-else>◆</b
            >{{ mode === "Price" ? "Actual price" : "Price-change day" }}</span
          ><button
            v-for="m in [...trained, baseline].filter(Boolean)"
            :aria-pressed="selected.includes(m.id)"
            @click="toggle(m.id)"
            :style="{ '--series': styleOf(m).color }"
          >
            <i :style="{ borderTopStyle: styleOf(m).line }"></i
            >{{ styleOf(m).name }}
          </button>
        </div>
        <div class="chart-footer">
          <CalendarDays :size="15" /><b>Holdout period</b
          ><span>{{ date(snapshot.testStart) }} – {{ date(last, true) }}</span
          ><span class="tag">{{ snapshot.testDays }} days</span>
          <a class="forecast-link" href="#forecast">Extend forecast →</a>
        </div>
      </section>
      <section class="panel">
        <div class="panel-head">
          <div>
            <div class="title-icon">
              <Table2 :size="19" />
              <h2>Model leaderboard</h2>
            </div>
            <p>Errors in KHR/L <span>·</span> Lower is better</p>
          </div>
          <label class="sort"
            ><ArrowDown :size="14" />Rank by
            <select v-model="sort" aria-label="Ranking metric">
              <option>RMSE</option>
              <option>MAE</option>
            </select></label
          >
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>RMSE</th>
                <th>MAE</th>
                <th>
                  Change-day MAE <small>({{ changed }})</small>
                </th>
                <th>
                  Flat-day MAE
                  <small>({{ fuel.dates.length - changed }})</small>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, i) in ranked" :key="m.id">
                <td>
                  <span class="rank" :class="{ first: i === 0 }">{{
                    i + 1
                  }}</span>
                </td>
                <td>
                  <strong
                    ><i :style="{ background: styleOf(m).color }"></i
                    >{{ styleOf(m).name }}</strong
                  ><small>{{ m.author }}</small>
                </td>
                <td :class="{ bold: sort === 'RMSE' }">
                  {{ num(m.scores.RMSE, 2) }}
                </td>
                <td :class="{ bold: sort === 'MAE' }">
                  {{ num(m.scores.MAE, 2) }}
                </td>
                <td>{{ num(m.changeMAE, 2) }}</td>
                <td>{{ num(m.flatMAE, 2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="chart-footer">
          <CircleHelp :size="16" /><span
            >RMSE gives large misses more weight. MAE is the average absolute
            miss.</span
          >
        </div>
      </section>
    </template>
    <Forecast v-else-if="tab === 'Forecast'" :snapshot="snapshot" :fuel-id="fuelId" v-model:quotes="quotes" />
    <Method
      v-else-if="tab === 'Methodology'"
      :snapshot="snapshot"
      :fuel="fuel"
      :fuel-id="fuelId"
    />
    <Analysis v-else :snapshot="snapshot" :fuel="fuel" :fuel-id="fuelId" />
    <footer>
      <div>
        <FlaskConical :size="15" /> FuelLab <span>/</span> Cambodia fuel price
        study
      </div>
      <div>
        Data through {{ date(last, true) }}
        <span aria-hidden="true">/</span>
        <a
          href="https://data.mef.gov.kh/km/datasets/pd_681d89b4dbc953000126f5e7"
          target="_blank"
          rel="noopener"
        >MEF fuel price dataset</a>
      </div>
    </footer>
  </main>
  <main v-else class="shell empty" role="status">
    <h1>{{ loadError ? "Study data unavailable" : "Loading study…" }}</h1>
    <p v-if="loadError">
      Generate the snapshot with python src/compare_models.py and retry.
    </p>
    <button v-if="loadError" @click="load">Retry</button>
  </main>
</template>
