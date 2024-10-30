<script lang="ts">
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';
	import ComboBox from './ui/combobox.svelte';

	let { value = $bindable(''), autofocus, onkeydown } = $props<{
		value: string;
		autofocus?: boolean;
        onkeydown?: (event: KeyboardEvent) => void;
	}>();

	const db = getDbContext();

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});
</script>

<div class="form-control">
	<ComboBox
		bind:value
		onCreateItem={async () => {
			return {};
		}}
		items={$categories ? $categories : []}
		displayProperty="label"
		valueProperty="id"
		placeholder="Select a category"
		required
		{autofocus}
        {onkeydown}
	/>
</div>
