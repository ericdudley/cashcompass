<!-- DateInput.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { format, parseISO, addDays, subDays } from 'date-fns';
	import LeftIcon from './icons/left-icon.svelte';
	import RightIcon from './icons/right-icon.svelte';

	let {
		value = $bindable(''),
		autofocus,
		onkeydown
	}: {
		value: string | null;
		autofocus?: boolean;
		onkeydown?: (event: KeyboardEvent) => void;
	} = $props();

	let inputRef: HTMLInputElement | null = null;
	let dateString = $state('');
	let dateValue = $state<Date | null>(null);

	onMount(() => {
		syncFromProp();
		if (autofocus && inputRef) {
			inputRef.focus();
		}
	});

	$effect(() => {
		if (value) {
			const iso = dateValue?.toISOString() ?? '';
			if (iso !== value) {
				dateValue = parseISO(value);
				dateString = format(dateValue, 'yyyy-MM-dd');
			}
		} else if (dateValue) {
			dateValue = null;
			dateString = '';
		}
	});

	function syncFromProp() {
		if (value) {
			dateValue = parseISO(value);
			dateString = format(dateValue, 'yyyy-MM-dd');
		} else {
			dateString = '';
			dateValue = null;
		}
	}

	function onInput(e: Event) {
		dateString = (e.target as HTMLInputElement).value;
		if (dateString) {
			dateValue = parseISO(dateString);
			value = dateValue.toISOString();
		} else {
			dateValue = null;
			value = '';
		}
	}

	function adjustDate(days: number) {
		dateValue = dateValue ? addDays(dateValue, days) : addDays(new Date(), days);
		dateString = format(dateValue, 'yyyy-MM-dd');
		value = dateValue.toISOString();
	}

	function selectPastDay(daysAgo: number) {
		dateValue = subDays(new Date(), daysAgo);
		dateString = format(dateValue, 'yyyy-MM-dd');
		value = dateValue.toISOString();
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
