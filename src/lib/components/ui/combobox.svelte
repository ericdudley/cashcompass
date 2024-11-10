<script lang="ts">
	import { onMount } from 'svelte';
	import CheckIcon from './icons/check-icon.svelte';

	let {
		items,
		displayProperty,
		valueProperty,
		placeholder,
		required,
		value = $bindable(''),
		autofocus,
		onCreateItem,
		onkeydown
	} = $props<{
		items: {
			[key: string]: any;
		}[];
		displayProperty: string;
		valueProperty: string;
		placeholder: string;
		required: boolean;
		value: string;
		autofocus?: boolean;
		onkeydown?: (event: KeyboardEvent) => void;
		onCreateItem: (inputValue: string) => Promise<any>;
	}>();

	// Local state
	let isOpen = $state(false);
	let inputValue = $state('');
	let focusedIndex = $state(-1);
	let isCreatingItem = $state(false);

	// Declare a reference to the input element
	let inputRef: HTMLInputElement;

	onMount(() => {
		// Focus the input if autofocus is true
		if (autofocus && inputRef) {
			inputRef.focus();
		}
	});

	// Watch for changes in value to update inputValue
	$effect(() => {
		const selectedItem = items.find((item: any) => item[valueProperty] === value);
		if (selectedItem) {
			inputValue = selectedItem[displayProperty];
		}
	});

	// Filtered items based on input
	const filteredItems = $derived.by(() => {
		const matchingItems = items.filter((item: any) =>
			item[displayProperty].toLowerCase().includes(inputValue.toLowerCase())
		);
		const nonMatchingItems = items.filter(
			(item: any) => !item[displayProperty].toLowerCase().includes(inputValue.toLowerCase())
		);
		return [...matchingItems, ...nonMatchingItems];
	});

	// Handle input changes
	function onInput(event: Event) {
		inputValue = (event.target as HTMLInputElement).value;
		const matchingItem = items.find(
			(item: any) => item[displayProperty].toLowerCase() === inputValue.toLowerCase()
		);
		value = matchingItem ? matchingItem[valueProperty] : '';
		focusedIndex = -1; // Reset focused index when input changes
		isOpen = true; // Open dropdown when typing
	}

	function onBlur() {
		// Delay closing to allow click events to register
		setTimeout(() => {
			isOpen = false;
			focusedIndex = -1;
		}, 100);
	}

	function onFocus() {
		isOpen = true;
	}

	// Handle selection from the dropdown
	function selectItem(item: any) {
		inputValue = item[displayProperty];
		value = item[valueProperty];
		isOpen = false;
		focusedIndex = -1;
	}

	// Handle keydown events for keyboard navigation
	function onKeyDown(event: KeyboardEvent) {
		if (!isOpen) return;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			if (focusedIndex < filteredItems.length - 1) {
				focusedIndex += 1;
			} else {
				focusedIndex = 0;
			}
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			if (focusedIndex > 0) {
				focusedIndex -= 1;
			} else {
				focusedIndex = filteredItems.length - 1;
			}
		} else if (event.key === 'Enter') {
			event.preventDefault();
			if (focusedIndex >= 0 && focusedIndex < filteredItems.length) {
				selectItem(filteredItems[focusedIndex]);
			} else if (
				inputValue.trim() !== '' &&
				items.find((item: any) => item[displayProperty] === inputValue)
			) {
				isOpen = false;
			} else {
				confirmAndCreateItem();
			}
		} else if (event.key === 'Escape') {
			isOpen = false;
			focusedIndex = -1;
		}

		if (onkeydown) {
			onkeydown(event);
		}
	}

	// Function to handle submission if the item doesn't exist
	async function confirmAndCreateItem() {
		const existingItem = items.find(
			(item: any) => item[displayProperty].toLowerCase() === inputValue.toLowerCase()
		);

		if (!existingItem && inputValue.trim() !== '') {
			const confirmed = window.confirm(
				`The ${displayProperty} "${inputValue}" does not exist. Do you want to create it?`
			);
			if (confirmed) {
				try {
					isCreatingItem = true;
					const newItem = await onCreateItem(inputValue);
					value = newItem[valueProperty];
				} finally {
					isCreatingItem = false;
				}
			} else {
				// Reset input and value if user cancels
				inputValue = '';
				value = '';
			}
		}
	}
</script>

<div class="relative">
	<input
		type="text"
		class="input input-bordered w-full input-sm"
		{placeholder}
		bind:value={inputValue}
		oninput={onInput}
		onfocus={onFocus}
		onblur={onBlur}
		onkeydown={onKeyDown}
		aria-expanded={isOpen}
		aria-autocomplete="list"
		aria-controls="combobox-listbox"
		role="combobox"
		{required}
		bind:this={inputRef}
	/>
	{#if isCreatingItem}
		<div
			class="absolute top-0 right-0 flex items-center transform translate-y-[calc(-100%-0.5rem)] translate-x-[-5%] gap-2 z-[100]"
		>
			<div class="loading-spinner loading w-4 h-4"></div>
			<span class="text-xs font-medium text-neutral-500">Creating...</span>
		</div>
	{/if}
	{#if isOpen}
		<ul
			id="combobox-listbox"
			class="absolute z-10 bg-base-100 border border-neutral w-full mt-1 max-h-60 overflow-auto shadow-lg"
			role="listbox"
		>
			{#if filteredItems.length > 0}
				{#each filteredItems as item, index}
					<li
						class="p-2 cursor-pointer flex items-center gap-2 {focusedIndex === index
							? 'bg-base-200'
							: 'hover:bg-base-200'}"
						onmousedown={() => selectItem(item)}
						role="option"
						aria-selected={focusedIndex === index}
						tabindex="-1"
					>
						{#if value === item[valueProperty]}
							<CheckIcon />
						{/if}
						{item[displayProperty]}
					</li>
				{/each}
			{:else}
				<li class="p-2 text-gray-500" role="option" tabindex="-1" aria-selected="false">
					No results found (press Enter to create)
				</li>
			{/if}
		</ul>
	{/if}
</div>
