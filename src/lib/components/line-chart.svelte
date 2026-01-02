<script lang="ts">
	import { formatAmount } from '$lib/format';
	import { scaleLinear, scalePoint } from 'd3-scale';

	let {
		data,
		months
	}: {
		data: { [accountLabel: string]: { [month: string]: number } };
		months: string[];
	} = $props();

	// Dimensions and margins
	let width = $state(500);
	let height = 350;
	const padding = { top: 20, right: 120, bottom: 60, left: 70 };

	// Colors for different accounts
	const colors = [
		'#4b7bec',
		'#26de81',
		'#fd9644',
		'#fc5c65',
		'#a55eea',
		'#20bf6b',
		'#eb3b5a',
		'#fa8231',
		'#2d98da',
		'#8854d0'
	];

	// Get all values to determine y scale
	let allValues = $derived.by(() => {
		const values: number[] = [];
		Object.values(data).forEach((accountData) => {
			months.forEach((month) => {
				if (accountData[month] !== undefined) {
					values.push(accountData[month]);
				}
			});
		});
		return values;
	});

	let minValue = $derived(Math.min(0, ...allValues));
	let maxValue = $derived(Math.max(...allValues));

	// Round to nice values
	let yMin = $derived(Math.floor(minValue / 1000) * 1000);
	let yMax = $derived(Math.ceil(maxValue / 1000) * 1000 || 1000);

	// Create tick values for y-axis
	let yTicks = $derived([yMin, yMin + (yMax - yMin) * 0.25, yMin + (yMax - yMin) * 0.5, yMin + (yMax - yMin) * 0.75, yMax]);

	// Set up scales
	let xScale = $derived(
		scalePoint<string>()
			.domain(months)
			.range([padding.left, width - padding.right])
	);

	let yScale = $derived(
		scaleLinear()
			.domain([yMin, yMax])
			.range([height - padding.bottom, padding.top])
	);

	// Generate path data for each account
	let accountEntries = $derived(Object.entries(data));

	function getPath(accountData: { [month: string]: number }): string {
		return months
			.map((month, i) => {
				const x = xScale(month) ?? 0;
				const y = yScale(accountData[month] ?? 0);
				return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
			})
			.join(' ');
	}
</script>

<div class="chart" bind:clientWidth={width}>
	<svg {width} {height}>
		<!-- Y-axis grid lines -->
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
						{formatAmount(tick)}
					</text>
				</g>
			{/each}
		</g>

		<!-- X-axis -->
		<g class="axis x-axis">
			{#each months as month, i}
				{#if i % Math.ceil(months.length / 8) === 0 || i === months.length - 1}
					<g class="tick" transform="translate({xScale(month)}, {height - padding.bottom + 15})">
						<text text-anchor="middle">
							{month}
						</text>
					</g>
				{/if}
			{/each}
		</g>

		<!-- Lines for each account -->
		{#each accountEntries as [_accountLabel, accountData], i}
			<path
				d={getPath(accountData)}
				fill="none"
				stroke={colors[i % colors.length]}
				stroke-width="2"
			/>
		{/each}

		<!-- Legend -->
		<g class="legend" transform="translate({width - padding.right + 10}, {padding.top})">
			{#each accountEntries as [accountLabel], i}
				<g transform="translate(0, {i * 20})">
					<rect width="12" height="12" fill={colors[i % colors.length]} rx="2" />
					<text x="16" y="10" font-size="10">{accountLabel}</text>
				</g>
			{/each}
		</g>

		<!-- Title -->
		<text x={width / 2} y={padding.top / 2} text-anchor="middle" font-size="14" font-weight="bold">
			Account Values Over Time
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

