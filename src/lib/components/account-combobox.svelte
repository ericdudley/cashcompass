<script lang="ts">
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';
	import ComboBox from './ui/combobox.svelte';

	let {
		value = $bindable(''),
		autofocus,
		onkeydown
	} = $props<{
		value: string;
		autofocus?: boolean;
		onkeydown?: (event: KeyboardEvent) => void;
	}>();

	const db = getDbContext();

	const accounts = $derived.by(() => {
		return liveQuery(() => db.account.toArray());
	});

	console.log($accounts);
</script>

<div class="form-control">
	<ComboBox
		bind:value
		onCreateItem={async () => {
			return {};
		}}
		items={$accounts ? $accounts : []}
		displayProperty="label"
		valueProperty="id"
		placeholder="Select an account"
		required
		{autofocus}
		{onkeydown}
	/>
</div>
