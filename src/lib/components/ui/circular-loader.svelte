<script lang="ts">
	let { size, isAbsolute, class: className }: { size?: number; isAbsolute?: boolean, class?: string } = $props();

	let sizeClass = $derived(size ? `h-${size} w-${size}` : 'h-6 w-6');
</script>

<div
	class="loading loading-spinner {sizeClass} {isAbsolute || isAbsolute == null ? 'absolute' : ''} {className}"
></div>
