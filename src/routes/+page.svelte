<script>
	import CategoryForm from '$lib/components/category-form.svelte';
	import CategoryList from '$lib/components/category-list.svelte';

	let prefix = $state('');
</script>

<div>
	<h1>Friends</h1>

	<input type="text" bind:value={prefix} />

	<CategoryList prefix={prefix} />
	<CategoryForm />
</div>
