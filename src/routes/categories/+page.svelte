<script>
	import CategoryForm from '$lib/components/category-form.svelte';

	import CategoryList from '$lib/components/category-list.svelte';
	import QuestionIcon from '$lib/components/ui/icons/question-icon.svelte';

	let prefix = $state('');
</script>

<!-- <CategoryForm /> -->
<div class="container max-w-lg mx-auto flex flex-col items-center gap-4">
	<CategoryForm bind:label={prefix} />
	<div class="max-w-sm w-full">
		<CategoryList {prefix} />
	</div>
</div>
