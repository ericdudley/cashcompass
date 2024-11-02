<!-- DateInput.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { format, parseISO, addDays, subDays } from 'date-fns';
	import LeftIcon from './icons/left-icon.svelte';
	import RightIcon from './icons/right-icon.svelte';

	// Props with default values and types
	let {
		value = $bindable(''),
		autofocus,
		onkeydown
	}: {
		value: string;
		autofocus?: boolean;
		onkeydown?: (event: KeyboardEvent) => void;
	} = $props();

	// Local state variables
	let dateString = $state('');
	let dateValue = $state<Date | null>(null);
	let inputRef: HTMLInputElement | null = null;

	// Initialize dateString and dateValue based on value
	onMount(() => {
		if (value) {
			dateValue = parseISO(value);
			dateString = value; // Since value is already in 'yyyy-MM-dd' format
		} else {
			dateString = '';
			dateValue = null;
		}

		// Focus the input if autofocus is true
		if (autofocus && inputRef) {
			inputRef.focus();
		}
	});

	// Handle input changes
	function onInput(event: Event) {
		dateString = (event.target as HTMLInputElement).value;
		if (dateString) {
			dateValue = parseISO(dateString);
			value = dateString;
		} else {
			dateValue = null;
			value = '';
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
		value = dateString;
	}

	// Select a specific past day
	function selectPastDay(daysAgo: number) {
		dateValue = subDays(new Date(), daysAgo);
		dateString = format(dateValue, 'yyyy-MM-dd');
		value = dateString;
	}
</script>

<div class="flex flex-col gap-1">
	<div class="input-group flex-nowrap flex items-center gap-1">
		<button type="button" class="btn btn-xs btn-square" onclick={() => adjustDate(-1)}>
			<LeftIcon />
		</button>
		<input
			bind:this={inputRef}
			type="date"
			class="input input-bordered input-sm"
			bind:value={dateString}
			oninput={onInput}
			{onkeydown}
		/>
		<button type="button" class="btn btn-xs btn-square" onclick={() => adjustDate(1)}>
			<RightIcon />
		</button>
	</div>
	<div class="flex gap-2 mt-2 flex-nowrap">
		{#snippet quickButton({ label, days }: { label: string; days: number })}
			<button type="button" class="btn btn-xs btn-outline" onclick={() => selectPastDay(days)}>
				{label}
			</button>
		{/snippet}
		{@render quickButton({ label: 'Today', days: 0 })}
		{@render quickButton({ label: 'Yesterday', days: 1 })}
		{@render quickButton({ label: '2 Days Ago', days: 2 })}
	</div>
</div>
