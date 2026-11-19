<script setup>
import { ref, computed, onMounted } from "vue";
import {
  BookImage,
  Download,
  ExternalLink,
  Table2,
  ChartNoAxesCombined,
  ChartColumn,
  Image as ImageIcon,
} from "lucide-vue-next";
import { axisChart, line } from "./chart";
import notebookUrl from "../../fuel_price_study.ipynb?url";
import { fuelNames, date, num } from "./study";
import Plot from "./Plot.vue";
const props = defineProps({ snapshot: Object, fuel: Object, fuelId: String });
const gallery = ref(null),
  galleryError = ref(false),
  base = import.meta.env.BASE_URL + "study/";
const activeFigure = ref(0);
const stage = ref("Holdout");
const study = computed(() => gallery.value?.study);
const result = computed(() => study.value?.fuels[props.fuelId]);
const changed = computed(() => result.value.changed.filter(Boolean).length);
const validationPick = computed(() => result.value.models.find(m => m.name === result.value.choice));
const rows = computed(() => [...result.value.models].sort((a, b) =>
  stage.value === "Validation" ? a.validationRMSE - b.validationRMSE : a.rmse - b.rmse));
const figure = computed(() => gallery.value?.figures[activeFigure.value]);
const notes = {
  "What price can we use on the missing day?": ["Missing date", "The 26 June gap was filled with the last posted quote to build lagged inputs. Only observed prices were used as outcomes."],
  "How often do prices actually move?": ["Price revisions", "Most daily changes were zero. The large jumps stayed in the training data because they represent the revisions a forecast needs to anticipate."],
  "Does a weekly rhythm persist?": ["Timing of revisions", "Summer revisions often fell a week apart. By late training they clustered on the 1st, 11th and 21st, giving the study two calendar patterns to test."],
  "How much does feature selection matter?": ["Feature selection", "Four expanding validation windows tested six input sets. Yesterday’s quote and recent price history were the only sets selected for the fitted models."],
  "How accurate were the one-day forecasts?": ["Forecast errors", "Each forecast uses the prices available through the previous day. The largest errors line up with the few dates when the posted price changed."],
};
function figureNote(f) {
  return f.source === "fuel_price_study.ipynb" ? notes[f.title] : null;
}
function modelName(name) {
  return name === "Persistence" ? "Yesterday’s price" : name;
}
async function loadGallery() {
  galleryError.value = false;
  try {
    const r = await fetch(base + "notebook/gallery.json");
    if (!r.ok) throw Error();
    gallery.value = await r.json();
  } catch {
    galleryError.value = true;
  }
}
onMounted(loadGallery);
const history = computed(() =>
  axisChart(
    props.snapshot.dates,
    Object.entries(props.snapshot.fuels).map(([k, f]) =>
      line(
        fuelNames[k],
        f.actual,
        {
          color: k === "regu_gas" ? "#c85a35" : "#167d73",
          line: k === "regu_gas" ? "solid" : "dashed",
        },
        "end",
      ),
    ),
  ),
);
const deltas = computed(() => {
  const x = props.fuel.actual;
  const values = x.slice(1).map((v, i) => v - x[i]);
  return axisChart(
    props.snapshot.dates.slice(1),
    [
      {
        name: "Change (KHR/L)",
        type: "bar",
        data: values,
        itemStyle: { color: "#bc6143" },
      },
    ],
    true,
  );
});
</script>
<template>
  <div v-if="galleryError" class="panel gallery-body" role="status">
    Study results could not be loaded. <button class="retry" @click="loadGallery">Retry</button>
  </div>
  <p v-else-if="!gallery" role="status">Loading notebook results…</p>
  <template v-if="result">
    <section class="panel study-overview" aria-label="Notebook findings">
      <div class="study-choice">
        <span class="study-label">Forecast selected in validation</span>
        <h2>{{ modelName(result.choice) }}</h2>
        <p>{{ num(validationPick.validationRMSE, 2) }} KHR/L pooled RMSE across {{ study.folds }} expanding windows</p>
      </div>
      <div class="study-cadence">
        <h3>Price revisions during the holdout</h3>
        <p><strong>{{ changed }} changed</strong> · {{ result.testDates.length - changed }} flat days</p>
        <div class="day-strip" role="img" :aria-label="'Revision dates: ' + result.testDates.filter((d, i) => result.changed[i]).map(d => date(d, true)).join(', ')">
          <span v-for="(day, i) in result.testDates" :key="day" :class="{ revised: result.changed[i] }"
            :title="date(day, true) + (result.changed[i] ? ' · Price changed' : ' · Flat')" />
        </div>
        <div class="strip-range"><span>{{ date(result.testDates[0]) }}</span><span>{{ date(result.testDates.at(-1), true) }}</span></div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <div class="title-icon"><Table2 /><h2>Notebook model results</h2></div>
          <p>{{ fuelNames[fuelId] }} · {{ stage === 'Validation' ? study.featureSets + ' candidate feature sets' :
            result.trainDays + ' observed training days · ' + result.testDates.length + ' test days' }} · KHR/L</p>
        </div>
        <div class="segmented" role="group" aria-label="Model result view">
          <button v-for="view in ['Holdout', 'Validation', 'Change days']" :key="view"
            :aria-pressed="stage === view" @click="stage = view">{{ view }}</button>
        </div>
      </div>
      <div class="table-scroll">
        <table class="study-table">
          <thead><tr><th scope="col">Model</th>
            <template v-if="stage === 'Holdout'"><th scope="col">Test RMSE ↓</th><th scope="col">Test MAE</th></template>
            <template v-else-if="stage === 'Validation'"><th scope="col">Validation RMSE ↓</th><th scope="col">Selected inputs</th></template>
            <template v-else><th scope="col">Changed MAE</th><th scope="col">Flat MAE</th></template>
          </tr></thead>
          <tbody><tr v-for="m in rows" :key="m.name">
            <th scope="row">{{ modelName(m.name) }}</th>
            <template v-if="stage === 'Holdout'"><td>{{ num(m.rmse, 2) }}</td><td>{{ num(m.mae, 2) }}</td></template>
            <template v-else-if="stage === 'Validation'"><td>{{ num(m.validationRMSE, 2) }}</td><td>{{ m.inputs }}</td></template>
            <template v-else><td>{{ num(m.changeMAE, 2) }}</td><td>{{ num(m.flatMAE, 2) }}</td></template>
          </tr></tbody>
        </table>
      </div>
      <div class="chart-footer">
        {{ stage === "Validation" ? "Each algorithm kept the inputs with the lowest error on later validation dates." :
           stage === "Holdout" ? "RMSE gives large misses more weight. MAE is the average absolute miss." :
           "Average absolute error on dates when the posted price changed or stayed flat." }}
      </div>
    </section>
  </template>
  <section v-if="gallery" class="panel">
    <div class="panel-head">
      <div class="title-icon"><BookImage /><h2>Notebook figures</h2></div>
      <a class="notebook-link" :href="notebookUrl" download="fuel_price_study.ipynb"><Download :size="15" /> Download notebook</a>
    </div>
    <div v-if="figure" class="figure-reader">
      <div class="figure-list" role="group" aria-label="Choose a notebook figure">
        <button v-for="(f, i) in gallery.figures" :key="f.file" @click="activeFigure = i"
          :aria-pressed="activeFigure === i">{{ figureNote(f)?.[0] || f.title }}</button>
      </div>
      <figure>
        <figcaption>
          <h3>{{ figure.title }}</h3>
          <p v-if="figureNote(figure)">{{ figureNote(figure)[1] }}</p>
        </figcaption>
        <a :href="base + 'notebook/' + figure.file" target="_blank" rel="noopener" :aria-label="'Open full-size figure: ' + figure.title">
          <img :src="base + 'notebook/' + figure.file" :alt="figure.title" />
        </a>
        <div class="figure-source"><span>{{ figure.source }} · cell {{ figure.cell }}, output {{ figure.output }}</span>
          <a :href="base + 'notebook/' + figure.file" target="_blank" rel="noopener">Full size <ExternalLink :size="12" /></a>
        </div>
      </figure>
    </div>
    <p v-else class="gallery-body">No saved notebook figures are available.</p>
    <p v-for="f in gallery.unavailable" :key="f.source + f.cell + '-' + f.output" class="gallery-body">
      {{ f.source }} · cell {{ f.cell }}, output {{ f.output }} needs a saved image.
    </p>
  </section>
  <section class="panel">
    <div class="panel-head">
      <div>
        <div class="title-icon">
          <ChartNoAxesCombined />
          <h2>Daily retail prices</h2>
        </div>
        <p>
          Cleaned CSV · KHR/L · {{ date(snapshot.dates[0]) }} –
          {{ date(snapshot.dates.at(-1), true) }}
        </p>
      </div>
    </div>
    <Plot :option="history" label="Full history for both fuels" />
    <div class="legend">
      <span class="actual"
        ><i style="border-color: #c85a35"></i>Regular gasoline</span
      ><span class="actual"
        ><i style="border-color: #167d73; border-top-style: dashed"></i
        >Diesel</span
      >
    </div>
  </section>
  <section class="panel">
    <div class="panel-head">
      <div>
        <div class="title-icon">
          <ChartColumn />
          <h2>Daily price changes</h2>
        </div>
        <p>
          {{ fuelNames[fuelId] }} · Day-over-day difference in KHR/L · Cleaned
          CSV
        </p>
      </div>
    </div>
    <Plot :option="deltas" label="Day-over-day price changes" />
  </section>
  <section class="panel">
    <div class="panel-head">
      <div>
        <div class="title-icon">
          <ImageIcon />
          <h2>Holdout RMSE by model</h2>
        </div>
        <p>Study models and yesterday’s price · KHR/L</p>
      </div>
    </div>
    <a :href="base + 'model_comparison.png'" target="_blank" rel="noopener"
      ><img
        class="report-img"
        :src="base + 'model_comparison.png'"
        alt="Ranked horizontal bars of holdout RMSE for both fuels. Exact scores are in Model comparison."
    /></a>
  </section>
</template>

<style scoped>
.study-overview { display: grid; grid-template-columns: 1fr 1fr; }
.study-choice, .study-cadence { padding: 22px 24px; }
.study-choice { background: #fff3e9; border-left: 4px solid var(--orange); }
.study-label { color: #854525; font-size: 13px; font-weight: 600; }
.study-choice h2 { font-size: clamp(24px, 2.6vw, 34px); margin: 6px 0; }
.study-overview p, .figure-reader p { color: var(--muted); font-size: 13px; line-height: 1.5; margin: 4px 0; }
.study-cadence strong { color: #9c4326; }
.day-strip { display: flex; gap: 2px; margin: 9px 0 4px; }
.day-strip span { flex: 1; height: 16px; background: #e0e7e7; border-radius: 2px; }
.day-strip .revised { background: #b75230; }
.strip-range, .figure-source { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); }
.study-table th, .study-table td { width: auto; text-align: right; }
.study-table th:first-child { text-align: left; }
.study-table tbody th { font-size: 14px; font-weight: 500; letter-spacing: 0; background: transparent; color: var(--ink); }
.notebook-link, .figure-source a, .retry { display: inline-flex; align-items: center; gap: 6px; color: #814125; font-size: 13px; }
.notebook-link { border: 1px solid var(--border); padding: 7px 10px; border-radius: 6px; text-decoration: none; }
.notebook-link:hover, .figure-list button:hover { background: #f7f4f1; }
.figure-reader { display: grid; grid-template-columns: minmax(160px, 22%) 1fr; border-top: 1px solid var(--border); }
.figure-list { padding: 13px; background: #fafbfb; border-right: 1px solid var(--border); }
.figure-list button { display: block; width: 100%; text-align: left; padding: 11px; border-radius: 6px; color: var(--muted); }
.figure-list button[aria-pressed="true"] { background: #f7e8dc; color: #873f22; font-weight: 600; }
.figure-reader figure { margin: 0; padding: 18px 22px; min-width: 0; }
.figure-reader img { display: block; width: 100%; height: auto; margin: 12px 0; }
.figure-source { align-items: center; gap: 10px; flex-wrap: wrap; }
@media (max-width: 650px) {
  .study-overview, .figure-reader { grid-template-columns: 1fr; }
  .study-choice, .study-cadence, .figure-reader figure { padding: 14px; }
  .figure-list { display: flex; flex-wrap: wrap; gap: 3px; padding: 8px 10px; border-right: 0; border-bottom: 1px solid var(--border); }
  .figure-list button { width: auto; font-size: 12px; padding: 8px; }
  .study-table th, .study-table td { padding: 10px; white-space: normal; }
}
</style>
