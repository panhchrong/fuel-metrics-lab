<script setup>
import { computed } from "vue";
import { Route, Layers3, BookOpen } from "lucide-vue-next";
import { date, num, styleOf, fuelNames } from "./study";

const props = defineProps({ snapshot: Object, fuel: Object, fuelId: String });
const models = computed(() =>
  props.fuel.models.filter((m) => m.id !== "baseline"),
);
const descriptions = {
  linear_regression_time_lags__kay: [
    "Standardize the seven inputs and fit a linear regression to the price level. The saved estimator and the project README describe Kay’s pipeline. The checkout does not include its training script.",
    "README.md · saved Linear Regression bundle",
  ],
  random_tree__heng: [
    "Learn the change from yesterday with a regularized decision tree. Tune on four chronological 28-day validation folds inside training, select a simpler tree within one standard error, then refit the selected configuration.",
    "src/train_random_tree.py · src/random_tree_model.py",
  ],
  xgboost_delta__sokundo: [
    "Fit 100 depth-two boosted trees to the change from yesterday using four lag-based inputs. Add the estimated change to yesterday’s actual price.",
    "src/train_xgboost.py · src/gas_wrappers.py",
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
    "Use the day index, month, weekday, one- and seven-day price lags, yesterday’s other-fuel price and a seven-day mean ending yesterday. Drop the first seven days while the lag window fills.",
    "src/gas_common.py · make_features",
  ],
  [
    "Split in chronological order",
    "Training uses " +
      props.snapshot.trainDays +
      " days from " +
      date(props.snapshot.trainStart) +
      " through " +
      date(
        props.snapshot.dates[
          props.snapshot.dates.indexOf(props.snapshot.testStart) - 1
        ],
      ) +
      ". Reserve the next " +
      props.snapshot.testDays +
      " days for testing.",
    "src/gas_common.py · train_test_split_time",
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
