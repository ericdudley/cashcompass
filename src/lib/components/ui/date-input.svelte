<!-- DateInput.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { format, parseISO, addDays, subDays } from 'date-fns';

	// Props with default values and types
	let { unixMs = $bindable(null) }: { unixMs: number | null } = $props();

	// Local state variables
	let dateString = $state('');
	let dateValue = $state<Date | null>(null);

	// Initialize dateString and dateValue based on unixMs
	onMount(() => {
		if (unixMs !== null) {
			dateValue = new Date(unixMs);
			dateString = format(dateValue, 'yyyy-MM-dd');
		} else {
			dateString = '';
			dateValue = null;
		}
	});

	// Handle input changes
	function onInput(event: Event) {
		dateString = (event.target as HTMLInputElement).value;
		if (dateString) {
			dateValue = parseISO(dateString);
			unixMs = dateValue.getTime();
		} else {
			dateValue = null;
			unixMs = null;
		}
	}

	// Adjust the date by a certain number of days
	function adjustDate(days: number) {
		if (dateValue) {
			dateValue = addDays(dateValue, days);
		} else {
			dateValue = addDays(new Date(), days);
		}
		dateString = format(dateValue, 'yyyy-MM-dd');
		unixMs = dateValue.getTime();
	}

	// Select a specific past day
	function selectPastDay(daysAgo: number) {
		dateValue = subDays(new Date(), daysAgo);
		dateString = format(dateValue, 'yyyy-MM-dd');
		unixMs = dateValue.getTime();
	}
</script>

<div class="input-group">
	<button type="button" class="btn" onclick={() => adjustDate(-1)}>&lt;</button>
	<input type="date" class="input input-bordered" value={dateString} oninput={onInput} />
	<button type="button" class="btn" onclick={() => adjustDate(1)}>&gt;</button>
</div>
<div class="flex gap-2 mt-2">
	{#snippet quickButton({ label, days }: { label: string; days: number })}
		<button type="button" class="btn btn-xs btn-outline" onclick={() => selectPastDay(days)}>
			{label}
		</button>
	{/snippet}
	{@render quickButton({ label: 'Today', days: 0 })}
	{@render quickButton({ label: 'Yesterday', days: 1 })}
	{@render quickButton({ label: '2 Days Ago', days: 2 })}
</div>
