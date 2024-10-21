<script lang="ts">
	import { onMount } from 'svelte';
	import currency from 'currency.js';

	let {
		value = $bindable(0),
		currencyCode: _currencyCode
	}: { value: number | null; currencyCode?: string } = $props();
	let inputValue = $state<string>('');

	let currencySymbol = '$'; // default to USD TODO Support other currencies

	onMount(() => {
		// Format the initial value using currency.js
		if (value !== null) {
			inputValue = currency(value, { symbol: currencySymbol, precision: 2 }).format();
		} else {
			inputValue = '';
		}
	});

	function onInput(event: Event) {
		inputValue = (event.target as HTMLInputElement).value;

		// Parse the input using currency.js, ignoring non-numeric characters
		const parsedValue = currency(inputValue, { symbol: currencySymbol }).value;

		// Update value only if parsed value is valid
		if (!isNaN(parsedValue)) {
			value = parsedValue;
		} else {
			value = null;
		}
	}

	function onBlur() {
		// Format the value using currency.js when the input loses focus
		if (value !== null) {
			inputValue = currency(value, { symbol: currencySymbol, precision: 2 }).format();
		} else {
			inputValue = '';
		}
	}

	function onFocus() {
		// Show raw number on focus
		if (value !== null) {
			inputValue = value.toString();
		} else {
			inputValue = '';
		}
	}
</script>

<input
	class="input w-full input-bordered"
	type="text"
	bind:value={inputValue}
	oninput={onInput}
	onblur={onBlur}
	onfocus={onFocus}
/>
