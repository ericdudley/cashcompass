<script>
	import AccountForm from '$lib/components/account-form.svelte';

	import AccountList from '$lib/components/account-list.svelte';

	let prefix = $state('');
</script>

<div class="container max-w-4xl mx-auto flex flex-wrap justify-center gap-4">
	<div class="flex-1">
		<AccountForm bind:label={prefix} />
	</div>
	<div class="flex-1">
		<AccountList {prefix} />
	</div>
</div>
