<script>
	import CategoryForm from '$lib/components/category-form.svelte';

	import CategoryList from '$lib/components/category-list.svelte';
	import TransactionForm from '$lib/components/transaction-form.svelte';
	import TransactionList from '$lib/components/transaction-list.svelte';
	import QuestionIcon from '$lib/components/ui/icons/question-icon.svelte';

	let prefix = $state('');
</script>

<!-- <CategoryForm /> -->
<div class="container max-w-lg mx-auto flex flex-col items-center gap-4">
	<TransactionForm bind:label={prefix} />
	<div class="max-w-sm w-full">
		<TransactionList {prefix} />
	</div>
</div>
