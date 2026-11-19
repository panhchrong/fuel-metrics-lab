<script setup>
import { computed } from "vue";
import { Route, Layers3, BookOpen } from "lucide-vue-next";
import { date, num, styleOf, fuelNames } from "./study";

const props = defineProps({ snapshot: Object, fuel: Object, fuelId: String });
const models = computed(() =>
  props.fuel.models.filter((m) => m.id !== "baseline"),
);
const descriptions = {
  linear_regression__kay: [
    "Standardize the selected inputs and fit a linear regression to the next day’s price.",
    "fuel_price_study.ipynb",
  ],
  random_tree__heng: [
    "Fit a shallow randomized decision tree to the daily price change. Smooth the estimate toward the average training change, halve it, and add it to yesterday’s price.",
    "fuel_price_study.ipynb · src/random_tree_model.py",
  ],
  xgboost__sokundo: [
    "Fit 100 depth-two boosted trees to the daily price change and add the estimated change to yesterday’s price.",
    "fuel_price_study.ipynb · src/gas_wrappers.py",
  ],
};
const steps = computed(() => [
  [
    "Build the daily price series",
    props.snapshot.observedDays +
      " observed rows cover both fuels. Sort the CSV by date, reindex daily, and carry the previous notification price forward on " +
      props.snapshot.filled.map((d) => date(d, true)).join(", ") +
      ".",
    "src/gas_common.py · load_clean_data",
  ],
  [
    "Construct past-only features",
    "Build price lags, a trailing seven-day average, calendar inputs and recent price-change features. The first seven days supply lag history.",
    "src/gas_common.py · make_features",
  ],
  [
    "Split in chronological order",
    "The training period covers " +
      props.snapshot.trainDays +
      " days from " +
      date(props.snapshot.trainStart) +
      " through " +
      date(
        props.snapshot.dates[
          props.snapshot.dates.indexOf(props.snapshot.testStart) - 1
        ],
      ) +
      ". The filled day supplies history. Reserve the next " +
      props.snapshot.testDays +
      " days for testing.",
    "src/gas_common.py · train_test_split_time",
  ],
  [
    "Select features and refit",
    "Compare six feature sets for each algorithm on four expanding 28-day validation windows. Choose the lowest pooled validation RMSE and refit on the observed prices in the training period.",
    "fuel_price_study.ipynb",
  ],
  [
    "Evaluate the saved models",
    "Run each bundle on its own feature columns using actual observations available before each test day. Compare daily predictions with observed prices and the persistence baseline. Reject bundles with training dates inside the holdout.",
    "src/compare_models.py · src/gas_common.py",
  ],
]);
</script>
<template>
  <section class="panel">
    <div class="panel-head">
      <div class="title-icon">
        <Route />
        <h2>Study workflow</h2>
      </div>
    </div>
    <ol class="timeline">
      <li v-for="[title, body, source] in steps">
        <h3>{{ title }}</h3>
        <p>{{ body }}</p>
        <code>{{ source }}</code>
      </li>
    </ol>
  </section>
  <section class="panel">
    <div class="panel-head">
      <div class="title-icon">
        <Layers3 />
        <h2>How each model predicts</h2>
      </div>
    </div>
    <div class="method-model" v-for="m in models">
      <h3>
        {{ styleOf(m).name }} <small>· {{ m.author }}</small>
      </h3>
      <p>{{ descriptions[m.id]?.[0] ?? m.name }}</p>
      <div class="feature-list">
        <code v-for="f in m.features">{{ f }}</code>
      </div>
      <small>{{ descriptions[m.id]?.[1] }}</small>
    </div>
  </section>
  <section class="panel conclusion">
    <div class="title-icon">
      <BookOpen />
      <h2>What the backtest supports</h2>
    </div>
    <p v-if="models.length">
      {{ styleOf(models[0]).name }} has the lowest fitted-model RMSE for
      {{ fuelNames[fuelId].toLowerCase() }} at
      {{ num(models[0].scores.RMSE, 2) }} KHR/L.
      {{
        styleOf([...fuel.models].sort((a, b) => a.scores.MAE - b.scores.MAE)[0])
          .name
      }}
      has the lowest MAE. Only {{ fuel.changed.filter(Boolean).length }} of
      {{ fuel.dates.length }} holdout days changed price, so evidence about
      predicting price jumps is limited.
    </p>
  </section>
</template>
