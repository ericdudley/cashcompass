<script lang="ts">
	import {
		format,
		subMonths,
		subYears,
		startOfYear,
		endOfYear,
		eachMonthOfInterval
	} from 'date-fns';

	let { startDate = $bindable(new Date()), endDate = $bindable(new Date()) } = $props<{
		startDate?: Date;
		endDate?: Date;
	}>();

	let startDateValue = $derived(format(startDate, 'yyyy-MM-dd'));
	let endDateValue = $derived(format(endDate, 'yyyy-MM-dd'));

	const presets: { label: string; range: () => [Date, Date] }[] = [
		{ label: 'Last 30 days', range: () => [subMonths(new Date(), 1), new Date()] },
		{ label: 'Last 3 months', range: () => [subMonths(new Date(), 3), new Date()] },
		{ label: 'This year', range: () => [startOfYear(new Date()), endOfYear(new Date())] },
		{
			label: 'Full months this year',
			range: () => {
				const yearStart = startOfYear(new Date());
				const yearEnd = endOfYear(new Date());
				return [eachMonthOfInterval({ start: yearStart, end: yearEnd })[0], yearEnd];
			}
		},
		{
			label: 'Last year',
			range: () => [startOfYear(subYears(new Date(), 1)), endOfYear(subYears(new Date(), 1))]
		},
		{ label: 'Last 5 years', range: () => [startOfYear(subYears(new Date(), 5)), new Date()] }
	];

	function selectPreset(range: () => [Date, Date]) {
		const [start, end] = range();
		startDate = start;
		endDate = end;
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex items-center gap-2">
		<input
			type="date"
			value={startDateValue}
			oninput={(e: Event) => {
				const input = (e.target as HTMLInputElement)?.value;
				startDate = input ? new Date(`${input}T00:00:00`) : new Date();
			}}
			class="input input-bordered w-full max-w-xs"
		/>

		<span class="px-2 text-base-content">to</span>
		<input
			type="date"
			value={endDateValue}
			oninput={(e: Event) => {
				const input = (e.target as HTMLInputElement)?.value;
				endDate = input ? new Date(`${input}T00:00:00`) : new Date();
			}}
			class="input input-bordered w-full max-w-xs"
		/>
	</div>

	<div class="flex flex-wrap gap-2">
		{#each presets as { label, range }}
			<button class="btn btn-outline btn-sm" onclick={() => selectPreset(range)}>
				{label}
			</button>
		{/each}
	</div>
</div>
