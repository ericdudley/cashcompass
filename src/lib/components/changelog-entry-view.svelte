<script lang="ts">
	import type { ChangelogEntry } from '$lib/changelog';

	let { entry }: { entry: ChangelogEntry } = $props();
</script>

<div>
	<div class="flex gap-2 items-center">
		<h3 class="text-xl font-bold">Version {entry.semver}</h3>
        <p class="text-sm text-gray-500">{entry.date}</p>
	</div>
	<p>{entry.releaseNotes}</p>
</div>
