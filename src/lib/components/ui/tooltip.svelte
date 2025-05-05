<script lang="ts">
	let { tip, children }: { tip: string; children: any } = $props();
</script>

<div class="tooltip" data-tip={tip}>
	{@render children()}
</div> 