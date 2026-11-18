<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import { use, init } from "echarts/core";
import { LineChart, BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkAreaComponent,
  MarkPointComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";

use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkAreaComponent,
  MarkPointComponent,
  SVGRenderer,
]);
const props = defineProps({ option: Object, label: String });
const el = ref();
const keyboardDetail = ref("");
let chart,
  observer,
  cursor = 0;
function draw() {
  keyboardDetail.value = "";
  cursor = props.option.xAxis.data.length - 1;
  chart.setOption(props.option, true);
}
function inspect(event) {
  if (event.key === "ArrowLeft") cursor--;
  if (event.key === "ArrowRight") cursor++;
  cursor = Math.max(0, Math.min(props.option.xAxis.data.length - 1, cursor));
  const day = props.option.xAxis.data[cursor];
  const formatter = props.option.tooltip.formatter;
  keyboardDetail.value = formatter
    ? formatter([{ axisValue: day }])
    : [
        day,
        ...props.option.series.map(
          (s) => s.name + "   " + s.data[cursor].toLocaleString(),
        ),
      ].join("\n");
}
onMounted(() => {
  chart = init(el.value, null, { renderer: "svg" });
  draw();
  observer = new ResizeObserver(() => chart.resize());
  observer.observe(el.value);
});
watch(
  () => props.option,
  () => {
    if (chart) draw();
  },
);
onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
});
</script>
<template>
  <div class="plot-wrap">
    <div
      class="plot"
      ref="el"
      tabindex="0"
      role="group"
      :aria-label="label + '. Use left and right arrows to inspect dates.'"
      @focus="inspect"
      @keydown.left.prevent="inspect"
      @keydown.right.prevent="inspect"
      @blur="keyboardDetail = ''"
    ></div>
    <output v-if="keyboardDetail" class="keyboard-detail" aria-live="polite">{{
      keyboardDetail
    }}</output>
  </div>
</template>
