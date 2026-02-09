<script>
	import TransactionForm from '$lib/components/transaction-form.svelte';
	import TransactionList from '$lib/components/transaction-list.svelte';
</script>

<div
	class="container max-w-4xl mx-auto flex flex-col md:flex-row md:flex-nowrap justify-center gap-6"
>
	<div class="flex-1 min-w-0">
		<TransactionForm />
	</div>
	<div class="flex-1 min-w-0">
		<TransactionList />
	</div>
</div>
