<script>
	import CategoryForm from '$lib/components/category-form.svelte';

	import CategoryList from '$lib/components/category-list.svelte';

	let prefix = $state('');
</script>

<div class="container max-w-4xl mx-auto flex flex-wrap justify-center gap-4">
	<div class="flex-1">
		<CategoryForm bind:label={prefix} />
	</div>
	<div class="flex-1">
		<CategoryList {prefix} />
	</div>
</div>
