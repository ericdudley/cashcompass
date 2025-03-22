<script lang="ts">
	import { formatAmount } from '$lib/format';
	import { scaleLinear, scaleBand } from 'd3-scale';

	// Props: accept byMonthTotals data as a prop
	let {
		data
	}: {
		data: { month: string; total: number }[];
	} = $props();

	// Dimensions and margins
	let width = $state(500);
	let height = 350;
	const padding = { top: 20, right: 15, bottom: 60, left: 50 };

	// Calculate max value for y scale domain
	let maxValue = $derived(Math.max(...data.map((d) => d.total)));
	// Round up to nearest 500 for a nice y-axis scale
	let yMax = $derived(Math.ceil(maxValue / 500) * 500);

	// Create tick values for y-axis
	let yTicks = $derived([0, yMax * 0.25, yMax * 0.5, yMax * 0.75, yMax]);

	// Set up scales
	let xScale = $derived(
		scaleBand()
			.domain(data.map((d) => d.month))
			.range([padding.left, width - padding.right])
			.padding(0.2)
	);

	let yScale = $derived(
		scaleLinear()
			.domain([0, yMax])
			.range([height - padding.bottom, padding.top])
	);

	// Calculate bar width based on scale
	let barWidth = $derived(xScale.bandwidth());

	// Format numbers with commas
	function formatNumber(num: number) {
		return formatAmount(num);
	}
</script>

<div class="chart" bind:clientWidth={width}>
	<svg {width} {height}>
		<!-- Bars -->
		<g class="bars">
			{#each data as d}
				<rect
					x={xScale(d.month)}
					y={yScale(d.total)}
					width={barWidth}
					height={height - padding.bottom - yScale(d.total)}
					fill="#4b7bec"
				/>

				<!-- Bar value on top -->
				<text
					x={(xScale(d.month) ?? 0) + barWidth / 2}
					y={yScale(d.total) - 5}
					text-anchor="middle"
					font-size="10"
				>
					{formatNumber(d.total)}
				</text>
			{/each}
		</g>

		<!-- Y-axis -->
		<g class="axis y-axis">
			{#each yTicks as tick}
				<g class="tick" transform="translate(0, {yScale(tick)})">
					<line
						x1={padding.left - 5}
						x2={width - padding.right}
						stroke="#fcd34d"
						stroke-dasharray="2"
					/>
					<text x={padding.left - 10} y="4" text-anchor="end">
						{formatNumber(tick)}
					</text>
				</g>
			{/each}
		</g>

		<!-- X-axis -->
		<g class="axis x-axis">
			{#each data as d}
				<g
					class="tick"
					transform="translate({(xScale(d.month) ?? 0) + barWidth / 2}, {height -
						padding.bottom +
						15})"
				>
					<text text-anchor="middle">
						{d.month}
					</text>
				</g>
			{/each}
		</g>

		<!-- Title -->
		<text x={width / 2} y={padding.top / 2} text-anchor="middle" font-size="14" font-weight="bold">
			Monthly Totals
		</text>
	</svg>
</div>

<style>
	.chart {
		width: 90%;
		max-width: 1280px;
		margin: 0 auto;
	}

	svg {
		border-radius: 8px;
	}

	.tick text {
		font-family: Poppins, sans-serif;
		font-size: 0.725em;
		font-weight: 200;
	}

	.tick line {
		opacity: 0.5;
	}

	.x-axis .tick text {
		font-size: 0.7em;
	}
</style>
