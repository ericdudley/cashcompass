<script lang="ts">
	import AccountIcon from './ui/icons/account-icon.svelte';

	let { label = $bindable('') }: { label: string } = $props();
</script>

<div class="badge badge-sm flex items-center gap-1">
	<AccountIcon />
	{label}
</div>
