<script>
	import TransactionForm from '$lib/components/transaction-form.svelte';
	import TransactionList from '$lib/components/transaction-list.svelte';
</script>

<div class="container max-w-4xl mx-auto flex flex-wrap justify-center gap-6">
	<div class="flex-1">
		<TransactionForm />
	</div>
	<div class="flex-1">
		<TransactionList />
	</div>
</div>
