<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';
	import type { Category } from '$lib/dexie/models/category';

	const dispatch = createEventDispatcher();

	let { selectedCategoryId = $bindable('') }: { selectedCategoryId: string } = $props();

	const db = getDbContext();

	// Fetch categories from the database
	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	// Local state
	let isOpen = $state(false);
	let inputValue = $state('');
	let focusedIndex = $state(-1); // For keyboard navigation

	// Filtered categories based on input
	const filteredCategories = $derived.by(() => {
		const query = inputValue.toLowerCase();
		return ($categories ?? []).filter((category) => category.label.toLowerCase().includes(query));
	});

	// Handle input changes
	function onInput(event: Event) {
		inputValue = (event.target as HTMLInputElement).value;
		const matchingCategory = $categories?.find(
			(c) => c.label.toLowerCase() === inputValue.toLowerCase()
		);
		selectedCategoryId = matchingCategory ? matchingCategory.id : '';
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
	function selectCategory(category: Category) {
		inputValue = category.label;
		selectedCategoryId = category.id;
		isOpen = false;
		focusedIndex = -1;
	}

	// Handle keydown events for keyboard navigation
	function onKeyDown(event: KeyboardEvent) {
		if (!isOpen) return;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			if (focusedIndex < filteredCategories.length - 1) {
				focusedIndex += 1;
			} else {
				focusedIndex = 0;
			}
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			if (focusedIndex > 0) {
				focusedIndex -= 1;
			} else {
				focusedIndex = filteredCategories.length - 1;
			}
		} else if (event.key === 'Enter') {
			event.preventDefault();
			if (focusedIndex >= 0 && focusedIndex < filteredCategories.length) {
				selectCategory(filteredCategories[focusedIndex]);
			} else {
				confirmAndCreateCategory();
			}
		} else if (event.key === 'Escape') {
			isOpen = false;
			focusedIndex = -1;
		}
	}

	// Function to handle submission if the category doesn't exist
	async function confirmAndCreateCategory() {
		const existingCategory = $categories?.find(
			(c) => c.label.toLowerCase() === inputValue.toLowerCase()
		);

		if (!existingCategory && inputValue.trim() !== '') {
			const confirmed = window.confirm(
				`The category "${inputValue}" does not exist. Do you want to create it?`
			);
			if (confirmed) {
				const newCategory = {
					id: crypto.randomUUID(),
					label: inputValue
				};
				await db.category.add(newCategory);
				selectedCategoryId = newCategory.id;
				dispatch('categoryCreated', newCategory);
				isOpen = false;
			} else {
				// Reset input and selectedCategoryId if user cancels
				inputValue = '';
				selectedCategoryId = '';
			}
		}
	}
</script>

<div class="relative">
	<input
		type="text"
		class="input input-bordered w-full"
		placeholder="Select or type a category"
		value={inputValue}
		oninput={onInput}
		onfocus={onFocus}
		onblur={onBlur}
		onkeydown={onKeyDown}
		aria-expanded={isOpen}
		aria-autocomplete="list"
		aria-controls="category-listbox"
		role="combobox"
		required
	/>
	{#if isOpen}
		<ul
			id="category-listbox"
			class="absolute z-10 bg-base-100 border border-neutral w-full mt-1 max-h-60 overflow-auto shadow-lg"
			role="listbox"
		>
			{#if filteredCategories.length > 0}
				{#each filteredCategories as category, index}
					<li
						class="p-2 cursor-pointer {focusedIndex === index
							? 'bg-base-200'
							: 'hover:bg-base-200'}"
						onmousedown={() => selectCategory(category)}
						role="option"
						aria-selected={focusedIndex === index}
						tabindex="-1"
					>
						{category.label}
					</li>
				{/each}
			{:else}
				<li class="p-2 text-gray-500" role="option" tabindex="-1">No results found</li>
			{/if}
		</ul>
	{/if}
</div>
