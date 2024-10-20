<script lang="ts">
	import CategoryIcon from './ui/icons/category-icon.svelte';

	let { label = $bindable('') }: { label: string } = $props();
</script>

<div class="badge badge-info badge-sm flex items-center gap-1">
	<CategoryIcon />
	{label}
</div>
