<script>
	import CategoryForm from '$lib/components/category-form.svelte';

	import CategoryList from '$lib/components/category-list.svelte';

	let prefix = $state('');
</script>

<div class="container max-w-lg mx-auto flex flex-col items-center gap-6">
	<CategoryForm bind:label={prefix} />
	<div class="max-w-sm w-full">
		<CategoryList {prefix} />
	</div>
</div>
