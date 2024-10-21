<script>
	import TransactionForm from '$lib/components/transaction-form.svelte';
	import TransactionList from '$lib/components/transaction-list.svelte';

	let prefix = $state('');
</script>

<div class="container max-w-4xl mx-auto flex flex-wrap justify-center gap-4">
	<div class="flex-1">
		<TransactionForm bind:label={prefix} />
	</div>
	<div class="flex-1">
		<TransactionList {prefix} />
	</div>
</div>
